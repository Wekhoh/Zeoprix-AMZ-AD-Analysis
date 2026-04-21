"""展示位置 schema"""

from typing import Optional

from pydantic import BaseModel


class PlacementOut(BaseModel):
    id: int
    date: str
    campaign_id: int
    campaign_name: Optional[str] = None
    placement_type: str
    bidding_strategy: Optional[str] = None
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
    notes: Optional[str] = None

    model_config = {"from_attributes": True}
