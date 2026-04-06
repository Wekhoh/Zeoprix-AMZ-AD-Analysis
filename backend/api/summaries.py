"""数据汇总 API — 替代 Excel 的 eng_ 汇总表"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.middleware import validate_date_param
from backend.services.summary_service import (
    summary_by_date,
    summary_by_campaign,
    summary_by_placement,
    dashboard_overview,
    compare_periods,
)

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    marketplace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """首页仪表盘数据"""
    validate_date_param(date_from, "date_from")
    validate_date_param(date_to, "date_to")
    return dashboard_overview(db, date_from, date_to, marketplace_id)


@router.get("/by-date")
def get_summary_by_date(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    campaign_id: Optional[int] = Query(None),
    marketplace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """按日期汇总"""
    validate_date_param(date_from, "date_from")
    validate_date_param(date_to, "date_to")
    return summary_by_date(db, date_from, date_to, campaign_id, marketplace_id)


@router.get("/by-campaign")
def get_summary_by_campaign(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    marketplace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """按广告活动汇总"""
    validate_date_param(date_from, "date_from")
    validate_date_param(date_to, "date_to")
    return summary_by_campaign(db, date_from, date_to, marketplace_id)


@router.get("/by-placement")
def get_summary_by_placement(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    campaign_id: Optional[int] = Query(None),
    marketplace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """按展示位置汇总"""
    return summary_by_placement(db, date_from, date_to, campaign_id, marketplace_id)


@router.get("/comparison")
def get_comparison(
    period_a_from: str = Query(...),
    period_a_to: str = Query(...),
    period_b_from: str = Query(...),
    period_b_to: str = Query(...),
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """周期对比分析"""
    return compare_periods(db, period_a_from, period_a_to, period_b_from, period_b_to, campaign_id)


@router.get("/campaign-comparison")
def get_campaign_comparison(
    campaign_a: int = Query(...),
    campaign_b: int = Query(...),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """两个活动的 KPI 对比"""
    validate_date_param(date_from, "date_from")
    validate_date_param(date_to, "date_to")

    all_campaigns = summary_by_campaign(db, date_from, date_to)
    kpi_map = {c["campaign_id"]: c for c in all_campaigns}

    a_data = kpi_map.get(campaign_a, {})
    b_data = kpi_map.get(campaign_b, {})

    kpi_fields = [
        "impressions",
        "clicks",
        "spend",
        "orders",
        "sales",
        "ctr",
        "cpc",
        "roas",
        "acos",
        "cvr",
    ]
    lower_is_better = {"acos", "cpc", "spend"}

    period_a = {k: a_data.get(k, 0) or 0 for k in kpi_fields}
    period_b = {k: b_data.get(k, 0) or 0 for k in kpi_fields}

    deltas = {}
    for key in kpi_fields:
        a_val = period_a[key]
        b_val = period_b[key]
        absolute = round(b_val - a_val, 4)
        percent = round((b_val - a_val) / a_val * 100, 1) if a_val else None
        favorable = absolute <= 0 if key in lower_is_better else absolute >= 0
        deltas[key] = {"absolute": absolute, "percent": percent, "favorable": favorable}

    return {
        "campaign_a": a_data.get("campaign_name", f"ID {campaign_a}"),
        "campaign_b": b_data.get("campaign_name", f"ID {campaign_b}"),
        "period_a": period_a,
        "period_b": period_b,
        "deltas": deltas,
    }
