"""Tests for summary_service — dashboard KPI, by-date, by-campaign, comparison"""

from backend.services.summary_service import (
    summary_by_date,
    summary_by_campaign,
    dashboard_overview,
    compare_periods,
    compare_multi_periods,
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


class TestCompareMultiPeriods:
    def test_returns_N_periods_in_chronological_order(self, db_session, seed_campaign_data):
        result = compare_multi_periods(db_session, unit="week", count=4, end_date="2025-11-11")
        assert result["unit"] == "week"
        assert result["count"] == 4
        assert len(result["periods"]) == 4
        # Chronological order: first period "from" < last period "from"
        first = result["periods"][0]["from"]
        last = result["periods"][-1]["from"]
        assert first < last

    def test_series_has_one_value_per_period(self, db_session, seed_campaign_data):
        result = compare_multi_periods(db_session, unit="week", count=4, end_date="2025-11-11")
        for metric_key, values in result["series"].items():
            assert len(values) == 4, f"{metric_key} should have 4 values"

    def test_count_bounds_clamped(self, db_session, seed_campaign_data):
        # count > 52 should be clamped
        result = compare_multi_periods(db_session, unit="week", count=100, end_date="2025-11-11")
        assert result["count"] == 52
        # count < 1 should be clamped to 1
        result2 = compare_multi_periods(db_session, unit="week", count=0, end_date="2025-11-11")
        assert result2["count"] == 1

    def test_invalid_unit_defaults_to_week(self, db_session, seed_campaign_data):
        result = compare_multi_periods(db_session, unit="invalid", count=2, end_date="2025-11-11")
        assert result["unit"] == "week"

    def test_invalid_end_date_uses_today(self, db_session, seed_campaign_data):
        # Should not crash, uses today instead
        result = compare_multi_periods(db_session, unit="week", count=2, end_date="not-a-date")
        assert len(result["periods"]) == 2
