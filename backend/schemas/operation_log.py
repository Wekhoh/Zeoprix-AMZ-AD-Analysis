"""操作日志 schema"""

from typing import Optional
from pydantic import BaseModel


class OperationLogOut(BaseModel):
    id: int
    date: str
    time: str
    operator: Optional[str] = None
    level_type: str
    campaign_id: int
    campaign_name: Optional[str] = None
    change_type: str
    from_value: Optional[str] = None
    to_value: Optional[str] = None

    model_config = {"from_attributes": True}
