"""Tests for date parser utility functions"""

from backend.utils.date_parser import (
    is_datetime_like,
    parse_amazon_datetime,
    parse_date_from_filename,
)


class TestParseAmazonDatetime:
    def test_am(self):
        """'Nov 13, 2025 4:49 AM' -> correct date + time"""
        date_str, time_str = parse_amazon_datetime("Nov 13, 2025 4:49 AM")
        assert date_str == "2025-11-13"
        assert time_str == "04:49"

    def test_pm(self):
        """PM conversion: 3:30 PM -> 15:30"""
        date_str, time_str = parse_amazon_datetime("Jan 5, 2025 3:30 PM")
        assert date_str == "2025-01-05"
        assert time_str == "15:30"

    def test_noon_pm(self):
        """12 PM stays 12"""
        date_str, time_str = parse_amazon_datetime("Feb 1, 2025 12:00 PM")
        assert date_str == "2025-02-01"
        assert time_str == "12:00"

    def test_midnight_am(self):
        """12 AM -> 00"""
        date_str, time_str = parse_amazon_datetime("Mar 10, 2025 12:15 AM")
        assert date_str == "2025-03-10"
        assert time_str == "00:15"


class TestParseDateFromFilename:
    def test_known_filename(self):
        result = parse_date_from_filename("DBL-TP01-LOT01-SP-1.94bid1116.csv")
        assert result == "2025-11-16"

    def test_no_date(self):
        result = parse_date_from_filename("no-date-here.csv")
        assert result is None


class TestIsDatetimeLike:
    def test_amazon_format(self):
        assert is_datetime_like("Nov 13, 2025 4:49 AM") is True

    def test_iso_format(self):
        assert is_datetime_like("2025-11-13") is True

    def test_slash_format(self):
        assert is_datetime_like("11/13/2025") is True

    def test_empty(self):
        assert is_datetime_like("") is False

    def test_random_text(self):
        assert is_datetime_like("hello world") is False
