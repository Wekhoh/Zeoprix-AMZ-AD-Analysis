"""
搜索词分析服务
- 解析亚马逊搜索词报告 CSV
- 高转化词识别
- 否定词建议
- 关键词汇总统计
"""

import csv
import io
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Campaign
from backend.models.search_term import SearchTermReport

# 亚马逊搜索词报告的可能列名映射
COLUMN_MAP = {
    # 英文列名 → 标准字段
    "Customer Search Term": "search_term",
    "Search term": "search_term",
    "7 Day Total Orders (#)": "orders",
    "7 Day Total Sales": "sales",
    "Impressions": "impressions",
    "Clicks": "clicks",
    "Spend": "spend",
    "Match Type": "match_type",
    "Campaign Name": "campaign_name",
    "Ad Group Name": "ad_group_name",
    # 中文列名
    "客户搜索词": "search_term",
    "搜索词": "search_term",
    "7天总订单数": "orders",
    "7天总销售额": "sales",
    "曝光量": "impressions",
    "点击量": "clicks",
    "花费": "spend",
    "匹配类型": "match_type",
    "广告活动名称": "campaign_name",
    "广告组名称": "ad_group_name",
}


def _clean_numeric(val: str) -> float:
    if not val or val in ("—", "-", "N/A"):
        return 0.0
    return float(str(val).replace("$", "").replace(",", "").replace("%", "").strip())


def _map_columns(header: list[str]) -> dict[int, str]:
    """将 CSV 列索引映射到标准字段名"""
    mapping = {}
    for i, col in enumerate(header):
        col_clean = col.strip().strip("\ufeff")
        if col_clean in COLUMN_MAP:
            mapping[i] = COLUMN_MAP[col_clean]
    return mapping


def parse_search_term_csv(content: str) -> list[dict]:
    """解析搜索词报告 CSV"""
    reader = csv.reader(io.StringIO(content))

    # 跳过亚马逊报告的元数据行（通常前几行不是数据）
    header = None
    col_map = {}
    rows = []

    for line in reader:
        if not line or not any(line):
            continue

        # 尝试识别表头
        if not header:
            test_map = _map_columns(line)
            if "search_term" in test_map.values():
                header = line
                col_map = test_map
                continue
            continue

        # 解析数据行
        row = {}
        for idx, field in col_map.items():
            if idx < len(line):
                val = line[idx].strip()
                if field in ("impressions", "clicks", "orders"):
                    row[field] = int(_clean_numeric(val))
                elif field in ("spend", "sales"):
                    row[field] = _clean_numeric(val)
                else:
                    row[field] = val
        if row.get("search_term"):
            rows.append(row)

    return rows


def import_search_terms(db: Session, content: str, filename: str) -> dict:
    """导入搜索词数据到数据库"""
    rows = parse_search_term_csv(content)
    if not rows:
        return {
            "imported": 0,
            "skipped": 0,
            "error": "未识别到搜索词数据，请检查 CSV 格式",
        }

    imported = 0
    skipped = 0

    for row in rows:
        campaign_name = row.get("campaign_name", "")
        search_term = row.get("search_term", "")

        if not search_term:
            continue

        # 查找或跳过 campaign
        campaign = None
        if campaign_name:
            campaign = db.query(Campaign).filter_by(name=campaign_name).first()

        # 简单去重：同 campaign + 同 search_term（聚合而非逐日）
        if campaign:
            existing = (
                db.query(SearchTermReport)
                .filter_by(
                    campaign_id=campaign.id,
                    search_term=search_term,
                )
                .first()
            )

            if existing:
                # 累加数据
                existing.impressions += row.get("impressions", 0)
                existing.clicks += row.get("clicks", 0)
                existing.spend += row.get("spend", 0.0)
                existing.orders += row.get("orders", 0)
                existing.sales += row.get("sales", 0.0)
                skipped += 1
                continue

        record = SearchTermReport(
            date=filename.replace(".csv", "")[-8:] if len(filename) > 8 else "",
            campaign_id=campaign.id if campaign else None,
            search_term=search_term,
            match_type=row.get("match_type", ""),
            impressions=row.get("impressions", 0),
            clicks=row.get("clicks", 0),
            spend=row.get("spend", 0.0),
            orders=row.get("orders", 0),
            sales=row.get("sales", 0.0),
        )
        db.add(record)
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped}


