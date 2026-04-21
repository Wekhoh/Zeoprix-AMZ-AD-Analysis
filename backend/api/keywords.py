"""关键词管理 API — Ad Group / Keyword 层级查询 + 导入"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.keyword_service import (
    get_ad_groups_for_campaign,
    get_keyword_history,
    get_keywords_for_ad_group,
    import_keyword_report,
)
from backend.utils.encoding_helper import decode_with_fallback

router = APIRouter()


@router.get("/campaigns/{campaign_id}/ad-groups")
def list_ad_groups(campaign_id: int, db: Session = Depends(get_db)):
    """列出广告活动下的广告组（含关键词数 + 聚合 KPI）"""
    return get_ad_groups_for_campaign(db, campaign_id)


@router.get("/ad-groups/{ad_group_id}/keywords")
def list_keywords(ad_group_id: int, db: Session = Depends(get_db)):
    """列出广告组下的关键词（含聚合 KPI）"""
    return get_keywords_for_ad_group(db, ad_group_id)


@router.get("/keywords/{keyword_id}/history")
def keyword_history(
    keyword_id: int,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取单个关键词的日趋势数据"""
    return get_keyword_history(db, keyword_id, date_from, date_to)


@router.post("/keywords/import")
async def import_keywords_csv(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """导入 Amazon SP Keyword Performance Report CSV"""
    total = {
        "imported_keywords": 0,
        "updated_keywords": 0,
        "imported_daily": 0,
        "updated_daily": 0,
        "skipped": 0,
    }
    details: list[dict] = []

    for f in files:
        raw = await f.read()
        content = decode_with_fallback(raw) or ""

        if not content:
            details.append({"file": f.filename, "error": "encoding"})
            continue

        result = import_keyword_report(db, content, f.filename or "")
        for key in total:
            total[key] += result.get(key, 0)
        details.append({"file": f.filename, **result})

    return {**total, "details": details}
