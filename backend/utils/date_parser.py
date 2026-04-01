"""
亚马逊日期格式解析器
直接提取自 data_importer.py L136-139, L301-316, L411-459
已通过 520 条数据审计验证
"""

import re
from datetime import datetime
from typing import Optional

# 月份名称映射（英文 → 数字）
MONTH_MAP = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def parse_amazon_datetime(datetime_str: str) -> tuple[Optional[str], Optional[str]]:
    """
    解析亚马逊日期时间格式
    "Nov 13, 2025 4:49 AM" → ("2025-11-13", "04:49")
    """
    pattern = r"(\w+)\s+(\d+),\s+(\d+)\s+(\d+):(\d+)\s*(AM|PM)?"
    match = re.match(pattern, datetime_str.strip())
    if not match:
        return None, None

    month_name, day, year, hour, minute, ampm = match.groups()
    month = MONTH_MAP.get(month_name, 1)
    day = int(day)
    year = int(year)
    hour = int(hour)
    minute = int(minute)

    if ampm:
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0

    date_str = f"{year}-{month:02d}-{day:02d}"
    time_str = f"{hour:02d}:{minute:02d}"
    return date_str, time_str


def parse_date_from_filename(filename: str) -> Optional[str]:
    """
    从文件名提取日期
    DBL-TP01-LOT01-SP自动紧密动低-1.94bid1116.csv → 2025-11-16
    """
    match = re.search(r"(\d{4})\.csv$", filename)
    if not match:
        return None

    mmdd = match.group(1)
    month = int(mmdd[:2])
    day = int(mmdd[2:])
    current_year = datetime.now().year
    current_month = datetime.now().month
    year = current_year if month <= current_month else current_year - 1
    return f"{year}-{month:02d}-{day:02d}"


def is_datetime_like(s: str) -> bool:
    """检测字符串是否像日期时间格式"""
    if not s:
        return False
    patterns = [
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}",
        r"\d{1,2}/\d{1,2}/\d{4}",
        r"\d{4}-\d{2}-\d{2}",
        r"\d{4}/\d{2}/\d{2}",
    ]
    return any(re.search(p, s, re.IGNORECASE) for p in patterns)
