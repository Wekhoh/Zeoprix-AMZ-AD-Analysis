"""Inventory report parsing + import + risk analysis.

Handles Amazon FBA Inventory Health / Stock Summary CSV reports.
Supports both English and Chinese column headers.
"""

import csv
import io
import json
from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Campaign, InventorySnapshot, ProductVariant
from backend.services.csv_parser import _clean_num


# Column mapping: Amazon report header → normalized field
# Supports English (default Seller Central) + Chinese (卖家中心 zh-CN)
COLUMN_MAP = {
    # SKU
    "sku": "sku",
    "seller-sku": "sku",
    "msku": "sku",
    "SKU": "sku",
    "商家 SKU": "sku",
    "MSKU": "sku",
    "卖家 SKU": "sku",
    # ASIN
    "asin": "asin",
    "ASIN": "asin",
    # Available
    "afn-fulfillable-quantity": "units_available",
    "Available": "units_available",
    "available": "units_available",
    "Sellable": "units_available",
    "可售数量": "units_available",
    "可用库存": "units_available",
    # Inbound
    "afn-inbound-working-quantity": "units_inbound",
    "Inbound": "units_inbound",
    "Inbound Quantity": "units_inbound",
    "inbound-quantity": "units_inbound",
    "在途库存": "units_inbound",
    "入库中数量": "units_inbound",
    # Reserved
    "afn-reserved-quantity": "units_reserved",
    "Reserved": "units_reserved",
    "Reserved Quantity": "units_reserved",
    "预留数量": "units_reserved",
    # Days of Supply
    "Days of Supply": "days_of_supply",
    "DoS": "days_of_supply",
    "days-of-supply": "days_of_supply",
    "days_of_supply": "days_of_supply",
    "供货天数": "days_of_supply",
    "库存天数": "days_of_supply",
}


def _calc_alert_level(days_of_supply: Optional[float]) -> str:
    """Compute alert severity from days of supply.

    Thresholds: critical <3d, warning <7d, ok >=7d.
    If days_of_supply is None (not provided), returns "unknown".
    """
    if days_of_supply is None:
        return "unknown"
    if days_of_supply < 3:
        return "critical"
    if days_of_supply < 7:
        return "warning"
    return "ok"


def parse_inventory_csv(content: str) -> list[dict]:
    """Parse Amazon Inventory Health CSV.

    Flexible column mapping (English + Chinese). Skips metadata rows until
    a recognized header row is found. Returns list of normalized dicts.
    """
    if not content or not content.strip():
        return []

    reader = csv.reader(io.StringIO(content))
    header: Optional[list[str]] = None
    col_map: dict[int, str] = {}
    rows: list[dict] = []

    for line in reader:
        if not line or not any(c.strip() for c in line):
            continue

        # Find header row (must contain at least SKU column)
        if header is None:
            test_map: dict[int, str] = {}
            for i, col in enumerate(line):
                clean = col.strip().strip("\ufeff")
                if clean in COLUMN_MAP:
                    test_map[i] = COLUMN_MAP[clean]
            if "sku" in test_map.values():
                header = line
                col_map = test_map
            continue

        # Parse data row
        row: dict = {}
        for idx, field in col_map.items():
            if idx >= len(line):
                continue
            val = line[idx].strip()
            if field == "sku" or field == "asin":
                row[field] = val
            elif field == "days_of_supply":
                try:
                    row[field] = float(_clean_num(val)) if val else None
                except (ValueError, TypeError):
                    row[field] = None
            else:
                # units_* are integers
                try:
                    row[field] = int(_clean_num(val, as_int=True))
                except (ValueError, TypeError):
                    row[field] = 0

        if row.get("sku"):
            rows.append(row)

    return rows


def import_inventory(db: Session, content: str, filename: str = "") -> dict:
    """Parse + upsert inventory rows for today's snapshot date.

    Returns {imported, updated, skipped, critical_count, warning_count, error?}.
    """
    parsed = parse_inventory_csv(content)
    if not parsed:
        return {
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "critical_count": 0,
            "warning_count": 0,
            "error": "未识别到库存数据。请确认 CSV 包含 SKU 列。",
        }

    today = date.today().isoformat()

    # Pre-fetch variants by code for fast matching
    variants = {v.variant_code: v.id for v in db.query(ProductVariant).all() if v.variant_code}

    imported = 0
    updated = 0
    skipped = 0
    critical_count = 0
    warning_count = 0

    for row in parsed:
        sku = row.get("sku", "").strip()
        if not sku:
            skipped += 1
            continue

        dos = row.get("days_of_supply")
        alert_level = _calc_alert_level(dos)
        if alert_level == "critical":
            critical_count += 1
        elif alert_level == "warning":
            warning_count += 1

        # Upsert by (date, sku)
        existing = (
            db.query(InventorySnapshot)
            .filter(
                InventorySnapshot.date == today,
                InventorySnapshot.sku == sku,
            )
            .first()
        )

        if existing:
            existing.asin = row.get("asin") or existing.asin
            existing.units_available = row.get("units_available", 0)
            existing.units_inbound = row.get("units_inbound", 0) or 0
            existing.units_reserved = row.get("units_reserved", 0) or 0
            existing.days_of_supply = dos
            existing.alert_level = alert_level
            existing.variant_id = variants.get(sku) or existing.variant_id
            existing.raw_csv_row = json.dumps(row, ensure_ascii=False)
            updated += 1
        else:
            snap = InventorySnapshot(
                date=today,
                sku=sku,
                asin=row.get("asin"),
                variant_id=variants.get(sku),
                units_available=row.get("units_available", 0),
                units_inbound=row.get("units_inbound", 0) or 0,
                units_reserved=row.get("units_reserved", 0) or 0,
                days_of_supply=dos,
                alert_level=alert_level,
                raw_csv_row=json.dumps(row, ensure_ascii=False),
            )
            db.add(snap)
            imported += 1

    db.commit()
    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "critical_count": critical_count,
        "warning_count": warning_count,
    }


