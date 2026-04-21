"""
智能优化建议引擎
规则驱动的广告优化建议
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Campaign, PlacementRecord, SuggestionStatus
from backend.services.kpi_calculator import calc_acos, calc_roas
from backend.utils.amazon_rules import (
    calc_max_possible_cpc,
    get_bidding_strategy_advice,
)


def _suggestion_hash(suggestion_type: str, campaign_id: int | None) -> str:
    """Stable identifier for a suggestion used for lifecycle tracking."""
    return f"{suggestion_type}:{campaign_id or 0}"


def _calc_target_bid(
    base_bid: float, actual_acos: float, target_acos: float = settings.ACOS_TARGET
) -> float:
    """Calculate target bid to achieve target ACOS, assuming linear bid-CPC relationship."""
    return round(max(base_bid * (target_acos / actual_acos), 0.02), 2)


def generate_suggestions(
    db: Session,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """生成所有广告活动的优化建议（可选日期范围）"""
    suggestions = []

    # 获取每个活动的汇总数据
    base_q = db.query(
        Campaign.id,
        Campaign.name,
        Campaign.status,
        Campaign.base_bid,
        Campaign.ad_type,
        Campaign.bidding_strategy,
        func.sum(PlacementRecord.impressions).label("imp"),
        func.sum(PlacementRecord.clicks).label("clk"),
        func.sum(PlacementRecord.spend).label("spd"),
        func.sum(PlacementRecord.orders).label("ord"),
        func.sum(PlacementRecord.sales).label("sal"),
        func.min(PlacementRecord.date).label("first_date"),
        func.max(PlacementRecord.date).label("last_date"),
    ).outerjoin(PlacementRecord)

    if date_from:
        base_q = base_q.filter(PlacementRecord.date >= date_from)
    if date_to:
        base_q = base_q.filter(PlacementRecord.date <= date_to)

    campaign_stats = base_q.group_by(Campaign.id).all()

    for stat in campaign_stats:
        cid, name, status, base_bid = stat[0], stat[1], stat[2], stat[3]
        # stat[4] ad_type reserved for future per-ad-type rule branches
        bidding_strategy = stat[5]
        imp, clk, spd, orders, sales = (
            stat[6] or 0,
            stat[7] or 0,
            stat[8] or 0.0,
            stat[9] or 0,
            stat[10] or 0.0,
        )
        # stat[11]/stat[12] first_date/last_date reserved for date-range surfacing

        roas = calc_roas(sales, spd)
        acos = calc_acos(spd, sales)

        # 规则 1: 高 ACOS 预警
        if acos and acos > settings.ACOS_WARNING_THRESHOLD:
            strategy = bidding_strategy or "Fixed bids"
            strategy_advice = get_bidding_strategy_advice(strategy, acos, roas)

            if base_bid:
                target_bid = _calc_target_bid(base_bid, acos)
                action_text = (
                    f"建议将竞价从 ${base_bid:.2f} 降至 ${target_bid:.2f}"
                    f"（目标 ACOS 30%，降幅 {(1 - target_bid / base_bid) * 100:.0f}%）"
                )
            else:
                action_text = "建议降低竞价 20-30% 或暂停表现最差的展示位置"

            if strategy_advice:
                action_text = f"{action_text}。{strategy_advice}"
            suggestions.append(
                {
                    "type": "high_acos",
                    "severity": "high",
                    "priority": 1,
                    "campaign_id": cid,
                    "campaign_name": name,
                    "title": f"ACOS 过高: {acos * 100:.1f}%",
                    "description": f"广告活动 ACOS 为 {acos * 100:.1f}%，远超盈利阈值。每花 $1 广告费只带来 ${1 / acos:.2f} 销售额。（竞价策略: {strategy}）",
                    "action": action_text,
                    "metric": {
                        "acos": round(acos, 4),
                        "spend": round(spd, 2),
                        "roas": roas,
                        "target_bid": _calc_target_bid(base_bid, acos) if base_bid else None,
                    },
                }
            )

        # 规则 2: 有花费零订单
        if spd > settings.ZERO_ORDERS_MIN_SPEND and orders == 0:
            suggestions.append(
                {
                    "type": "zero_orders",
                    "severity": "critical",
                    "priority": 0,
                    "campaign_id": cid,
                    "campaign_name": name,
                    "title": f"花费 ${spd:.2f} 但零订单",
                    "description": f"已花费 ${spd:.2f} 获得 {clk} 次点击，但没有产生任何订单。广告预算正在浪费。",
                    "action": "建议立即暂停此活动，或大幅降低竞价至 $0.50 以下测试",
                    "metric": {
                        "spend": round(spd, 2),
                        "clicks": clk,
                        "impressions": imp,
                    },
                }
            )

        # 规则 3: 高 ROAS 活动（ROAS > 3）— 增加预算建议
        if roas and roas > settings.ROAS_SCALE_UP_THRESHOLD and status != "Paused":
            suggestions.append(
                {
                    "type": "scale_up",
                    "severity": "opportunity",
                    "priority": 2,
                    "campaign_id": cid,
                    "campaign_name": name,
                    "title": f"ROAS 优秀: {roas:.2f}，可扩量",
                    "description": f"ROAS 达到 {roas:.2f}，每花 $1 带来 ${roas:.2f} 销售额。这是扩大投入的好时机。",
                    "action": "建议增加日预算 30-50%，同时监控 ACOS 变化",
                    "metric": {"roas": roas, "acos": acos, "orders": orders},
                }
            )

        # 规则 4: 低点击率（CTR < 0.2%）— 可能listing或关键词有问题
        if imp > settings.CTR_MIN_IMPRESSIONS and clk > 0:
            ctr = clk / imp
            if ctr < settings.CTR_WARNING_THRESHOLD:
                suggestions.append(
                    {
                        "type": "low_ctr",
                        "severity": "medium",
                        "priority": 3,
                        "campaign_id": cid,
                        "campaign_name": name,
                        "title": f"点击率过低: {ctr * 100:.2f}%",
                        "description": f"曝光 {imp:,} 次但点击率仅 {ctr * 100:.2f}%。可能是主图、标题或价格缺乏吸引力。",
                        "action": "建议优化商品主图和标题，或检查竞品定价",
                        "metric": {
                            "ctr": round(ctr, 4),
                            "impressions": imp,
                            "clicks": clk,
                        },
                    }
                )

        # 规则 5: 高 CPC 相对于出价（实际 CPC 远高于基础出价）
        if clk > 0 and base_bid:
            actual_cpc = spd / clk
            if actual_cpc > base_bid * settings.CPC_OVERPAY_RATIO:
                strategy = bidding_strategy or "Fixed bids"
                max_cpc = calc_max_possible_cpc(base_bid, 0, strategy)

                # Calculate recommended bid reduction
                if acos and acos > 0:
                    target_bid = _calc_target_bid(base_bid, acos)
                    action_text = (
                        f"建议将基础出价从 ${base_bid:.2f} 降至 ${target_bid:.2f}，"
                        f"并降低搜索顶部竞价调整百分比"
                    )
                else:
                    action_text = "考虑降低搜索顶部的竞价调整百分比"

                suggestions.append(
                    {
                        "type": "high_cpc",
                        "severity": "medium",
                        "priority": 4,
                        "campaign_id": cid,
                        "campaign_name": name,
                        "title": f"CPC ${actual_cpc:.2f} 远超基础出价 ${base_bid}",
                        "description": f"实际 CPC (${actual_cpc:.2f}) 是基础出价 (${base_bid}) 的 {actual_cpc / base_bid:.1f} 倍，竞争可能过于激烈。理论最高 CPC（无广告位调整）: ${max_cpc}",
                        "action": action_text,
                        "metric": {
                            "cpc": round(actual_cpc, 2),
                            "base_bid": base_bid,
                            "max_cpc": max_cpc,
                        },
                    }
                )

        # 规则 7: 投放中但零花费/曝光（可能丢失 Buy Box）
        if status != "Paused" and spd == 0 and imp == 0:
            suggestions.append(
                {
                    "type": "zero_spend",
                    "severity": "critical",
                    "priority": 0,
                    "campaign_id": cid,
                    "campaign_name": name,
                    "title": "投放中但无花费/曝光",
                    "description": "广告活动处于投放状态但没有任何花费和曝光。",
                    "action": (
                        "常见原因：1) 失去 Buy Box 资格 2) 出价过低 "
                        "3) 关键词全部被否定 4) 商品下架或无库存。"
                        "请检查 Seller Central 中的商品状态。"
                    ),
                    "metric": {
                        "status": status,
                        "impressions": imp,
                        "spend": round(spd, 2),
                    },
                }
            )

    # 获取展示位置级别的洞察
    place_q = db.query(
        PlacementRecord.placement_type,
        func.sum(PlacementRecord.impressions),
        func.sum(PlacementRecord.clicks),
        func.sum(PlacementRecord.spend),
        func.sum(PlacementRecord.orders),
        func.sum(PlacementRecord.sales),
    )
    if date_from:
        place_q = place_q.filter(PlacementRecord.date >= date_from)
    if date_to:
        place_q = place_q.filter(PlacementRecord.date <= date_to)
    placement_stats = place_q.group_by(PlacementRecord.placement_type).all()

    for pstat in placement_stats:
        ptype, imp, clk, spd, orders, sales = pstat
        imp, clk, spd, orders, sales = (
            imp or 0,
            clk or 0,
            spd or 0.0,
            orders or 0,
            sales or 0.0,
        )
        roas = calc_roas(sales, spd)
        acos = calc_acos(spd, sales)

        # 规则 6: 某展示位置表现突出
        if roas and roas > 2.0 and spd > 10:
            suggestions.append(
                {
                    "type": "placement_insight",
                    "severity": "info",
                    "priority": 5,
                    "campaign_id": None,
                    "campaign_name": f"所有活动 - {ptype}",
                    "title": f"「{ptype}」表现优秀 (ROAS {roas:.2f})",
                    "description": f"在「{ptype}」展示位置上，整体 ROAS 达到 {roas:.2f}。可以考虑增加该位置的竞价调整。",
                    "action": f"建议提高「{ptype}」的竞价调整百分比",
                    "metric": {
                        "roas": roas,
                        "acos": acos,
                        "spend": round(spd, 2),
                        "orders": orders,
                    },
                }
            )

    # Add stable hashes for lifecycle tracking
    for s in suggestions:
        s["hash"] = _suggestion_hash(s["type"], s.get("campaign_id"))

    # Filter out resolved/dismissed/active-snoozed suggestions (DB-level filtering)
    from datetime import date

    from sqlalchemy import and_, or_

    today_str = date.today().isoformat()
    hidden_rows = (
        db.query(SuggestionStatus.suggestion_hash)
        .filter(
            or_(
                SuggestionStatus.status.in_(["resolved", "dismissed"]),
                and_(
                    SuggestionStatus.status == "snoozed",
                    SuggestionStatus.snooze_until.isnot(None),
                    SuggestionStatus.snooze_until > today_str,
                ),
            )
        )
        .all()
    )
    hidden_hashes = {row[0] for row in hidden_rows}

    suggestions = [s for s in suggestions if s["hash"] not in hidden_hashes]

    # 按优先级排序
    suggestions.sort(key=lambda x: x["priority"])
    return suggestions
