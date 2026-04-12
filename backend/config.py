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

    # 建议引擎阈值（用于 analysis_service / rule_engine 的建议生成）
    ACOS_WARNING_THRESHOLD: float = 0.50
    ACOS_TARGET: float = 0.30
    ROAS_SCALE_UP_THRESHOLD: float = 3.0
    CTR_WARNING_THRESHOLD: float = 0.002
    CTR_MIN_IMPRESSIONS: int = 1000
    ZERO_ORDERS_MIN_SPEND: float = 5.0
    CPC_OVERPAY_RATIO: float = 1.5

    # 月度预算 Pacing（用于 budget_service 超支预测）
    # 设为 0 表示不启用预算监控。可在 .env 中覆盖。
    MONTHLY_BUDGET: float = 0.0  # 月度广告总预算 (USD)
    BUDGET_WARNING_THRESHOLD: float = 0.9  # 预计超支到 90% 时预警

    # Dashboard alert 阈值（用于 summary_service._generate_dashboard_alerts）
    # 注意：这些比建议引擎阈值更敏感——dashboard 要"一眼发现需要立即处理的"，
    # 而建议引擎是"值得运营审查的"，两者故意不同
    DASHBOARD_ACOS_ALERT_THRESHOLD: float = 0.40  # dashboard 今日行动清单里的高 ACOS 门槛
    DASHBOARD_ROAS_SCALE_UP_THRESHOLD: float = 3.0  # "扩量机会" 门槛，目前与建议引擎同值

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
