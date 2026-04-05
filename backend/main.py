"""FastAPI 应用入口"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy import text

from backend.config import settings
from backend.database import init_db, SessionLocal, engine
from backend.api import api_router
from backend.logging_config import setup_logging, get_logger
from backend.middleware import RequestLoggingMiddleware

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库并修复状态"""
    setup_logging()
    logger.info("应用启动中...")
    init_db()
    # 启动时修复广告活动状态（从操作日志推断）
    db = SessionLocal()
    try:
        from backend.services.status_service import update_campaign_statuses
        from backend.services.rule_engine import seed_default_rules

        updated = update_campaign_statuses(db)
        if updated:
            logger.info(f"已修复 {updated} 个广告活动状态")

        # 首次启动时播种默认规则
        seeded = seed_default_rules(db)
        if seeded:
            logger.info(f"已创建 {seeded} 条默认自动化规则")
    finally:
        db.close()
    logger.info(f"应用启动完成 v{settings.VERSION}")
    yield
    logger.info("应用关闭")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS — 开发模式允许前端 dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(api_router)


@app.get("/api/health")
def health():
    """Enhanced health check with DB stats"""
    from backend.models import Campaign, PlacementRecord, Backup

    result = {
        "status": "ok",
        "version": settings.VERSION,
        "db": {"connected": False},
    }

    db = SessionLocal()
    try:
        # DB connectivity
        db.execute(text("SELECT 1"))
        result["db"]["connected"] = True

        # DB file size
        db_path = settings.DATA_DIR / "tracker.db"
        if db_path.exists():
            size_bytes = os.path.getsize(db_path)
            result["db"]["size_mb"] = round(size_bytes / (1024 * 1024), 2)

        # Record counts
        result["db"]["campaigns"] = db.query(Campaign).count()
        result["db"]["placements"] = db.query(PlacementRecord).count()

        # Last backup
        last_backup = db.query(Backup).order_by(Backup.created_at.desc()).first()
        if last_backup:
            result["db"]["last_backup"] = str(last_backup.created_at)
    except Exception as e:
        result["status"] = "degraded"
        result["db"]["error"] = str(e)
        logger.warning(f"Health check DB error: {e}")
    finally:
        db.close()

    return result


# 静态文件（生产模式：serve 前端构建产物）— 必须在所有 API 路由之后
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # 静态资源（JS/CSS/图片）
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    # SPA catch-all: 所有非 /api 路径都返回 index.html（React Router 处理）
    @app.get("/{path:path}")
    async def spa_fallback(request: Request, path: str):
        # 如果是静态文件（有扩展名），尝试直接返回
        file_path = frontend_dist / path
        if file_path.is_file():
            return FileResponse(file_path)
        # 否则返回 index.html 让 React Router 处理
        return FileResponse(frontend_dist / "index.html")
