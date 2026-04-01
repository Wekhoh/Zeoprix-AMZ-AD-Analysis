"""
广告活动名称解析器
直接提取自 data_importer.py L152-182
已通过 520 条数据审计验证
"""

import re
from typing import Optional

# 广告组合映射（根据广告活动名称前缀）
PORTFOLIO_MAP = {
    "DBL": "ZP-TP01-DBL-LOT01",
    "BLK": "ZP-TP01-BLK-LOT01",
}

# 展示位置转换映射
PLACEMENT_MAP = {
    "PLACEMENT_TOP": "搜索顶部",
    "PLACEMENT_REST_OF_SEARCH": "搜索其他位置",
    "PLACEMENT_PRODUCT_PAGE": "产品页面",
}


def get_portfolio_name(campaign_name: str) -> Optional[str]:
    """根据广告活动名称获取组合名称"""
    if not campaign_name:
        return None
    for prefix, portfolio in PORTFOLIO_MAP.items():
        if campaign_name.startswith(prefix):
            return portfolio
    return None


def extract_default_bid(campaign_name: str) -> Optional[float]:
    """
    从广告活动名称提取默认竞价值
    DBL-TP01-LOT01-SP自动紧密动低-1.94bid → 1.94
    """
    if not campaign_name:
        return None
    match = re.search(r"(\d+\.?\d*)bid", campaign_name, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def extract_variant_code(campaign_name: str) -> Optional[str]:
    """
    从广告活动名称提取产品变体代码
    DBL-TP01-LOT01-... → 'DBL'
    BLK-TP01-LOT01-... → 'BLK'
    """
    if not campaign_name:
        return None
    for prefix in PORTFOLIO_MAP:
        if campaign_name.startswith(prefix):
            return prefix
    return None


def extract_bidding_strategy_type(campaign_name: str) -> str:
    """
    从广告活动名称推断竞价策略类型
    ...动低... → 'Dynamic bidding (down only)'
    ...动提高低... → 'Dynamic bidding (up and down)'
    ...固定... → 'Fixed bids'
    """
    if not campaign_name:
        return "Fixed bids"
    if "动提高低" in campaign_name:
        return "Dynamic bidding (up and down)"
    if "动低" in campaign_name:
        return "Dynamic bidding (down only)"
    return "Fixed bids"


def translate_placement(raw: str) -> str:
    """展示位置英文 → 中文"""
    return PLACEMENT_MAP.get(raw, raw)
