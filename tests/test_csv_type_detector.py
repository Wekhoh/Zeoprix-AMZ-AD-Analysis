"""Tests for csv_type_detector.detect_csv_type.

Pure-function; no DB. Covers all 5 report types plus "unknown" + filename
fallback behavior.
"""

from backend.utils.csv_type_detector import detect_csv_type


class TestPlacementDetection:
    def test_english_placement_header(self):
        csv = (
            "Placement,Campaign bidding strategy,Bid adjustment,Impressions,Clicks\n"
            "PLACEMENT_TOP,Fixed bids,50%,1000,50\n"
        )
        assert detect_csv_type(csv) == "placement"

    def test_filename_hint_placement(self):
        # Weak content but filename hints
        csv = "some,random,headers\n1,2,3"
        assert detect_csv_type(csv, "2025-10-01 展示位置.csv") == "placement"


class TestSearchTermDetection:
    def test_english_search_term_header(self):
        csv = "Campaign,Ad Group,Customer Search Term,Impressions\nX,Y,keyword,100\n"
        assert detect_csv_type(csv) == "search_term"

    def test_chinese_search_term_header(self):
        csv = "广告活动,广告组,搜索词,曝光量\nX,Y,关键词,100\n"
        assert detect_csv_type(csv) == "search_term"

    def test_filename_hint_search_term(self):
        assert detect_csv_type("x,y,z\n1,2,3", "搜索词报告.csv") == "search_term"


class TestInventoryDetection:
    def test_fba_inventory_header(self):
        csv = "sku,asin,afn-fulfillable-quantity,afn-inbound-working-quantity\nSKU-1,B0X,100,50\n"
        assert detect_csv_type(csv) == "inventory"

    def test_chinese_inventory_header(self):
        csv = "商家 SKU,ASIN,可售数量,库存天数\nSKU-1,B0X,100,30\n"
        assert detect_csv_type(csv) == "inventory"


class TestKeywordDetection:
    def test_keyword_report_header(self):
        csv = "Campaign Name,Ad Group Name,Targeting,Match Type,Bid\nCamp-1,AG-1,kw1,Exact,1.50\n"
        assert detect_csv_type(csv) == "keyword"

    def test_chinese_keyword_report_header(self):
        csv = "广告活动名称,广告组名称,关键词,匹配类型,竞价\nA,B,k,精准,1.50\n"
        assert detect_csv_type(csv) == "keyword"


class TestOperationLogDetection:
    def test_pipe_delimited_txt(self):
        text = (
            "Date and time | Change type | From | To\n"
            "Nov 13, 2025 4:49 AM | Campaign status | Paused | Delivering"
        )
        assert detect_csv_type(text) == "operation_log"

    def test_chinese_operation_log(self):
        text = "日期时间 | 变更类型 | 从 | 到\nNov 13, 2025 | X | a | b"
        assert detect_csv_type(text) == "operation_log"

    def test_filename_hint_operation_log(self):
        # Content without clear markers but .txt + 操作日志 name
        assert (
            detect_csv_type("random\ntext\nwith\nno signature", "Camp-X 操作日志.txt")
            == "operation_log"
        )


class TestSponsoredBrandsDetection:
    def test_sb_header_with_branded_searches(self):
        csv = (
            "campaignName,impressions,clicks,cost,"
            "attributedSales14d,attributedBrandedSearches14d\n"
            "Brand-Camp-1,10000,200,50.00,1500.00,40\n"
        )
        assert detect_csv_type(csv) == "sb"

    def test_sb_header_with_top_of_search_impression_share(self):
        csv = (
            "campaignName,keywordText,impressions,clicks,topOfSearchImpressionShare\n"
            "C,kw,5000,100,0.42\n"
        )
        assert detect_csv_type(csv) == "sb"

    def test_sb_filename_hint(self):
        # Generic content but filename says "SB" or "Sponsored Brands"
        csv = "col_a,col_b,col_c\n1,2,3"
        assert detect_csv_type(csv, "sb-campaign-report.csv") == "sb"
        assert detect_csv_type(csv, "Sponsored Brands Weekly.csv") == "sb"
        assert detect_csv_type(csv, "2025 品牌广告周报.csv") == "sb"


