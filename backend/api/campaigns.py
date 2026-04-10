"""广告活动 API"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import (
    Campaign,
    AdGroup,
    PlacementRecord,
    CampaignDailyRecord,
    AdGroupDailyRecord,
)
from backend.schemas.campaign import CampaignOut, CampaignDetail
from backend.services.summary_service import summary_by_campaign
from backend.services.kpi_calculator import calc_ctr, calc_cpc, calc_roas, calc_acos, calc_cvr

router = APIRouter()


@router.get("")
def list_campaigns(
    status: Optional[str] = Query(None),
    ad_type: Optional[str] = Query(None),
    marketplace_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取广告活动列表（含 KPI）"""
    q = db.query(Campaign)
    if status:
        q = q.filter(Campaign.status == status)
    if ad_type:
        q = q.filter(Campaign.ad_type == ad_type)
    if marketplace_id:
        q = q.filter(Campaign.marketplace_id == marketplace_id)
    campaigns = q.order_by(Campaign.name).all()

    # Build KPI lookup from summary_by_campaign (single batch query)
    kpi_list = summary_by_campaign(db, date_from, date_to, marketplace_id)
    kpi_map = {row["campaign_id"]: row for row in kpi_list}

    # Batch fetch latest budget per campaign (single query using subquery for max date)
    from sqlalchemy.orm import aliased

    latest_budget_sq = (
        db.query(
            CampaignDailyRecord.campaign_id,
            func.max(CampaignDailyRecord.date).label("max_date"),
        )
        .filter(CampaignDailyRecord.budget != None)
        .group_by(CampaignDailyRecord.campaign_id)
        .subquery()
    )
    budget_rows = (
        db.query(CampaignDailyRecord.campaign_id, CampaignDailyRecord.budget)
        .join(
            latest_budget_sq,
            (CampaignDailyRecord.campaign_id == latest_budget_sq.c.campaign_id)
            & (CampaignDailyRecord.date == latest_budget_sq.c.max_date),
        )
        .all()
    )
    budget_map = {r[0]: r[1] for r in budget_rows}

    result = []
    for c in campaigns:
        row = CampaignOut.model_validate(c).model_dump()
        kpi = kpi_map.get(c.id, {})
        row["spend"] = kpi.get("spend", 0)
        row["orders"] = kpi.get("orders", 0)
        row["sales"] = kpi.get("sales", 0)
        row["acos"] = kpi.get("acos")
        row["roas"] = kpi.get("roas")
        row["impressions"] = kpi.get("impressions", 0)
        row["clicks"] = kpi.get("clicks", 0)
        row["daily_budget"] = budget_map.get(c.id)
        # Parse tags JSON
        try:
            row["tags"] = json.loads(c.tags) if c.tags else []
        except (json.JSONDecodeError, TypeError):
            row["tags"] = []
        result.append(row)
    return result


class CampaignTagsUpdate(BaseModel):
    tags: list[str]


@router.put("/{campaign_id}/tags")
def update_campaign_tags(
    campaign_id: int,
    body: CampaignTagsUpdate,
    db: Session = Depends(get_db),
):
    """Update campaign tags (replaces existing)"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.tags = json.dumps(body.tags, ensure_ascii=False) if body.tags else None
    db.commit()
    return {"id": campaign.id, "tags": body.tags}


@router.get("/tags/all")
def list_all_tags(db: Session = Depends(get_db)):
    """Get distinct list of all tags across campaigns"""
    rows = db.query(Campaign.tags).filter(Campaign.tags.isnot(None)).all()
    tag_set = set()
    for (tags_json,) in rows:
        try:
            parsed = json.loads(tags_json) if tags_json else []
            tag_set.update(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    return sorted(tag_set)


@router.get("/{campaign_id}", response_model=CampaignDetail)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """获取广告活动详情（含 KPI 汇总）"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="广告活动不存在")

    # 汇总 KPI
    agg = (
        db.query(
            func.sum(PlacementRecord.impressions),
            func.sum(PlacementRecord.clicks),
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
            func.min(PlacementRecord.date),
            func.max(PlacementRecord.date),
        )
        .filter(PlacementRecord.campaign_id == campaign_id)
        .first()
    )

    total_imp, total_clk, total_spd, total_ord, total_sal, first_dt, last_dt = agg

    return CampaignDetail(
        **CampaignOut.model_validate(campaign).model_dump(),
        total_impressions=total_imp or 0,
        total_clicks=total_clk or 0,
        total_spend=total_spd or 0.0,
        total_orders=total_ord or 0,
        total_sales=total_sal or 0.0,
        ctr=(total_clk / total_imp) if total_imp else None,
        cpc=(total_spd / total_clk) if total_clk else None,
        roas=(total_sal / total_spd) if total_spd else None,
        acos=(total_spd / total_sal) if total_sal else None,
        first_date=first_dt,
        last_date=last_dt,
    )


