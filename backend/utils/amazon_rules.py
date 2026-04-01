"""Amazon Advertising platform rules and constants (sourced from official docs 2026)"""

# Attribution windows by ad type
ATTRIBUTION_WINDOW = {
    "SP": 7,  # Sponsored Products (seller)
    "SB": 14,  # Sponsored Brands
    "SD": 14,  # Sponsored Display
    "SBV": 14,  # Sponsored Brands Video
    "DSP": 14,  # Amazon DSP
}

# Budget rules
MAX_DAILY_OVERSPEND_PCT = 1.0  # Amazon allows up to 100% daily overspend
MONTHLY_BUDGET_FORMULA = "daily_budget x days_in_month"

# Negative keyword buffer
NEGATIVE_KEYWORD_BUFFER_HOURS = 72
NEGATIVE_ASIN_BUFFER_HOURS = 96

# Placement adjustment limits
MAX_PLACEMENT_ADJUSTMENT_PCT = 900  # +900% = 10x

# Dynamic bidding multipliers
DYNAMIC_MULTIPLIERS = {
    "Dynamic bidding (up and down)": {"max_up": 2.0, "max_down": 0.0},
    "Dynamic bidding (down only)": {"max_up": 1.0, "max_down": 0.0},
    "Fixed bids": {"max_up": 1.0, "max_down": 1.0},
}

# Ad eligibility checklist
AD_ELIGIBILITY_CHECKLIST = [
    {"item": "专业卖家账户", "description": "必须是 Professional Seller 账户"},
    {"item": "账户信誉良好", "description": "无严重违规或欠款"},
    {"item": "Buy Box 资格", "description": "受定价、库存、配送速度、客户评价影响"},
    {"item": "商品有库存", "description": "FBA 或 FBM 库存 > 0"},
    {"item": "Listing 标题合规", "description": "≤ 200 字符，无特殊字符堆砌"},
    {"item": "无违规标记", "description": "商品未被限制或下架"},
]

# Keyword match type descriptions
MATCH_TYPE_RULES = {
    "Broad": "词序不限，匹配同义词。关键词可能完全不出现在搜索词中。",
    "Phrase": "必须保持关键词词序。允许前后缀。",
    "Exact": "精确匹配，但也匹配近义词和近似变体。",
    "Negative Phrase": "包含该短语即排除。最多 4 词，80 字符。",
    "Negative Exact": "完全一致才排除。最多 10 词，80 字符。",
}

# Auto targeting types
AUTO_TARGETING_TYPES = {
    "Close Match": "搜索词与商品紧密相关",
    "Loose Match": "搜索词与商品宽泛相关",
    "Substitutes": "展示在竞品详情页",
    "Complements": "展示在互补品详情页",
}


def get_attribution_window(ad_type: str) -> int:
    return ATTRIBUTION_WINDOW.get(ad_type, 7)


def calc_max_possible_cpc(
    base_bid: float,
    placement_adjustment_pct: float,
    bidding_strategy: str,
) -> float:
    placement_multiplier = 1 + (placement_adjustment_pct / 100)
    multiplier_info = DYNAMIC_MULTIPLIERS.get(bidding_strategy, {"max_up": 1.0})
    dynamic_multiplier = multiplier_info["max_up"]
    return round(base_bid * placement_multiplier * dynamic_multiplier, 2)


def get_bidding_strategy_advice(strategy: str, acos: float | None, roas: float | None) -> str:
    if not acos:
        return ""

    if strategy == "Fixed bids":
        if acos > 0.5:
            return "您使用固定竞价策略。建议直接降低基础出价 20-30%。"
        return ""

    if strategy == "Dynamic bidding (down only)":
        if acos > 0.5:
            return (
                "动态竞价（仅降低）已在低转化时自动降低出价。"
                "如果 ACOS 仍高，考虑降低基础出价或切换到固定竞价。"
            )
        return ""

    if strategy == "Dynamic bidding (up and down)":
        if acos > 0.5:
            return (
                "动态竞价（提高和降低）会在高转化机会时自动加价，导致 CPC 上升。"
                "建议切换到「仅降低」或降低广告位调整百分比。"
            )
        if roas and roas > 3.0:
            return "动态竞价正确识别了高转化机会，ROAS 表现优秀。建议保持当前策略。"
        return ""

    return ""
