"""Tests for benchmark_service — category KPI benchmark comparison.

Pure-function service; no DB fixtures needed. Guards:
1. get_benchmarks returns None for unknown categories
2. compare_with_benchmark returns [] for unknown category
3. Nullish actual metrics are skipped (not assigned "below" by default)
4. LOWER_IS_BETTER metrics (acos, cpc) invert the status comparison
5. diff_pct is rounded correctly with sign
6. Result row shape matches the frontend contract
"""

from backend.services.benchmark_service import (
    CATEGORY_BENCHMARKS,
    LOWER_IS_BETTER,
    compare_with_benchmark,
    get_benchmarks,
)


class TestGetBenchmarks:
    def test_known_category_returns_all_four_metrics(self):
        b = get_benchmarks("beauty")
        assert b is not None
        assert set(b.keys()) == {"cpc", "ctr", "cvr", "acos"}

    def test_unknown_category_returns_none(self):
        assert get_benchmarks("nonexistent_category") is None


class TestCompareWithBenchmark:
    def test_unknown_category_returns_empty_list(self):
        result = compare_with_benchmark({"cpc": 1.0}, "nonexistent")
        assert result == []

    def test_skips_null_actual_metrics(self):
        # Only cpc provided; ctr/cvr/acos missing → only 1 row returned
        result = compare_with_benchmark(
            {"cpc": 1.0, "ctr": None, "cvr": None, "acos": None}, "beauty"
        )
        assert len(result) == 1
        assert result[0]["metric"] == "CPC"

    def test_lower_is_better_inverts_status(self):
        # beauty ACOS benchmark is 0.25. 0.20 < 0.25 → "below" benchmark = GOOD
        result = compare_with_benchmark({"acos": 0.20}, "beauty")
        assert len(result) == 1
        assert result[0]["status"] == "below"

        # 0.30 > 0.25 → "above" = BAD for acos
        result = compare_with_benchmark({"acos": 0.30}, "beauty")
        assert result[0]["status"] == "above"

    def test_higher_is_better_status(self):
        # beauty CTR benchmark is 0.0052. 0.0060 > 0.0052 → "above" = GOOD
        result = compare_with_benchmark({"ctr": 0.0060}, "beauty")
        assert result[0]["metric"] == "CTR"
        assert result[0]["status"] == "above"

        # 0.0040 < 0.0052 → "below" = BAD for ctr
        result = compare_with_benchmark({"ctr": 0.0040}, "beauty")
        assert result[0]["status"] == "below"

    def test_diff_pct_is_signed_integer_percent(self):
        # beauty CPC benchmark 1.35. actual 1.62 → +20% diff
        result = compare_with_benchmark({"cpc": 1.62}, "beauty")
        assert result[0]["diff_pct"] == 20

        # actual 1.08 → -20%
        result = compare_with_benchmark({"cpc": 1.08}, "beauty")
        assert result[0]["diff_pct"] == -20

    def test_result_row_shape(self):
        result = compare_with_benchmark({"cpc": 1.35}, "beauty")
        assert len(result) == 1
        row = result[0]
        assert set(row.keys()) == {"metric", "actual", "benchmark", "status", "diff_pct"}
        # All known metrics have human labels (not keys like "cpc")
        assert row["metric"] == "CPC"

    def test_lower_is_better_set_is_acos_and_cpc(self):
        assert LOWER_IS_BETTER == {"acos", "cpc"}

    def test_all_nine_categories_have_complete_benchmarks(self):
        # Every bundled category must have all four metric rows defined.
        for cat, metrics in CATEGORY_BENCHMARKS.items():
            assert set(metrics.keys()) == {
                "cpc",
                "ctr",
                "cvr",
                "acos",
            }, f"category {cat} has incomplete benchmarks: {metrics.keys()}"
