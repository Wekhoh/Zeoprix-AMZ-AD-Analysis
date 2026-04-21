"""运营决策笔记模型"""

from sqlalchemy import Column, ForeignKey, Index, Integer, String

from backend.models.base import Base, TimestampMixin


class Note(Base, TimestampMixin):
    __tablename__ = "notes"
    __table_args__ = (Index("ix_note_campaign", "campaign_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    date = Column(String)  # YYYY-MM-DD，可选
    content = Column(String, nullable=False)
    note_type = Column(String, default="decision")  # decision / observation / reminder
    deleted_at = Column(String)  # Soft delete timestamp, null = active
