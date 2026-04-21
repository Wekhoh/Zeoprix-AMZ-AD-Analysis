"""报告导出 API"""

from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.middleware import validate_date_param
from backend.services.report_service import generate_excel_report

router = APIRouter()

EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_CONTENT_TYPE = "application/pdf"


@router.get("/excel")
def export_excel(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """导出 Excel 报告"""
    validate_date_param(date_from, "date_from")
    validate_date_param(date_to, "date_to")

    file_bytes = generate_excel_report(db, date_from, date_to)

    filename = "ad-report"
    if date_from:
        filename += f"_{date_from}"
    if date_to:
        filename += f"_{date_to}"
    filename += ".xlsx"

    return StreamingResponse(
        BytesIO(file_bytes),
        media_type=EXCEL_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf")
def export_pdf(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """导出 PDF 摘要报告（打印友好格式）"""
    validate_date_param(date_from, "date_from")
    validate_date_param(date_to, "date_to")

    try:
        from backend.services.pdf_report_service import generate_pdf_report
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF 生成依赖未安装。请运行 pip install reportlab。详情: {e}",
        )

    file_bytes = generate_pdf_report(db, date_from, date_to)

    filename = "ad-report"
    if date_from:
        filename += f"_{date_from}"
    if date_to:
        filename += f"_{date_to}"
    filename += ".pdf"

    return StreamingResponse(
        BytesIO(file_bytes),
        media_type=PDF_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
