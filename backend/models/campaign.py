"""广告活动和广告组模型"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint("name", "marketplace_id", name="uq_campaign_name_marketplace"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)  # 完整广告活动名称
    variant_id = Column(Integer, ForeignKey("product_variants.id"))
    marketplace_id = Column(Integer, ForeignKey("marketplaces.id"), nullable=False)
    ad_type = Column(String, nullable=False, default="SP")  # SP, SB, SD, SBV
    targeting_type = Column(String, nullable=False, default="auto")  # auto, manual
    match_type = Column(String)  # close, loose, substitutes, complements
    bidding_strategy = Column(
        String, nullable=False
    )  # Fixed bids / Dynamic bidding (down only) / ...
    base_bid = Column(Float)  # 从名称提取，如 1.94
    portfolio = Column(String)  # ZP-TP01-DBL-LOT01
    status = Column(String, nullable=False, default="Delivering")
    status_updated_at = Column(String)
    tags = Column(String)  # JSON array of tag strings, e.g. '["新品", "清库存"]'

    ad_groups = relationship("AdGroup", back_populates="campaign")
    placement_records = relationship("PlacementRecord", back_populates="campaign")
    daily_records = relationship("CampaignDailyRecord", back_populates="campaign")
    operation_logs = relationship("OperationLog", back_populates="campaign")


class AdGroup(Base, TimestampMixin):
    __tablename__ = "ad_groups"
    __table_args__ = (UniqueConstraint("campaign_id", "name", name="uq_adgroup_campaign_name"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Enabled")
    default_bid = Column(Float)

    campaign = relationship("Campaign", back_populates="ad_groups")
    daily_records = relationship("AdGroupDailyRecord", back_populates="ad_group")
    keywords = relationship("Keyword", back_populates="ad_group")
