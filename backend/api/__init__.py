from fastapi import APIRouter
from backend.api import (
    imports,
    campaigns,
    placements,
    operation_logs,
    summaries,
    migration,
    backups,
    products,
    organic_sales,
    data_manage,
    notes,
    search_terms,
    analysis,
    rules,
    reports,
    benchmarks,
)

api_router = APIRouter(prefix="/api")

api_router.include_router(imports.router, prefix="/import", tags=["数据导入"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["广告活动"])
api_router.include_router(placements.router, prefix="/placements", tags=["展示位置"])
api_router.include_router(operation_logs.router, prefix="/operation-logs", tags=["操作日志"])
api_router.include_router(summaries.router, prefix="/summaries", tags=["数据汇总"])
api_router.include_router(migration.router, prefix="/migration", tags=["数据迁移"])
api_router.include_router(backups.router, prefix="/settings", tags=["备份管理"])
api_router.include_router(products.router, prefix="/settings", tags=["产品管理"])
api_router.include_router(organic_sales.router, prefix="/settings", tags=["有机销售"])
api_router.include_router(data_manage.router, prefix="/settings", tags=["数据管理"])
api_router.include_router(notes.router, prefix="/notes", tags=["运营笔记"])
api_router.include_router(search_terms.router, prefix="/search-terms", tags=["搜索词分析"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["智能建议"])
api_router.include_router(rules.router, prefix="/rules", tags=["自动化规则"])
api_router.include_router(reports.router, prefix="/reports", tags=["报告导出"])
api_router.include_router(benchmarks.router, prefix="/benchmarks", tags=["品类基准"])
