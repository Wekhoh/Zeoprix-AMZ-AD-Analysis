"""Data-quality anomaly detection for imported placement CSVs.

Two layers:

1. :func:`detect_data_quality_anomalies` — intra-file sanity checks
   that flag obvious-garbage rows (orders > clicks, extreme ACOS/CPC,
   date gaps) based purely on the incoming file.

2. :func:`detect_historical_anomalies` — cross-file sanity checks that
   compare incoming daily averages against the last 30 days of the
   same campaign's historical data, flagging >300% deviations that
   usually indicate a unit error or a wrong-file upload.

Both return a list of ``{level, message}`` dicts where ``level`` is
one of ``'error'`` (blocks import), ``'warning'`` (allows but flags),
or ``'info'``.
"""

from datetime import datetime, timedelta

from sqlalchemy import func

from backend.models import Campaign, PlacementRecord


def detect_data_quality_anomalies(placement_data: list[dict]) -> list[dict]:
    """Intra-file sanity checks on a parsed placement CSV.

    Flags: empty file (error), orders-exceeds-clicks (error, usually a
    column-alignment bug), spend-without-impressions (warning), extreme
    ACOS >10x (warning), extreme CPC >$50 (warning), date gaps (info).
    """
    warnings: list[dict] = []

    if not placement_data:
        warnings.append({"level": "error", "message": "文件中未找到有效数据行"})
        return warnings

    impossible_rows = 0
    zero_imp_with_spend = 0
    extreme_acos_rows = 0
    extreme_cpc_rows = 0

    for row in placement_data:
        imp = row.get("impressions", 0) or 0
        clk = row.get("clicks", 0) or 0
        spd = row.get("spend", 0) or 0
        orders = row.get("orders", 0) or 0
        sales = row.get("sales", 0) or 0

        # Impossible: orders > clicks
        if orders > clk and clk >= 0:
            impossible_rows += 1
        # Spend > 0 but impressions = 0 is impossible
        if spd > 0 and imp == 0:
            zero_imp_with_spend += 1
        # ACOS > 1000% is extreme (possible unit mix-up)
        if sales > 0 and (spd / sales) > 10:
            extreme_acos_rows += 1
        # CPC > $50 is extreme for most categories
        if clk > 0 and (spd / clk) > 50:
            extreme_cpc_rows += 1

    if impossible_rows > 0:
        warnings.append(
            {
                "level": "error",
                "message": f"{impossible_rows} 行数据订单数 > 点击数（不可能），可能是列对齐错误",
            }
        )
    if zero_imp_with_spend > 0:
        warnings.append(
            {
                "level": "warning",
                "message": f"{zero_imp_with_spend} 行有花费但零曝光，请检查数据完整性",
            }
        )
    if extreme_acos_rows > 0:
        warnings.append(
            {
                "level": "warning",
                "message": f"{extreme_acos_rows} 行 ACOS > 1000%，可能是单位错误或数据异常",
            }
        )
    if extreme_cpc_rows > 0:
        warnings.append(
            {
                "level": "warning",
                "message": f"{extreme_cpc_rows} 行 CPC > $50，请确认数据合理性",
            }
        )

    # Date continuity check
    dates = sorted({row["date"] for row in placement_data if row.get("date")})
    if len(dates) >= 2:
        try:
            date_objs = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
            gaps = []
            for i in range(1, len(date_objs)):
                diff = (date_objs[i] - date_objs[i - 1]).days
                if diff > 1:
                    gaps.append(f"{date_objs[i - 1]} → {date_objs[i]} ({diff - 1} 天缺失)")
            if gaps:
                warnings.append(
                    {
                        "level": "info",
                        "message": f"日期不连续: {'; '.join(gaps[:3])}{' ...' if len(gaps) > 3 else ''}",
                    }
                )
        except (ValueError, TypeError):
            pass

    return warnings


def detect_historical_anomalies(db, placement_data: list[dict], campaign_name: str) -> list[dict]:
    """Cross-file sanity: compare incoming daily averages against the
    campaign's last 30 days of historical placement data.

    Flags >300% (5x) daily-average deviations in spend / orders / sales
    as warnings. Requires at least 3 days of history for a baseline;
    returns ``[]`` otherwise (first-time import, stale campaign, etc).
    """
    warnings: list[dict] = []
    if not placement_data or not campaign_name:
        return warnings

    campaign = db.query(Campaign).filter(Campaign.name == campaign_name).first()
    if not campaign:
        # First-time import for this campaign — no historical baseline
        return warnings

    # Incoming file: compute daily averages
    incoming_dates = {row["date"] for row in placement_data if row.get("date")}
    incoming_day_count = max(len(incoming_dates), 1)
    incoming_spend = sum(row.get("spend", 0) or 0 for row in placement_data)
    incoming_orders = sum(row.get("orders", 0) or 0 for row in placement_data)
    incoming_sales = sum(row.get("sales", 0) or 0 for row in placement_data)
    avg_new = {
        "spend": incoming_spend / incoming_day_count,
        "orders": incoming_orders / incoming_day_count,
        "sales": incoming_sales / incoming_day_count,
    }

    # Historical baseline: last 30 days before the earliest incoming date
    earliest_incoming = min(incoming_dates) if incoming_dates else None
    if not earliest_incoming:
        return warnings
    try:
        earliest_dt = datetime.strptime(earliest_incoming, "%Y-%m-%d").date()
    except ValueError:
        return warnings
    hist_end = (earliest_dt - timedelta(days=1)).isoformat()
    hist_start = (earliest_dt - timedelta(days=30)).isoformat()

    hist_agg = (
        db.query(
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
            func.count(func.distinct(PlacementRecord.date)),
        )
        .filter(
            PlacementRecord.campaign_id == campaign.id,
            PlacementRecord.date >= hist_start,
            PlacementRecord.date <= hist_end,
        )
        .first()
    )
    if not hist_agg or not hist_agg[3] or hist_agg[3] < 3:
        # Insufficient history (<3 days) — skip comparison
        return warnings

    hist_days = hist_agg[3]
    avg_hist = {
        "spend": float(hist_agg[0] or 0) / hist_days,
        "orders": float(hist_agg[1] or 0) / hist_days,
        "sales": float(hist_agg[2] or 0) / hist_days,
    }

    def _check(metric: str, label: str, threshold: float = 3.0) -> None:
        if avg_hist[metric] < 0.01:
            return  # too small to compare meaningfully
        ratio = avg_new[metric] / avg_hist[metric]
        if ratio > (1 + threshold):
            warnings.append(
                {
                    "level": "warning",
                    "message": (
                        f"{label} 日均 {avg_new[metric]:.2f} vs 历史 {avg_hist[metric]:.2f} "
                        f"(+{(ratio - 1) * 100:.0f}%)，请确认数据准确性"
                    ),
                }
            )
        elif ratio < (1 / (1 + threshold)):
            warnings.append(
                {
                    "level": "warning",
                    "message": (
                        f"{label} 日均 {avg_new[metric]:.2f} vs 历史 {avg_hist[metric]:.2f} "
                        f"({(ratio - 1) * 100:.0f}%)，可能数据缺失"
                    ),
                }
            )

    _check("spend", "花费")
    _check("orders", "订单")
    _check("sales", "销售额")

    return warnings
