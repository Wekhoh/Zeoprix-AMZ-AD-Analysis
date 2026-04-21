"""通用 schema"""

from typing import Any, Optional

from pydantic import BaseModel


class KPIMixin(BaseModel):
    """KPI 计算字段 mixin"""

    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    orders: int = 0
    sales: float = 0.0
    ctr: Optional[float] = None
    cpc: Optional[float] = None
    roas: Optional[float] = None
    acos: Optional[float] = None
    cvr: Optional[float] = None


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 50


class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    error: Optional[str] = None
