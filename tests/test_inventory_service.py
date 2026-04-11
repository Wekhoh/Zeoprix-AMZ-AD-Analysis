"""Tests for inventory_service — CSV parsing, alert thresholds, upsert, campaign join"""

from backend.models import (
    Campaign,
    InventorySnapshot,
    Marketplace,
    Product,
    ProductVariant,
)
from backend.services.inventory_service import (
    _calc_alert_level,
    get_inventory_risk_for_campaigns,
    get_latest_inventory,
    get_risk_summary,
    import_inventory,
    parse_inventory_csv,
)


class TestCalcAlertLevel:
    def test_none_is_unknown(self):
        assert _calc_alert_level(None) == "unknown"

    def test_critical_below_3_days(self):
        assert _calc_alert_level(0) == "critical"
        assert _calc_alert_level(2.99) == "critical"

    def test_warning_between_3_and_7_days(self):
        assert _calc_alert_level(3) == "warning"
        assert _calc_alert_level(6.99) == "warning"

    def test_ok_at_or_above_7_days(self):
        assert _calc_alert_level(7) == "ok"
        assert _calc_alert_level(30) == "ok"


class TestParseInventoryCsv:
    def test_empty_string_returns_empty(self):
        assert parse_inventory_csv("") == []
        assert parse_inventory_csv("   \n   ") == []

    def test_english_headers(self):
        content = (
            "sku,asin,Available,Inbound Quantity,Days of Supply\n"
            "SKU-A,B001,100,20,15\n"
            "SKU-B,B002,5,0,2\n"
        )
        rows = parse_inventory_csv(content)
        assert len(rows) == 2
        assert rows[0]["sku"] == "SKU-A"
        assert rows[0]["asin"] == "B001"
        assert rows[0]["units_available"] == 100
        assert rows[0]["units_inbound"] == 20
        assert rows[0]["days_of_supply"] == 15.0
        assert rows[1]["days_of_supply"] == 2.0

    def test_chinese_headers(self):
        content = "商家 SKU,ASIN,可售数量,在途库存,供货天数\nSKU-CN-1,B999,50,10,5\n"
        rows = parse_inventory_csv(content)
        assert len(rows) == 1
        assert rows[0]["sku"] == "SKU-CN-1"
        assert rows[0]["asin"] == "B999"
        assert rows[0]["units_available"] == 50
        assert rows[0]["units_inbound"] == 10
        assert rows[0]["days_of_supply"] == 5.0

    def test_skips_metadata_rows_before_header(self):
        content = (
            "Report Date: 2026-04-10\n"
            "Marketplace: US\n"
            "\n"
            "sku,Available,Days of Supply\n"
            "SKU-X,42,10\n"
        )
        rows = parse_inventory_csv(content)
        assert len(rows) == 1
        assert rows[0]["sku"] == "SKU-X"
        assert rows[0]["units_available"] == 42

    def test_missing_days_of_supply_stays_none(self):
        content = "sku,Available,Days of Supply\nSKU-NoDoS,10,\n"
        rows = parse_inventory_csv(content)
        assert len(rows) == 1
        assert rows[0]["days_of_supply"] is None

    def test_numeric_cleaning_handles_commas(self):
        content = 'sku,Available\nSKU-Big,"1,250"\n'
        rows = parse_inventory_csv(content)
        assert rows[0]["units_available"] == 1250

    def test_rows_without_sku_are_dropped(self):
        content = "sku,Available\n,100\nSKU-A,50\n"
        rows = parse_inventory_csv(content)
        assert len(rows) == 1
        assert rows[0]["sku"] == "SKU-A"