class TestSponsoredDisplayDetection:
    def test_sd_header_with_viewable_impressions(self):
        csv = (
            "campaignName,impressions,viewableImpressions,clicks,cost\n"
            "SD-Camp,10000,7500,50,20.00\n"
        )
        assert detect_csv_type(csv) == "sd"

    def test_sd_header_with_add_to_carts(self):
        # 2025 new metric — unique to SD
        csv = "campaignName,attributedAddToCarts14d,attributedAddToCartsPercentage14d\nC,15,0.03\n"
        assert detect_csv_type(csv) == "sd"

    def test_sd_filename_hint(self):
        csv = "col_a,col_b\n1,2"
        assert detect_csv_type(csv, "sd_campaign_2025.csv") == "sd"
        assert detect_csv_type(csv, "Sponsored Display Performance.csv") == "sd"


class TestSponsoredBrandsVideoDetection:
    def test_sbv_header_with_video_views(self):
        csv = (
            "campaignName,impressions,clicks,videoViews,video5SecondViews,videoCompleteViews\n"
            "SBV-Camp,5000,100,4800,1200,800\n"
        )
        assert detect_csv_type(csv) == "sbv"

    def test_sbv_wins_over_sb_when_both_markers_present(self):
        # Per spec: SBV reports include SB markers plus video metrics.
        # We return "sbv" (more specific) not "sb".
        csv = "campaignName,attributedBrandedSearches14d,videoViews\nSBV-Camp,20,3000\n"
        assert detect_csv_type(csv) == "sbv"

    def test_sbv_filename_hint(self):
        csv = "col_a\n1"
        assert detect_csv_type(csv, "sbv-campaigns.csv") == "sbv"
        assert detect_csv_type(csv, "sponsored-brands-video-2026.csv") == "sbv"
        assert detect_csv_type(csv, "品牌视频报告.csv") == "sbv"


class TestEdgeCases:
    def test_empty_content_is_unknown(self):
        assert detect_csv_type("") == "unknown"
        assert detect_csv_type("   ") == "unknown"

    def test_unknown_headers_without_filename(self):
        csv = "col_a,col_b,col_c\n1,2,3"
        assert detect_csv_type(csv) == "unknown"

    def test_empty_string_filename_treated_as_none(self):
        csv = "col_a,col_b\n1,2"
        # Empty filename must not raise and must still return unknown
        assert detect_csv_type(csv, "") == "unknown"

    def test_search_term_beats_keyword_when_both_markers_present(self):
        # Some keyword reports may include a search-term column too — but
        # we classify the more specific type first.
        csv = "Campaign,Targeting,Customer Search Term,Match Type,Impressions\nA,k,sterm,Exact,10\n"
        assert detect_csv_type(csv) == "search_term"

    def test_operation_log_wins_over_csv_detection_when_pipes_present(self):
        # Safety: if a file has pipes AND "Date and time" in header,
        # always treat as operation log even with CSV-like structure
        text = "Date and time | Change type\nfoo | bar"
        assert detect_csv_type(text) == "operation_log"

    def test_bom_prefix_does_not_break_detection(self):
        csv = "\ufeffPlacement,Campaign bidding strategy\nPLACEMENT_TOP,Fixed\n"
        assert detect_csv_type(csv) == "placement"

    def test_large_content_only_reads_head(self):
        # Even a 5MB noise tail must not affect detection of the first header
        header = "Placement,Campaign bidding strategy,Impressions\n"
        tail = "A,B,C\n" * 100_000
        assert detect_csv_type(header + tail) == "placement"