def get_search_term_summary(db: Session, campaign_id: Optional[int] = None) -> list[dict]:
    """搜索词汇总（按搜索词聚合）"""
    q = db.query(
        SearchTermReport.search_term,
        func.sum(SearchTermReport.impressions).label("impressions"),
        func.sum(SearchTermReport.clicks).label("clicks"),
        func.sum(SearchTermReport.spend).label("spend"),
        func.sum(SearchTermReport.orders).label("orders"),
        func.sum(SearchTermReport.sales).label("sales"),
    )
    if campaign_id:
        q = q.filter(SearchTermReport.campaign_id == campaign_id)

    rows = (
        q.group_by(SearchTermReport.search_term)
        .order_by(func.sum(SearchTermReport.spend).desc())
        .all()
    )

    results = []
    for r in rows:
        imp, clk, spd, orders, sales = (
            r[1] or 0,
            r[2] or 0,
            r[3] or 0.0,
            r[4] or 0,
            r[5] or 0.0,
        )
        results.append(
            {
                "search_term": r[0],
                "impressions": imp,
                "clicks": clk,
                "spend": round(spd, 2),
                "orders": orders,
                "sales": round(sales, 2),
                "ctr": round(clk / imp, 4) if imp > 0 else None,
                "cpc": round(spd / clk, 2) if clk > 0 else None,
                "cvr": round(orders / clk, 4) if clk > 0 else None,
                "acos": round(spd / sales, 4) if sales > 0 else None,
                "roas": round(sales / spd, 2) if spd > 0 else None,
            }
        )
    return results


def get_top_converting_terms(
    db: Session, min_orders: int = 1, campaign_id: Optional[int] = None
) -> list[dict]:
    """高转化搜索词（有订单的）"""
    all_terms = get_search_term_summary(db, campaign_id)
    return [t for t in all_terms if t["orders"] >= min_orders]


def get_negative_candidates(
    db: Session, min_clicks: int = 5, campaign_id: Optional[int] = None
) -> list[dict]:
    """否定词候选（高点击零订单）"""
    all_terms = get_search_term_summary(db, campaign_id)
    return [
        {**t, "reason": f"点击 {t['clicks']} 次，花费 ${t['spend']:.2f}，零订单"}
        for t in all_terms
        if t["clicks"] >= min_clicks and t["orders"] == 0
    ]


def _bucket_terms_with_campaign(db: Session, campaign_id: Optional[int] = None) -> list[dict]:
    """搜索词汇总（按 search_term + campaign 聚合，包含来源活动名称）"""
    q = db.query(
        SearchTermReport.search_term,
        SearchTermReport.campaign_id,
        Campaign.name.label("campaign_name"),
        func.sum(SearchTermReport.impressions).label("impressions"),
        func.sum(SearchTermReport.clicks).label("clicks"),
        func.sum(SearchTermReport.spend).label("spend"),
        func.sum(SearchTermReport.orders).label("orders"),
        func.sum(SearchTermReport.sales).label("sales"),
    ).outerjoin(Campaign, SearchTermReport.campaign_id == Campaign.id)

    if campaign_id:
        q = q.filter(SearchTermReport.campaign_id == campaign_id)

    rows = (
        q.group_by(SearchTermReport.search_term, SearchTermReport.campaign_id)
        .order_by(func.sum(SearchTermReport.spend).desc())
        .all()
    )

    results = []
    for r in rows:
        imp, clk, spd, orders, sales = (
            r[3] or 0,
            r[4] or 0,
            r[5] or 0.0,
            r[6] or 0,
            r[7] or 0.0,
        )
        results.append(
            {
                "search_term": r[0],
                "campaign_id": r[1],
                "campaign_name": r[2] or "未关联",
                "impressions": imp,
                "clicks": clk,
                "spend": round(spd, 2),
                "orders": orders,
                "sales": round(sales, 2),
                "ctr": round(clk / imp, 4) if imp > 0 else None,
                "cpc": round(spd / clk, 2) if clk > 0 else None,
                "cvr": round(orders / clk, 4) if clk > 0 else None,
                "acos": round(spd / sales, 4) if sales > 0 else None,
                "roas": round(sales / spd, 2) if spd > 0 else None,
            }
        )
    return results


