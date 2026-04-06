"""应用配置"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "亚马逊广告智能追踪系统"
    VERSION: str = "1.0.0"

    # 路径
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    BACKUP_DIR: Path = DATA_DIR / "backups"

    # 数据库
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'tracker.db'}"

    # 前端（开发模式）
    FRONTEND_URL: str = "http://localhost:5173"

    # 备份
    MAX_BACKUPS: int = 10

    # 建议引擎阈值
    ACOS_WARNING_THRESHOLD: float = 0.50
    ACOS_TARGET: float = 0.30
    ROAS_SCALE_UP_THRESHOLD: float = 3.0
    CTR_WARNING_THRESHOLD: float = 0.002
    CTR_MIN_IMPRESSIONS: int = 1000
    ZERO_ORDERS_MIN_SPEND: float = 5.0
    CPC_OVERPAY_RATIO: float = 1.5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
