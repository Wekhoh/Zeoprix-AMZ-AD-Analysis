"""
操作日志解析器
直接提取自 data_importer.py L460-617
已通过 520 条数据审计验证
"""

import re
from backend.utils.date_parser import parse_amazon_datetime, is_datetime_like


def parse_operation_log_text(
    text: str,
    campaign_name: str = "",
    is_adgroup: bool = False,
) -> list[dict]:
    """
    解析从亚马逊后台复制的操作日志文本
    v2.6: 智能识别每行的列格式，兼容混合格式文件
    """
    results = []
    lines = text.strip().split("\n")

    # 检测默认列顺序（基于表头，作为 fallback）
    default_column_order = None
    for line in lines:
        if "Date and time" in line and "Change type" in line:
            parts = [p.strip().lower() for p in line.split("|")]
            parts = [p for p in parts if p]
            for i, part in enumerate(parts):
                if "date" in part:
                    default_column_order = "campaign" if i <= 1 else "adgroup"
                    break
            break

    if not default_column_order:
        default_column_order = "adgroup" if is_adgroup else "campaign"

    for line in lines:
        if (
            not line.strip()
            or "---" in line
            or "Date and time" in line
            or line.split("|")[0].strip().lower() == "change type"
        ):
            continue

        if "|" not in line:
            continue

        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]

        if len(parts) < 4:
            continue

        # v2.6: 智能检测每行的格式
        first_part = parts[0]

        if is_datetime_like(first_part):
            # campaign 格式: Date | Change type | From | To
            try:
                int(first_part)
                datetime_str = parts[1]
                change_type = parts[2]
                from_value = parts[3] if len(parts) > 3 else ""
                to_value = parts[4] if len(parts) > 4 else ""
            except ValueError:
                datetime_str = parts[0]
                change_type = parts[1]
                from_value = parts[2] if len(parts) > 2 else ""
                to_value = parts[3] if len(parts) > 3 else ""
        else:
            last_part = parts[-1] if parts else ""

            if is_datetime_like(last_part):
                # 标准 adgroup 格式
                change_type = parts[0]
                from_value = parts[1] if len(parts) > 1 else ""
                to_value = parts[2] if len(parts) > 2 else ""
                datetime_str = parts[3] if len(parts) > 3 else ""
            else:
                # 尝试查找日期列
                datetime_str = None
                datetime_idx = -1
                for idx, p in enumerate(parts):
                    if is_datetime_like(p):
                        datetime_str = p
                        datetime_idx = idx
                        break

                if datetime_str and datetime_idx >= 0:
                    if datetime_idx == 0:
                        change_type = parts[1] if len(parts) > 1 else ""
                        from_value = parts[2] if len(parts) > 2 else ""
                        to_value = parts[3] if len(parts) > 3 else ""
                    elif datetime_idx == 1:
                        change_type = parts[2] if len(parts) > 2 else ""
                        from_value = parts[3] if len(parts) > 3 else ""
                        to_value = parts[4] if len(parts) > 4 else ""
                    else:
                        if default_column_order == "campaign":
                            change_type = parts[1] if len(parts) > 1 else ""
                            from_value = parts[2] if len(parts) > 2 else ""
                            to_value = parts[3] if len(parts) > 3 else ""
                        else:
                            change_type = parts[0]
                            from_value = parts[1] if len(parts) > 1 else ""
                            to_value = parts[2] if len(parts) > 2 else ""
                else:
                    if default_column_order == "campaign":
                        datetime_str = parts[0]
                        change_type = parts[1] if len(parts) > 1 else ""
                        from_value = parts[2] if len(parts) > 2 else ""
                        to_value = parts[3] if len(parts) > 3 else ""
                    else:
                        change_type = parts[0]
                        from_value = parts[1] if len(parts) > 1 else ""
                        to_value = parts[2] if len(parts) > 2 else ""
                        datetime_str = parts[3] if len(parts) > 3 else ""

        date_str, time_str = parse_amazon_datetime(datetime_str)

        if date_str:
            results.append(
                {
                    "date": date_str,
                    "time": time_str,
                    "operator": "Jack Huang",
                    "level_type": "ad_group" if is_adgroup else "campaign",
                    "campaign_name": campaign_name,
                    "ad_group_name": campaign_name,
                    "operation_type": "Ad group change"
                    if is_adgroup
                    else "Campaign change",
                    "change_type": change_type,
                    "from_value": from_value,
                    "to_value": to_value,
                }
            )

    return results


def parse_operation_log_content(
    content: str,
    filename: str,
    campaign_name: str = "",
) -> tuple[list[dict], bool]:
    """
    解析操作日志文件内容

    Args:
        content: TXT 文件文本内容
        filename: 原始文件名
        campaign_name: 广告活动名称

    Returns:
        (解析结果列表, 是否为广告组日志)
    """
    is_adgroup = "广告组" in filename

    if not campaign_name:
        # 尝试从文件名提取
        name = (
            filename.replace("操作日志", "")
            .replace("广告组", "")
            .replace(".txt", "")
            .strip()
        )
        campaign_name = name

    return parse_operation_log_text(content, campaign_name, is_adgroup), is_adgroup
