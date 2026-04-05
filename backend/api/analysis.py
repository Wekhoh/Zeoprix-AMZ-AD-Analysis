"""智能建议 API"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.analysis_service import generate_suggestions

router = APIRouter()


@router.get("/suggestions")
def get_suggestions(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取智能优化建议（可选日期范围）"""
    return generate_suggestions(db, date_from, date_to)
