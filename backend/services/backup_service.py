"""数据库备份服务"""

import shutil
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.system import Backup


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

    path = Path(record.file_path)
    if path.exists():
        path.unlink()

    db.delete(record)
    db.commit()
    return True


def _cleanup_old_backups(db: Session):
    """保留最近 MAX_BACKUPS 个备份，清理更早的"""
    backups = db.query(Backup).order_by(Backup.created_at.desc()).all()
    if len(backups) <= settings.MAX_BACKUPS:
        return

    for old in backups[settings.MAX_BACKUPS :]:
        path = Path(old.file_path)
        if path.exists():
            path.unlink(missing_ok=True)
        db.delete(old)

    db.commit()
