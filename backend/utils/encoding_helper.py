"""Encoding fallback decoder for user-uploaded CSV files.

Amazon Seller Central exports vary between UTF-8 (BOM or not) and
GBK / GB2312 depending on the marketplace and seller's browser locale.
This helper tries them in order and returns ``None`` only when none work,
so callers can decide how to surface "unknown encoding" to the user.
"""

from __future__ import annotations

# Order matters: try UTF-8 with BOM first since Excel exports often include it,
# then plain UTF-8, then the two GB-family encodings used by Chinese sellers.
_FALLBACK_ENCODINGS = ("utf-8-sig", "utf-8", "gbk", "gb2312")


def decode_with_fallback(raw: bytes) -> str | None:
    """Decode bytes using a fixed fallback chain.

    Returns the decoded string on the first encoding that succeeds, or
    ``None`` if every encoding raises ``UnicodeDecodeError`` / ``LookupError``.
    """
    for encoding in _FALLBACK_ENCODINGS:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return None
