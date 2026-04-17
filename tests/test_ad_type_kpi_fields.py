"""Tests for KPI_FIELDS_BY_AD_TYPE catalog in backend/utils/amazon_rules.py.

These guard the stability of the cross-cutting contract used by:
- CSV parsers (which columns to map for each ad type)
- frontend column-settings dropdown (which columns to show)
- a future SP API integration (must reuse same keys)
"""

from backend.utils.amazon_rules import (
    AD_TYPE_LABELS,
    KPI_FIELD_LABELS,
    KPI_FIELDS_BY_AD_TYPE,
    KPI_FIELDS_CORE,
    get_kpi_exclusive_fields,
    get_kpi_fields,
)


class TestCoreFields:
    def test_core_has_the_9_standard_kpis(self):
        assert set(KPI_FIELDS_CORE) == {
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

    def test_every_ad_type_includes_core_fields(self):
        for ad_type, fields in KPI_FIELDS_BY_AD_TYPE.items():
            for core in KPI_FIELDS_CORE:
                assert core in fields, f"{ad_type} is missing core field {core}"


class TestSBExclusives:
    def test_sb_has_branded_searches(self):
        sb = get_kpi_fields("SB")
        assert "attributedBrandedSearches14d" in sb

    def test_sb_has_top_of_search_impression_share(self):
        assert "topOfSearchImpressionShare" in get_kpi_fields("SB")

    def test_sb_has_new_to_brand_suite(self):
        sb = get_kpi_fields("SB")
        for f in (
            "attributedOrdersNewToBrand14d",
            "attributedSalesNewToBrand14d",
            "attributedOrdersNewToBrandPercentage14d",
        ):
            assert f in sb

    def test_sb_does_not_have_sd_exclusives(self):
        sb = set(get_kpi_fields("SB"))
        assert "viewableImpressions" not in sb
        assert "attributedAddToCarts14d" not in sb


class TestSDExclusives:
    def test_sd_has_viewable_impressions(self):
        assert "viewableImpressions" in get_kpi_fields("SD")

    def test_sd_has_add_to_cart_metrics(self):
        sd = get_kpi_fields("SD")
        assert "attributedAddToCarts14d" in sd
        assert "attributedAddToCartsPercentage14d" in sd

    def test_sd_has_detail_page_views(self):
        sd = get_kpi_fields("SD")
        assert "attributedDetailPageView14d" in sd
        assert "attributedDetailPageViewNewToBrand14d" in sd


class TestSBVExclusives:
    def test_sbv_has_video_engagement_metrics(self):
        sbv = get_kpi_fields("SBV")
        for f in (
            "videoViews",
            "video5SecondViews",
            "videoCompleteViews",
            "vctr",
            "vtr",
        ):
            assert f in sbv

    def test_sbv_includes_sb_brand_metrics(self):
        # SBV reports are SB reports with extra video columns, so NTB + branded
        # searches should still be present.
        sbv = get_kpi_fields("SBV")
        assert "attributedBrandedSearches14d" in sbv
        assert "attributedOrdersNewToBrand14d" in sbv


class TestGetKpiFields:
    def test_returns_sp_for_unknown_ad_type(self):
        assert get_kpi_fields("UNKNOWN_AD_TYPE") == KPI_FIELDS_CORE
        assert get_kpi_fields("") == KPI_FIELDS_CORE

    def test_case_insensitive(self):
        assert get_kpi_fields("sp") == get_kpi_fields("SP")
        assert get_kpi_fields("sbv") == get_kpi_fields("SBV")


class TestGetKpiExclusiveFields:
    def test_sp_has_no_exclusive_fields(self):
        assert get_kpi_exclusive_fields("SP") == ()

    def test_sb_exclusive_fields_all_non_core(self):
        exclusive = get_kpi_exclusive_fields("SB")
        assert len(exclusive) > 0
        for f in exclusive:
            assert f not in KPI_FIELDS_CORE

    def test_sbv_has_video_in_exclusive(self):
        assert "videoViews" in get_kpi_exclusive_fields("SBV")


class TestLabels:
    def test_every_ad_type_has_a_label(self):
        for ad_type in KPI_FIELDS_BY_AD_TYPE:
            assert ad_type in AD_TYPE_LABELS

    def test_every_exclusive_field_has_a_chinese_label(self):
        # Ensures the frontend column-settings dropdown never shows a raw API key
        missing: list[str] = []
        for ad_type in ("SB", "SBV", "SD"):
            for field in get_kpi_exclusive_fields(ad_type):
                if field not in KPI_FIELD_LABELS:
                    missing.append(f"{ad_type}/{field}")
        assert missing == [], f"fields missing labels: {missing}"
