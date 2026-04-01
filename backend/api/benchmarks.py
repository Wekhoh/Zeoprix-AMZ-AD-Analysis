"""品类基准对比 API"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Product
from backend.services.benchmark_service import (
    CATEGORY_BENCHMARKS,
    CATEGORY_LABELS,
    compare_with_benchmark,
)
from backend.services.summary_service import dashboard_overview

router = APIRouter()


@router.get("/categories")
def list_categories():
    """获取可用的品类基准列表"""
    return [
        {"key": key, "label": CATEGORY_LABELS.get(key, key)}
        for key in CATEGORY_BENCHMARKS
    ]


@router.get("/compare")
def compare_benchmarks(
    category: str = Query(..., description="品类 key"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """对比当前 KPI 与品类基准"""
    overview = dashboard_overview(db, date_from, date_to)
    kpi = overview["kpi"]

    actual_kpis = {
        "cpc": kpi.get("cpc"),
        "ctr": kpi.get("ctr"),
        "cvr": kpi.get("cvr"),
        "acos": kpi.get("acos"),
    }

    comparisons = compare_with_benchmark(actual_kpis, category)
    return {
        "category": category,
        "category_label": CATEGORY_LABELS.get(category, category),
        "comparisons": comparisons,
    }
