"""操作日志模型"""

from sqlalchemy import Column, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin


class OperationLog(Base, TimestampMixin):
    """操作日志 — 对应 Excel「广告活动操作日志」+「广告组操作日志」"""

    __tablename__ = "operation_logs"
    __table_args__ = (
        UniqueConstraint(
            "date",
            "time",
            "level_type",
            "campaign_id",
            "change_type",
            "from_value",
            "to_value",
            name="uq_oplog_composite",
        ),
        Index("ix_oplog_campaign_date", "campaign_id", "date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    time = Column(String, nullable=False)  # HH:MM
    operator = Column(String)  # Jack Huang
    level_type = Column(String, nullable=False)  # campaign / ad_group
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    ad_group_id = Column(Integer, ForeignKey("ad_groups.id"))
    operation_type = Column(String)  # Campaign change / Ad group change
    change_type = Column(String, nullable=False)  # Campaign status / Daily budget / ...
    from_value = Column(String)
    to_value = Column(String)

    campaign = relationship("Campaign", back_populates="operation_logs")
