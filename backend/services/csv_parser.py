"""
亚马逊广告 CSV 数据解析器
支持多种报告类型：SP 展示位置、SB/SD 广告活动报告、通用广告报告
"""

import csv
import io
import os
import re
from typing import Optional

from backend.utils.date_parser import parse_date_from_filename
from backend.utils.campaign_parser import translate_placement


def _clean_num(val, as_int=False):
    """清理数值：去 $、逗号、百分号"""
    if not val or val in ("—", "-", "N/A", ""):
        return 0 if as_int else 0.0
    cleaned = str(val).replace("$", "").replace(",", "").replace("%", "").strip()
    return int(float(cleaned)) if as_int else float(cleaned)


def detect_report_type(headers: list[str]) -> str:
    """
    根据 CSV 列名自动识别报告类型
    返回: 'sp_placement' | 'sb_campaign' | 'sd_campaign' | 'generic_campaign'
    """
    header_set = {h.strip().lower() for h in headers}

    if "placement" in header_set:
        return "sp_placement"
    if "campaign bidding strategy" in header_set and "placement" not in header_set:
        return "generic_campaign"

    # SB 报告通常有这些列
    sb_markers = {
        "campaign name",
        "impressions",
        "clicks",
        "spend",
        "14 day total sales",
    }
    if sb_markers.issubset(header_set):
        return "sb_campaign"

    # SD 报告
    sd_markers = {
        "campaign name",
        "impressions",
        "clicks",
        "spend",
        "viewable impressions",
    }
    if sd_markers.issubset(header_set):
        return "sd_campaign"

    # 通用：有 Campaign Name + 基本指标
    if "campaign name" in header_set and "impressions" in header_set:
        return "generic_campaign"

    return "sp_placement"  # fallback


def _infer_ad_type(campaign_name: str, report_type: str) -> str:
    """从广告活动名称和报告类型推断广告类型"""
    name_lower = campaign_name.lower() if campaign_name else ""

    if report_type == "sb_campaign" or "sb" in name_lower.split("-"):
        return "SB"
    if report_type == "sd_campaign" or "sd" in name_lower.split("-"):
        return "SD"
    if "sbv" in name_lower or "video" in name_lower:
        return "SBV"

    # SP 进一步区分自动 vs 手动
    if "自动" in campaign_name or "auto" in name_lower:
        return "SP"  # SP Auto
    if "手动" in campaign_name or "manual" in name_lower:
        return "SP"  # SP Manual

    return "SP"  # 默认 SP


def parse_csv_placement_data(
    content: str,
    filename: str,
    campaign_name: Optional[str] = None,
) -> tuple[list[dict], dict]:
    """
    解析 SP 展示位置 CSV（原始逻辑，保持不变）
    """
    date_str = parse_date_from_filename(filename)
    if not date_str:
        raise ValueError(f"无法从文件名提取日期: {filename}")

    if not campaign_name:
        stem = os.path.splitext(filename)[0]
        campaign_name = re.sub(r"\d{4}$", "", stem)

    placement_results = []
    total_impressions = 0
    total_clicks = 0
    total_spend = 0.0
    total_orders = 0
    total_sales = 0.0
    bidding_strategy_raw = ""
    top_bid_adjustment = ""

    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        placement_raw = row.get("Placement", "")
        placement = translate_placement(placement_raw)
        bidding_strategy_raw = row.get("Campaign bidding strategy", "")
        bidding_strategy = bidding_strategy_raw

        impressions = _clean_num(row.get("Impressions", 0), as_int=True)
        clicks = _clean_num(row.get("Clicks", 0), as_int=True)
        spend = _clean_num(row.get("Spend (USD)", row.get("Spend", 0)))
        orders = _clean_num(
            row.get("Orders", row.get("14 Day Total Orders (#)", 0)), as_int=True
        )
        sales = _clean_num(row.get("Sales (USD)", row.get("14 Day Total Sales", 0)))

        if placement_raw == "PLACEMENT_TOP":
            top_bid_adjustment = row.get("Bid adjustment", "")

        total_impressions += impressions
        total_clicks += clicks
        total_spend += spend
        total_orders += orders
        total_sales += sales

        placement_results.append(
            {
                "date": date_str,
                "campaign_name": campaign_name,
                "placement": placement,
                "bidding_strategy": bidding_strategy,
                "impressions": impressions,
                "clicks": clicks,
                "spend": spend,
                "orders": orders,
                "sales": sales,
            }
        )

    campaign_summary = {
        "date": date_str,
        "campaign_name": campaign_name,
        "bidding_strategy": bidding_strategy_raw,
        "impressions": total_impressions,
        "clicks": total_clicks,
        "spend": total_spend,
        "orders": total_orders,
        "sales": total_sales,
        "top_bid_adjustment": top_bid_adjustment,
        "ad_type": _infer_ad_type(campaign_name, "sp_placement"),
    }

    return placement_results, campaign_summary


def parse_csv_campaign_report(
    content: str,
    filename: str,
) -> list[dict]:
    """
    解析 SB/SD/通用广告活动 CSV 报告
    返回广告活动级别的汇总数据列表
    """
    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames or []
    report_type = detect_report_type(headers)

    results = []
    for row in reader:
        campaign_name = (
            row.get("Campaign Name", "")
            or row.get("Campaign name", "")
            or row.get("campaign_name", "")
        ).strip()

        if not campaign_name:
            continue

        # 统一提取指标（兼容不同列名）
        impressions = _clean_num(
            row.get("Impressions", row.get("impressions", 0)), as_int=True
        )
        clicks = _clean_num(row.get("Clicks", row.get("clicks", 0)), as_int=True)
        spend = _clean_num(row.get("Spend", row.get("Spend (USD)", row.get("Cost", 0))))
        orders = _clean_num(
            row.get(
                "14 Day Total Orders (#)", row.get("Orders", row.get("Purchases", 0))
            ),
            as_int=True,
        )
        sales = _clean_num(
            row.get("14 Day Total Sales", row.get("Sales (USD)", row.get("Sales", 0)))
        )

        ad_type = _infer_ad_type(campaign_name, report_type)

        # 日期：尝试从行数据中获取，否则从文件名
        date_str = row.get("Date", row.get("date", ""))
        if not date_str:
            date_str = parse_date_from_filename(filename) or ""

        results.append(
            {
                "date": date_str,
                "campaign_name": campaign_name,
                "ad_type": ad_type,
                "impressions": impressions,
                "clicks": clicks,
                "spend": spend,
                "orders": orders,
                "sales": sales,
                "bidding_strategy": row.get(
                    "Bidding strategy", row.get("Campaign bidding strategy", "")
                ),
            }
        )

    return results
