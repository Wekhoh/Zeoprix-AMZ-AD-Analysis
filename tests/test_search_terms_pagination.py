"""Tests for /api/search-terms/actions backward-compatible pagination.

Mirrors the contract used by /api/campaigns:
- No page/page_size → legacy list[dict] (capped at 200 most recent)
- Either provided → {data, total, page, page_size}
- Same validation bounds
"""

from backend.models import KeywordAction


def _seed_actions(db, count: int = 12) -> None:
    for i in range(count):
        db.add(
            KeywordAction(
                search_term=f"kw-{i:02d}",
                action_type="harvest_exact",
            )
        )
    db.commit()


class TestLegacyShape:
    def test_no_params_returns_flat_list(self, client, db_session):
        _seed_actions(db_session, count=3)
        resp = client.get("/api/search-terms/actions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 3

    def test_legacy_cap_at_200(self, client, db_session):
        _seed_actions(db_session, count=250)
        resp = client.get("/api/search-terms/actions")
        assert len(resp.json()) == 200


class TestPaginatedShape:
    def test_page_triggers_pagination(self, client, db_session):
        _seed_actions(db_session, count=12)
        resp = client.get("/api/search-terms/actions?page=1")
        body = resp.json()
        assert isinstance(body, dict)
        assert set(body.keys()) == {"data", "total", "page", "page_size"}
        assert body["total"] == 12
        assert body["page_size"] == 50

    def test_page_2_slice(self, client, db_session):
        _seed_actions(db_session, count=12)
        r1 = client.get("/api/search-terms/actions?page=1&page_size=5").json()
        r2 = client.get("/api/search-terms/actions?page=2&page_size=5").json()
        r3 = client.get("/api/search-terms/actions?page=3&page_size=5").json()

        assert len(r1["data"]) == 5
        assert len(r2["data"]) == 5
        assert len(r3["data"]) == 2

        # Combined, no overlap, full coverage
        ids = {r["id"] for r in r1["data"] + r2["data"] + r3["data"]}
        assert len(ids) == 12

    def test_paginated_beyond_cap_returns_everything(self, client, db_session):
        _seed_actions(db_session, count=250)
        # Paginated path should NOT have the legacy 200-cap — can reach 250
        resp = client.get("/api/search-terms/actions?page=1&page_size=500")
        body = resp.json()
        assert body["total"] == 250
        assert len(body["data"]) == 250

    def test_empty_db_paginated(self, client):
        resp = client.get("/api/search-terms/actions?page=1&page_size=10")
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []


class TestValidation:
    def test_page_zero_rejected(self, client):
        assert client.get("/api/search-terms/actions?page=0").status_code == 422

    def test_page_size_over_max_rejected(self, client):
        assert client.get("/api/search-terms/actions?page_size=501").status_code == 422
