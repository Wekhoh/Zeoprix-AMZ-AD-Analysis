"""Tests for pdf_report_service.generate_pdf_report.

These are smoke tests — the function is heavy (reportlab) but
deterministic given the same data. We verify:
1. Empty DB still returns a valid PDF (no crash on zero data)
2. Seeded data produces a larger PDF (more content)
3. Output starts with PDF magic bytes
4. date_from / date_to filters do not crash
"""

from backend.services.pdf_report_service import generate_pdf_report


class TestGeneratePdfReport:
    def test_empty_db_returns_valid_pdf(self, db_session):
        buf = generate_pdf_report(db_session)
        assert isinstance(buf, bytes)
        assert len(buf) > 100  # Arbitrary — blank PDF is still ~1KB
        assert buf.startswith(b"%PDF-")

    def test_seeded_db_produces_larger_pdf(self, db_session, seed_campaign_data):
        buf = generate_pdf_report(db_session)
        assert buf.startswith(b"%PDF-")
        # With campaigns + placements seeded, output should be measurably larger
        assert len(buf) > 1500

    def test_date_filter_does_not_crash(self, db_session, seed_campaign_data):
        # Both dates are within the seeded data range (2025-11-10 / 11)
        buf = generate_pdf_report(db_session, date_from="2025-11-10", date_to="2025-11-11")
        assert buf.startswith(b"%PDF-")

    def test_date_filter_outside_data_range_still_succeeds(self, db_session, seed_campaign_data):
        # No data in this range — should still produce a PDF (empty sections)
        buf = generate_pdf_report(db_session, date_from="2099-01-01", date_to="2099-12-31")
        assert buf.startswith(b"%PDF-")

    def test_pdf_ends_with_eof_marker(self, db_session):
        # Every valid PDF ends with %%EOF (optionally followed by newline)
        buf = generate_pdf_report(db_session)
        # Strip trailing whitespace/newlines, then check
        stripped = buf.rstrip(b"\r\n ")
        assert stripped.endswith(b"%%EOF"), (
            f"PDF must end with %%EOF marker; last 30 bytes: {stripped[-30:]!r}"
        )
