"""设置 API — 备份管理 + 产品配置 + 有机销售"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.logging_config import get_logger

settings_logger = get_logger("settings")

from backend.models import (
    Product,
    ProductVariant,
    Marketplace,
    OrganicSales,
    ImportHistory,
    Campaign,
    AdGroup,
    PlacementRecord,
    OperationLog,
    CampaignDailyRecord,
    AdGroupDailyRecord,
    SearchTermReport,
    Note,
)
from backend.services.backup_service import (
    create_backup,
    list_backups,
    delete_backup,
    restore_backup,
)

router = APIRouter()


class ProductVariantUpdate(BaseModel):
    variant_code: Optional[str] = None
    variant_name: Optional[str] = None
    asin: Optional[str] = None
    unit_cost: Optional[float] = None
    fba_fee: Optional[float] = None
    referral_fee_pct: Optional[float] = None


class OrganicSalesItem(BaseModel):
    date: str
    total_sales: float
    total_orders: int
    notes: Optional[str] = None


class ProductCategoryUpdate(BaseModel):
    category_key: Optional[str] = None


# === 备份管理 ===


@router.post("/backups")
def create_backup_endpoint(db: Session = Depends(get_db)):
    """创建手动备份"""
    return create_backup(db, backup_type="manual")


@router.get("/backups")
def list_backups_endpoint(db: Session = Depends(get_db)):
    """列出所有备份"""
    return list_backups(db)


@router.delete("/backups/{backup_id}")
def delete_backup_endpoint(backup_id: int, db: Session = Depends(get_db)):
    """删除指定备份"""
    if not delete_backup(db, backup_id):
        raise HTTPException(status_code=404, detail="备份不存在")
    settings_logger.warning(f"DESTRUCTIVE: backup {backup_id} deleted")
    return {"success": True}


@router.post("/backups/{backup_id}/restore")
def restore_backup_endpoint(backup_id: int, db: Session = Depends(get_db)):
    """Restore database from a backup"""
    result = restore_backup(db, backup_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# === 产品管理 ===


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    """获取产品列表（含变体和成本信息）"""
    from sqlalchemy.orm import joinedload

    products = db.query(Product).options(joinedload(Product.variants)).all()
    result = []
    for p in products:
        result.append(
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "category": p.category,
                "category_key": p.category_key,
                "variants": [
                    {
                        "id": v.id,
                        "variant_code": v.variant_code,
                        "variant_name": v.variant_name,
                        "asin": v.asin,
                        "unit_cost": v.unit_cost,
                        "fba_fee": v.fba_fee,
                        "referral_fee_pct": v.referral_fee_pct,
                    }
                    for v in variants
                ],
            }
        )
    return result


@router.put("/products/{variant_id}")
def update_product_variant(
    variant_id: int,
    body: ProductVariantUpdate,
    db: Session = Depends(get_db),
):
    """更新产品变体信息（名称、代码、ASIN、成本）"""
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="产品变体不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(variant, key, value)

    db.commit()
    return {
        "id": variant.id,
        "unit_cost": variant.unit_cost,
        "fba_fee": variant.fba_fee,
        "referral_fee_pct": variant.referral_fee_pct,
    }


@router.get("/marketplaces")
def list_marketplaces(db: Session = Depends(get_db)):
    """获取站点列表"""
    return [
        {"id": m.id, "code": m.code, "name": m.name, "currency": m.currency}
        for m in db.query(Marketplace).all()
    ]


# === 有机销售数据 ===


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


# === 导入历史 ===


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


# === 产品品类设置 ===


# === 数据管理 ===


@router.get("/data-stats")
def get_data_stats(db: Session = Depends(get_db)):
    """获取各表数据量统计"""
    return {
        "campaigns": db.query(Campaign).count(),
        "ad_groups": db.query(AdGroup).count(),
        "placement_records": db.query(PlacementRecord).count(),
        "operation_logs": db.query(OperationLog).count(),
        "campaign_daily": db.query(CampaignDailyRecord).count(),
        "ad_group_daily": db.query(AdGroupDailyRecord).count(),
        "search_terms": db.query(SearchTermReport).count(),
        "notes": db.query(Note).count(),
        "organic_sales": db.query(OrganicSales).count(),
        "import_history": db.query(ImportHistory).count(),
    }


@router.delete("/clear-data")
def clear_advertising_data(db: Session = Depends(get_db)):
    """清空所有广告数据（保留产品配置、规则、备份）

    自动创建备份作为安全网。
    清空顺序遵循外键约束。
    """
    # Safety: auto-backup before destructive operation
    backup_result = create_backup(db, backup_type="pre_clear")

    # Delete in FK-safe order (children first)
    counts = {}
    for model, label in [
        (PlacementRecord, "placement_records"),
        (OperationLog, "operation_logs"),
        (CampaignDailyRecord, "campaign_daily"),
        (AdGroupDailyRecord, "ad_group_daily"),
        (SearchTermReport, "search_terms"),
        (Note, "notes"),
        (AdGroup, "ad_groups"),
        (Campaign, "campaigns"),
        (OrganicSales, "organic_sales"),
        (ImportHistory, "import_history"),
    ]:
        count = db.query(model).delete()
        counts[label] = count

    db.commit()

    total_deleted = sum(counts.values())
    settings_logger.warning(
        f"DESTRUCTIVE: clear-data executed. {total_deleted} records deleted. "
        f"Backup #{backup_result.get('id')} created."
    )

    return {
        "success": True,
        "deleted": counts,
        "backup_id": backup_result.get("id"),
        "backup_path": backup_result.get("file_path"),
    }


@router.put("/products/{product_id}/category-key")
def update_product_category_key(
    product_id: int,
    body: ProductCategoryUpdate,
    db: Session = Depends(get_db),
):
    """更新产品的品类基准 key"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    product.category_key = body.category_key
    db.commit()
    return {"id": product.id, "category_key": product.category_key}
