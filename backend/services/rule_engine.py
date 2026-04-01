"""规则引擎 — 自动化规则评估"""

import operator
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Campaign, PlacementRecord, Rule
from backend.services.kpi_calculator import (
    calc_ctr,
    calc_cpc,
    calc_roas,
    calc_acos,
)

OPERATOR_MAP = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
}

ACTION_LABELS = {
    "flag_pause": "建议暂停广告活动",
    "suggest_negative": "建议添加否定关键词",
    "suggest_bid_increase": "建议提高竞价",
    "suggest_bid_decrease": "建议降低竞价",
    "suggest_budget_increase": "建议增加预算",
}


def _get_campaign_metrics(db: Session, campaign: Campaign, period_days: int) -> dict:
    """获取广告活动在指定时间段内的聚合指标"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=period_days)).strftime("%Y-%m-%d")

    row = (
        db.query(
            func.sum(PlacementRecord.impressions),
            func.sum(PlacementRecord.clicks),
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
        )
        .filter(
            PlacementRecord.campaign_id == campaign.id,
            PlacementRecord.date >= cutoff,
        )
        .first()
    )

    if not row or row[0] is None:
        return {}

    imp = row[0] or 0
    clk = row[1] or 0
    spd = float(row[2] or 0)
    orders = row[3] or 0
    sales = float(row[4] or 0)

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
    }


def _check_condition(
    metrics: dict, field: str, op_str: str, value: float, min_data: int
) -> tuple[bool, float | None]:
    """检查单个规则条件, 返回 (是否触发, 实际值)"""
    # 最低数据量检查
    clicks = metrics.get("clicks", 0)
    if min_data > 0 and clicks < min_data:
        return False, None

    actual = metrics.get(field)
    if actual is None:
        return False, None

    op_func = OPERATOR_MAP.get(op_str)
    if op_func is None:
        return False, None

    return op_func(actual, value), actual


def evaluate_rules(db: Session) -> list[dict]:
    """评估所有活跃规则，返回触发结果列表"""
    rules = db.query(Rule).filter(Rule.is_active == 1).all()
    campaigns = db.query(Campaign).all()
    results: list[dict] = []

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    for rule in rules:
        for campaign in campaigns:
            metrics = _get_campaign_metrics(db, campaign, rule.period_days)
            if not metrics:
                continue

            triggered, actual_value = _check_condition(
                metrics,
                rule.condition_field,
                rule.condition_operator,
                rule.condition_value,
                rule.condition_min_data,
            )

            if triggered:
                results.append(
                    {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.name,
                        "condition_field": rule.condition_field,
                        "condition_operator": rule.condition_operator,
                        "condition_value": rule.condition_value,
                        "triggered_value": round(actual_value, 4)
                        if actual_value is not None
                        else None,
                        "action_type": rule.action_type,
                        "recommended_action": ACTION_LABELS.get(rule.action_type, rule.action_type),
                    }
                )

        # 更新 last_run_at
        rule.last_run_at = now_str

    db.commit()
    return results


def get_rule_results(db: Session, rule_id: int) -> list[dict]:
    """评估指定规则"""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        return []

    campaigns = db.query(Campaign).all()
    results: list[dict] = []

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    for campaign in campaigns:
        metrics = _get_campaign_metrics(db, campaign, rule.period_days)
        if not metrics:
            continue

        triggered, actual_value = _check_condition(
            metrics,
            rule.condition_field,
            rule.condition_operator,
            rule.condition_value,
            rule.condition_min_data,
        )

        if triggered:
            results.append(
                {
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "campaign_id": campaign.id,
                    "campaign_name": campaign.name,
                    "condition_field": rule.condition_field,
                    "condition_operator": rule.condition_operator,
                    "condition_value": rule.condition_value,
                    "triggered_value": round(actual_value, 4) if actual_value is not None else None,
                    "action_type": rule.action_type,
                    "recommended_action": ACTION_LABELS.get(rule.action_type, rule.action_type),
                }
            )

    rule.last_run_at = now_str
    db.commit()
    return results


def seed_default_rules(db: Session) -> int:
    """首次启动时播种默认规则，返回创建数量"""
    existing = db.query(Rule).count()
    if existing > 0:
        return 0

    defaults = [
        Rule(
            name="高 ACOS 预警",
            description="ACOS 超过 50% 的广告活动，建议暂停",
            condition_field="acos",
            condition_operator=">",
            condition_value=0.5,
            condition_min_data=0,
            period_days=7,
            action_type="flag_pause",
            is_active=1,
        ),
        Rule(
            name="零订单否定",
            description="点击 20 次以上但零订单，建议添加否定词",
            condition_field="orders",
            condition_operator="==",
            condition_value=0,
            condition_min_data=20,
            period_days=7,
            action_type="suggest_negative",
            is_active=1,
        ),
        Rule(
            name="高 ROAS 扩量",
            description="ROAS 超过 3.0 的优质广告，建议增加预算",
            condition_field="roas",
            condition_operator=">",
            condition_value=3.0,
            condition_min_data=0,
            period_days=7,
            action_type="suggest_budget_increase",
            is_active=1,
        ),
    ]

    for rule in defaults:
        db.add(rule)
    db.commit()
    return len(defaults)
