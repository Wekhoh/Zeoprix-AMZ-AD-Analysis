"""智能建议 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.analysis_service import generate_suggestions

router = APIRouter()


@router.get("/suggestions")
def get_suggestions(db: Session = Depends(get_db)):
    """获取智能优化建议"""
    return generate_suggestions(db)
