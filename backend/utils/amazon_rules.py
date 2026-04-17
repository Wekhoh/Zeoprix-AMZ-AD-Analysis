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

# Human-readable ad-type labels, used in UI tabs and alerts.
AD_TYPE_LABELS = {
    "SP": "Sponsored Products",
    "SB": "Sponsored Brands",
    "SBV": "Sponsored Brands Video",
    "SD": "Sponsored Display",
    "ST": "Sponsored TV",
    "DSP": "Amazon DSP",
}

# KPI field catalog by ad type.
#
# Every ad type shares the "core" set (impressions/clicks/spend/orders/sales +
# derived acos/roas/ctr/cpc). The "exclusive" set lists fields that ONLY exist
# for that type — frontend should branch on ad_type to show/hide these columns,
# and CSV parsers should map these headers only when the file was detected as
# that type.
#
# Field names match the Amazon Ads API v2 reporting schema (2025-2026),
# chosen so a future SP API integration can reuse the same keys.
KPI_FIELDS_CORE = (
    "impressions",
    "clicks",
    "spend",
    "orders",
    "sales",
    "acos",
    "roas",
    "ctr",
    "cpc",
)

KPI_FIELDS_BY_AD_TYPE: dict[str, tuple[str, ...]] = {
    # Sponsored Products — baseline set, nothing exclusive
    "SP": KPI_FIELDS_CORE,
    # Sponsored Brands — brand-awareness + new-to-brand metrics
    "SB": KPI_FIELDS_CORE
    + (
        "attributedBrandedSearches14d",
        "attributedOrdersNewToBrand14d",
        "attributedSalesNewToBrand14d",
        "attributedOrdersNewToBrandPercentage14d",
        "topOfSearchImpressionShare",
        "searchTermImpressionShare",
        "searchTermImpressionRank",
        "attributedBrandStorePageViews14d",
    ),
    # Sponsored Brands Video — SB plus video engagement
    "SBV": KPI_FIELDS_CORE
    + (
        "attributedBrandedSearches14d",
        "attributedOrdersNewToBrand14d",
        "videoViews",
        "video5SecondViews",
        "videoCompleteViews",
        "video5SecondViewRate",
        "videoCompleteViewRate",
        "videoUnmutes",
        "vctr",
        "vtr",
    ),
    # Sponsored Display — viewable-impression + cart-intent metrics
    "SD": KPI_FIELDS_CORE
    + (
        "viewableImpressions",
        "attributedDetailPageView14d",
        "attributedDetailPageViewNewToBrand14d",
        "attributedAddToCarts14d",
        "attributedAddToCartsPercentage14d",
        "attributedAddToCartClicks14d",
        "attributedBrandedSearches14d",
        "attributedOrdersNewToBrand14d",
        "viewAttributedSales14d",
        "viewAttributedDetailPageView14d",
    ),
    # Sponsored TV — limited rollout (2024+). Schema still stabilizing;
    # placeholder core set only. Extend when Unified Reporting exposes stable columns.
    "ST": KPI_FIELDS_CORE,
}

# Chinese labels for ad-type-specific KPI columns. Used by the frontend
# column-settings dropdown when an SB/SD/SBV report is active.
KPI_FIELD_LABELS = {
    "impressions": "曝光",
    "clicks": "点击",
    "spend": "花费",
    "orders": "订单",
    "sales": "销售额",
    "acos": "ACOS",
    "roas": "ROAS",
    "ctr": "CTR",
    "cpc": "CPC",
    # SB
    "attributedBrandedSearches14d": "品牌搜索 (14d)",
    "attributedOrdersNewToBrand14d": "新客订单 (14d)",
    "attributedSalesNewToBrand14d": "新客销售 (14d)",
    "attributedOrdersNewToBrandPercentage14d": "新客订单占比",
    "topOfSearchImpressionShare": "置顶搜索份额",
    "searchTermImpressionShare": "搜索词展示份额",
    "searchTermImpressionRank": "搜索词展示排名",
    "attributedBrandStorePageViews14d": "品牌店铺访问",
    # SBV
    "videoViews": "视频播放",
    "video5SecondViews": "5秒播放",
    "videoCompleteViews": "完整播放",
    "video5SecondViewRate": "5秒率",
    "videoCompleteViewRate": "完整率",
    "videoUnmutes": "取消静音",
    "vctr": "视频 CTR",
    "vtr": "视频观看率",
    # SD
    "viewableImpressions": "可见曝光",
    "attributedDetailPageView14d": "详情页浏览 (14d)",
    "attributedDetailPageViewNewToBrand14d": "新客详情页",
    "attributedAddToCarts14d": "加购 (14d)",
    "attributedAddToCartsPercentage14d": "加购率",
    "attributedAddToCartClicks14d": "加购点击",
    "viewAttributedSales14d": "视图归因销售",
    "viewAttributedDetailPageView14d": "视图归因详情页",
}


def get_kpi_fields(ad_type: str) -> tuple[str, ...]:
    """Return the KPI field catalog for a given ad type (core + exclusive).

    Unknown ad_types fall back to the SP (core-only) set so the UI still
    has something sensible to show.
    """
    return KPI_FIELDS_BY_AD_TYPE.get(ad_type.upper(), KPI_FIELDS_CORE)


def get_kpi_exclusive_fields(ad_type: str) -> tuple[str, ...]:
    """Fields that ONLY exist for this ad type (not in the core set)."""
    return tuple(f for f in get_kpi_fields(ad_type) if f not in KPI_FIELDS_CORE)


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
