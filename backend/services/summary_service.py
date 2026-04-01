"""多维度汇总服务 — 替代 Excel 的 SUMIFS 公式"""

from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import PlacementRecord, Campaign, ProductVariant, OrganicSales
from backend.services.kpi_calculator import (
    calc_ctr,
    calc_cpc,
    calc_roas,
    calc_acos,
    calc_cvr,
)


def _base_query(
    db: Session,
    date_from: Optional[str],
    date_to: Optional[str],
    campaign_id: Optional[int] = None,
    marketplace_id: Optional[int] = None,
):
    q = db.query(PlacementRecord)
    if date_from:
        q = q.filter(PlacementRecord.date >= date_from)
    if date_to:
        q = q.filter(PlacementRecord.date <= date_to)
    if campaign_id:
        q = q.filter(PlacementRecord.campaign_id == campaign_id)
    if marketplace_id:
        q = q.join(Campaign, PlacementRecord.campaign_id == Campaign.id).filter(
            Campaign.marketplace_id == marketplace_id
        )
    return q


def _build_kpi_row(imp, clk, spd, orders, sales) -> dict:
    imp = imp or 0
    clk = clk or 0
    spd = spd or 0.0
    orders = orders or 0
    sales = sales or 0.0
    return {
        "impressions": imp,
        "clicks": clk,
        "spend": round(spd, 2),
        "orders": orders,
        "sales": round(sales, 2),
        "ctr": calc_ctr(clk, imp),
        "cpc": calc_cpc(spd, clk),
        "roas": calc_roas(sales, spd),
        "acos": calc_acos(spd, sales),
        "cvr": calc_cvr(orders, clk),
    }


def summary_by_date(
    db: Session,
    date_from=None,
    date_to=None,
    campaign_id=None,
    marketplace_id=None,
) -> list[dict]:
    q = _base_query(db, date_from, date_to, campaign_id, marketplace_id)
    rows = (
        q.with_entities(
            PlacementRecord.date,
            func.sum(PlacementRecord.impressions),
            func.sum(PlacementRecord.clicks),
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
        )
        .group_by(PlacementRecord.date)
        .order_by(PlacementRecord.date)
        .all()
    )

    return [{"date": r[0], **_build_kpi_row(*r[1:])} for r in rows]


def summary_by_campaign(
    db: Session, date_from=None, date_to=None, marketplace_id=None
) -> list[dict]:
    q = _base_query(db, date_from, date_to, marketplace_id=marketplace_id)
    rows = (
        q.join(Campaign)
        .with_entities(
            Campaign.id,
            Campaign.name,
            Campaign.status,
            func.sum(PlacementRecord.impressions),
            func.sum(PlacementRecord.clicks),
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
            func.min(PlacementRecord.date),
            func.max(PlacementRecord.date),
        )
        .group_by(Campaign.id)
        .order_by(Campaign.name)
        .all()
    )

    return [
        {
            "campaign_id": r[0],
            "campaign_name": r[1],
            "status": r[2],
            **_build_kpi_row(*r[3:8]),
            "first_date": r[8],
            "last_date": r[9],
        }
        for r in rows
    ]


def summary_by_placement(
    db: Session,
    date_from=None,
    date_to=None,
    campaign_id=None,
    marketplace_id=None,
) -> list[dict]:
    q = _base_query(db, date_from, date_to, campaign_id, marketplace_id)
    rows = (
        q.with_entities(
            PlacementRecord.placement_type,
            func.sum(PlacementRecord.impressions),
            func.sum(PlacementRecord.clicks),
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
        )
        .group_by(PlacementRecord.placement_type)
        .all()
    )

    return [{"placement_type": r[0], **_build_kpi_row(*r[1:])} for r in rows]


