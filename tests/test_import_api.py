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
