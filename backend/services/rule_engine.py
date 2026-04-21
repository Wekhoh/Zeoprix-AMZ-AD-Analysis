"""规则引擎 — 自动化规则评估"""

import operator
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Campaign, PlacementRecord, Rule
from backend.services.kpi_calculator import (
    calc_acos,
    calc_cpc,
    calc_ctr,
    calc_roas,
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
    "diagnose_zero_spend": "诊断零花费原因",
    "flag_budget_risk": "预算耗尽风险",
    "attribution_reminder": "归因窗口提醒",
    "negative_buffer_reminder": "否定词生效提醒",
}


def _batch_campaign_metrics(db: Session, period_days: int) -> dict[int, dict]:
    """批量获取所有广告活动在指定时间段内的聚合指标（单次 SQL）"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=period_days)).strftime("%Y-%m-%d")

    rows = (
        db.query(
            PlacementRecord.campaign_id,
            func.sum(PlacementRecord.impressions),
            func.sum(PlacementRecord.clicks),
            func.sum(PlacementRecord.spend),
            func.sum(PlacementRecord.orders),
            func.sum(PlacementRecord.sales),
        )
        .filter(PlacementRecord.date >= cutoff)
        .group_by(PlacementRecord.campaign_id)
        .all()
    )

    result: dict[int, dict] = {}
    for row in rows:
        cid = row[0]
        imp = row[1] or 0
        clk = row[2] or 0
        spd = float(row[3] or 0)
        orders = row[4] or 0
        sales = float(row[5] or 0)

        result[cid] = {
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
    return result


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

    # Batch-load metrics per unique period_days (N+1 → O(unique_periods))
    period_cache: dict[int, dict[int, dict]] = {}
    for rule in rules:
        if rule.period_days not in period_cache:
            period_cache[rule.period_days] = _batch_campaign_metrics(db, rule.period_days)

    for rule in rules:
        metrics_by_campaign = period_cache[rule.period_days]
        for campaign in campaigns:
            metrics = metrics_by_campaign.get(campaign.id, {})
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


def get_rule_results(db: Session, rule_id: int, dry_run: bool = False) -> list[dict]:
    """评估指定规则。

    Args:
        dry_run: if True, skip updating last_run_at and committing.
            Used for preview ("if I ran this rule, what would trigger?")
            without side effects.
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        return []

    campaigns = db.query(Campaign).all()
    results: list[dict] = []

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Single batch query for this rule's period
    metrics_by_campaign = _batch_campaign_metrics(db, rule.period_days)

    for campaign in campaigns:
        metrics = metrics_by_campaign.get(campaign.id, {})
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

    if not dry_run:
        rule.last_run_at = now_str
        db.commit()
    return results


def seed_default_rules(db: Session) -> int:
    """首次启动时播种默认规则，返回创建数量（按 name 去重）"""
    existing_names = {r.name for r in db.query(Rule.name).all()}

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
        Rule(
            name="投放中无花费诊断",
            description="广告活动投放中但连续 3 天无花费，可能是 Buy Box 丢失或出价过低",
            condition_field="spend",
            condition_operator="==",
            condition_value=0,
            condition_min_data=0,
            period_days=3,
            action_type="diagnose_zero_spend",
            is_active=1,
        ),
        Rule(
            name="预算耗尽风险",
            description="花费超过预算 80%，注意亚马逊允许单日超支最多 100%",
            condition_field="spend",
            condition_operator=">",
            condition_value=0.8,
            condition_min_data=0,
            period_days=1,
            action_type="flag_budget_risk",
            is_active=1,
        ),
        Rule(
            name="归因窗口提醒",
            description="最近 7 天的 SP 数据可能尚未完全归因，建议等待完整数据再做决策",
            condition_field="orders",
            condition_operator=">=",
            condition_value=0,
            condition_min_data=0,
            period_days=7,
            action_type="attribution_reminder",
            is_active=1,
        ),
        Rule(
            name="否定词生效提醒",
            description="否定关键词需 72 小时生效，否定 ASIN 需 96 小时",
            condition_field="clicks",
            condition_operator=">",
            condition_value=20,
            condition_min_data=20,
            period_days=3,
            action_type="negative_buffer_reminder",
            is_active=1,
        ),
    ]

    created = 0
    for rule in defaults:
        if rule.name not in existing_names:
            db.add(rule)
            created += 1
    if created > 0:
        db.commit()
    return created
