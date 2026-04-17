"""数据导入 API"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.import_result import ImportResult
from backend.utils.csv_type_detector import detect_csv_type
from backend.utils.encoding_helper import decode_with_fallback

router = APIRouter()


@router.post("/auto-detect")
async def auto_detect_files(files: list[UploadFile] = File(...)):
    """Classify each uploaded file by column signature.

    The frontend batch-upload flow POSTs all dropped files here first, then
    dispatches each to the right typed endpoint based on the returned
    `csv_type`. This keeps the detection logic out of the UI and lets us
    evolve signatures without a frontend release.

    Returns: ``{"files": [{"filename": str, "csv_type": str, "error": str?}]}``
    """
    results: list[dict] = []
    for f in files:
        try:
            raw = await f.read()
        except Exception as exc:
            results.append(
                {
                    "filename": f.filename,
                    "csv_type": "unknown",
                    "error": f"read failed: {exc}",
                }
            )
            continue

        content = decode_with_fallback(raw) or ""
        if not content:
            results.append(
                {
                    "filename": f.filename,
                    "csv_type": "unknown",
                    "error": "cannot decode (unsupported encoding)",
                }
            )
            continue

        csv_type = detect_csv_type(content, f.filename)
        row: dict = {"filename": f.filename, "csv_type": csv_type}
        if csv_type == "unknown":
            row["error"] = "unrecognized file type"
        results.append(row)

    return {"files": results}


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
async def preview_import(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Preview CSV data without importing"""
    from backend.services.import_service import preview_csv_upload

    return await preview_csv_upload(files, db)
