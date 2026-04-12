"""月度预算 Pacing 服务 — 预测本月广告花费是否会超支。

核心逻辑：
  projected_spend = current_spend × (total_days / elapsed_days)
  if projected_spend > budget × warning_threshold → warning
  if projected_spend > budget → danger

数据来源：PlacementRecord.spend 按本月日期范围汇总。
配置来源：settings.MONTHLY_BUDGET / settings.BUDGET_WARNING_THRESHOLD。
"""

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import PlacementRecord


def calc_budget_pacing(db: Session) -> dict:
    """Calculate monthly budget pacing status.

    Returns:
        {
            "enabled": bool,
            "monthly_budget": float,
            "current_spend": float,
            "projected_spend": float | None,
            "days_elapsed": int,
            "days_total": int,
            "pacing_pct": float | None,   # projected / budget (1.0 = exactly on track)
            "level": "ok" | "warning" | "danger" | "disabled",
            "message": str | None,
        }
    """
    budget = settings.MONTHLY_BUDGET
    if budget <= 0:
        return {
            "enabled": False,
            "monthly_budget": 0,
            "current_spend": 0,
            "projected_spend": None,
            "days_elapsed": 0,
            "days_total": 0,
            "pacing_pct": None,
            "level": "disabled",
            "message": None,
        }

    today = date.today()
    first_of_month = today.replace(day=1)
    days_elapsed = (today - first_of_month).days + 1  # include today

    # Total days in this month
    if today.month == 12:
        next_month_first = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month_first = today.replace(month=today.month + 1, day=1)
    days_total = (next_month_first - first_of_month).days

    # Current month spend from PlacementRecord
    month_start = first_of_month.isoformat()
    month_end = today.isoformat()
    current_spend = (
        db.query(func.sum(PlacementRecord.spend))
        .filter(
            PlacementRecord.date >= month_start,
            PlacementRecord.date <= month_end,
        )
        .scalar()
    ) or 0.0

    # Project end-of-month spend
    if days_elapsed > 0:
        projected_spend = round(current_spend * (days_total / days_elapsed), 2)
    else:
        projected_spend = 0.0

    pacing_pct = round(projected_spend / budget, 4) if budget > 0 else None

    # Determine alert level
    warning_threshold = settings.BUDGET_WARNING_THRESHOLD
    if projected_spend > budget:
        level = "danger"
        over_amount = round(projected_spend - budget, 2)
        message = f"预计本月超支 ${over_amount:.0f}（预计花费 ${projected_spend:.0f} / 预算 ${budget:.0f}）"
    elif projected_spend > budget * warning_threshold:
        level = "warning"
        message = f"预算使用接近上限（预计 ${projected_spend:.0f} / 预算 ${budget:.0f}，{pacing_pct * 100:.0f}%）"
    else:
        level = "ok"
        message = None

    return {
        "enabled": True,
        "monthly_budget": budget,
        "current_spend": round(current_spend, 2),
        "projected_spend": projected_spend,
        "days_elapsed": days_elapsed,
        "days_total": days_total,
        "pacing_pct": pacing_pct,
        "level": level,
        "message": message,
    }
