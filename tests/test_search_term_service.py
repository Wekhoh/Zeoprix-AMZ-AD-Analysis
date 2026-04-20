"""Tests for backend.services.search_term_service (H1).

Covers:
- _clean_numeric helper (pure)
- parse_search_term_csv (English + Chinese headers, numeric parsing,
  metadata-row skipping)
- import_search_terms (aggregates duplicates; links to campaigns)
- classify_search_terms_4bucket (bucket thresholds + whitelist behavior)
"""

from backend.models import Campaign, Marketplace
from backend.models.search_term import SearchTermReport
from backend.services.search_term_service import (
    _clean_numeric,
    classify_search_terms_4bucket,
    import_search_terms,
    parse_search_term_csv,
)


class TestCleanNumeric:
    def test_plain_number(self):
        assert _clean_numeric("42") == 42.0

    def test_dollar_prefix_stripped(self):
        assert _clean_numeric("$1234.56") == 1234.56

    def test_comma_thousands_separator_stripped(self):
        assert _clean_numeric("$1,234,567.89") == 1234567.89

    def test_percent_suffix_stripped(self):
        assert _clean_numeric("35%") == 35.0

    def test_empty_returns_zero(self):
        assert _clean_numeric("") == 0.0

    def test_em_dash_returns_zero(self):
        assert _clean_numeric("—") == 0.0

    def test_plain_dash_returns_zero(self):
        assert _clean_numeric("-") == 0.0

    def test_na_returns_zero(self):
        assert _clean_numeric("N/A") == 0.0


class TestParseSearchTermCsv:
    def test_english_headers(self):
        csv = (
            "Customer Search Term,Impressions,Clicks,Spend,7 Day Total Orders (#),7 Day Total Sales\n"
            "wireless earbuds,1000,50,12.50,5,100.00\n"
        )
        rows = parse_search_term_csv(csv)
        assert len(rows) == 1
        assert rows[0]["search_term"] == "wireless earbuds"
        assert rows[0]["impressions"] == 1000
        assert rows[0]["clicks"] == 50
        assert rows[0]["spend"] == 12.50
        assert rows[0]["orders"] == 5
        assert rows[0]["sales"] == 100.00

    def test_chinese_headers(self):
        csv = (
            "客户搜索词,曝光量,点击量,花费,7天总订单数,7天总销售额\n无线耳机,500,20,5.00,2,40.00\n"
        )
        rows = parse_search_term_csv(csv)
        assert len(rows) == 1
        assert rows[0]["search_term"] == "无线耳机"
        assert rows[0]["impressions"] == 500
        assert rows[0]["clicks"] == 20

    def test_skips_metadata_rows_before_header(self):
        csv = (
            "Report Name,Weekly Sales Report\n"
            "Date Range,2026-04-01 to 2026-04-07\n"
            "\n"
            "Customer Search Term,Impressions,Clicks,Spend\n"
            "memory foam pillow,800,30,9.00\n"
        )
        rows = parse_search_term_csv(csv)
        assert len(rows) == 1
        assert rows[0]["search_term"] == "memory foam pillow"

    def test_currency_and_percent_cleaned(self):
        csv = 'Customer Search Term,Impressions,Clicks,Spend\nyoga mat,"1,200",75,"$18.50"\n'
        rows = parse_search_term_csv(csv)
        assert rows[0]["impressions"] == 1200
        assert rows[0]["spend"] == 18.50

    def test_rows_without_search_term_dropped(self):
        csv = "Customer Search Term,Impressions,Clicks,Spend\n,100,5,1.00\nvalid term,200,10,2.00\n"
        rows = parse_search_term_csv(csv)
        assert len(rows) == 1
        assert rows[0]["search_term"] == "valid term"

    def test_empty_content_returns_empty_list(self):
        assert parse_search_term_csv("") == []

    def test_no_matching_header_returns_empty(self):
        csv = "Random,Columns,That,Dont,Match\nfoo,bar,baz,qux,quux\n"
        assert parse_search_term_csv(csv) == []


def _seed_campaign(db, name: str = "US-Launch") -> Campaign:
    mp = db.query(Marketplace).filter_by(code="US").first()
    if not mp:
        mp = Marketplace(code="US", name="US", currency="USD")
        db.add(mp)
        db.flush()
    c = Campaign(
        name=name,
        marketplace_id=mp.id,
        ad_type="SP",
        targeting_type="manual",
        bidding_strategy="Fixed bids",
        status="Delivering",
    )
    db.add(c)
    db.commit()
    return c


