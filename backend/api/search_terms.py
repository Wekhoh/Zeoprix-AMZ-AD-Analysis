"""搜索词分析 API"""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Campaign, KeywordAction, NegativeWhitelist
from backend.services.search_term_service import (
    classify_search_terms_4bucket,
    get_negative_candidates,
    get_search_term_summary,
    get_top_converting_terms,
    import_search_terms,
)

router = APIRouter()


def _validate_campaign_id(db: Session, campaign_id: int | None) -> None:
    """Raise 404 if campaign_id is provided but does not exist."""
    if campaign_id is not None:
        if not db.query(Campaign).filter(Campaign.id == campaign_id).first():
            raise HTTPException(status_code=404, detail="Campaign not found")


@router.post("/import")
async def import_search_term_csv(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """导入搜索词报告 CSV"""
    total_imported = 0
    total_skipped = 0
    details = []

    for file in files:
        raw = await file.read()
        for enc in ["utf-8-sig", "utf-8", "gbk", "gb2312"]:
            try:
                content = raw.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            details.append({"file": file.filename, "error": "encoding"})
            continue

        result = import_search_terms(db, content, file.filename or "")
        total_imported += result.get("imported", 0)
        total_skipped += result.get("skipped", 0)
        details.append({"file": file.filename, **result})

    return {"imported": total_imported, "skipped": total_skipped, "details": details}


@router.get("/summary")
def search_term_summary(
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """搜索词汇总"""
    _validate_campaign_id(db, campaign_id)
    return get_search_term_summary(db, campaign_id)


@router.get("/top-converting")
def top_converting(
    min_orders: int = Query(1),
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """高转化搜索词"""
    _validate_campaign_id(db, campaign_id)
    return get_top_converting_terms(db, min_orders, campaign_id)


@router.get("/negative-candidates")
def negative_candidates(
    min_clicks: int = Query(5),
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """否定词候选"""
    _validate_campaign_id(db, campaign_id)
    return get_negative_candidates(db, min_clicks, campaign_id)


@router.get("/buckets")
def search_term_buckets(
    campaign_id: Optional[int] = Query(None),
    target_acos: float = Query(0.30),
    db: Session = Depends(get_db),
):
    """4-Bucket 搜索词分析"""
    _validate_campaign_id(db, campaign_id)
    return classify_search_terms_4bucket(db, campaign_id, target_acos)


# === 搜索词处理记录 ===


class KeywordActionCreate(BaseModel):
    search_term: str
    from_campaign_id: Optional[int] = None
    from_campaign_name: Optional[str] = None
    action_type: str
    target_bid: Optional[float] = None
    notes: Optional[str] = None


@router.get("/actions")
def list_keyword_actions(db: Session = Depends(get_db)):
    """获取所有搜索词处理记录"""
    records = db.query(KeywordAction).order_by(KeywordAction.created_at.desc()).limit(200).all()
    return [
        {
            "id": r.id,
            "search_term": r.search_term,
            "from_campaign_id": r.from_campaign_id,
            "from_campaign_name": r.from_campaign_name,
            "action_type": r.action_type,
            "target_bid": r.target_bid,
            "notes": r.notes,
            "created_at": str(r.created_at) if r.created_at else None,
        }
        for r in records
    ]


@router.post("/actions")
def create_keyword_action(body: KeywordActionCreate, db: Session = Depends(get_db)):
    """记录搜索词处理操作（harvest/negate）"""
    record = KeywordAction(
        search_term=body.search_term,
        from_campaign_id=body.from_campaign_id,
        from_campaign_name=body.from_campaign_name,
        action_type=body.action_type,
        target_bid=body.target_bid,
        notes=body.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "search_term": record.search_term}


@router.get("/processed-terms")
def get_processed_terms(db: Session = Depends(get_db)):
    """获取已处理搜索词集合（用于前端标记）"""
    rows = db.query(KeywordAction.search_term, KeywordAction.action_type).all()
    result: dict[str, str] = {}
    for term, action in rows:
        result[term] = action
    return result


# ============================================================
# Never-Negative Whitelist CRUD
# ============================================================


class WhitelistAddBody(BaseModel):
    """Body for adding one or more terms to the whitelist."""

    terms: list[str]
    reason: str | None = None


@router.get("/whitelist")
def list_whitelist(db: Session = Depends(get_db)):
    """列出所有白名单搜索词"""
    rows = db.query(NegativeWhitelist).order_by(NegativeWhitelist.search_term).all()
    return [
        {
            "id": r.id,
            "search_term": r.search_term,
            "reason": r.reason,
            "created_at": str(r.created_at) if r.created_at else None,
        }
        for r in rows
    ]


@router.post("/whitelist")
def add_to_whitelist(body: WhitelistAddBody, db: Session = Depends(get_db)):
    """批量添加搜索词到白名单。已存在的词自动跳过。"""
    added = 0
    skipped = 0
    for term in body.terms:
        term = term.strip()
        if not term:
            continue
        existing = db.query(NegativeWhitelist).filter(NegativeWhitelist.search_term == term).first()
        if existing:
            skipped += 1
            continue
        db.add(NegativeWhitelist(search_term=term, reason=body.reason))
        added += 1
    db.commit()
    return {"added": added, "skipped": skipped}


@router.delete("/whitelist/{item_id}")
def remove_from_whitelist(item_id: int, db: Session = Depends(get_db)):
    """从白名单移除指定条目"""
    record = db.query(NegativeWhitelist).filter_by(id=item_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="白名单条目不存在")
    db.delete(record)
    db.commit()
    return {"success": True, "removed": record.search_term}