def classify_search_terms_4bucket(
    db: Session,
    campaign_id: Optional[int] = None,
    target_acos: float = 0.30,
) -> dict:
    """
    4-Bucket 搜索词分析框架
    - Winners: orders >= 2 且 ACoS < 目标
    - Potential: impressions > 100 且 CTR < 0.3%，或 clicks > 10 且 orders = 0 但花费不高
    - Money Pits: clicks > 20 且 orders = 0（烧钱词）
    - Low Data: clicks < 15（数据不足，暂不操作）

    B2 enhancements:
    - Never-Negative whitelist: money_pits terms on the whitelist get
      ``whitelisted=True`` and a different action message instead of being
      hidden. The operator can still see the data but the system won't
      suggest negating them.
    - Suggested bid: winners and potential items get a ``suggested_bid``
      computed from their average CPC (winners +10%, potential -20%).

    Returns: {"winners": [...], "potential": [...], "money_pits": [...], "low_data": [...], "stats": {...}}
    """
    from backend.models import NegativeWhitelist

    all_terms = _bucket_terms_with_campaign(db, campaign_id)

    # Pre-fetch whitelist as a set for O(1) lookups
    whitelist_terms = {r.search_term for r in db.query(NegativeWhitelist.search_term).all()}

    winners = []
    potential = []
    money_pits = []
    low_data = []

    for t in all_terms:
        clicks = t["clicks"]
        orders = t["orders"]
        acos = t["acos"]
        impressions = t["impressions"]
        ctr = t["ctr"]
        cpc = t["cpc"]
        is_whitelisted = t["search_term"] in whitelist_terms

        if clicks < 15:
            low_data.append({**t, "bucket": "low_data", "action": "等待数据积累，暂不操作"})
        elif orders >= 2 and acos is not None and acos < target_acos:
            suggested_bid = round(cpc * 1.1, 2) if cpc else None
            winners.append(
                {
                    **t,
                    "bucket": "winners",
                    "action": "提高竞价 10-20%，迁移至精准匹配独立广告",
                    "suggested_bid": suggested_bid,
                }
            )
        elif clicks >= 20 and orders == 0:
            if is_whitelisted:
                money_pits.append(
                    {
                        **t,
                        "bucket": "money_pits",
                        "whitelisted": True,
                        "action": f"已加入白名单（已烧 ${t['spend']:.2f}），不建议否定",
                    }
                )
            else:
                money_pits.append(
                    {
                        **t,
                        "bucket": "money_pits",
                        "whitelisted": False,
                        "action": f"立即加入精准否定（已烧 ${t['spend']:.2f}）",
                    }
                )
        elif (impressions > 100 and ctr is not None and ctr < 0.003) or (
            clicks > 10 and orders == 0
        ):
            suggested_bid = round(cpc * 0.8, 2) if cpc else None
            potential.append(
                {
                    **t,
                    "bucket": "potential",
                    "action": "优化 Listing（主图、标题、价格）提升转化",
                    "suggested_bid": suggested_bid,
                }
            )
        elif orders >= 1:
            suggested_bid = round(cpc * 1.1, 2) if cpc else None
            winners.append(
                {
                    **t,
                    "bucket": "winners",
                    "action": "有转化潜力，观察并适度提高竞价",
                    "suggested_bid": suggested_bid,
                }
            )
        else:
            suggested_bid = round(cpc * 0.8, 2) if cpc else None
            potential.append(
                {
                    **t,
                    "bucket": "potential",
                    "action": "继续观察，考虑优化匹配方式",
                    "suggested_bid": suggested_bid,
                }
            )

    return {
        "winners": winners,
        "potential": potential,
        "money_pits": money_pits,
        "low_data": low_data,
        "stats": {
            "total": len(all_terms),
            "winners_count": len(winners),
            "potential_count": len(potential),
            "money_pits_count": len(money_pits),
            "low_data_count": len(low_data),
        },
    }
