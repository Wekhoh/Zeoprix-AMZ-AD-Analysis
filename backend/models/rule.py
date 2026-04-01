"""自动化规则模型"""

from sqlalchemy import Column, Integer, String, Float
from backend.models.base import Base, TimestampMixin


class Rule(Base, TimestampMixin):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String)
    condition_field = Column(String, nullable=False)  # acos, roas, clicks, orders, spend, ctr, cpc
    condition_operator = Column(String, nullable=False)  # >, <, >=, <=, ==
    condition_value = Column(Float, nullable=False)
    condition_min_data = Column(Integer, default=0)  # min clicks/impressions to trigger
    period_days = Column(Integer, default=7)  # lookback period
    action_type = Column(
        String, nullable=False
    )  # flag_pause, suggest_negative, suggest_bid_increase, suggest_bid_decrease, suggest_budget_increase
    is_active = Column(Integer, default=1)
    last_run_at = Column(String)
