"""Detect which Amazon report a user-uploaded CSV is, by column signature.

Used by the batch-import flow so a seller can drag multiple files and the
server routes each to the correct parser without asking "which kind?".

Signatures were lifted directly from the existing per-type parsers:
- placement: backend/services/csv_parser.py → "Placement" column
- keyword: backend/services/keyword_service.py::COLUMN_MAP
- inventory: backend/services/inventory_service.py::COLUMN_MAP
- search_term: well-known "Customer Search Term" / "Search Term" header
- operation_log: pipe-delimited TXT, not CSV — detected via format shape
"""

from __future__ import annotations

from typing import Literal

CsvType = Literal[
    "placement",
    "search_term",
    "operation_log",
    "inventory",
    "keyword",
    "unknown",
]

# Authoritative signature set per file type. First match wins. Order matters:
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

    # Order matters: check more specific before more generic.
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
        if "搜索词" in filename or "search-term" in filename.lower():
            return "search_term"
        if "库存" in filename or "inventory" in filename.lower():
            return "inventory"
        if "展示位置" in filename or "placement" in filename.lower():
            return "placement"
        if "关键词" in filename or "keyword" in filename.lower():
            return "keyword"

    return "unknown"
