"""KPI 计算工具 — 替代 Excel 公式列"""

from typing import Optional
from backend.models.placement import PlacementRecord
from backend.schemas.placement import PlacementOut


def calc_ctr(clicks: int, impressions: int) -> Optional[float]:
    return round(clicks / impressions, 6) if impressions > 0 else None


def calc_cpc(spend: float, clicks: int) -> Optional[float]:
    return round(spend / clicks, 2) if clicks > 0 else None


def calc_roas(sales: float, spend: float) -> Optional[float]:
    return round(sales / spend, 2) if spend > 0 else None


def calc_acos(spend: float, sales: float) -> Optional[float]:
    return round(spend / sales, 4) if sales > 0 else None


def calc_cvr(orders: int, clicks: int) -> Optional[float]:
    return round(orders / clicks, 4) if clicks > 0 else None


def enrich_placement_kpis(
    record: PlacementRecord, campaign_name: str = ""
) -> PlacementOut:
    """为展示位置记录附加计算的 KPI"""
    return PlacementOut(
        id=record.id,
        date=record.date,
        campaign_id=record.campaign_id,
        campaign_name=campaign_name,
        placement_type=record.placement_type,
        bidding_strategy=record.bidding_strategy,
        impressions=record.impressions,
        clicks=record.clicks,
        spend=record.spend,
        orders=record.orders,
        sales=record.sales,
        ctr=calc_ctr(record.clicks, record.impressions),
        cpc=calc_cpc(record.spend, record.clicks),
        roas=calc_roas(record.sales, record.spend),
        acos=calc_acos(record.spend, record.sales),
        cvr=calc_cvr(record.orders, record.clicks),
        notes=record.notes,
    )
