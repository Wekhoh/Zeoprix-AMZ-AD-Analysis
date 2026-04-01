"""
智能优化建议引擎
规则驱动的广告优化建议
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Campaign, PlacementRecord
from backend.services.kpi_calculator import calc_roas, calc_acos


def generate_suggestions(db: Session) -> list[dict]:
    """生成所有广告活动的优化建议"""
    suggestions = []

    # 获取每个活动的汇总数据
    campaign_stats = (
        db.query(
            Campaign.id,
            Campaign.name,
            Campaign.status,
            Campaign.base_bid,
            func.sum(PlacementRecord.impressions).label("imp"),
            func.sum(PlacementRecord.clicks).label("clk"),
            func.sum(PlacementRecord.spend).label("spd"),
            func.sum(PlacementRecord.orders).label("ord"),
            func.sum(PlacementRecord.sales).label("sal"),
            func.min(PlacementRecord.date).label("first_date"),
            func.max(PlacementRecord.date).label("last_date"),
        )
        .outerjoin(PlacementRecord)
        .group_by(Campaign.id)
        .all()
    )

    for stat in campaign_stats:
        cid, name, status, base_bid = stat[0], stat[1], stat[2], stat[3]
        imp, clk, spd, orders, sales = (
            stat[4] or 0,
            stat[5] or 0,
            stat[6] or 0.0,
            stat[7] or 0,
            stat[8] or 0.0,
        )
        first_date, last_date = stat[9], stat[10]

        roas = calc_roas(sales, spd)
        acos = calc_acos(spd, sales)

        # 规则 1: 高 ACOS 预警（ACOS > 50%）
        if acos and acos > 0.50:
            suggestions.append(
                {
                    "type": "high_acos",
                    "severity": "high",
                    "priority": 1,
                    "campaign_id": cid,
                    "campaign_name": name,
                    "title": f"ACOS 过高: {acos * 100:.1f}%",
                    "description": f"广告活动 ACOS 为 {acos * 100:.1f}%，远超盈利阈值。每花 $1 广告费只带来 ${1 / acos:.2f} 销售额。",
                    "action": "建议降低竞价 20-30% 或暂停表现最差的展示位置",
                    "metric": {
                        "acos": round(acos, 4),
                        "spend": round(spd, 2),
                        "roas": roas,
                    },
                }
            )

        # 规则 2: 有花费零订单
        if spd > 5.0 and orders == 0:
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
        if roas and roas > 3.0 and status != "Paused":
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
        if imp > 1000 and clk > 0:
            ctr = clk / imp
            if ctr < 0.002:
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
            if actual_cpc > base_bid * 1.5:
                suggestions.append(
                    {
                        "type": "high_cpc",
                        "severity": "medium",
                        "priority": 4,
                        "campaign_id": cid,
                        "campaign_name": name,
                        "title": f"CPC ${actual_cpc:.2f} 远超基础出价 ${base_bid}",
                        "description": f"实际 CPC (${actual_cpc:.2f}) 是基础出价 (${base_bid}) 的 {actual_cpc / base_bid:.1f} 倍，竞争可能过于激烈。",
                        "action": "考虑降低搜索顶部的竞价调整百分比",
                        "metric": {"cpc": round(actual_cpc, 2), "base_bid": base_bid},
                    }
                )

    # 获取展示位置级别的洞察
    placement_stats = (
        db.query(
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

    # 按优先级排序
    suggestions.sort(key=lambda x: x["priority"])
    return suggestions
