"""Tests for log_parser.parse_operation_log_text / parse_operation_log_content.

Guards the "pipe-delimited Amazon operation log" parsing contract used
during TXT imports. The parser is v2.6 with per-line format detection.

Key behaviors verified:
1. Parses standard campaign format: Date | Change type | From | To
2. Parses standard adgroup format: Change type | From | To | Date
3. Skips header, separator, and blank lines
4. Requires at least 4 pipe-separated columns
5. AM/PM conversion in datetime_str
6. filename "广告组" keyword toggles level_type to "ad_group"
7. Output rows have stable shape with all required keys
"""

from backend.services.log_parser import (
    parse_operation_log_content,
    parse_operation_log_text,
)


class TestParseOperationLogText:
    def test_empty_returns_empty_list(self):
        assert parse_operation_log_text("") == []

    def test_parses_standard_campaign_format(self):
        text = "Nov 13, 2025 4:49 AM | Campaign status | Paused | Delivering"
        rows = parse_operation_log_text(text, campaign_name="Test-SP")

        assert len(rows) == 1
        r = rows[0]
        assert r["date"] == "2025-11-13"
        assert r["time"] == "04:49"
        assert r["change_type"] == "Campaign status"
        assert r["from_value"] == "Paused"
        assert r["to_value"] == "Delivering"
        assert r["level_type"] == "campaign"
        assert r["operation_type"] == "Campaign change"
        assert r["campaign_name"] == "Test-SP"

    def test_parses_adgroup_format_date_at_end(self):
        text = (
            "Change type | From | To | Date and time\n"
            "Default bid | 1.50 | 1.75 | Dec 3, 2025 2:15 PM"
        )
        rows = parse_operation_log_text(text, campaign_name="AG-1", is_adgroup=True)

        assert len(rows) == 1
        r = rows[0]
        assert r["date"] == "2025-12-03"
        assert r["time"] == "14:15"  # 2:15 PM → 14:15
        assert r["change_type"] == "Default bid"
        assert r["level_type"] == "ad_group"
        assert r["operation_type"] == "Ad group change"

    def test_skips_header_separator_and_blank_lines(self):
        text = (
            "Date and time | Change type | From value | To value\n"
            "--- | --- | --- | ---\n"
            "\n"
            "Nov 13, 2025 4:49 AM | Campaign status | Paused | Delivering\n"
            "   \n"
        )
        rows = parse_operation_log_text(text)
        assert len(rows) == 1

    def test_requires_at_least_four_pipe_columns(self):
        # 3-column line → skipped
        text = "Nov 13, 2025 4:49 AM | Campaign status | Paused"
        rows = parse_operation_log_text(text)
        assert rows == []

    def test_lines_without_pipes_are_skipped(self):
        text = (
            "This is a comment line with no pipe\n"
            "Nov 13, 2025 4:49 AM | Campaign status | Paused | Delivering"
        )
        rows = parse_operation_log_text(text)
        assert len(rows) == 1

    def test_unparseable_datetime_is_dropped(self):
        # No datetime-like string anywhere → row filtered out (date_str is None)
        text = "not-a-date | Change | a | b"
        rows = parse_operation_log_text(text)
        assert rows == []

    def test_am_pm_conversion(self):
        text_pm = "Nov 13, 2025 11:30 PM | X | a | b"
        rows = parse_operation_log_text(text_pm)
        assert rows[0]["time"] == "23:30"

        text_12am = "Nov 13, 2025 12:00 AM | X | a | b"
        rows = parse_operation_log_text(text_12am)
        assert rows[0]["time"] == "00:00"

        text_12pm = "Nov 13, 2025 12:00 PM | X | a | b"
        rows = parse_operation_log_text(text_12pm)
        assert rows[0]["time"] == "12:00"

    def test_output_row_has_expected_keys(self):
        text = "Nov 13, 2025 4:49 AM | Campaign status | Paused | Delivering"
        rows = parse_operation_log_text(text)
        r = rows[0]
        for key in (
            "date",
            "time",
            "operator",
            "level_type",
            "campaign_name",
            "ad_group_name",
            "operation_type",
            "change_type",
            "from_value",
            "to_value",
        ):
            assert key in r, f"missing key: {key}"

    def test_multiple_lines_preserved_in_order(self):
        text = (
            "Nov 13, 2025 4:49 AM | Campaign status | Paused | Delivering\n"
            "Nov 14, 2025 9:00 AM | Daily budget | 20.00 | 30.00\n"
            "Nov 15, 2025 10:00 AM | Bidding strategy | Down | Up"
        )
        rows = parse_operation_log_text(text)
        assert len(rows) == 3
        assert [r["change_type"] for r in rows] == [
            "Campaign status",
            "Daily budget",
            "Bidding strategy",
        ]


class TestParseOperationLogContent:
    def test_campaign_filename_marks_campaign_level(self):
        text = "Nov 13, 2025 4:49 AM | Campaign status | Paused | Delivering"
        rows, is_adgroup = parse_operation_log_content(text, "Camp-X 操作日志.txt")
        assert is_adgroup is False
        assert rows[0]["level_type"] == "campaign"

    def test_adgroup_filename_marks_adgroup_level(self):
        text = "Nov 13, 2025 4:49 AM | Default bid | 1.00 | 1.50"
        rows, is_adgroup = parse_operation_log_content(text, "Camp-X 广告组 操作日志.txt")
        assert is_adgroup is True
        assert rows[0]["level_type"] == "ad_group"

    def test_extracts_campaign_name_from_filename(self):
        text = "Nov 13, 2025 4:49 AM | Campaign status | Paused | Delivering"
        rows, _ = parse_operation_log_content(text, "Winter-2025 操作日志.txt")
        # strips "操作日志" and ".txt"
        assert rows[0]["campaign_name"].startswith("Winter-2025")

    def test_explicit_campaign_name_overrides_filename(self):
        text = "Nov 13, 2025 4:49 AM | Campaign status | Paused | Delivering"
        rows, _ = parse_operation_log_content(
            text, "Winter-2025 操作日志.txt", campaign_name="Override-Name"
        )
        assert rows[0]["campaign_name"] == "Override-Name"
