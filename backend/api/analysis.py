"""智能建议 API"""

from datetime import date, timedelta
from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import SuggestionStatus
from backend.services.analysis_service import generate_suggestions

router = APIRouter()


class SuggestionResolve(BaseModel):
    hash: str
    campaign_id: Optional[int] = None
    suggestion_type: str
    action: Literal["resolved", "dismissed", "snoozed"]
    snooze_days: Optional[int] = 7
    notes: Optional[str] = None


@router.get("/suggestions")
def get_suggestions(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取智能优化建议（可选日期范围）"""
    return generate_suggestions(db, date_from, date_to)


@router.post("/suggestions/resolve")
def resolve_suggestion(body: SuggestionResolve, db: Session = Depends(get_db)):
    """标记建议为已处理/忽略/延后 (action validated by Pydantic Literal)"""
    snooze_until = None
    if body.action == "snoozed":
        days = body.snooze_days or 7
        snooze_until = (date.today() + timedelta(days=days)).isoformat()

    # Upsert by hash
    existing = (
        db.query(SuggestionStatus).filter(SuggestionStatus.suggestion_hash == body.hash).first()
    )
    if existing:
        existing.status = body.action
        existing.snooze_until = snooze_until
        existing.notes = body.notes
    else:
        db.add(
            SuggestionStatus(
                suggestion_hash=body.hash,
                campaign_id=body.campaign_id,
                suggestion_type=body.suggestion_type,
                status=body.action,
                snooze_until=snooze_until,
                notes=body.notes,
            )
        )
    db.commit()
    return {"success": True, "hash": body.hash, "action": body.action}


@router.delete("/suggestions/resolve/{suggestion_hash}")
def clear_suggestion_status(suggestion_hash: str, db: Session = Depends(get_db)):
    """撤销建议的已处理/延后状态"""
    row = (
        db.query(SuggestionStatus)
        .filter(SuggestionStatus.suggestion_hash == suggestion_hash)
        .first()
    )
    if row:
        db.delete(row)
        db.commit()
    return {"success": True}
