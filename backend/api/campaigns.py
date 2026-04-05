"""广告活动 API"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import Campaign, PlacementRecord
from backend.schemas.campaign import CampaignOut, CampaignDetail
from backend.services.summary_service import summary_by_campaign

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
        result.append(row)
    return result


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
