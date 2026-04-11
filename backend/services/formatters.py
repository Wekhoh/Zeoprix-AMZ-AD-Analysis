"""Shared formatting helpers for report / export generation.

Two responsibilities:

1. **safe_cell** — Excel/CSV formula-injection defense. Any string starting
   with ``=``, ``+``, ``-``, ``@``, tab, or carriage-return is prefixed
   with a single quote, which spreadsheet apps strip on display but which
   prevents the cell from being parsed as a formula. Protects against
   malicious campaign names like ``=cmd|'/c calc'!A1`` making their way
   from Amazon seller central → CSV import → exported report → Excel open.

2. **Formatters** (currency / percent / int / float) — consolidated from
   duplicated implementations across ``report_service.py`` (Excel) and
   ``pdf_report_service.py`` (PDF). Both services now import from here so
   a single format change propagates to all exports.
"""

from typing import Any

# Characters that trigger formula interpretation in Excel / LibreOffice /
# Google Sheets. Keep the order stable — it's tested.
_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r", "\x00")


def safe_cell(value: Any) -> Any:
    """Return a cell value safe against Excel/CSV formula injection.

    Strings whose first character is a formula-trigger get a leading
    single quote prepended. All other values (None, int, float, bool,
    etc.) pass through unchanged so numeric cells remain typed.

    Example:
        >>> safe_cell("=SUM(A1:A10)")
        "'=SUM(A1:A10)"
        >>> safe_cell("Normal Campaign")
        'Normal Campaign'
        >>> safe_cell(42.5)
        42.5
        >>> safe_cell(None) is None
        True
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    if value and value[0] in _FORMULA_TRIGGERS:
        return "'" + value
    return value


def format_currency(value: Any, default: str = "-", symbol: str = "$") -> str:
    """Format as currency string, e.g., ``1234.56`` → ``'$1,234.56'``."""
    if value is None:
        return default
    try:
        return f"{symbol}{float(value):,.2f}"
    except (TypeError, ValueError):
        return default


def format_percent(value: Any, decimals: int = 2, default: str = "-") -> str:
    """Format a ratio as percentage, e.g., ``0.1234`` → ``'12.34%'``."""
    if value is None:
        return default
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return default


def format_int(value: Any, default: str = "-") -> str:
    """Format an integer with thousand separators, e.g., ``12345`` → ``'12,345'``."""
    if value is None:
        return default
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return default


def format_float(value: Any, decimals: int = 2, default: str = "-") -> str:
    """Format as fixed-precision float, e.g., ``3.14159`` → ``'3.14'``."""
    if value is None:
        return default
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return default
