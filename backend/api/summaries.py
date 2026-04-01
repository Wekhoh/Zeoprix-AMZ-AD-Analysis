"""数据汇总 API — 替代 Excel 的 eng_ 汇总表"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
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
    return summary_by_date(db, date_from, date_to, campaign_id, marketplace_id)


@router.get("/by-campaign")
def get_summary_by_campaign(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    marketplace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """按广告活动汇总"""
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
