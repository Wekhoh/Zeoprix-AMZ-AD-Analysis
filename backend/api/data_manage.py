"""数据管理 API — 数据统计 + 清空"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.logging_config import get_logger
from backend.models import (
    AdGroup,
    AdGroupDailyRecord,
    Campaign,
    CampaignDailyRecord,
    ImportHistory,
    InventorySnapshot,
    Keyword,
    KeywordAction,
    KeywordDailyRecord,
    Note,
    OperationLog,
    OrganicSales,
    PlacementRecord,
    SearchTermReport,
    SuggestionStatus,
)
from backend.services.backup_service import create_backup

router = APIRouter()
logger = get_logger("settings")


@router.get("/data-stats")
def get_data_stats(db: Session = Depends(get_db)):
    """获取各表数据量统计"""
    return {
        "campaigns": db.query(Campaign).count(),
        "ad_groups": db.query(AdGroup).count(),
        "placement_records": db.query(PlacementRecord).count(),
        "operation_logs": db.query(OperationLog).count(),
        "campaign_daily": db.query(CampaignDailyRecord).count(),
        "ad_group_daily": db.query(AdGroupDailyRecord).count(),
        "search_terms": db.query(SearchTermReport).count(),
        "notes": db.query(Note).count(),
        "organic_sales": db.query(OrganicSales).count(),
        "import_history": db.query(ImportHistory).count(),
        "inventory_snapshots": db.query(InventorySnapshot).count(),
    }


@router.delete("/clear-data")
def clear_advertising_data(db: Session = Depends(get_db)):
    """清空所有广告数据（保留产品配置、规则、备份）

    自动创建备份作为安全网。
    清空顺序遵循外键约束。
    """
    backup_result = create_backup(db, backup_type="pre_clear")

    # FK-safe deletion order:
    #   KeywordDailyRecord -> Keyword -> AdGroup (Keyword hangs off AdGroup)
    #   KeywordAction.from_campaign_id -> Campaign (must precede Campaign)
    counts = {}
    for model, label in [
        (KeywordDailyRecord, "keyword_daily"),
        (Keyword, "keywords"),
        (PlacementRecord, "placement_records"),
        (OperationLog, "operation_logs"),
        (CampaignDailyRecord, "campaign_daily"),
        (AdGroupDailyRecord, "ad_group_daily"),
        (SearchTermReport, "search_terms"),
        (Note, "notes"),
        (AdGroup, "ad_groups"),
        (KeywordAction, "keyword_actions"),
        (Campaign, "campaigns"),
        (OrganicSales, "organic_sales"),
        (ImportHistory, "import_history"),
        (SuggestionStatus, "suggestion_status"),
        (InventorySnapshot, "inventory_snapshots"),
    ]:
        count = db.query(model).delete()
        counts[label] = count

    db.commit()

    total_deleted = sum(counts.values())
    logger.warning(
        f"DESTRUCTIVE: clear-data executed. {total_deleted} records deleted. "
        f"Backup #{backup_result.get('id')} created."
    )

    return {
        "success": True,
        "deleted": counts,
        "backup_id": backup_result.get("id"),
        "backup_path": backup_result.get("file_path"),
    }
