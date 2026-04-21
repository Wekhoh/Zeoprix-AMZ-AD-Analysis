"""Excel 数据迁移 API"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.import_result import ImportResult

router = APIRouter()


@router.post("/from-excel", response_model=ImportResult)
async def migrate_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """从 Excel 迁移历史数据到 SQLite（一次性操作）"""
    from backend.services.migration_service import migrate_excel_to_db

    return await migrate_excel_to_db(db, file)
