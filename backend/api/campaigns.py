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


class BidSimulationRequest(BaseModel):
    new_base_bid: float
    lookback_days: int = 30


@router.post("/{campaign_id}/simulate-bid")
def simulate_bid_change(
    campaign_id: int,
    body: BidSimulationRequest,
    db: Session = Depends(get_db),
):
    """Estimate the impact of changing the campaign's base bid.

    Assumptions (linear extrapolation, conservative):
    - CPC scales proportionally with base_bid (new_cpc = old_cpc * ratio)
    - Click volume unchanged (first-order estimate — real world may have
      impression loss or gain, but we avoid predicting auction dynamics)
    - CVR unchanged — conversion quality doesn't directly depend on bid
    - Sales = clicks * cvr * avg_order_value

    Returns current metrics, projected metrics, and deltas.
    """
    from datetime import datetime, timedelta

    if body.new_base_bid <= 0:
        raise HTTPException(status_code=400, detail="new_base_bid must be > 0")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if not campaign.base_bid or campaign.base_bid <= 0:
        raise HTTPException(
            status_code=400,
            detail="Campaign has no base_bid configured, cannot simulate",
        )

    # Aggregate historical data (lookback_days from latest placement record)
    latest_date = (
        db.query(func.max(PlacementRecord.date))
        .filter(PlacementRecord.campaign_id == campaign_id)
        .scalar()
    )
    if not latest_date:
        raise HTTPException(status_code=400, detail="No historical data for campaign")

    try:
        latest_dt = datetime.strptime(latest_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date in records")

    cutoff = (latest_dt - timedelta(days=body.lookback_days)).isoformat()

    agg = (
        db.query(
            func.sum(PlacementRecord.impressions),
            func.sum(PlacementRecord.clicks),
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
        )
        .filter(
            PlacementRecord.campaign_id == campaign_id,
            PlacementRecord.date >= cutoff,
        )
        .first()
    )
    imp, clk, spend, orders, sales = (
        agg[0] or 0,
        agg[1] or 0,
        float(agg[2] or 0),
        agg[3] or 0,
        float(agg[4] or 0),
    )

    if clk == 0 or spend == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data in last {body.lookback_days} days (no clicks)",
        )

    current_cpc = spend / clk
    current_cvr = orders / clk if clk > 0 else 0
    current_acos = spend / sales if sales > 0 else None
    current_roas = sales / spend if spend > 0 else None

    # Linear projection
    bid_ratio = body.new_base_bid / campaign.base_bid
    projected_cpc = round(current_cpc * bid_ratio, 2)
    projected_clicks = clk  # assumption: unchanged
    projected_spend = round(projected_cpc * projected_clicks, 2)
    projected_orders = round(projected_clicks * current_cvr)
    projected_sales = sales  # assumption: sales unchanged
    projected_acos = round(projected_spend / projected_sales, 4) if projected_sales > 0 else None
    projected_roas = round(projected_sales / projected_spend, 2) if projected_spend > 0 else None

    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "lookback_days": body.lookback_days,
        "data_points": {
            "from": cutoff,
            "to": latest_date,
            "impressions": imp,
            "clicks": clk,
        },
        "current": {
            "base_bid": campaign.base_bid,
            "cpc": round(current_cpc, 2),
            "cvr": round(current_cvr, 4),
            "spend": round(spend, 2),
            "orders": orders,
            "sales": round(sales, 2),
            "acos": round(current_acos, 4) if current_acos else None,
            "roas": round(current_roas, 2) if current_roas else None,
        },
        "projected": {
            "base_bid": body.new_base_bid,
            "cpc": projected_cpc,
            "cvr": round(current_cvr, 4),
            "spend": projected_spend,
            "orders": projected_orders,
            "sales": round(projected_sales, 2),
            "acos": projected_acos,
            "roas": projected_roas,
        },
        "deltas": {
            "spend_pct": round((projected_spend - spend) / spend * 100, 1) if spend > 0 else None,
            "orders_pct": round((projected_orders - orders) / orders * 100, 1)
            if orders > 0
            else None,
            "acos_pct": round(
                ((projected_acos or 0) - (current_acos or 0)) / (current_acos or 1) * 100,
                1,
            )
            if current_acos
            else None,
        },
        "disclaimer": "此为基于历史 CPC 和 CVR 的线性估算，假设点击量不变。实际结果受广告位竞争、展示量变化等因素影响。",
    }


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
