"""数据导入 API"""

from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.import_result import ImportResult

router = APIRouter()


@router.post("/placement-csv", response_model=ImportResult)
async def import_placement_csv(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """导入展示位置 CSV 文件"""
    from backend.services.import_service import process_placement_csv_upload

    return await process_placement_csv_upload(db, files)


@router.post("/operation-log", response_model=ImportResult)
async def import_operation_log(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """导入操作日志 TXT 文件"""
    from backend.services.import_service import process_operation_log_upload

    return await process_operation_log_upload(db, files)


@router.post("/preview")
async def preview_import(files: list[UploadFile] = File(...)):
    """Preview CSV data without importing"""
    from backend.services.import_service import preview_csv_upload

    return await preview_csv_upload(files)
