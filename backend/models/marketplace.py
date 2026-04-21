"""站点模型"""

from sqlalchemy import Column, Integer, String

from backend.models.base import Base, TimestampMixin


class Marketplace(Base, TimestampMixin):
    __tablename__ = "marketplaces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)  # 'US', 'UK', 'DE', 'JP'
    name = Column(String, nullable=False)  # '美国站'
    currency = Column(String, nullable=False, default="USD")
