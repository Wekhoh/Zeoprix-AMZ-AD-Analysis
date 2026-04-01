"""广告活动 schema"""

from typing import Optional
from pydantic import BaseModel


class CampaignOut(BaseModel):
    id: int
    name: str
    ad_type: str
    targeting_type: str
    match_type: Optional[str] = None
    bidding_strategy: str
    base_bid: Optional[float] = None
    portfolio: Optional[str] = None
    status: str
    status_updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class CampaignDetail(CampaignOut):
    """广告活动详情（含 KPI 汇总）"""

    total_impressions: int = 0
    total_clicks: int = 0
    total_spend: float = 0.0
    total_orders: int = 0
    total_sales: float = 0.0
    ctr: Optional[float] = None
    cpc: Optional[float] = None
    roas: Optional[float] = None
    acos: Optional[float] = None
    first_date: Optional[str] = None
    last_date: Optional[str] = None
