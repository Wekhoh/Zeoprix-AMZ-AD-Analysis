"""产品和变体模型"""

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=False)  # 'ZP-TP01'
    name = Column(String, nullable=False)  # 'ZEOPRIX Travel Pillow'
    category = Column(String)  # '旅行枕'
    category_key = Column(String)  # benchmark category key (e.g. 'travel', 'beauty')

    variants = relationship("ProductVariant", back_populates="product")


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_code = Column(String, nullable=False)  # 'DBL', 'BLK'
    variant_name = Column(String, nullable=False)  # '双层枕', '黑色款'
    asin = Column(String)
    marketplace_id = Column(Integer, ForeignKey("marketplaces.id"), nullable=False)
    unit_cost = Column(Float)  # 产品成本
    fba_fee = Column(Float)  # FBA 费用
    referral_fee_pct = Column(Float, default=0.15)  # 佣金比例

    product = relationship("Product", back_populates="variants")
