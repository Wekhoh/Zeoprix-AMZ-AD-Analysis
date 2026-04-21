"""
广告活动状态推断服务
从操作日志中提取最新状态，更新 campaigns 表
"""

from sqlalchemy.orm import Session

from backend.models import Campaign, OperationLog

VALID_STATUSES = ["Paused", "Delivering", "Enabled", "Archived"]


def update_campaign_statuses(db: Session, campaign_ids: list[int] | None = None):
    """
    从操作日志推断广告活动当前状态

    Args:
        db: 数据库会话
        campaign_ids: 指定要更新的活动 ID 列表，None 表示更新全部
    """
    q = db.query(Campaign)
    if campaign_ids:
        q = q.filter(Campaign.id.in_(campaign_ids))
    campaigns = q.all()

    updated = 0
    for campaign in campaigns:
        # 只查 change_type 精确为 "Campaign status" 且 to_value 是有效运行状态的记录
        # 排除 "Targeting group status" 和 "In budget"/"Out of budget" 等预算状态
        last_status_log = (
            db.query(OperationLog)
            .filter(
                OperationLog.campaign_id == campaign.id,
                OperationLog.change_type == "Campaign status",
                OperationLog.to_value.in_(VALID_STATUSES),
            )
            .order_by(OperationLog.date.desc(), OperationLog.time.desc())
            .first()
        )

        if not last_status_log:
            continue

        to_value = last_status_log.to_value.strip()
        if campaign.status != to_value:
            campaign.status = to_value
            campaign.status_updated_at = last_status_log.date
            updated += 1

    if updated:
        db.commit()

    return updated
