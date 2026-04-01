"""展示位置 API"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import PlacementRecord, Campaign
from backend.schemas.placement import PlacementOut
from backend.services.kpi_calculator import enrich_placement_kpis

router = APIRouter()


@router.get("")
def list_placements(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    campaign_id: Optional[int] = Query(None),
    placement_type: Optional[str] = Query(None),
    marketplace_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """查询展示位置记录（分页）"""
    q = db.query(PlacementRecord, Campaign.name).join(
        Campaign, PlacementRecord.campaign_id == Campaign.id
    )
    if date_from:
        q = q.filter(PlacementRecord.date >= date_from)
    if date_to:
        q = q.filter(PlacementRecord.date <= date_to)
    if campaign_id:
        q = q.filter(PlacementRecord.campaign_id == campaign_id)
    if placement_type:
        q = q.filter(PlacementRecord.placement_type == placement_type)
    if marketplace_id:
        q = q.filter(Campaign.marketplace_id == marketplace_id)

    total = q.count()

    results = (
        q.order_by(PlacementRecord.date.desc(), Campaign.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    data = [enrich_placement_kpis(record, campaign_name) for record, campaign_name in results]

    return {"data": data, "total": total, "page": page, "page_size": page_size}
