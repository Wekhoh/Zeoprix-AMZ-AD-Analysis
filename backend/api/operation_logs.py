"""操作日志 API"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Campaign, OperationLog
from backend.schemas.operation_log import OperationLogOut

router = APIRouter()


@router.get("")
def list_operation_logs(
    campaign_id: Optional[int] = Query(None),
    change_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """查询操作日志（分页）"""
    q = db.query(OperationLog, Campaign.name).join(
        Campaign, OperationLog.campaign_id == Campaign.id
    )
    if campaign_id:
        q = q.filter(OperationLog.campaign_id == campaign_id)
    if change_type:
        q = q.filter(OperationLog.change_type.contains(change_type))
    if date_from:
        q = q.filter(OperationLog.date >= date_from)
    if date_to:
        q = q.filter(OperationLog.date <= date_to)

    total = q.count()

    results = (
        q.order_by(OperationLog.date.desc(), OperationLog.time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    data = [
        OperationLogOut(
            id=log.id,
            date=log.date,
            time=log.time,
            operator=log.operator,
            level_type=log.level_type,
            campaign_id=log.campaign_id,
            campaign_name=name,
            change_type=log.change_type,
            from_value=log.from_value,
            to_value=log.to_value,
        )
        for log, name in results
    ]

    return {"data": data, "total": total, "page": page, "page_size": page_size}
