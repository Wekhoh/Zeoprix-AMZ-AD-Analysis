"""Tests for /api/campaigns backward-compatible pagination.

- Legacy callers (no page/page_size) still get a flat list
- Callers passing page or page_size get {data, total, page, page_size}
- Pagination slicing is 1-indexed
- page_size cap (500) enforced at validation
"""

from backend.models import Campaign, Marketplace


def _seed_campaigns(db, count: int = 12) -> None:
    mp = Marketplace(code="US", name="US", currency="USD")
    db.add(mp)
    db.flush()
    for i in range(count):
        db.add(
            Campaign(
                name=f"Camp-{i:02d}",
                ad_type="SP",
                targeting_type="manual",
                bidding_strategy="Fixed bids",
                status="Delivering",
                marketplace_id=mp.id,
            )
        )
    db.commit()


class TestLegacyShape:
    def test_no_query_params_returns_flat_list(self, client, db_session):
        _seed_campaigns(db_session, count=3)
        resp = client.get("/api/campaigns")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 3

    def test_only_other_filters_still_returns_list(self, client, db_session):
        _seed_campaigns(db_session, count=3)
        resp = client.get("/api/campaigns?status=Delivering")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestPaginatedShape:
    def test_page_only_triggers_pagination(self, client, db_session):
        _seed_campaigns(db_session, count=12)
        resp = client.get("/api/campaigns?page=1")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert set(body.keys()) == {"data", "total", "page", "page_size"}
        assert body["total"] == 12
        assert body["page"] == 1
        assert body["page_size"] == 50  # default
        assert len(body["data"]) == 12

    def test_page_size_only_triggers_pagination(self, client, db_session):
        _seed_campaigns(db_session, count=12)
        resp = client.get("/api/campaigns?page_size=5")
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 5
        assert len(body["data"]) == 5
        assert body["total"] == 12

    def test_page_2_returns_correct_slice(self, client, db_session):
        _seed_campaigns(db_session, count=12)
        r1 = client.get("/api/campaigns?page=1&page_size=5").json()
        r2 = client.get("/api/campaigns?page=2&page_size=5").json()
        r3 = client.get("/api/campaigns?page=3&page_size=5").json()

        names1 = [c["name"] for c in r1["data"]]
        names2 = [c["name"] for c in r2["data"]]
        names3 = [c["name"] for c in r3["data"]]

        assert len(names1) == 5
        assert len(names2) == 5
        assert len(names3) == 2  # remainder
        # No overlap, full coverage
        all_names = names1 + names2 + names3
        assert sorted(all_names) == sorted(set(all_names))
        assert len(all_names) == 12

    def test_page_beyond_data_returns_empty_data_with_total(self, client, db_session):
        _seed_campaigns(db_session, count=3)
        resp = client.get("/api/campaigns?page=5&page_size=10")
        body = resp.json()
        assert body["total"] == 3
        assert body["data"] == []

    def test_empty_db_paginated_returns_empty(self, client):
        resp = client.get("/api/campaigns?page=1&page_size=10")
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []


class TestValidation:
    def test_page_zero_rejected(self, client):
        resp = client.get("/api/campaigns?page=0")
        assert resp.status_code == 422

    def test_page_size_too_large_rejected(self, client):
        resp = client.get("/api/campaigns?page_size=501")
        assert resp.status_code == 422

    def test_page_size_at_max_ok(self, client, db_session):
        _seed_campaigns(db_session, count=2)
        resp = client.get("/api/campaigns?page_size=500")
        assert resp.status_code == 200
        assert resp.json()["page_size"] == 500
