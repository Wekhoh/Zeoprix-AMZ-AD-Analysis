"""Tests for B2 search term harvest enhancements: whitelist exclusion + suggested bid."""

from backend.models import (
    Campaign,
    Marketplace,
    NegativeWhitelist,
    SearchTermReport,
)
from backend.services.search_term_service import classify_search_terms_4bucket


def _seed_search_terms(db_session):
    """Seed a campaign + search term data covering all 4 buckets."""
    mp = Marketplace(code="US", name="US", currency="USD")
    db_session.add(mp)
    db_session.flush()

    camp = Campaign(
        name="Test-Bucket-Camp",
        ad_type="SP",
        targeting_type="auto",
        bidding_strategy="Fixed bids",
        status="Delivering",
        marketplace_id=mp.id,
    )
    db_session.add(camp)
    db_session.flush()

    terms = [
        # Winner: orders=5, spend=$10, sales=$100 → ACOS=10% < 30% target
        SearchTermReport(
            date="2026-04-01",
            campaign_id=camp.id,
            search_term="winner term",
            match_type="BROAD",
            impressions=1000,
            clicks=50,
            spend=10.0,
            orders=5,
            sales=100.0,
        ),
        # Money Pit: clicks=30, orders=0, spend=$15 → should be negated
        SearchTermReport(
            date="2026-04-01",
            campaign_id=camp.id,
            search_term="money pit term",
            match_type="BROAD",
            impressions=500,
            clicks=30,
            spend=15.0,
            orders=0,
            sales=0.0,
        ),
        # Money Pit (whitelisted): same profile but we'll protect it
        SearchTermReport(
            date="2026-04-01",
            campaign_id=camp.id,
            search_term="brand term protected",
            match_type="BROAD",
            impressions=400,
            clicks=25,
            spend=12.0,
            orders=0,
            sales=0.0,
        ),
        # Low Data: clicks=5 < 15
        SearchTermReport(
            date="2026-04-01",
            campaign_id=camp.id,
            search_term="low data term",
            match_type="BROAD",
            impressions=100,
            clicks=5,
            spend=2.0,
            orders=0,
            sales=0.0,
        ),
    ]
    db_session.add_all(terms)
    db_session.commit()
    return camp


class TestWhitelistExclusion:
    def test_whitelisted_money_pit_is_marked(self, db_session):
        """A money pit term on the whitelist should have whitelisted=True
        and a different action message."""
        camp = _seed_search_terms(db_session)

        # Add "brand term protected" to whitelist
        db_session.add(NegativeWhitelist(search_term="brand term protected", reason="brand"))
        db_session.commit()

        result = classify_search_terms_4bucket(db_session, campaign_id=camp.id)
        money_pits = result["money_pits"]

        # Find the whitelisted one
        protected = [m for m in money_pits if m["search_term"] == "brand term protected"]
        assert len(protected) == 1
        assert protected[0]["whitelisted"] is True
        assert "白名单" in protected[0]["action"]

        # Find the non-whitelisted one
        normal = [m for m in money_pits if m["search_term"] == "money pit term"]
        assert len(normal) == 1
        assert normal[0]["whitelisted"] is False
        assert "否定" in normal[0]["action"]

    def test_no_whitelist_all_money_pits_unprotected(self, db_session):
        """Without any whitelist entries, all money pits should be whitelisted=False."""
        camp = _seed_search_terms(db_session)

        result = classify_search_terms_4bucket(db_session, campaign_id=camp.id)
        money_pits = result["money_pits"]

        for mp in money_pits:
            assert mp["whitelisted"] is False


class TestSuggestedBid:
    def test_winners_have_suggested_bid(self, db_session):
        """Winners should get suggested_bid = CPC * 1.1"""
        camp = _seed_search_terms(db_session)
        result = classify_search_terms_4bucket(db_session, campaign_id=camp.id)
        winners = result["winners"]
        assert len(winners) >= 1

        w = winners[0]
        assert "suggested_bid" in w
        if w["cpc"] is not None:
            expected = round(w["cpc"] * 1.1, 2)
            assert w["suggested_bid"] == expected

    def test_money_pits_have_no_suggested_bid(self, db_session):
        """Money pits are negate candidates, not bid candidates."""
        camp = _seed_search_terms(db_session)
        result = classify_search_terms_4bucket(db_session, campaign_id=camp.id)
        money_pits = result["money_pits"]
        for mp in money_pits:
            assert "suggested_bid" not in mp

    def test_low_data_have_no_suggested_bid(self, db_session):
        """Low data terms should not have suggested_bid."""
        camp = _seed_search_terms(db_session)
        result = classify_search_terms_4bucket(db_session, campaign_id=camp.id)
        low_data = result["low_data"]
        assert len(low_data) >= 1
        for ld in low_data:
            assert "suggested_bid" not in ld
