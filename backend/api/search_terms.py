"""搜索词分析 API"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.search_term_service import (
    import_search_terms,
    get_search_term_summary,
    get_top_converting_terms,
    classify_search_terms_4bucket,
    get_negative_candidates,
)

router = APIRouter()


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
    return get_search_term_summary(db, campaign_id)


@router.get("/top-converting")
def top_converting(
    min_orders: int = Query(1),
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """高转化搜索词"""
    return get_top_converting_terms(db, min_orders, campaign_id)


@router.get("/negative-candidates")
def negative_candidates(
    min_clicks: int = Query(5),
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """否定词候选"""
    return get_negative_candidates(db, min_clicks, campaign_id)


@router.get("/buckets")
def search_term_buckets(
    campaign_id: Optional[int] = Query(None),
    target_acos: float = Query(0.30),
    db: Session = Depends(get_db),
):
    """4-Bucket 搜索词分析"""
    return classify_search_terms_4bucket(db, campaign_id, target_acos)
