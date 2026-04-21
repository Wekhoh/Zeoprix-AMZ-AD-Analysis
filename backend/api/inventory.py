"""库存管理 API — FBA inventory snapshots + risk alerts"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.inventory_service import (
    get_latest_inventory,
    get_risk_summary,
    import_inventory,
)
from backend.utils.encoding_helper import decode_with_fallback

router = APIRouter()


@router.post("/import")
async def import_inventory_csv(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Import Amazon Inventory Health CSV report(s)."""
    total_imported = 0
    total_updated = 0
    total_skipped = 0
    critical = 0
    warning = 0
    details: list[dict] = []

    for f in files:
        raw = await f.read()
        content = decode_with_fallback(raw) or ""

        if not content:
            details.append({"file": f.filename, "error": "encoding"})
            continue

        result = import_inventory(db, content, f.filename or "")
        total_imported += result.get("imported", 0)
        total_updated += result.get("updated", 0)
        total_skipped += result.get("skipped", 0)
        critical += result.get("critical_count", 0)
        warning += result.get("warning_count", 0)
        details.append({"file": f.filename, **result})

    return {
        "imported": total_imported,
        "updated": total_updated,
        "skipped": total_skipped,
        "critical_count": critical,
        "warning_count": warning,
        "details": details,
    }


@router.get("/latest")
def list_latest_inventory(
    alert_level: Optional[str] = Query(
        None, description="Filter by alert level: critical/warning/ok/unknown"
    ),
    db: Session = Depends(get_db),
):
    """Get latest inventory snapshot per SKU."""
    levels = [alert_level] if alert_level else None
    return get_latest_inventory(db, alert_levels=levels)


@router.get("/risk-summary")
def get_inventory_risk_summary(db: Session = Depends(get_db)):
    """Summary of inventory risk: counts per level + top risk SKUs."""
    return get_risk_summary(db)
