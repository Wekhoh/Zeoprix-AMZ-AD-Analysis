"""Tests for data_manage API — /data-stats and destructive /clear-data endpoint.

Guards the destructive DELETE /api/settings/clear-data behavior:
1. /data-stats returns correct per-table counts
2. /clear-data empties all advertising tables
3. /clear-data preserves config tables (Product, Rule, Marketplace, NegativeWhitelist)
4. /clear-data creates an automatic pre_clear backup
5. /clear-data returns accurate deletion counts
6. /clear-data on empty DB succeeds idempotently
"""

from sqlalchemy.orm import Session

from backend.models import (
    AdGroup,
    AdGroupDailyRecord,
    Backup,
    Campaign,
    CampaignDailyRecord,
    ImportHistory,
    InventorySnapshot,
    Keyword,
    KeywordAction,
    KeywordDailyRecord,
    Marketplace,
    NegativeWhitelist,
    Note,
    OperationLog,
    OrganicSales,
    PlacementRecord,
    Product,
    ProductVariant,
    Rule,
    SearchTermReport,
    SuggestionStatus,
)
from backend.services import backup_service


def _seed_full_advertising_data(db: Session) -> dict:
    """Seed one row in every advertising table so /clear-data has work to do."""
    mp = Marketplace(code="US", name="US", currency="USD")
    prod = Product(sku="SKU1", name="Prod1", category="cat1")
    db.add_all([mp, prod])
    db.flush()

    variant = ProductVariant(
        product_id=prod.id,
        variant_code="V1",
        variant_name="Default",
        marketplace_id=mp.id,
        unit_cost=5.0,
    )
    rule = Rule(
        name="TestRule",
        condition_field="acos",
        condition_operator=">",
        condition_value=0.5,
        action_type="flag_pause",
        is_active=1,
    )
    wl = NegativeWhitelist(search_term="protected-term", reason="test protection")
    db.add_all([variant, rule, wl])
    db.flush()

    camp = Campaign(
        name="Camp1",
        ad_type="SP",
        targeting_type="manual",
        match_type="exact",
        bidding_strategy="Fixed bids",
        base_bid=1.0,
        status="Delivering",
        marketplace_id=mp.id,
    )
    db.add(camp)
    db.flush()

    ag = AdGroup(campaign_id=camp.id, name="AG1", default_bid=1.0, status="Enabled")
    db.add(ag)
    db.flush()

    kw = Keyword(ad_group_id=ag.id, keyword_text="kw1", match_type="Exact", bid=1.0)
    db.add(kw)
    db.flush()

    db.add_all(
        [
            PlacementRecord(
                date="2026-04-01",
                campaign_id=camp.id,
                placement_type="搜索顶部",
                impressions=100,
                clicks=5,
                spend=5.0,
                orders=1,
                sales=25.0,
            ),
            OperationLog(
                date="2026-04-01",
                time="10:00",
                level_type="campaign",
                campaign_id=camp.id,
                change_type="base_bid",
                from_value="0.5",
                to_value="1.0",
            ),
            CampaignDailyRecord(
                campaign_id=camp.id,
                date="2026-04-01",
                impressions=100,
                clicks=5,
                spend=5.0,
                orders=1,
                sales=25.0,
            ),
            AdGroupDailyRecord(
                ad_group_id=ag.id,
                campaign_id=camp.id,
                date="2026-04-01",
                impressions=100,
                clicks=5,
                spend=5.0,
                orders=1,
                sales=25.0,
            ),
            SearchTermReport(
                date="2026-04-01",
                campaign_id=camp.id,
                search_term="query1",
                impressions=100,
                clicks=5,
                spend=5.0,
                orders=1,
                sales=25.0,
            ),
            Note(campaign_id=camp.id, content="note1"),
            OrganicSales(date="2026-04-01", total_sales=100.0, total_orders=10),
            ImportHistory(
                import_type="placement_csv",
                file_name="f.csv",
                records_imported=1,
                records_updated=0,
                records_skipped=0,
                status="success",
            ),
            KeywordAction(
                search_term="x",
                action_type="harvest_exact",
                from_campaign_id=camp.id,
            ),
            SuggestionStatus(
                suggestion_hash="hash1",
                suggestion_type="high_acos",
                status="resolved",
            ),
            InventorySnapshot(
                date="2026-04-01",
                sku="SKU1",
                asin="B01",
                units_available=10,
                units_inbound=0,
            ),
            KeywordDailyRecord(
                keyword_id=kw.id,
                date="2026-04-01",
                impressions=100,
                clicks=5,
                spend=5.0,
                orders=1,
                sales=25.0,
            ),
        ]
    )
    db.commit()

    return {
        "product_id": prod.id,
        "variant_id": variant.id,
        "rule_id": rule.id,
        "whitelist_id": wl.id,
        "marketplace_id": mp.id,
        "campaign_id": camp.id,
        "ad_group_id": ag.id,
        "keyword_id": kw.id,
    }