@router.get("/{campaign_id}/placement-summary")
def get_campaign_placement_summary(
    campaign_id: int,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """按展示位置聚合 KPI（用于位置对比）"""
    from fastapi import HTTPException

    if not db.query(Campaign).filter(Campaign.id == campaign_id).first():
        raise HTTPException(status_code=404, detail="Campaign not found")
    q = db.query(
        PlacementRecord.placement_type,
        func.sum(PlacementRecord.impressions),
        func.sum(PlacementRecord.clicks),
        func.sum(PlacementRecord.spend),
        func.sum(PlacementRecord.orders),
        func.sum(PlacementRecord.sales),
    ).filter(PlacementRecord.campaign_id == campaign_id)

    if date_from:
        q = q.filter(PlacementRecord.date >= date_from)
    if date_to:
        q = q.filter(PlacementRecord.date <= date_to)

    rows = q.group_by(PlacementRecord.placement_type).all()

    return [
        {
            "placement_type": r[0],
            "impressions": r[1] or 0,
            "clicks": r[2] or 0,
            "spend": round(float(r[3] or 0), 2),
            "orders": r[4] or 0,
            "sales": round(float(r[5] or 0), 2),
            "ctr": calc_ctr(r[2] or 0, r[1] or 0),
            "cpc": calc_cpc(float(r[3] or 0), r[2] or 0),
            "roas": calc_roas(float(r[5] or 0), float(r[3] or 0)),
            "acos": calc_acos(float(r[3] or 0), float(r[5] or 0)),
        }
        for r in rows
    ]


@router.get("/{campaign_id}/ad-groups")
def get_campaign_ad_groups(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    """获取广告活动下的广告组及其 KPI"""
    from fastapi import HTTPException

    if not db.query(Campaign).filter(Campaign.id == campaign_id).first():
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get ad groups with aggregated daily metrics
    rows = (
        db.query(
            AdGroup.id,
            AdGroup.name,
            AdGroup.status,
            AdGroup.default_bid,
            func.sum(AdGroupDailyRecord.impressions),
            func.sum(AdGroupDailyRecord.clicks),
            func.sum(AdGroupDailyRecord.spend),
            func.sum(AdGroupDailyRecord.orders),
            func.sum(AdGroupDailyRecord.sales),
        )
        .outerjoin(AdGroupDailyRecord, AdGroup.id == AdGroupDailyRecord.ad_group_id)
        .filter(AdGroup.campaign_id == campaign_id)
        .group_by(AdGroup.id)
        .all()
    )

    return [
        {
            "id": r[0],
            "name": r[1],
            "status": r[2],
            "default_bid": r[3],
            "impressions": r[4] or 0,
            "clicks": r[5] or 0,
            "spend": round(float(r[6] or 0), 2),
            "orders": r[7] or 0,
            "sales": round(float(r[8] or 0), 2),
            "ctr": calc_ctr(r[5] or 0, r[4] or 0),
            "cpc": calc_cpc(float(r[6] or 0), r[5] or 0),
            "roas": calc_roas(float(r[8] or 0), float(r[6] or 0)),
            "acos": calc_acos(float(r[6] or 0), float(r[8] or 0)),
        }
        for r in rows
    ]