class TestImportSearchTerms:
    def test_empty_csv_returns_error(self, db_session):
        result = import_search_terms(db_session, "", "report.csv")
        assert result["imported"] == 0
        assert "error" in result

    def test_imports_linked_to_campaign(self, db_session):
        _seed_campaign(db_session, name="US-Launch")
        csv = (
            "Customer Search Term,Campaign Name,Impressions,Clicks,Spend,7 Day Total Orders (#),7 Day Total Sales\n"
            "wireless earbuds,US-Launch,1000,50,12.50,5,100.00\n"
        )
        result = import_search_terms(db_session, csv, "report_20260415.csv")
        assert result["imported"] == 1
        record = db_session.query(SearchTermReport).first()
        assert record.search_term == "wireless earbuds"
        assert record.impressions == 1000
        assert record.campaign_id is not None

    def test_same_term_second_import_aggregates(self, db_session):
        _seed_campaign(db_session, name="US-Launch")
        csv = (
            "Customer Search Term,Campaign Name,Impressions,Clicks,Spend,7 Day Total Orders (#),7 Day Total Sales\n"
            "wireless earbuds,US-Launch,1000,50,12.50,5,100.00\n"
        )
        import_search_terms(db_session, csv, "report1.csv")
        result2 = import_search_terms(db_session, csv, "report2.csv")
        assert result2["skipped"] == 1
        assert result2["imported"] == 0
        record = db_session.query(SearchTermReport).first()
        assert record.impressions == 2000
        assert record.clicks == 100
        assert record.orders == 10


def _seed_search_terms(db, campaign_id: int, terms: list[dict]) -> None:
    for t in terms:
        db.add(
            SearchTermReport(
                date=t.get("date", "2026-04-15"),
                campaign_id=campaign_id,
                search_term=t["term"],
                match_type=t.get("match_type", "BROAD"),
                impressions=t["impressions"],
                clicks=t["clicks"],
                spend=t["spend"],
                orders=t["orders"],
                sales=t["sales"],
            )
        )
    db.commit()


class TestClassify4Bucket:
    def test_low_data_when_clicks_lt_15(self, db_session):
        c = _seed_campaign(db_session)
        _seed_search_terms(
            db_session,
            c.id,
            [
                {
                    "term": "new term",
                    "impressions": 100,
                    "clicks": 5,
                    "spend": 1.0,
                    "orders": 0,
                    "sales": 0.0,
                },
            ],
        )
        result = classify_search_terms_4bucket(db_session)
        assert result["stats"]["low_data_count"] == 1
        assert result["stats"]["winners_count"] == 0
        assert result["stats"]["money_pits_count"] == 0

    def test_winner_when_2plus_orders_and_low_acos(self, db_session):
        c = _seed_campaign(db_session)
        # 20 clicks, 3 orders, spend=5, sales=50 → ACOS = 10%, below 30% target
        _seed_search_terms(
            db_session,
            c.id,
            [
                {
                    "term": "golden keyword",
                    "impressions": 500,
                    "clicks": 20,
                    "spend": 5.0,
                    "orders": 3,
                    "sales": 50.0,
                },
            ],
        )
        result = classify_search_terms_4bucket(db_session, target_acos=0.30)
        assert result["stats"]["winners_count"] == 1
        winner = result["winners"][0]
        assert winner["search_term"] == "golden keyword"
        assert winner["action"].startswith("提高竞价")
        assert winner["suggested_bid"] is not None

    def test_money_pit_when_20plus_clicks_and_0_orders(self, db_session):
        c = _seed_campaign(db_session)
        _seed_search_terms(
            db_session,
            c.id,
            [
                {
                    "term": "burn money",
                    "impressions": 1000,
                    "clicks": 25,
                    "spend": 10.0,
                    "orders": 0,
                    "sales": 0.0,
                },
            ],
        )
        result = classify_search_terms_4bucket(db_session)
        assert result["stats"]["money_pits_count"] == 1
        assert result["money_pits"][0]["search_term"] == "burn money"

    def test_campaign_filter_scopes_results(self, db_session):
        c1 = _seed_campaign(db_session, name="Camp-A")
        c2 = _seed_campaign(db_session, name="Camp-B")
        _seed_search_terms(
            db_session,
            c1.id,
            [
                {
                    "term": "a-term",
                    "impressions": 500,
                    "clicks": 25,
                    "spend": 5.0,
                    "orders": 0,
                    "sales": 0.0,
                }
            ],
        )
        _seed_search_terms(
            db_session,
            c2.id,
            [
                {
                    "term": "b-term",
                    "impressions": 500,
                    "clicks": 25,
                    "spend": 5.0,
                    "orders": 0,
                    "sales": 0.0,
                }
            ],
        )
        result_a = classify_search_terms_4bucket(db_session, campaign_id=c1.id)
        result_b = classify_search_terms_4bucket(db_session, campaign_id=c2.id)
        assert result_a["stats"]["money_pits_count"] == 1
        assert result_a["money_pits"][0]["search_term"] == "a-term"
        assert result_b["stats"]["money_pits_count"] == 1
        assert result_b["money_pits"][0]["search_term"] == "b-term"
