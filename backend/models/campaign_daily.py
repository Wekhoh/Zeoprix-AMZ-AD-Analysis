"""广告活动/广告组日数据模型"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin


class CampaignDailyRecord(Base, TimestampMixin):
    """广告活动日数据 — 对应 Excel「广告活动数据」表"""

    __tablename__ = "campaign_daily_records"
    __table_args__ = (
        UniqueConstraint("date", "campaign_id", name="uq_campaign_daily_date_campaign"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    status = Column(String)  # 从操作日志推断: Delivering / Paused
    budget = Column(Float)  # 从操作日志推断
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    orders = Column(Integer, nullable=False, default=0)
    sales = Column(Float, nullable=False, default=0.0)
    top_of_search_share = Column(Float)
    top_bid_adjustment = Column(Float)
    notes = Column(String)

    campaign = relationship("Campaign", back_populates="daily_records")


class AdGroupDailyRecord(Base, TimestampMixin):
    """广告组日数据 — 对应 Excel「广告组数据」表"""

    __tablename__ = "ad_group_daily_records"
    __table_args__ = (
        UniqueConstraint("date", "ad_group_id", name="uq_adgroup_daily_date_adgroup"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)
    ad_group_id = Column(Integer, ForeignKey("ad_groups.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    default_bid = Column(Float)
    suggested_bid = Column(Float)
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    orders = Column(Integer, nullable=False, default=0)
    sales = Column(Float, nullable=False, default=0.0)
    notes = Column(String)

    ad_group = relationship("AdGroup", back_populates="daily_records")
