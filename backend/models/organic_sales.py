"""有机销售数据模型 — 用于 TACoS 计算"""

from sqlalchemy import Column, Float, Integer, String

from backend.models.base import Base, TimestampMixin


class OrganicSales(Base, TimestampMixin):
    __tablename__ = "organic_sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False, unique=True)  # YYYY-MM-DD
    total_sales = Column(Float, nullable=False, default=0.0)  # Total sales (organic + ad)
    total_orders = Column(Integer, nullable=False, default=0)
    notes = Column(String)
    deleted_at = Column(String)  # Soft delete timestamp, null = active
