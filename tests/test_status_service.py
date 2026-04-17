"""Tests for status_service.update_campaign_statuses.

Guards the "infer current campaign status from OperationLog" behavior:
1. Picks the latest Campaign-status log by (date desc, time desc)
2. Ignores non-status change_types (e.g. Daily budget, Targeting group status)
3. Ignores invalid to_value strings (e.g. "In budget")
4. Only writes when status actually changes (idempotent)
5. Sets status_updated_at to the log's date
6. Respects the campaign_ids filter
"""

from backend.models import Campaign, Marketplace, OperationLog
from backend.services.status_service import update_campaign_statuses


def _make_campaign(db, name="Test-SP", status="Delivering") -> Campaign:
    mp = db.query(Marketplace).filter_by(code="US").first()
    if mp is None:
        mp = Marketplace(code="US", name="US", currency="USD")
        db.add(mp)
        db.flush()
    camp = Campaign(
        name=name,
        ad_type="SP",
        targeting_type="auto",
        bidding_strategy="Fixed bids",
        status=status,
        marketplace_id=mp.id,
    )
    db.add(camp)
    db.flush()
    return camp


def _add_log(
    db,
    campaign_id: int,
    date: str,
    time: str,
    change_type: str,
    to_value: str,
    from_value: str | None = None,
):
    db.add(
        OperationLog(
            date=date,
            time=time,
            level_type="campaign",
            campaign_id=campaign_id,
            change_type=change_type,
            from_value=from_value,
            to_value=to_value,
        )
    )
    db.flush()


class TestUpdateCampaignStatuses:
    def test_no_campaigns_returns_zero(self, db_session):
        assert update_campaign_statuses(db_session) == 0

    def test_picks_latest_status_log(self, db_session):
        """Among out-of-order logs, the one with greatest (date, time) wins."""
        camp = _make_campaign(db_session, status="Paused")
        _add_log(db_session, camp.id, "2026-04-10", "09:00", "Campaign status", "Paused")
        _add_log(db_session, camp.id, "2026-04-12", "14:30", "Campaign status", "Delivering")
        _add_log(db_session, camp.id, "2026-04-11", "10:00", "Campaign status", "Archived")

        # 2026-04-12 14:30 "Delivering" is the latest and differs from current Paused.
        assert update_campaign_statuses(db_session) == 1
        db_session.refresh(camp)
        assert camp.status == "Delivering"
        assert camp.status_updated_at == "2026-04-12"

    def test_writes_only_when_status_changes(self, db_session):
        camp = _make_campaign(db_session, status="Delivering")
        _add_log(db_session, camp.id, "2026-04-12", "09:00", "Campaign status", "Paused")

        updated = update_campaign_statuses(db_session)
        assert updated == 1
        db_session.refresh(camp)
        assert camp.status == "Paused"
        assert camp.status_updated_at == "2026-04-12"

        # Re-run: no changes this time
        assert update_campaign_statuses(db_session) == 0

    def test_ignores_non_status_change_types(self, db_session):
        camp = _make_campaign(db_session, status="Delivering")
        # These must NOT affect status
        _add_log(db_session, camp.id, "2026-04-12", "09:00", "Daily budget", "50.00")
        _add_log(
            db_session,
            camp.id,
            "2026-04-12",
            "10:00",
            "Targeting group status",
            "Paused",
        )

        assert update_campaign_statuses(db_session) == 0
        db_session.refresh(camp)
        assert camp.status == "Delivering"

    def test_ignores_invalid_to_value(self, db_session):
        camp = _make_campaign(db_session, status="Delivering")
        # "In budget" / "Out of budget" are noisy budget-state reports, not status
        _add_log(db_session, camp.id, "2026-04-12", "09:00", "Campaign status", "In budget")

        assert update_campaign_statuses(db_session) == 0
        db_session.refresh(camp)
        assert camp.status == "Delivering"

    def test_respects_campaign_ids_filter(self, db_session):
        a = _make_campaign(db_session, name="Camp-A", status="Delivering")
        b = _make_campaign(db_session, name="Camp-B", status="Delivering")
        _add_log(db_session, a.id, "2026-04-12", "09:00", "Campaign status", "Paused")
        _add_log(db_session, b.id, "2026-04-12", "09:00", "Campaign status", "Paused")

        # Only update A
        assert update_campaign_statuses(db_session, campaign_ids=[a.id]) == 1
        db_session.refresh(a)
        db_session.refresh(b)
        assert a.status == "Paused"
        assert b.status == "Delivering"  # unchanged

    def test_ties_on_date_break_on_time(self, db_session):
        camp = _make_campaign(db_session, status="Delivering")
        _add_log(db_session, camp.id, "2026-04-12", "09:00", "Campaign status", "Archived")
        _add_log(db_session, camp.id, "2026-04-12", "15:30", "Campaign status", "Paused")

        assert update_campaign_statuses(db_session) == 1
        db_session.refresh(camp)
        assert camp.status == "Paused"  # 15:30 wins
