"""
导入编排服务
整合: CSV 解析 → 去重检测 → 数据库写入 → 汇总更新
"""

from collections import Counter

from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.logging_config import get_logger
from backend.models import (
    AdGroup,
    ImportHistory,
    OperationLog,
)
from backend.schemas.import_result import ImportDetail, ImportResult
from backend.services.anomaly_detector import (
    detect_data_quality_anomalies,
    detect_historical_anomalies,
)
from backend.services.campaign_upsert import (
    get_or_create_campaign,
    upsert_campaign_daily_record,
    upsert_placement_record,
)
from backend.services.csv_parser import parse_csv_placement_data
from backend.services.log_parser import parse_operation_log_content
from backend.utils.encoding_helper import decode_with_fallback

logger = get_logger("import")

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB — byte-level DoS guard
# Row-level DoS guard: even a well-formed CSV can OOM the parser if it's
# 10M rows. Amazon reports are typically < 10K rows; 100K is generous.
MAX_CSV_ROWS = 100_000


async def process_placement_csv_upload(db: Session, files: list[UploadFile]) -> ImportResult:
    """处理展示位置 CSV 上传"""
    try:
        from backend.services.backup_service import create_backup

        create_backup(db, backup_type="pre_import")
    except Exception as exc:
        logger.warning(f"Pre-import backup failed (non-fatal): {exc}")

    total_imported = 0
    total_updated = 0
    total_skipped = 0
    details: list[ImportDetail] = []

    for file in files:
        try:
            raw = await file.read()
            if len(raw) > MAX_UPLOAD_SIZE:
                details.append(
                    ImportDetail(message=f"{file.filename}: 文件超过 50MB 限制", level="error")
                )
                continue
            # 尝试多种编码
            content = decode_with_fallback(raw)
            if content is None:
                details.append(
                    ImportDetail(message=f"无法解码文件: {file.filename}", level="error")
                )
                continue

            # Row-count DoS guard (cheap: no need to parse to count newlines)
            if content.count("\n") > MAX_CSV_ROWS:
                details.append(
                    ImportDetail(
                        message=f"{file.filename}: 行数超过 {MAX_CSV_ROWS} 限制",
                        level="error",
                    )
                )
                continue

            # 从文件名推断广告活动名称
            placement_data, campaign_summary = parse_csv_placement_data(
                content, file.filename or "unknown.csv"
            )

            campaign_name = campaign_summary["campaign_name"]
            campaign = get_or_create_campaign(
                db, campaign_name, campaign_summary.get("bidding_strategy", "")
            )

            file_imported = 0
            file_updated = 0
            file_skipped = 0

            for data in placement_data:
                result = upsert_placement_record(db, campaign.id, data)
                if result == "imported":
                    file_imported += 1
                elif result == "updated":
                    file_updated += 1
                else:
                    file_skipped += 1

            # 同时更新广告活动日汇总
            upsert_campaign_daily_record(db, campaign.id, campaign_summary)

            db.commit()

            total_imported += file_imported
            total_updated += file_updated
            total_skipped += file_skipped

            details.append(
                ImportDetail(
                    message=f"{file.filename}: 导入 {file_imported}, 更新 {file_updated}, 跳过 {file_skipped}"
                )
            )

        except Exception as e:
            logger.exception("Placement CSV import failed for file %s", file.filename)
            db.rollback()
            details.append(ImportDetail(message=f"{file.filename}: 错误 - {e}", level="error"))

    # 记录导入历史
    db.add(
        ImportHistory(
            import_type="placement_csv",
            records_imported=total_imported,
            records_updated=total_updated,
            records_skipped=total_skipped,
        )
    )
    db.commit()

    return ImportResult(
        imported=total_imported,
        updated=total_updated,
        skipped=total_skipped,
        details=details,
    )


