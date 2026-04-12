"""Amazon Campaign Manager Bulk Upload Excel generation.

Converts KeywordAction records into an Excel file matching Amazon's
Sponsored Products bulk upload format. The operator downloads this file
and uploads it directly to Seller Central → Campaign Manager → Bulk
Operations, avoiding manual keyword-by-keyword entry.

Format reference: Amazon Seller Central → Campaign Manager → Bulk
Operations → Download template. Columns are the minimum required set
for keyword operations (add exact keywords + add negative keywords).
"""

from io import BytesIO
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from sqlalchemy.orm import Session

from backend.models import KeywordAction
from backend.services.formatters import safe_cell

# Amazon Bulk Upload column headers (SP Keyword operations)
HARVEST_HEADERS = [
    "Record Type",
    "Campaign Name",
    "Ad Group Name",
    "State",
    "Keyword or Product Targeting",
    "Match Type",
    "Max Bid",
]

NEGATE_HEADERS = [
    "Record Type",
    "Campaign Name",
    "State",
    "Keyword or Product Targeting",
    "Match Type",
]

# Styles (consistent with report_service.py)
_HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF", size=10)
_HEADER_FILL = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
_BODY_FONT = Font(name="Arial", size=10)
_THIN_BORDER = Border(
    left=Side(style="thin", color="E5E7EB"),
    right=Side(style="thin", color="E5E7EB"),
    top=Side(style="thin", color="E5E7EB"),
    bottom=Side(style="thin", color="E5E7EB"),
)

# Map our action_type values to Amazon's Match Type column
_MATCH_TYPE_MAP = {
    "harvest_exact": "Exact",
    "harvest_phrase": "Phrase",
    "negate_exact": "Negative Exact",
    "negate_phrase": "Negative Phrase",
}

# Map to Amazon's Record Type
_RECORD_TYPE_MAP = {
    "harvest_exact": "Keyword",
    "harvest_phrase": "Keyword",
    "negate_exact": "Campaign Negative Keyword",
    "negate_phrase": "Campaign Negative Keyword",
}


def _style_header(ws, row, col_count):
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _THIN_BORDER


def _auto_width(ws, min_w=10, max_w=40):
    for col in ws.columns:
        letter = None
        max_len = 0
        for cell in col:
            if hasattr(cell, "column_letter"):
                letter = cell.column_letter
            val = str(cell.value) if cell.value is not None else ""
            max_len = max(max_len, len(val.encode("utf-8")))
        if letter:
            ws.column_dimensions[letter].width = max(min(max_len * 0.8 + 2, max_w), min_w)


def generate_bulk_upload_excel(
    db: Session,
    action_types: Optional[list[str]] = None,
) -> bytes:
    """Query KeywordAction records and generate an Amazon Bulk Upload Excel.

    Args:
        db: SQLAlchemy session
        action_types: filter by action_type (e.g., ["harvest_exact", "negate_exact"]).
            If None, exports all recorded actions.

    Returns:
        Excel file as bytes, ready for StreamingResponse or file write.
    """
    q = db.query(KeywordAction).order_by(KeywordAction.created_at.desc())
    if action_types:
        q = q.filter(KeywordAction.action_type.in_(action_types))
    actions = q.all()

    # Split into harvest (positive) and negate (negative) groups
    harvest_actions = [a for a in actions if a.action_type.startswith("harvest")]
    negate_actions = [a for a in actions if a.action_type.startswith("negate")]

    wb = Workbook()

    # === Sheet 1: Harvest Keywords (add new exact/phrase keywords)
    ws1 = wb.active
    ws1.title = "Harvest Keywords"
    ws1.sheet_properties.tabColor = "10B981"

    ws1.append(HARVEST_HEADERS)
    _style_header(ws1, 1, len(HARVEST_HEADERS))

    for a in harvest_actions:
        record_type = _RECORD_TYPE_MAP.get(a.action_type, "Keyword")
        match_type = _MATCH_TYPE_MAP.get(a.action_type, "Exact")
        row = [
            record_type,
            safe_cell(a.from_campaign_name or ""),
            "",  # Ad Group Name — operator fills manually
            "enabled",
            safe_cell(a.search_term),
            match_type,
            a.target_bid if a.target_bid else "",
        ]
        ws1.append(row)
        for col in range(1, len(HARVEST_HEADERS) + 1):
            ws1.cell(row=ws1.max_row, column=col).font = _BODY_FONT
            ws1.cell(row=ws1.max_row, column=col).border = _THIN_BORDER

    if not harvest_actions:
        ws1.append(["", "（无待收割关键词）", "", "", "", "", ""])

    _auto_width(ws1)

    # === Sheet 2: Negative Keywords (campaign-level negative)
    ws2 = wb.create_sheet("Negative Keywords")
    ws2.sheet_properties.tabColor = "EF4444"

    ws2.append(NEGATE_HEADERS)
    _style_header(ws2, 1, len(NEGATE_HEADERS))

    for a in negate_actions:
        record_type = _RECORD_TYPE_MAP.get(a.action_type, "Campaign Negative Keyword")
        match_type = _MATCH_TYPE_MAP.get(a.action_type, "Negative Exact")
        row = [
            record_type,
            safe_cell(a.from_campaign_name or ""),
            "enabled",
            safe_cell(a.search_term),
            match_type,
        ]
        ws2.append(row)
        for col in range(1, len(NEGATE_HEADERS) + 1):
            ws2.cell(row=ws2.max_row, column=col).font = _BODY_FONT
            ws2.cell(row=ws2.max_row, column=col).border = _THIN_BORDER

    if not negate_actions:
        ws2.append(["", "（无待否定关键词）", "", "", ""])

    _auto_width(ws2)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
