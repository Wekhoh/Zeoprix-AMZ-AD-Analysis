"""品类基准对比服务"""

from typing import Optional

CATEGORY_BENCHMARKS: dict[str, dict[str, float]] = {
    "beauty": {"cpc": 1.35, "ctr": 0.0052, "cvr": 0.135, "acos": 0.25},
    "home_kitchen": {"cpc": 1.02, "ctr": 0.0042, "cvr": 0.115, "acos": 0.30},
    "electronics": {"cpc": 1.25, "ctr": 0.0042, "cvr": 0.10, "acos": 0.28},
    "clothing": {"cpc": 0.90, "ctr": 0.0037, "cvr": 0.095, "acos": 0.32},
    "sports": {"cpc": 1.05, "ctr": 0.0042, "cvr": 0.105, "acos": 0.28},
    "grocery": {"cpc": 1.35, "ctr": 0.0047, "cvr": 0.15, "acos": 0.22},
    "toys": {"cpc": 0.85, "ctr": 0.0042, "cvr": 0.12, "acos": 0.25},
    "health": {"cpc": 1.25, "ctr": 0.0047, "cvr": 0.125, "acos": 0.27},
    "travel": {"cpc": 1.10, "ctr": 0.0045, "cvr": 0.11, "acos": 0.29},
}

CATEGORY_LABELS: dict[str, str] = {
    "beauty": "美妆个护",
    "home_kitchen": "家居厨房",
    "electronics": "电子产品",
    "clothing": "服装鞋靴",
    "sports": "运动户外",
    "grocery": "食品杂货",
    "toys": "玩具游戏",
    "health": "健康保健",
    "travel": "旅行出行",
}

# For ACOS and CPC, lower is better
LOWER_IS_BETTER = {"acos", "cpc"}

METRIC_LABELS: dict[str, str] = {
    "cpc": "CPC",
    "ctr": "CTR",
    "cvr": "CVR",
    "acos": "ACOS",
}


def get_benchmarks(category: str) -> Optional[dict[str, float]]:
    """Get benchmark values for a given category."""
    return CATEGORY_BENCHMARKS.get(category)


def compare_with_benchmark(actual_kpis: dict[str, float | None], category: str) -> list[dict]:
    """Compare actual KPIs against category benchmarks.

    Returns a list of comparisons with status indicators.
    """
    benchmarks = CATEGORY_BENCHMARKS.get(category)
    if not benchmarks:
        return []

    results: list[dict] = []
    for metric, bench_val in benchmarks.items():
        actual_val = actual_kpis.get(metric)
        if actual_val is None:
            continue

        diff_pct = round(((actual_val - bench_val) / bench_val) * 100) if bench_val else 0

        if metric in LOWER_IS_BETTER:
            status = "below" if actual_val <= bench_val else "above"
        else:
            status = "above" if actual_val >= bench_val else "below"

        results.append(
            {
                "metric": METRIC_LABELS.get(metric, metric.upper()),
                "actual": round(actual_val, 4),
                "benchmark": bench_val,
                "status": status,
                "diff_pct": diff_pct,
            }
        )

    return results
