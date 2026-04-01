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
