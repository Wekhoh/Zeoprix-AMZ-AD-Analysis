"""Tests for /api/ad-types read-only catalog endpoints."""


class TestListAdTypes:
    def test_list_returns_all_ad_types(self, client):
        resp = client.get("/api/ad-types")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"ad_types", "core_fields"}
        types = {row["ad_type"] for row in body["ad_types"]}
        assert types == {"SP", "SB", "SBV", "SD", "ST"}

    def test_each_row_has_label_and_counts(self, client):
        resp = client.get("/api/ad-types")
        for row in resp.json()["ad_types"]:
            assert set(row.keys()) == {
                "ad_type",
                "label",
                "field_count",
                "exclusive_field_count",
            }
            assert row["label"]  # non-empty
            assert row["field_count"] >= 9  # at least core
            # SP / ST have 0 exclusive; SB/SBV/SD have > 0
            if row["ad_type"] in {"SB", "SBV", "SD"}:
                assert row["exclusive_field_count"] > 0
            else:
                assert row["exclusive_field_count"] == 0

    def test_core_fields_in_list_response(self, client):
        body = client.get("/api/ad-types").json()
        core_keys = {c["key"] for c in body["core_fields"]}
        assert "impressions" in core_keys
        assert "clicks" in core_keys
        assert "acos" in core_keys


class TestGetAdTypeDetail:
    def test_sb_detail_includes_branded_searches(self, client):
        resp = client.get("/api/ad-types/SB")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ad_type"] == "SB"
        assert body["label"] == "Sponsored Brands"
        keys = {f["key"] for f in body["fields"]}
        assert "attributedBrandedSearches14d" in keys
        assert "topOfSearchImpressionShare" in keys

    def test_sd_detail_includes_viewable_impressions(self, client):
        body = client.get("/api/ad-types/SD").json()
        keys = {f["key"] for f in body["fields"]}
        assert "viewableImpressions" in keys
        assert "attributedAddToCarts14d" in keys

    def test_sbv_detail_includes_video_views(self, client):
        body = client.get("/api/ad-types/SBV").json()
        keys = {f["key"] for f in body["fields"]}
        assert "videoViews" in keys
        assert "video5SecondViews" in keys

    def test_lowercase_ad_type_accepted(self, client):
        resp = client.get("/api/ad-types/sb")
        assert resp.status_code == 200
        assert resp.json()["ad_type"] == "SB"

    def test_unknown_ad_type_returns_404(self, client):
        resp = client.get("/api/ad-types/UNKNOWN")
        assert resp.status_code == 404
        detail = resp.json()["detail"]
        assert "UNKNOWN" in detail
        # Message lists supported types
        for supported in ("SP", "SB", "SBV", "SD", "ST"):
            assert supported in detail

    def test_field_exclusive_flag_correct_for_sb(self, client):
        body = client.get("/api/ad-types/SB").json()
        fields_by_key = {f["key"]: f for f in body["fields"]}
        # Core field: exclusive = False
        assert fields_by_key["impressions"]["exclusive"] is False
        # SB-exclusive field: exclusive = True
        assert fields_by_key["attributedBrandedSearches14d"]["exclusive"] is True

    def test_exclusive_fields_array_only_contains_non_core(self, client):
        body = client.get("/api/ad-types/SD").json()
        core = {
            "impressions",
            "clicks",
            "spend",
            "orders",
            "sales",
            "acos",
            "roas",
            "ctr",
            "cpc",
        }
        for f in body["exclusive_fields"]:
            assert f not in core

    def test_chinese_labels_present(self, client):
        body = client.get("/api/ad-types/SB").json()
        # Ensure labels are populated (not just equal to raw API key)
        non_english = [f for f in body["fields"] if f["key"] != f["label"]]
        assert len(non_english) > 0
