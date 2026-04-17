"""数据库引擎、会话管理、初始化"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.config import settings

# SQLite WAL 模式 + 外键支持
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入: 数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_migrations(connection):
    """Run lightweight ALTER TABLE migrations for new columns on existing tables."""
    cursor = connection.cursor()
    # Check and add category_key to products
    cursor.execute("PRAGMA table_info(products)")
    product_cols = {row[1] for row in cursor.fetchall()}
    if "category_key" not in product_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN category_key TEXT")

    # Add tags column to campaigns for labeling/grouping
    cursor.execute("PRAGMA table_info(campaigns)")
    campaign_cols = {row[1] for row in cursor.fetchall()}
    if "tags" not in campaign_cols:
        cursor.execute("ALTER TABLE campaigns ADD COLUMN tags TEXT")

    # Add deleted_at to notes (soft delete)
    cursor.execute("PRAGMA table_info(notes)")
    note_cols = {row[1] for row in cursor.fetchall()}
    if "deleted_at" not in note_cols:
        cursor.execute("ALTER TABLE notes ADD COLUMN deleted_at TEXT")

    # Add deleted_at to organic_sales (soft delete)
    cursor.execute("PRAGMA table_info(organic_sales)")
    os_cols = {row[1] for row in cursor.fetchall()}
    if "deleted_at" not in os_cols:
        cursor.execute("ALTER TABLE organic_sales ADD COLUMN deleted_at TEXT")

    # Sprint 13.3 + Batch 15: Create performance indexes (idempotent)
    _indexes = [
        ("ix_placement_campaign_date", "placement_records", "campaign_id, date"),
        ("ix_cdaily_campaign_date", "campaign_daily_records", "campaign_id, date"),
        ("ix_adaily_adgroup_date", "ad_group_daily_records", "ad_group_id, date"),
        ("ix_oplog_campaign_date", "operation_logs", "campaign_id, date"),
        ("ix_sterm_campaign", "search_term_reports", "campaign_id"),
        ("ix_note_campaign", "notes", "campaign_id"),
        # Batch 15 perf: single-column indexes for date-only queries (dashboard, summary)
        ("ix_placement_date", "placement_records", "date"),
        # Batch 15 perf: placement_type filter used in placements endpoint
        ("ix_placement_type", "placement_records", "placement_type"),
        # Phase C6 perf: compound index for "filter by placement_type within a campaign"
        ("ix_placement_type_campaign", "placement_records", "placement_type, campaign_id"),
        # Batch 15 perf: soft-delete filtering
        ("ix_notes_deleted_at", "notes", "deleted_at"),
        ("ix_organic_sales_deleted_at", "organic_sales", "deleted_at"),
    ]
    for idx_name, table, cols in _indexes:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({cols})")

    cursor.close()


def init_db():
    """创建所有表"""
    from backend.models.base import Base  # noqa: F811

    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    # Run lightweight migrations for new columns on existing tables
    with engine.connect() as conn:
        _run_migrations(conn.connection)
        conn.commit()
