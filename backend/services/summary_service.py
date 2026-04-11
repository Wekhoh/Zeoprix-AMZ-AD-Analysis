"""多维度汇总服务 — 替代 Excel 的 SUMIFS 公式"""

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Campaign, ImportHistory, OrganicSales, PlacementRecord, ProductVariant
from backend.services.kpi_calculator import (
    calc_acos,
    calc_cpc,
    calc_ctr,
    calc_cvr,
    calc_roas,
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


def dashboard_overview(db: Session, date_from=None, date_to=None, marketplace_id=None) -> dict:
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
        db.query(Campaign.status, func.count(Campaign.id)).group_by(Campaign.status).all()
    )

    # 每日趋势
    daily_trend = summary_by_date(db, date_from, date_to, marketplace_id=marketplace_id)

    # TOP 5 花费活动
    all_campaigns = summary_by_campaign(db, date_from, date_to, marketplace_id=marketplace_id)
    all_campaigns.sort(key=lambda x: x["spend"], reverse=True)
    top_campaigns = all_campaigns[:5]

    alerts = _generate_dashboard_alerts(all_campaigns, db)
    profit_data = _calc_profit(db, kpi)
    tacos_data = _calc_tacos(db, kpi, date_from, date_to)
    freshness = _calc_data_freshness(db)
    inventory_status = _calc_inventory_status(db)

    return {
        "kpi": kpi,
        "status_counts": {s: c for s, c in status_counts},
        "daily_trend": daily_trend,
        "top_campaigns": top_campaigns,
        "alerts": alerts,
        "profit": profit_data,
        "tacos": tacos_data,
        "freshness": freshness,
        "inventory_status": inventory_status,
    }


