"""数据库备份服务"""

import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import engine
from backend.logging_config import get_logger
from backend.models.system import Backup

logger = get_logger("backup_service")


def _validate_backup_path(file_path: str) -> Path | None:
    """Verify a stored Backup.file_path points inside settings.BACKUP_DIR.

    Defends against tampered Backup records (e.g. a malicious insert
    pointing at ``/etc/passwd`` or ``C:\\Windows\\System32\\config\\SAM``)
    where ``delete_backup`` or ``restore_backup`` would otherwise act on
    arbitrary files. Logs and returns None on any violation so callers
    can refuse the operation cleanly instead of raising to the client.
    """
    try:
        path = Path(file_path).resolve()
    except (OSError, ValueError):
        logger.warning("backup path resolve failed: %r", file_path)
        return None

    backup_dir = settings.BACKUP_DIR.resolve()
    if not path.is_relative_to(backup_dir):
        logger.warning(
            "SECURITY: refusing backup op on path outside BACKUP_DIR. Got %r, expected under %r",
            file_path,
            str(backup_dir),
        )
        return None
    return path


def create_backup(db: Session, backup_type: str = "manual") -> dict:
    """创建数据库备份"""
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    src = settings.DATA_DIR / "tracker.db"
    if not src.exists():
        return {"error": "数据库文件不存在"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = settings.BACKUP_DIR / f"tracker_backup_{timestamp}.db"
    shutil.copy2(src, dest)

    file_size = dest.stat().st_size

    record = Backup(
        file_path=str(dest),
        file_size=file_size,
        backup_type=backup_type,
    )
    db.add(record)
    db.commit()

    _cleanup_old_backups(db)

    return {
        "id": record.id,
        "file_path": str(dest.name),
        "file_size": file_size,
        "backup_type": backup_type,
        "created_at": str(record.created_at),
    }


def list_backups(db: Session) -> list[dict]:
    """列出所有备份"""
    backups = db.query(Backup).order_by(Backup.created_at.desc()).all()
    return [
        {
            "id": b.id,
            "file_path": Path(b.file_path).name,
            "file_size": b.file_size,
            "backup_type": b.backup_type,
            "created_at": str(b.created_at),
        }
        for b in backups
    ]


def delete_backup(db: Session, backup_id: int) -> bool:
    """删除指定备份"""
    record = db.query(Backup).filter_by(id=backup_id).first()
    if not record:
        return False

    # Security: verify the stored path is inside BACKUP_DIR before unlinking.
    # A tampered Backup row could otherwise delete arbitrary files.
    path = _validate_backup_path(record.file_path)
    if path is None:
        # Remove the tampered record but do NOT touch the filesystem
        db.delete(record)
        db.commit()
        return False

    if path.exists():
        path.unlink()

    db.delete(record)
    db.commit()
    return True


def verify_backup(backup_path: str) -> dict:
    """Verify backup integrity using PRAGMA integrity_check"""
    import sqlite3

    conn = sqlite3.connect(backup_path)
    result = conn.execute("PRAGMA integrity_check").fetchone()
    conn.close()
    ok = result[0] == "ok"
    return {"path": backup_path, "integrity": result[0], "ok": ok}


def restore_backup(db: Session, backup_id: int) -> dict:
    """Restore from a backup: safety backup current, then copy backup over"""
    record = db.query(Backup).filter_by(id=backup_id).first()
    if not record:
        return {"error": "Backup not found"}

    # Security: verify the stored path is inside BACKUP_DIR before reading
    # it into the live database. A tampered Backup row could otherwise
    # clobber the live db with arbitrary file contents.
    backup_path = _validate_backup_path(record.file_path)
    if backup_path is None:
        return {"error": "Backup path failed security validation"}

    if not backup_path.exists():
        return {"error": "Backup file missing"}

    db_path = settings.DATA_DIR / "tracker.db"

    # Safety backup before restore
    safety = create_backup(db, backup_type="pre_restore")

    # Close session AND dispose engine pool to release all connections
    db.close()
    engine.dispose()
    shutil.copy2(backup_path, db_path)

    return {
        "restored_from": str(backup_path.name),
        "safety_backup": safety.get("file_path", ""),
        "note": "请重启应用以确保数据库连接刷新",
    }


def _cleanup_old_backups(db: Session):
    """保留最近 MAX_BACKUPS 个备份，清理更早的"""
    backups = db.query(Backup).order_by(Backup.created_at.desc()).all()
    if len(backups) <= settings.MAX_BACKUPS:
        return

    for old in backups[settings.MAX_BACKUPS :]:
        # Security: validate path before unlinking a tampered record
        path = _validate_backup_path(old.file_path)
        if path is not None and path.exists():
            path.unlink(missing_ok=True)
        db.delete(old)

    db.commit()
