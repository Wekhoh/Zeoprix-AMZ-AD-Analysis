"""产品管理 API"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Product, ProductVariant, Marketplace

router = APIRouter()


class ProductVariantUpdate(BaseModel):
    variant_code: Optional[str] = None
    variant_name: Optional[str] = None
    asin: Optional[str] = None
    unit_cost: Optional[float] = None
    fba_fee: Optional[float] = None
    referral_fee_pct: Optional[float] = None


class ProductCategoryUpdate(BaseModel):
    category_key: Optional[str] = None


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    """获取产品列表（含变体和成本信息）"""
    from sqlalchemy.orm import joinedload

    products = db.query(Product).options(joinedload(Product.variants)).all()
    return [
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
                for v in p.variants
            ],
        }
        for p in products
    ]


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