def dashboard_overview(
    db: Session, date_from=None, date_to=None, marketplace_id=None
) -> dict:
    q = _base_query(db, date_from, date_to, marketplace_id=marketplace_id)
    agg = q.with_entities(
        func.sum(PlacementRecord.impressions),
        func.sum(PlacementRecord.clicks),
        func.sum(PlacementRecord.spend),
        func.sum(PlacementRecord.orders),
        func.sum(PlacementRecord.sales),
    ).first()

    kpi = _build_kpi_row(*agg)

    # 广告活动状态分布
    status_counts = (
        db.query(Campaign.status, func.count(Campaign.id))
        .group_by(Campaign.status)
        .all()
    )

    # 每日趋势
    daily_trend = summary_by_date(db, date_from, date_to, marketplace_id=marketplace_id)

    # TOP 5 花费活动
    all_campaigns = summary_by_campaign(
        db, date_from, date_to, marketplace_id=marketplace_id
    )
    all_campaigns.sort(key=lambda x: x["spend"], reverse=True)
    top_campaigns = all_campaigns[:5]

    # 智能告警
    alerts: list[dict] = []
    for camp in all_campaigns:
        name = camp["campaign_name"]
        acos = camp.get("acos")
        spend = camp.get("spend", 0)
        orders = camp.get("orders", 0)
        roas = camp.get("roas")

        if acos and acos > 0.40:
            alerts.append(
                {
                    "type": "high_acos",
                    "severity": "warning",
                    "campaign_name": name,
                    "value": round(acos, 4),
                    "message": "ACOS 超过 40%，建议检查竞价策略",
                }
            )
        if spend > 0 and orders == 0:
            alerts.append(
                {
                    "type": "zero_orders",
                    "severity": "danger",
                    "campaign_name": name,
                    "value": round(spend, 2),
                    "message": "有花费但零订单，建议暂停或降低竞价",
                }
            )
        if roas and roas > 3.0:
            alerts.append(
                {
                    "type": "high_roas",
                    "severity": "success",
                    "campaign_name": name,
                    "value": round(roas, 2),
                    "message": "ROAS 优秀，可考虑增加预算",
                }
            )

    # 利润计算（仅当产品成本已配置时）
    profit_data: dict = {}
    variants_with_cost = (
        db.query(ProductVariant).filter(ProductVariant.unit_cost.isnot(None)).all()
    )

    if variants_with_cost:
        total_unit_cost = sum(v.unit_cost or 0 for v in variants_with_cost)
        total_fba_fee = sum(v.fba_fee or 0 for v in variants_with_cost)
        total_referral_pct = sum(v.referral_fee_pct or 0.15 for v in variants_with_cost)
        count = len(variants_with_cost)
        avg_unit_cost = total_unit_cost / count
        avg_fba_fee = total_fba_fee / count
        avg_referral_pct = total_referral_pct / count

        total_sales = kpi.get("sales", 0) or 0
        total_spend = kpi.get("spend", 0) or 0
        total_orders = kpi.get("orders", 0) or 0

        # 盈亏平衡 ACOS
        avg_price = (total_sales / total_orders) if total_orders > 0 else 0
        if avg_price > 0:
            break_even_acos = (
                1
                - avg_referral_pct
                - (avg_fba_fee / avg_price)
                - (avg_unit_cost / avg_price)
            )
        else:
            break_even_acos = None

        # 预估利润
        estimated_profit = (
            total_sales
            - total_spend
            - (total_sales * avg_referral_pct)
            - (total_orders * avg_fba_fee)
            - (total_orders * avg_unit_cost)
        )

        profit_data = {
            "break_even_acos": round(break_even_acos, 4)
            if break_even_acos is not None
            else None,
            "estimated_profit": round(estimated_profit, 2),
            "has_cost_data": True,
        }

    # TACoS 计算 (Total Advertising Cost of Sales)
    tacos_data: dict = {"value": None, "has_data": False}
    organic_q = db.query(
        func.sum(OrganicSales.total_sales),
    )
    if date_from:
        organic_q = organic_q.filter(OrganicSales.date >= date_from)
    if date_to:
        organic_q = organic_q.filter(OrganicSales.date <= date_to)
    organic_total_sales = organic_q.scalar()

    if organic_total_sales and organic_total_sales > 0:
        ad_spend = kpi.get("spend", 0) or 0
        tacos_value = (
            round(ad_spend / organic_total_sales, 4)
            if organic_total_sales > 0
            else None
        )
        tacos_data = {"value": tacos_value, "has_data": True}

    return {
        "kpi": kpi,
        "status_counts": {s: c for s, c in status_counts},
        "daily_trend": daily_trend,
        "top_campaigns": top_campaigns,
        "alerts": alerts,
        "profit": profit_data if profit_data else {"has_cost_data": False},
        "tacos": tacos_data,
    }


def compare_periods(
    db: Session,
    period_a_from: str,
    period_a_to: str,
    period_b_from: str,
    period_b_to: str,
    campaign_id: int | None = None,
) -> dict:
    """对比两个时间段的 KPI"""

    def _get_period_kpi(date_from: str, date_to: str) -> dict:
        q = _base_query(db, date_from, date_to, campaign_id)
        agg = q.with_entities(
            func.sum(PlacementRecord.impressions),
            func.sum(PlacementRecord.clicks),
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
        ).first()
        return _build_kpi_row(*agg)

    period_a = _get_period_kpi(period_a_from, period_a_to)
    period_b = _get_period_kpi(period_b_from, period_b_to)

    lower_is_better = {"acos", "cpc", "spend"}

    deltas = {}
    for key in period_a:
        a_val = period_a[key] or 0
        b_val = period_b[key] or 0
        absolute = b_val - a_val
        percent = ((b_val - a_val) / a_val * 100) if a_val else None
        favorable = absolute <= 0 if key in lower_is_better else absolute >= 0

        deltas[key] = {
            "absolute": round(absolute, 4),
            "percent": round(percent, 1) if percent is not None else None,
            "favorable": favorable,
        }

    return {"period_a": period_a, "period_b": period_b, "deltas": deltas}
