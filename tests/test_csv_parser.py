"""Tests for CSV parser functions"""

from backend.services.csv_parser import (
    _clean_num,
    detect_report_type,
    parse_csv_placement_data,
)


class TestParsePlacementCsv:
    def test_empty_content_returns_empty(self):
        placements, summary = parse_csv_placement_data("", "empty.csv")
        assert placements == []
        assert summary.get("error") == "Empty file"

    def test_whitespace_only_returns_empty(self):
        placements, summary = parse_csv_placement_data("  \n  \n", "blank.csv")
        assert placements == []
        assert summary.get("error") == "Empty file"

    def test_parse_3_rows(self, sample_csv):
        """Feed a 3-row CSV string, verify output structure, dates, numbers."""
        # Filename encodes date as MMDD: 1116 -> 2025-11-16
        placements, summary = parse_csv_placement_data(sample_csv, "TestCampaign1116.csv")

        assert len(placements) == 3
        assert placements[0]["date"] == "2025-11-16"
        assert placements[0]["impressions"] == 1000
        assert placements[0]["clicks"] == 50
        assert placements[0]["spend"] == 25.0
        assert placements[0]["orders"] == 5
        assert placements[0]["sales"] == 150.0

        # Summary totals
        assert summary["impressions"] == 1800
        assert summary["clicks"] == 80
        assert summary["spend"] == 40.0
        assert summary["orders"] == 8
        assert summary["sales"] == 240.0


class TestDetectReportType:
    def test_sp_placement(self):
        headers = ["Placement", "Impressions", "Clicks"]
        assert detect_report_type(headers) == "sp_placement"

    def test_sb_campaign(self):
        headers = [
            "Campaign Name",
            "Impressions",
            "Clicks",
            "Spend",
            "14 Day Total Sales",
        ]
        assert detect_report_type(headers) == "sb_campaign"

    def test_sd_campaign(self):
        headers = [
            "Campaign Name",
            "Impressions",
            "Clicks",
            "Spend",
            "Viewable Impressions",
        ]
        assert detect_report_type(headers) == "sd_campaign"


class TestCleanNum:
    def test_dollar_comma(self):
        assert _clean_num("$1,234.56") == 1234.56

    def test_dash(self):
        assert _clean_num("—") == 0.0

    def test_empty_string(self):
        assert _clean_num("") == 0.0

    def test_na(self):
        assert _clean_num("N/A") == 0.0

    def test_percent(self):
        assert _clean_num("45%") == 45.0

    def test_as_int(self):
        assert _clean_num("$1,234.56", as_int=True) == 1234