def _generate_dashboard_alerts(campaigns: list[dict], db: Session = None) -> list[dict]:
    """Generate dashboard alerts from campaign KPI + inventory data."""
    alerts: list[dict] = []

    # Index campaign metrics by id for inventory-risk join below
    camp_spend_by_id = {c.get("campaign_id"): c.get("spend", 0) or 0 for c in campaigns}
    camp_name_by_id = {c.get("campaign_id"): c.get("campaign_name", "") for c in campaigns}

    for camp in campaigns:
        name = camp["campaign_name"]
        acos = camp.get("acos")
        spend = camp.get("spend", 0)
        orders = camp.get("orders", 0)
        roas = camp.get("roas")

        if acos and acos > settings.DASHBOARD_ACOS_ALERT_THRESHOLD:
            threshold_pct = int(settings.DASHBOARD_ACOS_ALERT_THRESHOLD * 100)
            alerts.append(
                {
                    "type": "high_acos",
                    "severity": "warning",
                    "campaign_name": name,
                    "value": round(acos, 4),
                    "message": f"ACOS 超过 {threshold_pct}%，建议检查竞价策略",
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
        if roas and roas > settings.DASHBOARD_ROAS_SCALE_UP_THRESHOLD:
            alerts.append(
                {
                    "type": "high_roas",
                    "severity": "success",
                    "campaign_name": name,
                    "value": round(roas, 2),
                    "message": "ROAS 优秀，可考虑增加预算",
                }
            )

    # Inventory risk alerts (Path B #1): only when campaign has active spend
    if db is not None:
        try:
            from backend.services.inventory_service import get_inventory_risk_for_campaigns

            risks = get_inventory_risk_for_campaigns(db)
        except Exception:
            risks = []

        for risk in risks:
            cid = risk.get("campaign_id")
            spend = camp_spend_by_id.get(cid, 0)
            if spend <= 0:
                continue  # only alert when ad is actually spending
            dos = risk.get("days_of_supply")
            level = risk.get("alert_level")
            sku = risk.get("sku", "")
            severity = "danger" if level == "critical" else "warning"
            dos_str = f"{dos:.1f}" if dos is not None else "未知"
            alerts.append(
                {
                    "type": "inventory_risk",
                    "severity": severity,
                    "campaign_name": camp_name_by_id.get(cid, risk.get("campaign_name", "")),
                    "value": round(dos, 1) if dos is not None else 0,
                    "message": f"SKU {sku} 库存仅剩 {dos_str} 天（日花费 ${spend:.0f}），建议暂停或降价",
                }
            )

    return alerts


def _calc_inventory_status(db: Session) -> dict:
    """Summarize inventory status for dashboard header banner."""
    try:
        from backend.services.inventory_service import get_risk_summary

        summary = get_risk_summary(db)
    except Exception:
        return {
            "has_data": False,
            "last_import_date": None,
            "critical_count": 0,
            "warning_count": 0,
        }

    has_data = bool(summary.get("last_import_date"))
    critical = summary.get("critical_count", 0)
    warning = summary.get("warning_count", 0)

    message = None
    if critical > 0:
        message = f"{critical} 个 SKU 库存危急（<3 天）"
    elif warning > 0:
        message = f"{warning} 个 SKU 库存预警（<7 天）"

    return {
        "has_data": has_data,
        "last_import_date": summary.get("last_import_date"),
        "critical_count": critical,
        "warning_count": warning,
        "message": message,
    }


def _calc_profit(db: Session, kpi: dict) -> dict:
    """Calculate estimated profit from product cost data."""
    variants = db.query(ProductVariant).filter(ProductVariant.unit_cost.isnot(None)).all()
    if not variants:
        return {"has_cost_data": False}

    count = len(variants)
    avg_unit_cost = sum(v.unit_cost or 0 for v in variants) / count
    avg_fba_fee = sum(v.fba_fee or 0 for v in variants) / count
    avg_referral_pct = sum(v.referral_fee_pct or 0.15 for v in variants) / count

    total_sales = kpi.get("sales", 0) or 0
    total_spend = kpi.get("spend", 0) or 0
    total_orders = kpi.get("orders", 0) or 0

    avg_price = (total_sales / total_orders) if total_orders > 0 else 0
    break_even_acos = (
        (1 - avg_referral_pct - (avg_fba_fee / avg_price) - (avg_unit_cost / avg_price))
        if avg_price > 0
        else None
    )
    estimated_profit = (
        total_sales
        - total_spend
        - (total_sales * avg_referral_pct)
        - (total_orders * avg_fba_fee)
        - (total_orders * avg_unit_cost)
    )
    return {
        "break_even_acos": round(break_even_acos, 4) if break_even_acos is not None else None,
        "estimated_profit": round(estimated_profit, 2),
        "has_cost_data": True,
    }


def _calc_tacos(db: Session, kpi: dict, date_from=None, date_to=None) -> dict:
    """Calculate TACoS (Total Advertising Cost of Sales)."""
    organic_q = db.query(func.sum(OrganicSales.total_sales)).filter(
        OrganicSales.deleted_at.is_(None)
    )
    if date_from:
        organic_q = organic_q.filter(OrganicSales.date >= date_from)
    if date_to:
        organic_q = organic_q.filter(OrganicSales.date <= date_to)
    organic_total_sales = organic_q.scalar()

    if organic_total_sales and organic_total_sales > 0:
        ad_spend = kpi.get("spend", 0) or 0
        return {"value": round(ad_spend / organic_total_sales, 4), "has_data": True}
    return {"value": None, "has_data": False}


def _calc_data_freshness(db: Session) -> dict:
    """Calculate data freshness: latest data date + last import time + staleness level."""
    from datetime import date, datetime

    latest_data_date = db.query(func.max(PlacementRecord.date)).scalar()
    last_import = (
        db.query(ImportHistory)
        .filter(ImportHistory.status == "success")
        .order_by(ImportHistory.created_at.desc())
        .first()
    )

    if not latest_data_date:
        return {
            "latest_data_date": None,
            "last_import_at": None,
            "days_stale": None,
            "level": "empty",
            "message": "暂无数据，请先导入",
        }

    # Calculate days between latest data and today
    try:
        data_dt = datetime.strptime(latest_data_date, "%Y-%m-%d").date()
        days_stale = (date.today() - data_dt).days
    except (ValueError, TypeError):
        days_stale = None

    if days_stale is None:
        level = "unknown"
        message = f"最新数据: {latest_data_date}"
    elif days_stale <= 2:
        level = "fresh"
        message = f"数据最新至 {latest_data_date}（{days_stale} 天前）"
    elif days_stale <= 7:
        level = "warning"
        message = f"数据最新至 {latest_data_date}（{days_stale} 天前），建议导入最新数据"
    else:
        level = "stale"
        message = f"数据最新至 {latest_data_date}（{days_stale} 天前），数据可能过期"

    return {
        "latest_data_date": latest_data_date,
        "last_import_at": str(last_import.created_at) if last_import else None,
        "last_import_file": last_import.file_name if last_import else None,
        "days_stale": days_stale,
        "level": level,
        "message": message,
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


def compare_multi_periods(
    db: Session,
    unit: str = "week",
    count: int = 4,
    end_date: str | None = None,
    campaign_id: int | None = None,
) -> dict:
    """Compare KPIs across N consecutive periods (weekly or monthly).

    Returns periods in chronological order (oldest first) with a time series
    per metric, suitable for line charts.
    """
    from datetime import date, datetime, timedelta

    if unit not in ("week", "month"):
        unit = "week"
    count = max(1, min(count, 52))  # safety bounds

    # Determine anchor date
    anchor = date.today()
    if end_date:
        try:
            anchor = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # Build period ranges (newest first, then reverse for chronological)
    periods: list[dict] = []
    if unit == "week":
        # Week = 7 days ending on anchor
        for i in range(count):
            end = anchor - timedelta(days=7 * i)
            start = end - timedelta(days=6)
            periods.append(
                {
                    "label": f"{start.strftime('%m/%d')} - {end.strftime('%m/%d')}",
                    "from": start.isoformat(),
                    "to": end.isoformat(),
                }
            )
    else:  # month
        # Month = rolling 30 days for simplicity (calendar months vary)
        for i in range(count):
            end = anchor - timedelta(days=30 * i)
            start = end - timedelta(days=29)
            periods.append(
                {
                    "label": f"{start.strftime('%Y-%m')}",
                    "from": start.isoformat(),
                    "to": end.isoformat(),
                }
            )

    periods.reverse()  # chronological order

    # Fetch KPIs per period — reuse _build_kpi_row
    metric_keys = [
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
    series: dict[str, list] = {k: [] for k in metric_keys}

    for period in periods:
        q = _base_query(db, period["from"], period["to"], campaign_id)
        agg = q.with_entities(
            func.sum(PlacementRecord.impressions),
            func.sum(PlacementRecord.clicks),
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
        ).first()
        kpi = _build_kpi_row(*agg)
        for k in metric_keys:
            series[k].append(kpi.get(k))

    return {
        "unit": unit,
        "count": count,
        "periods": periods,
        "series": series,
    }
