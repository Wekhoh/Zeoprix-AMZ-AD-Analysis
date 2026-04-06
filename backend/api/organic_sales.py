"""有机销售 + 导入历史 API"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import OrganicSales, ImportHistory

router = APIRouter()


class OrganicSalesItem(BaseModel):
    date: str
    total_sales: float
    total_orders: int
    notes: Optional[str] = None


@router.post("/organic-sales")
def upsert_organic_sales(
    items: list[OrganicSalesItem],
    db: Session = Depends(get_db),
):
    """批量导入/更新有机销售数据"""
    created = 0
    updated = 0
    for item in items:
        existing = db.query(OrganicSales).filter(OrganicSales.date == item.date).first()
        if existing:
            existing.total_sales = item.total_sales
            existing.total_orders = item.total_orders
            existing.notes = item.notes
            updated += 1
        else:
            db.add(
                OrganicSales(
                    date=item.date,
                    total_sales=item.total_sales,
                    total_orders=item.total_orders,
                    notes=item.notes,
                )
            )
            created += 1
    db.commit()
    return {"created": created, "updated": updated}


@router.get("/organic-sales")
def list_organic_sales(db: Session = Depends(get_db)):
    """获取所有有机销售记录"""
    records = db.query(OrganicSales).order_by(OrganicSales.date.desc()).all()
    return [
        {
            "id": r.id,
            "date": r.date,
            "total_sales": r.total_sales,
            "total_orders": r.total_orders,
            "notes": r.notes,
        }
        for r in records
    ]


@router.delete("/organic-sales/{record_id}")
def delete_organic_sales(record_id: int, db: Session = Depends(get_db)):
    """删除有机销售记录"""
    record = db.query(OrganicSales).filter(OrganicSales.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"success": True}


@router.get("/import-history")
def list_import_history(db: Session = Depends(get_db)):
    """获取最近的导入历史记录"""
    records = db.query(ImportHistory).order_by(ImportHistory.created_at.desc()).limit(50).all()
    return [
        {
            "id": r.id,
            "import_type": r.import_type,
            "file_name": r.file_name,
            "records_imported": r.records_imported,
            "records_updated": r.records_updated,
            "records_skipped": r.records_skipped,
            "status": r.status,
            "created_at": str(r.created_at),
        }
        for r in records
    ]