async def preview_csv_upload(files: list[UploadFile], db=None) -> dict:
    """Preview CSV files without writing to database"""
    previews: list[dict] = []

    for file in files:
        try:
            raw = await file.read()
            content = decode_with_fallback(raw) or ""

            if not content:
                previews.append(
                    {
                        "filename": file.filename,
                        "error": "无法解码文件",
                        "campaign_name": "",
                        "date_range": "",
                        "record_count": 0,
                        "columns": [],
                        "sample_rows": [],
                        "ad_type": "",
                    }
                )
                continue

            placement_data, campaign_summary = parse_csv_placement_data(
                content, file.filename or "unknown.csv"
            )

            # Build date range
            dates = [row["date"] for row in placement_data if row.get("date")]
            date_range = ""
            if dates:
                date_range = f"{min(dates)} ~ {max(dates)}" if len(dates) > 1 else dates[0]

            # Sample rows (first 5)
            sample_rows = placement_data[:5]

            previews.append(
                {
                    "filename": file.filename,
                    "campaign_name": campaign_summary.get("campaign_name", ""),
                    "date_range": date_range,
                    "record_count": len(placement_data),
                    "columns": list(placement_data[0].keys()) if placement_data else [],
                    "sample_rows": sample_rows,
                    "ad_type": campaign_summary.get("ad_type", "SP"),
                    "warnings": (
                        detect_data_quality_anomalies(placement_data)
                        + (
                            detect_historical_anomalies(
                                db, placement_data, campaign_summary.get("campaign_name", "")
                            )
                            if db is not None
                            else []
                        )
                    ),
                }
            )

            # Reset file position for potential re-read
            await file.seek(0)

        except Exception as e:
            logger.exception("CSV preview failed for file %s", file.filename)
            previews.append(
                {
                    "filename": file.filename,
                    "error": str(e),
                    "campaign_name": "",
                    "date_range": "",
                    "record_count": 0,
                    "columns": [],
                    "sample_rows": [],
                    "ad_type": "",
                }
            )

    return {"files": previews}


async def process_operation_log_upload(db: Session, files: list[UploadFile]) -> ImportResult:
    """处理操作日志 TXT 上传"""
    try:
        from backend.services.backup_service import create_backup

        create_backup(db, backup_type="pre_import")
    except Exception as exc:
        logger.warning(f"Pre-import backup failed (non-fatal): {exc}")

    total_imported = 0
    total_skipped = 0
    details: list[ImportDetail] = []

    for file in files:
        try:
            raw = await file.read()
            if len(raw) > MAX_UPLOAD_SIZE:
                details.append(
                    ImportDetail(message=f"{file.filename}: 文件超过 50MB 限制", level="error")
                )
                continue
            content = raw.decode("utf-8")

            # Row-count DoS guard for operation logs too
            if content.count("\n") > MAX_CSV_ROWS:
                details.append(
                    ImportDetail(
                        message=f"{file.filename}: 行数超过 {MAX_CSV_ROWS} 限制",
                        level="error",
                    )
                )
                continue

            filename = file.filename or "unknown.txt"

            log_entries, is_adgroup = parse_operation_log_content(content, filename)

            file_imported = 0
            file_skipped = 0

            # v2.6: 使用 Counter 支持同一分钟内重复操作
            existing_keys: Counter = Counter()
            for entry in log_entries:
                campaign_name = entry["campaign_name"]
                campaign = get_or_create_campaign(db, campaign_name)

                key = f"{entry['date']}|{entry['time']}|{campaign.id}|{entry['change_type']}|{entry['from_value']}|{entry['to_value']}"
                existing_keys[key] += 1

                # 检查数据库中是否已存在
                db_count = (
                    db.query(OperationLog)
                    .filter_by(
                        date=entry["date"],
                        time=entry["time"],
                        campaign_id=campaign.id,
                        change_type=entry["change_type"],
                        from_value=entry["from_value"],
                        to_value=entry["to_value"],
                    )
                    .count()
                )

                if db_count >= existing_keys[key]:
                    file_skipped += 1
                    continue

                ad_group_id = None
                if is_adgroup:
                    ad_group = db.query(AdGroup).filter_by(campaign_id=campaign.id).first()
                    if ad_group:
                        ad_group_id = ad_group.id

                log_record = OperationLog(
                    date=entry["date"],
                    time=entry["time"],
                    operator=entry.get("operator", ""),
                    level_type=entry["level_type"],
                    campaign_id=campaign.id,
                    ad_group_id=ad_group_id,
                    operation_type=entry.get("operation_type", ""),
                    change_type=entry["change_type"],
                    from_value=entry.get("from_value", ""),
                    to_value=entry.get("to_value", ""),
                )
                db.add(log_record)
                file_imported += 1

            db.commit()
            total_imported += file_imported
            total_skipped += file_skipped

            log_type = "广告组日志" if is_adgroup else "广告活动日志"
            details.append(
                ImportDetail(
                    message=f"{filename} ({log_type}): 导入 {file_imported}, 跳过 {file_skipped}"
                )
            )

        except Exception as e:
            logger.exception("Operation log import failed for file %s", file.filename)
            db.rollback()
            details.append(ImportDetail(message=f"{file.filename}: 错误 - {e}", level="error"))

    # 导入完成后更新广告活动状态
    if total_imported > 0:
        from backend.services.status_service import update_campaign_statuses

        update_campaign_statuses(db)

    db.add(
        ImportHistory(
            import_type="operation_log",
            records_imported=total_imported,
            records_skipped=total_skipped,
        )
    )
    db.commit()

    return ImportResult(imported=total_imported, skipped=total_skipped, details=details)
