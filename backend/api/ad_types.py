"""Read-only catalog endpoints exposing the ad-type KPI schema.

The frontend calls these to render type-aware Column Settings dropdowns
and to label tabs without hard-coding the field lists on the client.
Source of truth is backend/utils/amazon_rules.py.
"""

from fastapi import APIRouter, HTTPException

from backend.utils.amazon_rules import (
    AD_TYPE_LABELS,
    KPI_FIELD_LABELS,
    KPI_FIELDS_BY_AD_TYPE,
    KPI_FIELDS_CORE,
    get_kpi_exclusive_fields,
    get_kpi_fields,
)

router = APIRouter()


def _describe(ad_type: str) -> dict:
    fields = get_kpi_fields(ad_type)
    return {
        "ad_type": ad_type,
        "label": AD_TYPE_LABELS.get(ad_type, ad_type),
        "fields": [
            {
                "key": f,
                "label": KPI_FIELD_LABELS.get(f, f),
                "exclusive": f not in KPI_FIELDS_CORE,
            }
            for f in fields
        ],
        "exclusive_fields": list(get_kpi_exclusive_fields(ad_type)),
    }


@router.get("")
def list_ad_types():
    """Catalog of all supported ad types with labels and field counts."""
    return {
        "ad_types": [
            {
                "ad_type": ad_type,
                "label": AD_TYPE_LABELS.get(ad_type, ad_type),
                "field_count": len(KPI_FIELDS_BY_AD_TYPE[ad_type]),
                "exclusive_field_count": len(get_kpi_exclusive_fields(ad_type)),
            }
            for ad_type in KPI_FIELDS_BY_AD_TYPE
        ],
        "core_fields": [{"key": f, "label": KPI_FIELD_LABELS.get(f, f)} for f in KPI_FIELDS_CORE],
    }


@router.get("/{ad_type}")
def get_ad_type(ad_type: str):
    """Detailed field catalog for one ad type (SP / SB / SBV / SD / ST / DSP)."""
    upper = ad_type.upper()
    if upper not in KPI_FIELDS_BY_AD_TYPE:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown ad_type '{ad_type}'. "
            f"Supported: {', '.join(sorted(KPI_FIELDS_BY_AD_TYPE.keys()))}",
        )
    return _describe(upper)
