"""pytest fixtures for Amazon Ad Tracker tests"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.models import Base  # noqa: F401 — imports all models so metadata is populated
from backend.database import get_db
from backend.main import app


@pytest.fixture()
def db_session():
    """In-memory SQLite session: create all tables, yield, teardown."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session):
    """FastAPI TestClient with db dependency override."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_csv() -> str:
    """Small SP placement CSV string (3 rows, known values)."""
    return (
        "Placement,Campaign bidding strategy,Bid adjustment,Impressions,Clicks,"
        "Spend (USD),Orders,Sales (USD)\r\n"
        "PLACEMENT_TOP,Dynamic bidding (down only),50%,1000,50,$25.00,5,$150.00\r\n"
        "PLACEMENT_REST_OF_SEARCH,Dynamic bidding (down only),,500,20,$10.00,2,$60.00\r\n"
        "PLACEMENT_PRODUCT_PAGE,Dynamic bidding (down only),,300,10,$5.00,1,$30.00\r\n"
    )