class TestDataStats:
    """GET /api/settings/data-stats — read-only count aggregator."""

    def test_returns_zero_counts_on_empty_db(self, client):
        response = client.get("/api/settings/data-stats")
        assert response.status_code == 200
        data = response.json()
        for key in [
            "campaigns",
            "ad_groups",
            "placement_records",
            "operation_logs",
            "campaign_daily",
            "ad_group_daily",
            "search_terms",
            "notes",
            "organic_sales",
            "import_history",
            "inventory_snapshots",
        ]:
            assert data[key] == 0, f"expected 0 for {key}, got {data[key]}"

    def test_reflects_seeded_rows(self, client, db_session):
        _seed_full_advertising_data(db_session)
        response = client.get("/api/settings/data-stats")
        assert response.status_code == 200
        data = response.json()
        assert data["campaigns"] == 1
        assert data["ad_groups"] == 1
        assert data["placement_records"] == 1
        assert data["operation_logs"] == 1
        assert data["campaign_daily"] == 1
        assert data["ad_group_daily"] == 1
        assert data["search_terms"] == 1
        assert data["notes"] == 1
        assert data["organic_sales"] == 1
        assert data["import_history"] == 1
        assert data["inventory_snapshots"] == 1


class TestClearDataEmptiesAdvertisingTables:
    """DELETE /api/settings/clear-data — must empty every advertising table."""

    def test_clears_all_advertising_tables(self, client, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        monkeypatch.setattr(backup_service.settings, "DATA_DIR", tmp_path)
        # Touch the db file so create_backup has something to copy
        (tmp_path / "tracker.db").write_bytes(b"stub")

        _seed_full_advertising_data(db_session)
        assert db_session.query(Campaign).count() == 1  # sanity

        response = client.delete("/api/settings/clear-data")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["success"] is True

        # Every advertising table must be empty
        for model in [
            PlacementRecord,
            OperationLog,
            CampaignDailyRecord,
            AdGroupDailyRecord,
            SearchTermReport,
            Note,
            AdGroup,
            Campaign,
            OrganicSales,
            ImportHistory,
            KeywordAction,
            SuggestionStatus,
            InventorySnapshot,
            # Keyword hierarchy must also be cleared — they hang off AdGroup
            Keyword,
            KeywordDailyRecord,
        ]:
            db_session.expire_all()
            count = db_session.query(model).count()
            assert count == 0, f"{model.__name__} should be empty after clear, found {count}"


class TestClearDataPreservesConfig:
    """Config-class tables must survive /clear-data."""

    def test_preserves_products_and_variants(self, client, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        monkeypatch.setattr(backup_service.settings, "DATA_DIR", tmp_path)
        (tmp_path / "tracker.db").write_bytes(b"stub")

        _seed_full_advertising_data(db_session)
        prod_count_before = db_session.query(Product).count()
        variant_count_before = db_session.query(ProductVariant).count()

        response = client.delete("/api/settings/clear-data")
        assert response.status_code == 200

        db_session.expire_all()
        assert db_session.query(Product).count() == prod_count_before
        assert db_session.query(ProductVariant).count() == variant_count_before

    def test_preserves_marketplaces(self, client, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        monkeypatch.setattr(backup_service.settings, "DATA_DIR", tmp_path)
        (tmp_path / "tracker.db").write_bytes(b"stub")

        _seed_full_advertising_data(db_session)
        before = db_session.query(Marketplace).count()

        response = client.delete("/api/settings/clear-data")
        assert response.status_code == 200

        db_session.expire_all()
        assert db_session.query(Marketplace).count() == before

    def test_preserves_rules(self, client, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        monkeypatch.setattr(backup_service.settings, "DATA_DIR", tmp_path)
        (tmp_path / "tracker.db").write_bytes(b"stub")

        _seed_full_advertising_data(db_session)
        before = db_session.query(Rule).count()

        response = client.delete("/api/settings/clear-data")
        assert response.status_code == 200

        db_session.expire_all()
        assert db_session.query(Rule).count() == before

    def test_preserves_negative_whitelist(self, client, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        monkeypatch.setattr(backup_service.settings, "DATA_DIR", tmp_path)
        (tmp_path / "tracker.db").write_bytes(b"stub")

        _seed_full_advertising_data(db_session)
        before = db_session.query(NegativeWhitelist).count()

        response = client.delete("/api/settings/clear-data")
        assert response.status_code == 200

        db_session.expire_all()
        assert db_session.query(NegativeWhitelist).count() == before


class TestClearDataBackup:
    """/clear-data must create a pre_clear Backup record before wiping."""

    def test_creates_pre_clear_backup_record(self, client, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        monkeypatch.setattr(backup_service.settings, "DATA_DIR", tmp_path)
        (tmp_path / "tracker.db").write_bytes(b"stub db contents")

        _seed_full_advertising_data(db_session)
        assert db_session.query(Backup).filter_by(backup_type="pre_clear").count() == 0

        response = client.delete("/api/settings/clear-data")
        assert response.status_code == 200
        body = response.json()
        assert body["backup_id"] is not None
        assert body["backup_path"], "backup_path must be present"

        db_session.expire_all()
        pre_clear = db_session.query(Backup).filter_by(backup_type="pre_clear").all()
        assert len(pre_clear) == 1, "exactly one pre_clear backup expected"
        # Backup survives the clear — Backup table is NOT in the delete list
        assert db_session.query(Backup).count() >= 1


class TestClearDataReturnsCorrectCounts:
    """The deleted-counts dict must reflect pre-delete row counts."""

    def test_counts_match_seeded_rows(self, client, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        monkeypatch.setattr(backup_service.settings, "DATA_DIR", tmp_path)
        (tmp_path / "tracker.db").write_bytes(b"stub")

        _seed_full_advertising_data(db_session)
        response = client.delete("/api/settings/clear-data")
        assert response.status_code == 200
        deleted = response.json()["deleted"]
        # Each table we seeded with 1 row
        for key in [
            "placement_records",
            "operation_logs",
            "campaign_daily",
            "ad_group_daily",
            "search_terms",
            "notes",
            "ad_groups",
            "campaigns",
            "organic_sales",
            "import_history",
            "keyword_actions",
            "suggestion_status",
            "inventory_snapshots",
        ]:
            assert deleted.get(key) == 1, f"{key} should report 1 deleted, got {deleted.get(key)}"


class TestClearDataOnEmptyDb:
    """Idempotent behavior: clearing an already-empty DB must not error."""

    def test_empty_db_succeeds(self, client, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        monkeypatch.setattr(backup_service.settings, "DATA_DIR", tmp_path)
        (tmp_path / "tracker.db").write_bytes(b"stub")

        response = client.delete("/api/settings/clear-data")
        assert response.status_code == 200
        assert response.json()["success"] is True
        # All counts should be 0
        for v in response.json()["deleted"].values():
            assert v == 0