class TestImportInventory:
    def test_import_new_snapshot(self, db_session):
        content = "sku,Available,Days of Supply\nSKU-NEW,100,15\n"
        result = import_inventory(db_session, content)
        assert result["imported"] == 1
        assert result["updated"] == 0
        assert result["critical_count"] == 0
        snap = db_session.query(InventorySnapshot).filter_by(sku="SKU-NEW").first()
        assert snap is not None
        assert snap.alert_level == "ok"
        assert snap.units_available == 100

    def test_import_critical_sku(self, db_session):
        content = "sku,Available,Days of Supply\nSKU-CRIT,5,2\n"
        result = import_inventory(db_session, content)
        assert result["imported"] == 1
        assert result["critical_count"] == 1
        assert result["warning_count"] == 0
        snap = db_session.query(InventorySnapshot).filter_by(sku="SKU-CRIT").first()
        assert snap.alert_level == "critical"

    def test_import_upsert_same_day(self, db_session):
        """Importing twice on same day should update, not duplicate."""
        content_v1 = "sku,Available,Days of Supply\nSKU-UP,100,10\n"
        import_inventory(db_session, content_v1)

        content_v2 = "sku,Available,Days of Supply\nSKU-UP,80,8\n"
        result = import_inventory(db_session, content_v2)
        assert result["updated"] == 1
        assert result["imported"] == 0

        snaps = db_session.query(InventorySnapshot).filter_by(sku="SKU-UP").all()
        assert len(snaps) == 1
        assert snaps[0].units_available == 80
        assert snaps[0].days_of_supply == 8.0

    def test_import_matches_variant_by_sku(self, db_session):
        """ProductVariant.variant_code matching SKU should populate variant_id."""
        mp = Marketplace(code="US", name="US", currency="USD")
        db_session.add(mp)
        db_session.flush()
        prod = Product(sku="P1", name="Test", category="test")
        db_session.add(prod)
        db_session.flush()
        variant = ProductVariant(
            product_id=prod.id,
            variant_code="SKU-MATCH",
            variant_name="V1",
            marketplace_id=mp.id,
        )
        db_session.add(variant)
        db_session.commit()

        content = "sku,Available,Days of Supply\nSKU-MATCH,50,10\n"
        import_inventory(db_session, content)
        snap = db_session.query(InventorySnapshot).filter_by(sku="SKU-MATCH").first()
        assert snap.variant_id == variant.id

    def test_import_empty_csv_returns_error(self, db_session):
        result = import_inventory(db_session, "not a csv\nrandom stuff\n")
        assert result["imported"] == 0
        assert "error" in result

    def test_import_over_row_limit_rejected(self, db_session, monkeypatch):
        """B0-3c: row-count DoS guard. Lower limit to 5 and feed 10 rows."""
        from backend.services import inventory_service

        monkeypatch.setattr(inventory_service, "MAX_INVENTORY_ROWS", 5)

        header = "sku,Available,Days of Supply\n"
        rows = "".join(f"SKU-HUGE-{i},100,15\n" for i in range(10))
        content = header + rows

        result = import_inventory(db_session, content)
        assert result["imported"] == 0
        assert "error" in result
        assert "行数超过" in result["error"]
        # Critical: nothing should have been written to db
        snaps = (
            db_session.query(InventorySnapshot)
            .filter(InventorySnapshot.sku.like("SKU-HUGE-%"))
            .count()
        )
        assert snaps == 0

    def test_import_under_row_limit_imports_normally(self, db_session, monkeypatch):
        """Regression: row count just under the limit still imports."""
        from backend.services import inventory_service

        monkeypatch.setattr(inventory_service, "MAX_INVENTORY_ROWS", 10)

        header = "sku,Available,Days of Supply\n"
        # 5 rows (under the limit of 10)
        rows = "".join(f"SKU-OK-{i},100,15\n" for i in range(5))
        content = header + rows

        result = import_inventory(db_session, content)
        assert result["imported"] == 5


class TestRiskSummary:
    def test_risk_summary_counts(self, db_session):
        content = (
            "sku,Available,Days of Supply\n"
            "SKU-1,5,2\n"  # critical
            "SKU-2,20,5\n"  # warning
            "SKU-3,100,15\n"  # ok
        )
        import_inventory(db_session, content)
        summary = get_risk_summary(db_session)
        assert summary["critical_count"] == 1
        assert summary["warning_count"] == 1
        assert summary["ok_count"] == 1
        assert len(summary["top_risk_skus"]) == 2  # only critical + warning
        # sorted by days ascending → SKU-1 first
        assert summary["top_risk_skus"][0]["sku"] == "SKU-1"

    def test_get_latest_inventory_filter(self, db_session):
        content = "sku,Available,Days of Supply\nSKU-C,5,2\nSKU-O,100,15\n"
        import_inventory(db_session, content)
        crit_only = get_latest_inventory(db_session, alert_levels=["critical"])
        assert len(crit_only) == 1
        assert crit_only[0]["sku"] == "SKU-C"


class TestCampaignInventoryJoin:
    def test_join_via_variant(self, db_session):
        """Campaign → ProductVariant → InventorySnapshot join populates risk list."""
        mp = Marketplace(code="US", name="US", currency="USD")
        db_session.add(mp)
        db_session.flush()
        prod = Product(sku="P-JOIN", name="JoinTest", category="test")
        db_session.add(prod)
        db_session.flush()
        variant = ProductVariant(
            product_id=prod.id,
            variant_code="SKU-JOIN",
            variant_name="V1",
            marketplace_id=mp.id,
        )
        db_session.add(variant)
        db_session.flush()
        camp = Campaign(
            name="JoinCamp",
            ad_type="SP",
            targeting_type="auto",
            bidding_strategy="Fixed bids",
            status="Delivering",
            marketplace_id=mp.id,
            variant_id=variant.id,
        )
        db_session.add(camp)
        db_session.commit()

        content = "sku,Available,Days of Supply\nSKU-JOIN,5,2\n"
        import_inventory(db_session, content)

        risks = get_inventory_risk_for_campaigns(db_session)
        assert len(risks) == 1
        assert risks[0]["campaign_name"] == "JoinCamp"
        assert risks[0]["sku"] == "SKU-JOIN"
        assert risks[0]["alert_level"] == "critical"
        assert risks[0]["days_of_supply"] == 2.0

    def test_no_risk_when_ok_level(self, db_session):
        mp = Marketplace(code="US", name="US", currency="USD")
        db_session.add(mp)
        db_session.flush()
        prod = Product(sku="P-OK", name="OK", category="test")
        db_session.add(prod)
        db_session.flush()
        variant = ProductVariant(
            product_id=prod.id,
            variant_code="SKU-OK",
            variant_name="V1",
            marketplace_id=mp.id,
        )
        db_session.add(variant)
        db_session.flush()
        camp = Campaign(
            name="OKCamp",
            ad_type="SP",
            targeting_type="auto",
            bidding_strategy="Fixed bids",
            status="Delivering",
            marketplace_id=mp.id,
            variant_id=variant.id,
        )
        db_session.add(camp)
        db_session.commit()

        content = "sku,Available,Days of Supply\nSKU-OK,100,15\n"
        import_inventory(db_session, content)

        risks = get_inventory_risk_for_campaigns(db_session)
        # get_inventory_risk_for_campaigns filters by critical/warning only
        assert risks == []
