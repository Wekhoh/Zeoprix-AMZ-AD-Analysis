"""Keyword report parsing + import + aggregation.

Handles Amazon SP Keyword Performance Report CSV.
Supports English + Chinese column headers.
"""

import csv
import io
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import AdGroup, Campaign, Keyword, KeywordDailyRecord
from backend.services.csv_parser import _clean_num

# Column mapping: Amazon report header → normalized field
COLUMN_MAP = {
    # Campaign
    "Campaign Name": "campaign_name",
    "广告活动名称": "campaign_name",
    # Ad Group
    "Ad Group Name": "ad_group_name",
    "广告组名称": "ad_group_name",
    # Keyword
    "Targeting": "keyword_text",
    "Keyword": "keyword_text",
    "关键词": "keyword_text",
    "投放": "keyword_text",
    # Match Type
    "Match Type": "match_type",
    "匹配类型": "match_type",
    # Bid
    "Bid": "bid",
    "Max Bid": "bid",
    "竞价": "bid",
    "最高竞价": "bid",
    # State
    "State": "state",
    "状态": "state",
    # Date
    "Date": "date",
    "日期": "date",
    "Start Date": "date",
    # Metrics
    "Impressions": "impressions",
    "曝光量": "impressions",
    "Clicks": "clicks",
    "点击量": "clicks",
    "Spend": "spend",
    "花费": "spend",
    "7 Day Total Orders (#)": "orders",
    "7 Day Total Orders": "orders",
    "订单": "orders",
    "7 Day Total Sales": "sales",
    "销售额": "sales",
}


def parse_keyword_report_csv(content: str) -> list[dict]:
    """Parse Amazon SP Keyword Report CSV with flexible column mapping."""
    if not content or not content.strip():
        return []

    reader = csv.reader(io.StringIO(content))
    header: Optional[list[str]] = None
    col_map: dict[int, str] = {}
    rows: list[dict] = []

    for line in reader:
        if not line or not any(c.strip() for c in line):
            continue

        if header is None:
            test_map: dict[int, str] = {}
            for i, col in enumerate(line):
                clean = col.strip().strip("\ufeff")
                if clean in COLUMN_MAP:
                    test_map[i] = COLUMN_MAP[clean]
            if "keyword_text" in test_map.values():
                header = line
                col_map = test_map
            continue

        row: dict = {}
        for idx, field in col_map.items():
            if idx >= len(line):
                continue
            val = line[idx].strip()
            if field in (
                "campaign_name",
                "ad_group_name",
                "keyword_text",
                "match_type",
                "state",
                "date",
            ):
                row[field] = val
            elif field == "bid":
                try:
                    row[field] = float(_clean_num(val)) if val else None
                except (ValueError, TypeError):
                    row[field] = None
            else:
                try:
                    if field in ("spend", "sales"):
                        row[field] = float(_clean_num(val)) if val else 0.0
                    else:
                        row[field] = int(_clean_num(val, as_int=True)) if val else 0
                except (ValueError, TypeError):
                    row[field] = 0

        if row.get("keyword_text"):
            rows.append(row)

    return rows


def import_keyword_report(db: Session, content: str, filename: str = "") -> dict:
    """Parse + upsert keyword data from Amazon Keyword Report CSV.

    Returns {imported_keywords, updated_keywords, imported_daily, updated_daily, skipped, error?}.
    """
    parsed = parse_keyword_report_csv(content)
    if not parsed:
        return {
            "imported_keywords": 0,
            "updated_keywords": 0,
            "imported_daily": 0,
            "updated_daily": 0,
            "skipped": 0,
            "error": "未识别到关键词数据。请确认 CSV 包含 Keyword/Targeting 列。",
        }

    imported_keywords = 0
    updated_keywords = 0
    imported_daily = 0
    updated_daily = 0
    skipped = 0

    # Cache lookups to avoid repeated queries
    campaign_cache: dict[str, Campaign] = {}
    ad_group_cache: dict[str, AdGroup] = {}
    keyword_cache: dict[str, Keyword] = {}

    for row in parsed:
        kw_text = row.get("keyword_text", "").strip()
        if not kw_text:
            skipped += 1
            continue

        campaign_name = row.get("campaign_name", "").strip()
        ad_group_name = row.get("ad_group_name", "").strip() or "Default"
        match_type = row.get("match_type", "Broad").strip()
        date = row.get("date", "").strip()

        # Find or create campaign
        if campaign_name not in campaign_cache:
            camp = db.query(Campaign).filter(Campaign.name == campaign_name).first()
            if not camp:
                skipped += 1
                continue
            campaign_cache[campaign_name] = camp
        camp = campaign_cache[campaign_name]

        # Find or create ad group
        ag_key = f"{camp.id}|{ad_group_name}"
        if ag_key not in ad_group_cache:
            ag = (
                db.query(AdGroup)
                .filter(AdGroup.campaign_id == camp.id, AdGroup.name == ad_group_name)
                .first()
            )
            if not ag:
                ag = AdGroup(campaign_id=camp.id, name=ad_group_name, status="Enabled")
                db.add(ag)
                db.flush()
            ad_group_cache[ag_key] = ag
        ag = ad_group_cache[ag_key]

        # Find or create keyword
        kw_key = f"{ag.id}|{kw_text}|{match_type}"
        if kw_key not in keyword_cache:
            kw = (
                db.query(Keyword)
                .filter(
                    Keyword.ad_group_id == ag.id,
                    Keyword.keyword_text == kw_text,
                    Keyword.match_type == match_type,
                )
                .first()
            )
            if kw:
                # Update bid/state if provided
                if row.get("bid") is not None:
                    kw.bid = row["bid"]
                if row.get("state"):
                    kw.state = row["state"]
                updated_keywords += 1
            else:
                kw = Keyword(
                    ad_group_id=ag.id,
                    keyword_text=kw_text,
                    match_type=match_type,
                    bid=row.get("bid"),
                    state=row.get("state", "enabled"),
                )
                db.add(kw)
                db.flush()
                imported_keywords += 1
            keyword_cache[kw_key] = kw
        kw = keyword_cache[kw_key]

        # Upsert daily record if date is present
        if date:
            existing = (
                db.query(KeywordDailyRecord)
                .filter(KeywordDailyRecord.keyword_id == kw.id, KeywordDailyRecord.date == date)
                .first()
            )
            if existing:
                existing.impressions = row.get("impressions", 0)
                existing.clicks = row.get("clicks", 0)
                existing.spend = row.get("spend", 0.0)
                existing.orders = row.get("orders", 0)
                existing.sales = row.get("sales", 0.0)
                updated_daily += 1
            else:
                db.add(
                    KeywordDailyRecord(
                        keyword_id=kw.id,
                        date=date,
                        impressions=row.get("impressions", 0),
                        clicks=row.get("clicks", 0),
                        spend=row.get("spend", 0.0),
                        orders=row.get("orders", 0),
                        sales=row.get("sales", 0.0),
                    )
                )
                imported_daily += 1

    db.commit()
    return {
        "imported_keywords": imported_keywords,
        "updated_keywords": updated_keywords,
        "imported_daily": imported_daily,
        "updated_daily": updated_daily,
        "skipped": skipped,
    }


