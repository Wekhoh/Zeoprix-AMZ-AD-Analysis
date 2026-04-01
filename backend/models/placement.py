"""展示位置记录模型"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin


class PlacementRecord(Base, TimestampMixin):
    """展示位置日数据 — 对应 Excel「展示位置」表"""

    __tablename__ = "placement_records"
    __table_args__ = (
        UniqueConstraint(
            "date",
            "campaign_id",
            "placement_type",
            name="uq_placement_date_campaign_type",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    placement_type = Column(
        String, nullable=False
    )  # 搜索顶部 / 搜索其他位置 / 产品页面
    bidding_strategy = Column(String)
    bid_adjustment = Column(Integer, default=0)  # 竞价调整百分比
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    orders = Column(Integer, nullable=False, default=0)
    sales = Column(Float, nullable=False, default=0.0)
    notes = Column(String)

    campaign = relationship("Campaign", back_populates="placement_records")
