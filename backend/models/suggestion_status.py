"""建议生命周期状态 — 跟踪已处理/延后的建议"""

from sqlalchemy import Column, Integer, String

from backend.models.base import Base, TimestampMixin


class SuggestionStatus(Base, TimestampMixin):
    """Tracks whether a suggestion has been resolved, dismissed, or snoozed."""

    __tablename__ = "suggestion_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    suggestion_hash = Column(String, nullable=False, unique=True, index=True)
    # Hash is computed from type + campaign_id to make suggestions identifiable across re-generations
    campaign_id = Column(Integer)
    suggestion_type = Column(String, nullable=False)  # high_acos / zero_orders / etc
    status = Column(String, nullable=False)  # resolved / snoozed / dismissed
    snooze_until = Column(String)  # YYYY-MM-DD, null if not snoozed
    notes = Column(String)