def get_keywords_for_ad_group(db: Session, ad_group_id: int) -> list[dict]:
    """Get all keywords in an ad group with aggregated KPIs."""
    keywords = db.query(Keyword).filter(Keyword.ad_group_id == ad_group_id).all()
    results = []
    for kw in keywords:
        agg = (
            db.query(
                func.sum(KeywordDailyRecord.impressions),
                func.sum(KeywordDailyRecord.clicks),
                func.sum(KeywordDailyRecord.spend),
                func.sum(KeywordDailyRecord.orders),
                func.sum(KeywordDailyRecord.sales),
            )
            .filter(KeywordDailyRecord.keyword_id == kw.id)
            .first()
        )
        imp, clk, spd, orders, sales = agg if agg else (0, 0, 0, 0, 0)
        imp = imp or 0
        clk = clk or 0
        spd = spd or 0.0
        orders = orders or 0
        sales = sales or 0.0

        results.append(
            {
                "id": kw.id,
                "keyword_text": kw.keyword_text,
                "match_type": kw.match_type,
                "bid": kw.bid,
                "state": kw.state,
                "impressions": imp,
                "clicks": clk,
                "spend": round(spd, 2),
                "orders": orders,
                "sales": round(sales, 2),
                "ctr": round(clk / imp, 4) if imp > 0 else None,
                "cpc": round(spd / clk, 2) if clk > 0 else None,
                "acos": round(spd / sales, 4) if sales > 0 else None,
                "roas": round(sales / spd, 2) if spd > 0 else None,
            }
        )
    return results


def get_keyword_history(
    db: Session,
    keyword_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[dict]:
    """Get daily performance records for a single keyword."""
    q = db.query(KeywordDailyRecord).filter(KeywordDailyRecord.keyword_id == keyword_id)
    if date_from:
        q = q.filter(KeywordDailyRecord.date >= date_from)
    if date_to:
        q = q.filter(KeywordDailyRecord.date <= date_to)
    q = q.order_by(KeywordDailyRecord.date)

    return [
        {
            "date": r.date,
            "impressions": r.impressions,
            "clicks": r.clicks,
            "spend": round(r.spend, 2),
            "orders": r.orders,
            "sales": round(r.sales, 2),
            "ctr": round(r.clicks / r.impressions, 4) if r.impressions > 0 else None,
            "cpc": round(r.spend / r.clicks, 2) if r.clicks > 0 else None,
            "acos": round(r.spend / r.sales, 4) if r.sales > 0 else None,
            "roas": round(r.sales / r.spend, 2) if r.spend > 0 else None,
        }
        for r in q.all()
    ]


def get_ad_groups_for_campaign(db: Session, campaign_id: int) -> list[dict]:
    """List ad groups for a campaign with keyword count + aggregated KPIs."""
    ad_groups = db.query(AdGroup).filter(AdGroup.campaign_id == campaign_id).all()
    results = []
    for ag in ad_groups:
        kw_count = db.query(Keyword).filter(Keyword.ad_group_id == ag.id).count()
        agg = (
            db.query(
                func.sum(KeywordDailyRecord.impressions),
                func.sum(KeywordDailyRecord.clicks),
                func.sum(KeywordDailyRecord.spend),
                func.sum(KeywordDailyRecord.orders),
                func.sum(KeywordDailyRecord.sales),
            )
            .join(Keyword, KeywordDailyRecord.keyword_id == Keyword.id)
            .filter(Keyword.ad_group_id == ag.id)
            .first()
        )
        imp, clk, spd, orders, sales = agg if agg else (0, 0, 0, 0, 0)
        imp = imp or 0
        clk = clk or 0
        spd = spd or 0.0
        orders = orders or 0
        sales = sales or 0.0

        results.append(
            {
                "id": ag.id,
                "name": ag.name,
                "status": ag.status,
                "default_bid": ag.default_bid,
                "keyword_count": kw_count,
                "impressions": imp,
                "clicks": clk,
                "spend": round(spd, 2),
                "orders": orders,
                "sales": round(sales, 2),
                "acos": round(spd / sales, 4) if sales > 0 else None,
                "roas": round(sales / spd, 2) if spd > 0 else None,
            }
        )
    return results
