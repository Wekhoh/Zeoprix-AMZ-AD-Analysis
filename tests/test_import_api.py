"""Tests for import API endpoints"""

import io


class TestImportCsvCreatesRecords:
    def test_import_csv_creates_records(self, client, sample_csv):
        """POST CSV, check imported > 0"""
        files = [
            (
                "files",
                ("TestCampaign1116.csv", io.BytesIO(sample_csv.encode("utf-8")), "text/csv"),
            )
        ]
        response = client.post("/api/import/placement-csv", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] > 0


class TestImportCsvDeduplication:
    def test_dedup(self, client, sample_csv):
        """POST same CSV twice, second time skipped > 0"""
        files1 = [
            (
                "files",
                ("TestCampaign1116.csv", io.BytesIO(sample_csv.encode("utf-8")), "text/csv"),
            )
        ]
        resp1 = client.post("/api/import/placement-csv", files=files1)
        assert resp1.status_code == 200
        assert resp1.json()["imported"] > 0

        files2 = [
            (
                "files",
                ("TestCampaign1116.csv", io.BytesIO(sample_csv.encode("utf-8")), "text/csv"),
            )
        ]
        resp2 = client.post("/api/import/placement-csv", files=files2)
        assert resp2.status_code == 200
        assert resp2.json()["skipped"] > 0


class TestPreviewEndpoint:
    def test_preview_structure(self, client, sample_csv):
        """POST to /preview, check structure"""
        files = [
            (
                "files",
                ("TestCampaign1116.csv", io.BytesIO(sample_csv.encode("utf-8")), "text/csv"),
            )
        ]
        response = client.post("/api/import/preview", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert len(data["files"]) == 1
        preview = data["files"][0]
        assert preview["record_count"] == 3
        assert "campaign_name" in preview
        assert "columns" in preview


class TestImportRowCountDoSGuard:
    """B0-3b: CSV row-count DoS defense. Prevents unbounded memory
    consumption when an attacker uploads a well-formed but huge file.
    """

    def test_csv_over_row_limit_rejected(self, client, monkeypatch):
        """A CSV with more rows than MAX_CSV_ROWS must be rejected with
        a clear error, and must not be parsed further (no imports)."""
        from backend.services import import_service

        # Lower the limit temporarily to keep the test fast
        monkeypatch.setattr(import_service, "MAX_CSV_ROWS", 5)

        header = (
            "Placement,Campaign bidding strategy,Bid adjustment,Impressions,"
            "Clicks,Spend (USD),Orders,Sales (USD)\r\n"
        )
        row = "PLACEMENT_TOP,Dynamic bidding (down only),50%,100,5,$2.50,1,$20.00\r\n"
        # 10 rows > limit of 5
        csv_content = header + row * 10

        files = [
            (
                "files",
                ("HugeCampaign1116.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
            )
        ]
        response = client.post("/api/import/placement-csv", files=files)
        assert response.status_code == 200
        data = response.json()
        # No rows should have been imported
        assert data["imported"] == 0
        # At least one detail should mention the row limit
        errors = [d for d in data.get("details", []) if d.get("level") == "error"]
        assert any("行数超过" in d.get("message", "") for d in errors), (
            f"Expected row-limit error in details, got: {errors}"
        )

    def test_csv_under_row_limit_imports_normally(self, client, sample_csv):
        """Regression: normal-sized CSV (3 rows) still imports."""
        files = [
            (
                "files",
                ("NormalCampaign1116.csv", io.BytesIO(sample_csv.encode("utf-8")), "text/csv"),
            )
        ]
        response = client.post("/api/import/placement-csv", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] > 0
