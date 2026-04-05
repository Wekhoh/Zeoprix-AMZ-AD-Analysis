"""Tests for summary_service — dashboard KPI, by-date, by-campaign, comparison"""

from backend.services.summary_service import (
    summary_by_date,
    summary_by_campaign,
    dashboard_overview,
    compare_periods,
)


class TestSummaryByDate:
    def test_returns_rows_grouped_by_date(self, db_session, seed_campaign_data):
        rows = summary_by_date(db_session)
        dates = [r["date"] for r in rows]
        assert len(dates) >= 2
        assert len(dates) == len(set(dates))  # no duplicates

    def test_date_filtering(self, db_session, seed_campaign_data):
        rows = summary_by_date(db_session, date_from="2025-11-11", date_to="2025-11-11")
        assert len(rows) == 1
        assert rows[0]["date"] == "2025-11-11"

    def test_kpi_values_correct(self, db_session, seed_campaign_data):
        rows = summary_by_date(db_session, date_from="2025-11-10", date_to="2025-11-10")
        assert len(rows) == 1
        row = rows[0]
        # C1: spend=30, C2: spend=50 on 2025-11-10
        assert row["spend"] == 80.0
        assert row["orders"] == 5  # C1: 3+2, C2: 0

    def test_empty_db_returns_empty_list(self, db_session):
        rows = summary_by_date(db_session)
        assert rows == []


class TestSummaryByCampaign:
    def test_returns_one_row_per_campaign(self, db_session, seed_campaign_data):
        rows = summary_by_campaign(db_session)
        assert len(rows) == 2

    def test_includes_campaign_metadata(self, db_session, seed_campaign_data):
        rows = summary_by_campaign(db_session)
        names = {r["campaign_name"] for r in rows}
        assert "Test-SP-Auto" in names
        assert "Test-SP-Manual" in names


class TestDashboardOverview:
    def test_returns_all_sections(self, db_session, seed_campaign_data):
        result = dashboard_overview(db_session)
        assert "kpi" in result
        assert "status_counts" in result
        assert "daily_trend" in result
        assert "top_campaigns" in result

    def test_alerts_generated_for_high_acos(self, db_session, seed_campaign_data):
        result = dashboard_overview(db_session)
        alerts = result.get("alerts", [])
        # C2 has spend=100, sales=0 → ACOS undefined, but spend>0 orders=0 → zero_orders alert
        alert_types = {a["type"] for a in alerts}
        assert "zero_orders" in alert_types or "high_acos" in alert_types


class TestComparePeriods:
    def test_deltas_correct_sign(self, db_session, seed_campaign_data):
        result = compare_periods(
            db_session,
            "2025-11-10",
            "2025-11-10",
            "2025-11-11",
            "2025-11-11",
        )
        # Returns dict with period_a, period_b, deltas
        assert "period_a" in result
        assert "period_b" in result
        assert "deltas" in result
        # Both periods have same spend ($80) → delta=0 → favorable=True (not worse)
        assert result["deltas"]["spend"]["percent"] == 0.0
        # Verify deltas have expected structure
        for key in ("spend", "orders", "acos", "roas"):
            delta = result["deltas"][key]
            assert "absolute" in delta
            assert "percent" in delta
            assert "favorable" in delta

    def test_zero_base_period_handles_none(self, db_session, seed_campaign_data):
        # Period A has no data → should not crash with division by zero
        result = compare_periods(
            db_session,
            "2020-01-01",
            "2020-01-02",
            "2025-11-10",
            "2025-11-10",
        )
        assert "period_a" in result
        # period_a values should be 0
        assert result["period_a"]["spend"] == 0
        assert result["period_a"]["orders"] == 0
