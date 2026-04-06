"""备份管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.logging_config import get_logger
from backend.services.backup_service import (
    create_backup,
    list_backups,
    delete_backup,
    restore_backup,
)

router = APIRouter()
logger = get_logger("settings")


@router.post("/backups")
def create_backup_endpoint(db: Session = Depends(get_db)):
    """创建手动备份"""
    return create_backup(db, backup_type="manual")


@router.get("/backups")
def list_backups_endpoint(db: Session = Depends(get_db)):
    """列出所有备份"""
    return list_backups(db)


@router.delete("/backups/{backup_id}")
def delete_backup_endpoint(backup_id: int, db: Session = Depends(get_db)):
    """删除指定备份"""
    if not delete_backup(db, backup_id):
        raise HTTPException(status_code=404, detail="备份不存在")
    logger.warning(f"DESTRUCTIVE: backup {backup_id} deleted")
    return {"success": True}


@router.post("/backups/{backup_id}/restore")
def restore_backup_endpoint(backup_id: int, db: Session = Depends(get_db)):
    """Restore database from a backup"""
    result = restore_backup(db, backup_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
