"""Tests for keyword_service — CSV parsing, import, aggregation, history."""

from backend.models import AdGroup, Campaign, Keyword, KeywordDailyRecord, Marketplace
from backend.services.keyword_service import (
    get_ad_groups_for_campaign,
    get_keyword_history,
    get_keywords_for_ad_group,
    import_keyword_report,
    parse_keyword_report_csv,
)


class TestParseKeywordReportCsv:
    def test_empty_returns_empty(self):
        assert parse_keyword_report_csv("") == []

    def test_english_headers(self):
        content = (
            "Campaign Name,Ad Group Name,Targeting,Match Type,Impressions,Clicks,Spend,7 Day Total Orders (#),7 Day Total Sales,Date\n"
            "Camp-A,Group-1,wireless charger,Exact,1000,50,$25.00,5,$150.00,2026-04-01\n"
        )
        rows = parse_keyword_report_csv(content)
        assert len(rows) == 1
        assert rows[0]["keyword_text"] == "wireless charger"
        assert rows[0]["match_type"] == "Exact"
        assert rows[0]["campaign_name"] == "Camp-A"
        assert rows[0]["impressions"] == 1000
        assert rows[0]["spend"] == 25.0

    def test_chinese_headers(self):
        content = (
            "广告活动名称,广告组名称,关键词,匹配类型,曝光量,点击量,花费,订单,销售额,日期\n"
            "测试活动,默认组,蓝牙耳机,Broad,500,20,10.00,2,40.00,2026-04-01\n"
        )
        rows = parse_keyword_report_csv(content)
        assert len(rows) == 1
        assert rows[0]["keyword_text"] == "蓝牙耳机"
        assert rows[0]["orders"] == 2

    def test_rows_without_keyword_text_dropped(self):
        content = (
            "Campaign Name,Targeting,Match Type,Impressions\n"
            "Camp-A,,Exact,100\n"
            "Camp-A,real keyword,Exact,200\n"
        )
        rows = parse_keyword_report_csv(content)
        assert len(rows) == 1
        assert rows[0]["keyword_text"] == "real keyword"

    def test_bid_parsed(self):
        content = "Targeting,Match Type,Bid\ncharger,Exact,$1.50\n"
        rows = parse_keyword_report_csv(content)
        assert rows[0]["bid"] == 1.5


class TestImportKeywordReport:
    def _make_campaign(self, db_session, name="Test-KW-Camp"):
        mp = Marketplace(code="US", name="US", currency="USD")
        db_session.add(mp)
        db_session.flush()
        camp = Campaign(
            name=name,
            ad_type="SP",
            targeting_type="manual",
            bidding_strategy="Fixed bids",
            status="Delivering",
            marketplace_id=mp.id,
        )
        db_session.add(camp)
        db_session.commit()
        return camp

    def test_import_creates_keyword_and_daily(self, db_session):
        self._make_campaign(db_session)
        content = (
            "Campaign Name,Ad Group Name,Targeting,Match Type,Impressions,Clicks,Spend,7 Day Total Orders (#),7 Day Total Sales,Date\n"
            "Test-KW-Camp,Default,wireless charger,Exact,1000,50,25.00,5,150.00,2026-04-01\n"
        )
        result = import_keyword_report(db_session, content)
        assert result["imported_keywords"] == 1
        assert result["imported_daily"] == 1

        kw = db_session.query(Keyword).filter_by(keyword_text="wireless charger").first()
        assert kw is not None
        assert kw.match_type == "Exact"

        daily = db_session.query(KeywordDailyRecord).filter_by(keyword_id=kw.id).first()
        assert daily.spend == 25.0
        assert daily.orders == 5

    def test_import_upsert_same_keyword(self, db_session):
        self._make_campaign(db_session)
        content = (
            "Campaign Name,Ad Group Name,Targeting,Match Type,Bid,Impressions,Clicks,Spend,7 Day Total Orders (#),7 Day Total Sales,Date\n"
            "Test-KW-Camp,Default,charger,Exact,$1.00,100,10,5.00,1,20.00,2026-04-01\n"
        )
        import_keyword_report(db_session, content)

        content2 = (
            "Campaign Name,Ad Group Name,Targeting,Match Type,Bid,Impressions,Clicks,Spend,7 Day Total Orders (#),7 Day Total Sales,Date\n"
            "Test-KW-Camp,Default,charger,Exact,$1.50,200,20,10.00,2,40.00,2026-04-01\n"
        )
        result2 = import_keyword_report(db_session, content2)
        assert result2["updated_keywords"] >= 1
        assert result2["updated_daily"] >= 1

        kw = db_session.query(Keyword).filter_by(keyword_text="charger").first()
        assert kw.bid == 1.5  # updated

    def test_import_skips_unknown_campaign(self, db_session):
        content = (
            "Campaign Name,Targeting,Match Type,Date,Impressions\n"
            "NonExistentCampaign,test kw,Exact,2026-04-01,100\n"
        )
        result = import_keyword_report(db_session, content)
        assert result["skipped"] == 1
        assert result["imported_keywords"] == 0

    def test_import_empty_csv_returns_error(self, db_session):
        result = import_keyword_report(db_session, "random stuff\n")
        assert "error" in result


class TestKeywordAggregation:
    def _seed_keyword_data(self, db_session):
        mp = Marketplace(code="US", name="US", currency="USD")
        db_session.add(mp)
        db_session.flush()
        camp = Campaign(
            name="Agg-Camp",
            ad_type="SP",
            targeting_type="manual",
            bidding_strategy="Fixed bids",
            status="Delivering",
            marketplace_id=mp.id,
        )
        db_session.add(camp)
        db_session.flush()
        ag = AdGroup(campaign_id=camp.id, name="Agg-Group", status="Enabled")
        db_session.add(ag)
        db_session.flush()
        kw = Keyword(ad_group_id=ag.id, keyword_text="test kw", match_type="Exact", bid=1.0)
        db_session.add(kw)
        db_session.flush()
        db_session.add_all(
            [
                KeywordDailyRecord(
                    keyword_id=kw.id,
                    date="2026-04-01",
                    impressions=100,
                    clicks=10,
                    spend=5.0,
                    orders=2,
                    sales=40.0,
                ),
                KeywordDailyRecord(
                    keyword_id=kw.id,
                    date="2026-04-02",
                    impressions=200,
                    clicks=20,
                    spend=10.0,
                    orders=3,
                    sales=60.0,
                ),
            ]
        )
        db_session.commit()
        return camp, ag, kw

    def test_get_keywords_aggregates_daily(self, db_session):
        _, ag, _ = self._seed_keyword_data(db_session)
        results = get_keywords_for_ad_group(db_session, ag.id)
        assert len(results) == 1
        kw = results[0]
        assert kw["impressions"] == 300
        assert kw["clicks"] == 30
        assert kw["spend"] == 15.0
        assert kw["orders"] == 5
        assert kw["sales"] == 100.0

    def test_get_keyword_history_returns_daily(self, db_session):
        _, _, kw = self._seed_keyword_data(db_session)
        history = get_keyword_history(db_session, kw.id)
        assert len(history) == 2
        assert history[0]["date"] == "2026-04-01"
        assert history[1]["date"] == "2026-04-02"

    def test_get_ad_groups_for_campaign(self, db_session):
        camp, _, _ = self._seed_keyword_data(db_session)
        groups = get_ad_groups_for_campaign(db_session, camp.id)
        assert len(groups) == 1
        assert groups[0]["keyword_count"] == 1
        assert groups[0]["spend"] == 15.0
