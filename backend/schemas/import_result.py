"""导入结果 schema"""

from pydantic import BaseModel


class ImportDetail(BaseModel):
    message: str
    level: str = "info"  # info, warning, error


class ImportResult(BaseModel):
    imported: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    details: list[ImportDetail] = []
