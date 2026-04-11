"""PDF report generation service using reportlab.

Generates a professional printable summary suitable for weekly/monthly
stakeholder reports. Complements Excel export (which is for analysis).
"""

from datetime import datetime
from io import BytesIO
from typing import Optional

from sqlalchemy.orm import Session

from backend.services.formatters import (
    format_currency,
    format_float,
    format_int,
    format_percent,
)
from backend.services.summary_service import (
    dashboard_overview,
    summary_by_campaign,
    summary_by_date,
)


# Lazy reportlab import — only when PDF is actually requested
def _get_reportlab():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    # Register CJK font (built-in to reportlab, no external file needed)
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:
        pass  # Already registered

    return {
        "colors": colors,
        "A4": A4,
        "getSampleStyleSheet": getSampleStyleSheet,
        "ParagraphStyle": ParagraphStyle,
        "cm": cm,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Paragraph": Paragraph,
        "Spacer": Spacer,
        "Table": Table,
        "TableStyle": TableStyle,
        "PageBreak": PageBreak,
    }


def generate_pdf_report(
    db: Session,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> bytes:
    """Generate a PDF summary report as bytes."""
    rl = _get_reportlab()
    buf = BytesIO()

    # Chinese-capable styles
    styles = rl["getSampleStyleSheet"]()
    base_font = "STSong-Light"

    title_style = rl["ParagraphStyle"](
        name="ZhTitle",
        parent=styles["Title"],
        fontName=base_font,
        fontSize=22,
        textColor=rl["colors"].HexColor("#1F2937"),
        spaceAfter=12,
    )
    heading_style = rl["ParagraphStyle"](
        name="ZhHeading",
        parent=styles["Heading2"],
        fontName=base_font,
        fontSize=14,
        textColor=rl["colors"].HexColor("#2563EB"),
        spaceBefore=16,
        spaceAfter=8,
    )
    body_style = rl["ParagraphStyle"](
        name="ZhBody",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=10,
        textColor=rl["colors"].HexColor("#374151"),
    )
    meta_style = rl["ParagraphStyle"](
        name="ZhMeta",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=9,
        textColor=rl["colors"].HexColor("#6B7280"),
        spaceAfter=12,
    )

    doc = rl["SimpleDocTemplate"](
        buf,
        pagesize=rl["A4"],
        leftMargin=1.8 * rl["cm"],
        rightMargin=1.8 * rl["cm"],
        topMargin=2 * rl["cm"],
        bottomMargin=2 * rl["cm"],
        title="Amazon 广告报告",
        author="AMZ Ad Tracker",
    )

    story: list = []

    # === Title ===
    story.append(rl["Paragraph"]("亚马逊广告业绩报告", title_style))
    date_range_text = f"日期范围: {date_from or '全部'} ~ {date_to or '全部'}"
    generated_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(rl["Paragraph"](date_range_text, meta_style))
    story.append(rl["Paragraph"](generated_text, meta_style))
    story.append(rl["Spacer"](1, 0.3 * rl["cm"]))

    # === Executive Summary ===
    overview = dashboard_overview(db, date_from, date_to)
    kpi = overview["kpi"]

    story.append(rl["Paragraph"]("核心指标", heading_style))

    kpi_data = [
        ["指标", "数值", "指标", "数值"],
        [
            "总花费",
            format_currency(kpi.get("spend")),
            "总订单",
            format_int(kpi.get("orders")),
        ],
        [
            "总销售额",
            format_currency(kpi.get("sales")),
            "总曝光",
            format_int(kpi.get("impressions")),
        ],
        [
            "ACOS",
            format_percent(kpi.get("acos")),
            "ROAS",
            format_float(kpi.get("roas")),
        ],
        [
            "CTR",
            format_percent(kpi.get("ctr")),
            "CPC",
            format_currency(kpi.get("cpc")),
        ],
    ]
    kpi_table = rl["Table"](
        kpi_data,
        colWidths=[4 * rl["cm"], 4 * rl["cm"], 4 * rl["cm"], 4 * rl["cm"]],
    )
    kpi_table.setStyle(
        rl["TableStyle"](
            [
                ("FONTNAME", (0, 0), (-1, -1), base_font),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor("#EFF6FF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].HexColor("#1E40AF")),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(kpi_table)

    # === Profit (if available) ===
    profit = overview.get("profit") or {}
    if profit.get("has_cost_data"):
        story.append(rl["Spacer"](1, 0.3 * rl["cm"]))
        profit_text = (
            f"预估利润: {format_currency(profit.get('estimated_profit'))}  |  "
            f"盈亏平衡 ACOS: {format_percent(profit.get('break_even_acos'))}"
        )
        story.append(rl["Paragraph"](profit_text, body_style))

    # === Top Campaigns ===
    story.append(rl["Paragraph"]("Top 花费广告活动", heading_style))
    all_campaigns = summary_by_campaign(db, date_from, date_to)
    all_campaigns.sort(key=lambda x: x.get("spend") or 0, reverse=True)
    top = all_campaigns[:10]

    camp_data = [["广告活动", "花费", "订单", "销售额", "ACOS", "ROAS"]]
    for c in top:
        name = c.get("campaign_name", "")
        if len(name) > 30:
            name = name[:28] + "..."
        camp_data.append(
            [
                name,
                format_currency(c.get("spend")),
                format_int(c.get("orders")),
                format_currency(c.get("sales")),
                format_percent(c.get("acos")),
                format_float(c.get("roas")),
            ]
        )

    if len(camp_data) == 1:
        story.append(rl["Paragraph"]("无数据", body_style))
    else:
        camp_table = rl["Table"](
            camp_data,
            colWidths=[
                6 * rl["cm"],
                2.5 * rl["cm"],
                1.8 * rl["cm"],
                2.5 * rl["cm"],
                1.8 * rl["cm"],
                1.8 * rl["cm"],
            ],
        )
        camp_table.setStyle(
            rl["TableStyle"](
                [
                    ("FONTNAME", (0, 0), (-1, -1), base_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor("#F3F4F6")),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].HexColor("#374151")),
                    ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#E5E7EB")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [rl["colors"].white, rl["colors"].HexColor("#FAFAFA")],
                    ),
                ]
            )
        )
        story.append(camp_table)

    # === Daily trend table ===
    story.append(rl["PageBreak"]())
    story.append(rl["Paragraph"]("每日明细", heading_style))
    daily = summary_by_date(db, date_from, date_to)
    # Show at most 31 days (1 month)
    daily_shown = daily[:31]

    if not daily_shown:
        story.append(rl["Paragraph"]("无日期数据", body_style))
    else:
        daily_data = [["日期", "曝光", "点击", "花费", "订单", "销售额", "ACOS"]]
        for d in daily_shown:
            daily_data.append(
                [
                    d.get("date", ""),
                    format_int(d.get("impressions")),
                    format_int(d.get("clicks")),
                    format_currency(d.get("spend")),
                    format_int(d.get("orders")),
                    format_currency(d.get("sales")),
                    format_percent(d.get("acos")),
                ]
            )
        daily_table = rl["Table"](
            daily_data,
            colWidths=[
                2.5 * rl["cm"],
                2 * rl["cm"],
                1.8 * rl["cm"],
                2.3 * rl["cm"],
                1.8 * rl["cm"],
                2.5 * rl["cm"],
                1.8 * rl["cm"],
            ],
        )
        daily_table.setStyle(
            rl["TableStyle"](
                [
                    ("FONTNAME", (0, 0), (-1, -1), base_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor("#F3F4F6")),
                    ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#E5E7EB")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [rl["colors"].white, rl["colors"].HexColor("#FAFAFA")],
                    ),
                ]
            )
        )
        story.append(daily_table)

    # === Footer note ===
    story.append(rl["Spacer"](1, 0.5 * rl["cm"]))
    story.append(
        rl["Paragraph"](
            "本报告由 AMZ Ad Tracker 自动生成。数据来源为用户上传的亚马逊广告后台导出文件。",
            meta_style,
        )
    )

    doc.build(story)
    return buf.getvalue()
