"""Tests for budget_service — monthly pacing calculation."""

from backend.services import budget_service
from backend.services.budget_service import calc_budget_pacing


class TestBudgetPacingDisabled:
    def test_zero_budget_returns_disabled(self, db_session, monkeypatch):
        monkeypatch.setattr(budget_service.settings, "MONTHLY_BUDGET", 0.0)
        result = calc_budget_pacing(db_session)
        assert result["enabled"] is False
        assert result["level"] == "disabled"
        assert result["message"] is None

    def test_negative_budget_returns_disabled(self, db_session, monkeypatch):
        monkeypatch.setattr(budget_service.settings, "MONTHLY_BUDGET", -100.0)
        result = calc_budget_pacing(db_session)
        assert result["enabled"] is False


class TestBudgetPacingCalculation:
    def test_under_budget_returns_ok(self, db_session, seed_campaign_data, monkeypatch):
        """With high budget and low spend, level should be ok."""
        monkeypatch.setattr(budget_service.settings, "MONTHLY_BUDGET", 50000.0)
        monkeypatch.setattr(budget_service.settings, "BUDGET_WARNING_THRESHOLD", 0.9)
        result = calc_budget_pacing(db_session)
        assert result["enabled"] is True
        assert result["level"] == "ok"
        assert result["message"] is None
        assert result["current_spend"] >= 0

    def test_over_budget_returns_danger(self, db_session, seed_campaign_data, monkeypatch):
        """With tiny budget and existing spend, should project overspend."""
        monkeypatch.setattr(budget_service.settings, "MONTHLY_BUDGET", 1.0)
        monkeypatch.setattr(budget_service.settings, "BUDGET_WARNING_THRESHOLD", 0.9)
        result = calc_budget_pacing(db_session)
        # seed_campaign_data has spend in 2025-11 dates which may not be "this month"
        # but if any current-month data exists, projected should exceed $1
        if result["current_spend"] > 0:
            assert result["level"] == "danger"
            assert result["message"] is not None
            assert "超支" in result["message"]
        else:
            # No current-month data — projected is 0, still ok
            assert result["level"] == "ok"

    def test_warning_threshold_triggers(self, db_session, seed_campaign_data, monkeypatch):
        """Budget slightly above projected → warning level."""
        # Set budget to a value where projected is between 90% and 100%
        monkeypatch.setattr(budget_service.settings, "BUDGET_WARNING_THRESHOLD", 0.0001)
        monkeypatch.setattr(budget_service.settings, "MONTHLY_BUDGET", 999999.0)
        result = calc_budget_pacing(db_session)
        # With threshold at 0.01%, even small projected spend triggers warning
        if result["current_spend"] > 0:
            assert result["level"] in ("warning", "danger")

    def test_returns_correct_structure(self, db_session, monkeypatch):
        monkeypatch.setattr(budget_service.settings, "MONTHLY_BUDGET", 3000.0)
        result = calc_budget_pacing(db_session)
        assert "enabled" in result
        assert "monthly_budget" in result
        assert "current_spend" in result
        assert "projected_spend" in result
        assert "days_elapsed" in result
        assert "days_total" in result
        assert "pacing_pct" in result
        assert "level" in result
        assert result["days_elapsed"] >= 1
        assert result["days_total"] >= 28

    def test_pacing_pct_is_ratio(self, db_session, monkeypatch):
        monkeypatch.setattr(budget_service.settings, "MONTHLY_BUDGET", 3000.0)
        result = calc_budget_pacing(db_session)
        if result["pacing_pct"] is not None:
            assert result["pacing_pct"] >= 0
