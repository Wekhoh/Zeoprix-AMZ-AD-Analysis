"""pytest fixtures for Amazon Ad Tracker tests"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import get_db
from backend.main import app
from backend.models import Base  # noqa: F401 — imports all models so metadata is populated


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
def seed_campaign_data(db_session: Session):
    """Seed 1 Marketplace, 2 Campaigns, 6 PlacementRecords for service tests."""
    from backend.models import Campaign, Marketplace, PlacementRecord, Product, ProductVariant

    mp = Marketplace(code="US", name="US", currency="USD")
    db_session.add(mp)
    db_session.flush()

    c1 = Campaign(
        name="Test-SP-Auto",
        ad_type="SP",
        targeting_type="auto",
        match_type="close",
        bidding_strategy="Fixed bids",
        base_bid=1.50,
        status="Delivering",
        marketplace_id=mp.id,
    )
    c2 = Campaign(
        name="Test-SP-Manual",
        ad_type="SP",
        targeting_type="manual",
        match_type="exact",
        bidding_strategy="Dynamic bidding (down only)",
        base_bid=2.00,
        status="Paused",
        marketplace_id=mp.id,
    )
    db_session.add_all([c1, c2])
    db_session.flush()

    # C1: 3 placements across 2 dates — total spend=60, sales=200, orders=8
    placements = [
        PlacementRecord(
            date="2025-11-10",
            campaign_id=c1.id,
            placement_type="搜索顶部",
            impressions=500,
            clicks=20,
            spend=20.0,
            orders=3,
            sales=80.0,
        ),
        PlacementRecord(
            date="2025-11-10",
            campaign_id=c1.id,
            placement_type="产品页面",
            impressions=300,
            clicks=10,
            spend=10.0,
            orders=2,
            sales=50.0,
        ),
        PlacementRecord(
            date="2025-11-11",
            campaign_id=c1.id,
            placement_type="搜索顶部",
            impressions=600,
            clicks=25,
            spend=30.0,
            orders=3,
            sales=70.0,
        ),
        # C2: spend=100, sales=0, orders=0 (money pit)
        PlacementRecord(
            date="2025-11-10",
            campaign_id=c2.id,
            placement_type="搜索顶部",
            impressions=2000,
            clicks=50,
            spend=50.0,
            orders=0,
            sales=0.0,
        ),
        PlacementRecord(
            date="2025-11-11",
            campaign_id=c2.id,
            placement_type="搜索顶部",
            impressions=1500,
            clicks=40,
            spend=50.0,
            orders=0,
            sales=0.0,
        ),
    ]
    db_session.add_all(placements)

    # Product with cost data for profit calculation
    prod = Product(sku="TEST-SKU", name="Test Product", category="test")
    db_session.add(prod)
    db_session.flush()
    variant = ProductVariant(
        product_id=prod.id,
        variant_code="V1",
        variant_name="Default",
        marketplace_id=mp.id,
        unit_cost=5.0,
        fba_fee=3.0,
        referral_fee_pct=0.15,
    )
    db_session.add(variant)
    db_session.commit()

    return {"marketplace": mp, "campaigns": [c1, c2]}


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
