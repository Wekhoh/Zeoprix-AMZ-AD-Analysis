"""Tests for rule_engine — condition checking, batch metrics, rule evaluation"""

from backend.services.rule_engine import (
    _check_condition,
    _batch_campaign_metrics,
    evaluate_rules,
    get_rule_results,
    seed_default_rules,
)


class TestCheckCondition:
    def test_gt_operator_true(self):
        metrics = {"acos": 0.5, "clicks": 30}
        triggered, value = _check_condition(metrics, "acos", ">", 0.4, 0)
        assert triggered is True
        assert value == 0.5

    def test_gt_operator_false(self):
        metrics = {"acos": 0.3, "clicks": 30}
        triggered, _ = _check_condition(metrics, "acos", ">", 0.4, 0)
        assert triggered is False

    def test_min_data_blocks_low_clicks(self):
        metrics = {"acos": 0.8, "clicks": 5}
        triggered, _ = _check_condition(metrics, "acos", ">", 0.4, 20)
        assert triggered is False

    def test_missing_field_returns_false(self):
        metrics = {"clicks": 10}
        triggered, value = _check_condition(metrics, "acos", ">", 0.4, 0)
        assert triggered is False
        assert value is None

    def test_invalid_operator_returns_false(self):
        metrics = {"acos": 0.5, "clicks": 10}
        triggered, _ = _check_condition(metrics, "acos", "!=", 0.4, 0)
        assert triggered is False


class TestBatchCampaignMetrics:
    def test_returns_dict_keyed_by_campaign_id(self, db_session, seed_campaign_data):
        # Seed data is from 2025-11, use large period to include it
        result = _batch_campaign_metrics(db_session, 365)
        data = seed_campaign_data
        for c in data["campaigns"]:
            assert c.id in result

    def test_respects_period_cutoff(self, db_session, seed_campaign_data):
        # Period 0 days → cutoff is today, all historical data excluded
        result = _batch_campaign_metrics(db_session, 0)
        # Data is from 2025-11-10/11 which is in the past → should be empty
        assert len(result) == 0


class TestEvaluateRules:
    def test_seed_and_evaluate(self, db_session, seed_campaign_data):
        seeded = seed_default_rules(db_session)
        assert seeded >= 1
        results = evaluate_rules(db_session)
        # Should return a list (may or may not have triggered rules)
        assert isinstance(results, list)

    def test_updates_last_run_at(self, db_session, seed_campaign_data):
        from backend.models import Rule

        seed_default_rules(db_session)
        rules_before = db_session.query(Rule).all()
        old_times = {r.id: r.last_run_at for r in rules_before}
        evaluate_rules(db_session)
        for rule in db_session.query(Rule).all():
            assert rule.last_run_at is not None
            if old_times[rule.id] is None:
                assert rule.last_run_at is not None


class TestDryRun:
    """B4-1: dry_run mode should return results without side effects."""

    def test_dry_run_returns_results(self, db_session, seed_campaign_data):
        seeded = seed_default_rules(db_session)
        assert seeded >= 1

        from backend.models import Rule

        rule = db_session.query(Rule).first()
        results = get_rule_results(db_session, rule.id, dry_run=True)
        assert isinstance(results, list)

    def test_dry_run_does_not_update_last_run_at(self, db_session, seed_campaign_data):
        from backend.models import Rule

        seed_default_rules(db_session)
        rule = db_session.query(Rule).first()
        original_last_run = rule.last_run_at

        get_rule_results(db_session, rule.id, dry_run=True)

        db_session.refresh(rule)
        assert rule.last_run_at == original_last_run, (
            f"dry_run should NOT update last_run_at. "
            f"Was {original_last_run!r}, now {rule.last_run_at!r}"
        )

    def test_normal_run_does_update_last_run_at(self, db_session, seed_campaign_data):
        """Regression: non-dry-run still updates last_run_at."""
        from backend.models import Rule

        seed_default_rules(db_session)
        rule = db_session.query(Rule).first()
        assert rule.last_run_at is None

        get_rule_results(db_session, rule.id, dry_run=False)

        db_session.refresh(rule)
        assert rule.last_run_at is not None
