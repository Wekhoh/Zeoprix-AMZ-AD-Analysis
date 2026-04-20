"""Tests for /api/notes backward-compatible pagination (E5).

- Legacy callers (no page/page_size) still get a flat list
  (CampaignDetail.tsx:159 depends on this shape)
- Callers passing page or page_size get {data, total, page, page_size}
- Soft-deleted notes are excluded from both shapes
- page_size cap (500) and page minimum (1) enforced at validation
"""

from backend.models import Note


def _seed_notes(db, active: int = 12, deleted: int = 0) -> None:
    # campaign_id left None — Note FK is nullable. Avoids needing to seed
    # campaigns for pagination-only tests.
    for i in range(active):
        db.add(
            Note(
                campaign_id=None,
                content=f"note-{i:02d}",
                note_type="decision",
            )
        )
    for i in range(deleted):
        db.add(
            Note(
                campaign_id=None,
                content=f"trashed-{i:02d}",
                note_type="decision",
                deleted_at="2026-04-18T00:00:00",
            )
        )
    db.commit()


class TestLegacyShape:
    def test_no_query_params_returns_flat_list(self, client, db_session):
        _seed_notes(db_session, active=3)
        resp = client.get("/api/notes")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 3

    def test_soft_deleted_notes_excluded(self, client, db_session):
        _seed_notes(db_session, active=2, deleted=3)
        body = client.get("/api/notes").json()
        assert len(body) == 2  # 3 trashed notes filtered out

    def test_campaign_id_filter_still_returns_list(self, client, db_session):
        # Seed notes have campaign_id=None so the filter-by-id path
        # returns 0 matches — but the response should still be a list
        # (not the paginated dict shape).
        _seed_notes(db_session, active=3)
        resp = client.get("/api/notes?campaign_id=1")
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 0


class TestPaginatedShape:
    def test_page_param_triggers_paginated_shape(self, client, db_session):
        _seed_notes(db_session, active=12)
        body = client.get("/api/notes?page=1&page_size=5").json()
        assert set(body.keys()) == {"data", "total", "page", "page_size"}
        assert body["total"] == 12
        assert body["page"] == 1
        assert body["page_size"] == 5
        assert len(body["data"]) == 5

    def test_page_size_alone_triggers_paginated_shape(self, client, db_session):
        _seed_notes(db_session, active=7)
        body = client.get("/api/notes?page_size=3").json()
        assert isinstance(body, dict)
        assert body["total"] == 7
        assert len(body["data"]) == 3

    def test_page_2_returns_next_slice(self, client, db_session):
        _seed_notes(db_session, active=12)
        page1 = client.get("/api/notes?page=1&page_size=5").json()
        page2 = client.get("/api/notes?page=2&page_size=5").json()
        assert len(page2["data"]) == 5
        # Pages should be disjoint
        page1_ids = {n["id"] for n in page1["data"]}
        page2_ids = {n["id"] for n in page2["data"]}
        assert page1_ids.isdisjoint(page2_ids)

    def test_last_page_returns_partial_slice(self, client, db_session):
        _seed_notes(db_session, active=12)
        body = client.get("/api/notes?page=3&page_size=5").json()
        assert len(body["data"]) == 2  # 12 - 2*5 = 2 remaining
        assert body["total"] == 12

    def test_paginated_shape_also_excludes_trashed(self, client, db_session):
        _seed_notes(db_session, active=4, deleted=8)
        body = client.get("/api/notes?page=1&page_size=50").json()
        assert body["total"] == 4  # 8 trashed excluded from total too


class TestValidation:
    def test_page_size_over_max_rejected(self, client, db_session):
        _seed_notes(db_session, active=1)
        resp = client.get("/api/notes?page_size=501")
        assert resp.status_code == 422  # le=500

    def test_page_zero_rejected(self, client, db_session):
        _seed_notes(db_session, active=1)
        resp = client.get("/api/notes?page=0")
        assert resp.status_code == 422  # ge=1
