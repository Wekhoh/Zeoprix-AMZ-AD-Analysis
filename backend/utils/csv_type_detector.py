"""Detect which Amazon report a user-uploaded CSV is, by column signature.

Used by the batch-import flow so a seller can drag multiple files and the
server routes each to the correct parser without asking "which kind?".

Signatures were lifted directly from the existing per-type parsers and
from the Amazon Ads API v2 reporting docs (2025-2026):
- placement: backend/services/csv_parser.py → "Placement" column (SP)
- keyword: backend/services/keyword_service.py::COLUMN_MAP (SP)
- inventory: backend/services/inventory_service.py::COLUMN_MAP
- search_term: well-known "Customer Search Term" / "Search Term" header
- operation_log: pipe-delimited TXT, not CSV — detected via format shape
- sbv (Sponsored Brands Video): videoViews / video5SecondViews exclusive
- sb (Sponsored Brands): attributedBrandedSearches14d / topOfSearchImpressionShare
- sd (Sponsored Display): viewableImpressions / attributedAddToCarts14d
"""

from __future__ import annotations

from typing import Literal

CsvType = Literal[
    "placement",
    "search_term",
    "operation_log",
    "inventory",
    "keyword",
    "sb",
    "sd",
    "sbv",
    "unknown",
]

# Authoritative signature set per file type. First match wins. Order matters:
# - SBV (video subset of SB) before SB — video metrics are the tiebreaker
# - search_term before keyword (some keyword reports include search term column)
# - inventory before placement (both may appear but inventory is the more specific)
_SEARCH_TERM_MARKERS = frozenset({"Customer Search Term", "Search Term", "搜索词", "客户搜索词"})

_KEYWORD_MARKERS = frozenset({"Targeting", "Keyword", "Match Type", "关键词", "投放", "匹配类型"})

_PLACEMENT_MARKERS = frozenset({"Placement", "Campaign bidding strategy", "Bid adjustment"})

_INVENTORY_MARKERS = frozenset(
    {
        "afn-fulfillable-quantity",
        "Available",
        "Sellable",
        "Days of Supply",
        "DoS",
        "可售数量",
        "可用库存",
        "供货天数",
    }
)

# Sponsored Brands Video — metrics that only appear when creative is a video.
# Per 2025-2026 Amazon Ads API docs, SBV reports reuse the SB report schema
# plus these exclusive columns.
_SBV_MARKERS = frozenset(
    {
        "videoViews",
        "video5SecondViews",
        "videoCompleteViews",
        "video5SecondViewRate",
        "videoCompleteViewRate",
        "videoUnmutes",
        "vctr",
        "vtr",
    }
)

# Sponsored Brands — brand-awareness metrics exclusive to SB.
# NTB (new-to-brand) + Top-of-search impression share are the hallmarks.
_SB_MARKERS = frozenset(
    {
        "attributedBrandedSearches14d",
        "attributedOrdersNewToBrand14d",
        "attributedSalesNewToBrand14d",
        "attributedOrdersNewToBrandPercentage14d",
        "topOfSearchImpressionShare",
        "searchTermImpressionShare",
        "searchTermImpressionRank",
        "attributedBrandStorePageViews14d",
    }
)

# Sponsored Display — viewable-impressions + detail-page metrics exclusive to SD.
_SD_MARKERS = frozenset(
    {
        "viewableImpressions",
        "attributedDetailPageView14d",
        "attributedDetailPageViewNewToBrand14d",
        "attributedAddToCarts14d",
        "attributedAddToCartsPercentage14d",
        "attributedAddToCartClicks14d",
        "viewAttributedSales14d",
        "viewAttributedDetailPageView14d",
    }
)


def detect_csv_type(content: str, filename: str | None = None) -> CsvType:
    """Classify a user-uploaded report.

    - Looks at the first 2000 characters only — O(1) cost even for 50MB files.
    - Pipe-delimited content is assumed to be an operation log (Amazon's
      "Copy" format produces `Date and time | Change type | ...`).
    - Filename hints (like "操作日志", "搜索词", "库存") are a last-resort
      disambiguator when the header signatures are ambiguous.

    Returns "unknown" if no signature matches; callers should either
    reject the upload or prompt the user.
    """
    if not content or not content.strip():
        return "unknown"

    head = content[:2000]

    # 1. Operation log: pipe-delimited TXT, header contains "Date and time" or "Change type"
    if "|" in head and ("Date and time" in head or "Change type" in head or "变更类型" in head):
        return "operation_log"

    # Fallback filename hint for operation logs (common in Chinese UI exports)
    if filename and filename.lower().endswith(".txt") and "操作日志" in filename:
        return "operation_log"

    # Tokenize first header-ish line(s) — strip BOM and whitespace.
    # Split PER LINE first so newline-adjacent values don't merge into one token.
    tokens: set[str] = set()
    for line in head.splitlines()[:5]:
        for tok in line.replace("\t", ",").split(","):
            cleaned = tok.strip().strip("\ufeff")
            if cleaned:
                tokens.add(cleaned)

    # Order matters: check most specific before more generic.
    # SBV first (video metrics are exclusive to Sponsored Brands Video).
    if tokens & _SBV_MARKERS:
        return "sbv"
    # SB signature (NTB + Top-of-search IS). Check after SBV since video SB
    # reports also contain these SB markers.
    if tokens & _SB_MARKERS:
        return "sb"
    # SD signature (viewable impressions + add-to-cart metrics).
    if tokens & _SD_MARKERS:
        return "sd"
    if tokens & _SEARCH_TERM_MARKERS:
        return "search_term"
    if tokens & _INVENTORY_MARKERS:
        return "inventory"
    if tokens & _PLACEMENT_MARKERS:
        return "placement"
    if tokens & _KEYWORD_MARKERS:
        return "keyword"

    # Filename hint fallback
    if filename:
        low = filename.lower()
        if "搜索词" in filename or "search-term" in low:
            return "search_term"
        if "库存" in filename or "inventory" in low:
            return "inventory"
        if "展示位置" in filename or "placement" in low:
            return "placement"
        if "关键词" in filename or "keyword" in low:
            return "keyword"
        # New 2026: SB / SD / SBV filename hints
        if "sponsored-brands-video" in low or "sbv" in low or "品牌视频" in filename:
            return "sbv"
        if (
            "sponsored-brands" in low
            or "sponsored brands" in low
            or low.startswith("sb-")
            or low.startswith("sb_")
            or "品牌广告" in filename
        ):
            return "sb"
        if (
            "sponsored-display" in low
            or "sponsored display" in low
            or low.startswith("sd-")
            or low.startswith("sd_")
            or "展示广告" in filename
        ):
            return "sd"

    return "unknown"
