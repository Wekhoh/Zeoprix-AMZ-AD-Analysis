"""搜索词处理记录模型 — 跟踪 harvest/negate 操作"""

from sqlalchemy import Column, Float, ForeignKey, Integer, String

from backend.models.base import Base, TimestampMixin


class KeywordAction(Base, TimestampMixin):
    """Records when a search term is harvested or negated."""

    __tablename__ = "keyword_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    search_term = Column(String, nullable=False, index=True)
    from_campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    from_campaign_name = Column(String)
    action_type = Column(
        String, nullable=False
    )  # harvest_exact / harvest_phrase / negate_exact / negate_phrase
    target_bid = Column(Float)
    notes = Column(String)
