"""搜索词报告模型（Phase 3）"""

from sqlalchemy import Column, Index, Integer, String, Float, ForeignKey, UniqueConstraint
from backend.models.base import Base, TimestampMixin


class SearchTermReport(Base, TimestampMixin):
    """搜索词报告 — Phase 3 新功能"""

    __tablename__ = "search_term_reports"
    __table_args__ = (
        UniqueConstraint("date", "campaign_id", "search_term", name="uq_search_term_date_campaign"),
        Index("ix_sterm_campaign", "campaign_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    ad_group_id = Column(Integer, ForeignKey("ad_groups.id"))
    search_term = Column(String, nullable=False)
    match_type = Column(String)  # BROAD, PHRASE, EXACT, CLOSE_MATCH
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    orders = Column(Integer, nullable=False, default=0)
    sales = Column(Float, nullable=False, default=0.0)
