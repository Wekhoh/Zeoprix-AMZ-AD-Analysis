"""关键词模型 — 广告组下的投放关键词及其日维度绩效数据。

层级关系: Campaign → AdGroup → Keyword → KeywordDailyRecord
数据来源: Amazon Sponsored Products Keyword Report CSV
"""

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin


class Keyword(Base, TimestampMixin):
    """单个投放关键词，归属于某个广告组。"""

    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint(
            "ad_group_id", "keyword_text", "match_type", name="uq_kw_group_text_match"
        ),
        Index("ix_kw_text", "keyword_text"),
        Index("ix_kw_ad_group", "ad_group_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_group_id = Column(Integer, ForeignKey("ad_groups.id"), nullable=False)
    keyword_text = Column(String, nullable=False)
    match_type = Column(String, nullable=False)  # Broad / Phrase / Exact
    bid = Column(Float)  # current max bid
    state = Column(String, nullable=False, default="enabled")  # enabled / paused / archived

    ad_group = relationship("AdGroup", back_populates="keywords")
    daily_records = relationship("KeywordDailyRecord", back_populates="keyword")


class KeywordDailyRecord(Base, TimestampMixin):
    """关键词日维度绩效快照。"""

    __tablename__ = "keyword_daily_records"
    __table_args__ = (
        UniqueConstraint("keyword_id", "date", name="uq_kw_daily"),
        Index("ix_kw_daily_date", "date"),
        Index("ix_kw_daily_kw", "keyword_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    orders = Column(Integer, nullable=False, default=0)
    sales = Column(Float, nullable=False, default=0.0)

    keyword = relationship("Keyword", back_populates="daily_records")
