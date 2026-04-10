"""库存快照模型 — 对应亚马逊 Inventory Health / FBA Stock Summary 报告"""

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from backend.models.base import Base, TimestampMixin


class InventorySnapshot(Base, TimestampMixin):
    """Inventory snapshot per SKU per date.

    Populated by CSV import from Amazon Seller Central Inventory Health report.
    Used to trigger PPC alerts when ad spend is running but stock is low.
    """

    __tablename__ = "inventory_snapshots"
    __table_args__ = (
        UniqueConstraint("date", "sku", name="uq_inv_date_sku"),
        Index("ix_inv_sku", "sku"),
        Index("ix_inv_asin", "asin"),
        Index("ix_inv_date", "date"),
        Index("ix_inv_alert_level", "alert_level"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD snapshot date
    sku = Column(String, nullable=False)  # seller SKU (matches ProductVariant.variant_code)
    asin = Column(String)  # optional ASIN from report
    variant_id = Column(Integer, ForeignKey("product_variants.id"))  # soft link to variant

    units_available = Column(Integer, nullable=False, default=0)  # Available / sellable units
    units_inbound = Column(Integer, default=0)  # In transit to FBA
    units_reserved = Column(Integer, default=0)  # Reserved for customer orders

    days_of_supply = Column(Float)  # From Amazon DoS field, nullable
    alert_level = Column(String)  # "critical" (<3 days) / "warning" (<7 days) / "ok" (>=7)

    raw_csv_row = Column(String)  # JSON string of original row for audit