def get_latest_inventory(
    db: Session,
    alert_levels: Optional[list[str]] = None,
    limit: int = 500,
) -> list[dict]:
    """Get latest snapshot per SKU, optionally filtered by alert level."""
    # Subquery: latest date per SKU
    latest_dates = (
        db.query(
            InventorySnapshot.sku.label("sku"),
            func.max(InventorySnapshot.date).label("max_date"),
        )
        .group_by(InventorySnapshot.sku)
        .subquery()
    )

    q = (
        db.query(InventorySnapshot)
        .join(
            latest_dates,
            (InventorySnapshot.sku == latest_dates.c.sku)
            & (InventorySnapshot.date == latest_dates.c.max_date),
        )
        .order_by(InventorySnapshot.days_of_supply.asc().nulls_last())
    )

    if alert_levels:
        q = q.filter(InventorySnapshot.alert_level.in_(alert_levels))

    rows = q.limit(limit).all()

    return [
        {
            "id": r.id,
            "date": r.date,
            "sku": r.sku,
            "asin": r.asin,
            "units_available": r.units_available,
            "units_inbound": r.units_inbound,
            "units_reserved": r.units_reserved,
            "days_of_supply": r.days_of_supply,
            "alert_level": r.alert_level,
        }
        for r in rows
    ]


def get_risk_summary(db: Session) -> dict:
    """Summary: counts per alert level + top N risk SKUs."""
    # Latest snapshot per SKU via subquery
    latest_dates = (
        db.query(
            InventorySnapshot.sku.label("sku"),
            func.max(InventorySnapshot.date).label("max_date"),
        )
        .group_by(InventorySnapshot.sku)
        .subquery()
    )

    latest = (
        db.query(InventorySnapshot)
        .join(
            latest_dates,
            (InventorySnapshot.sku == latest_dates.c.sku)
            & (InventorySnapshot.date == latest_dates.c.max_date),
        )
        .all()
    )

    counts = {"critical": 0, "warning": 0, "ok": 0, "unknown": 0}
    for r in latest:
        level = r.alert_level or "unknown"
        if level in counts:
            counts[level] += 1

    # Top 10 risk SKUs (critical first, by days_of_supply ascending)
    risk_sorted = sorted(
        [r for r in latest if r.alert_level in ("critical", "warning")],
        key=lambda r: r.days_of_supply if r.days_of_supply is not None else 999,
    )[:10]

    last_import_date = db.query(func.max(InventorySnapshot.date)).scalar()

    return {
        "last_import_date": last_import_date,
        "critical_count": counts["critical"],
        "warning_count": counts["warning"],
        "ok_count": counts["ok"],
        "unknown_count": counts["unknown"],
        "top_risk_skus": [
            {
                "sku": r.sku,
                "asin": r.asin,
                "days_of_supply": r.days_of_supply,
                "units_available": r.units_available,
                "alert_level": r.alert_level,
            }
            for r in risk_sorted
        ],
    }


def get_inventory_risk_for_campaigns(db: Session) -> list[dict]:
    """Join Campaign → ProductVariant → InventorySnapshot.

    Returns list of {campaign_id, campaign_name, sku, days_of_supply, alert_level}
    for campaigns linked to variants with inventory risk (critical or warning).
    Used by dashboard alerts.
    """
    # Latest snapshot per SKU
    latest_dates = (
        db.query(
            InventorySnapshot.sku.label("sku"),
            func.max(InventorySnapshot.date).label("max_date"),
        )
        .group_by(InventorySnapshot.sku)
        .subquery()
    )

    rows = (
        db.query(
            Campaign.id,
            Campaign.name,
            InventorySnapshot.sku,
            InventorySnapshot.days_of_supply,
            InventorySnapshot.alert_level,
            InventorySnapshot.units_available,
        )
        .join(ProductVariant, Campaign.variant_id == ProductVariant.id)
        .join(InventorySnapshot, InventorySnapshot.variant_id == ProductVariant.id)
        .join(
            latest_dates,
            (InventorySnapshot.sku == latest_dates.c.sku)
            & (InventorySnapshot.date == latest_dates.c.max_date),
        )
        .filter(InventorySnapshot.alert_level.in_(["critical", "warning"]))
        .all()
    )

    return [
        {
            "campaign_id": r[0],
            "campaign_name": r[1],
            "sku": r[2],
            "days_of_supply": r[3],
            "alert_level": r[4],
            "units_available": r[5],
        }
        for r in rows
    ]
