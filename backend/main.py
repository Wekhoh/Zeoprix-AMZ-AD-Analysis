"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.config import settings
from backend.database import init_db, SessionLocal
from backend.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库并修复状态"""
    init_db()
    # 启动时修复广告活动状态（从操作日志推断）
    db = SessionLocal()
    try:
        from backend.services.status_service import update_campaign_statuses
        from backend.services.rule_engine import seed_default_rules

        updated = update_campaign_statuses(db)
        if updated:
            print(f"已修复 {updated} 个广告活动状态")

        # 首次启动时播种默认规则
        seeded = seed_default_rules(db)
        if seeded:
            print(f"已创建 {seeded} 条默认自动化规则")
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

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

# 静态文件（生产模式：serve 前端构建产物）
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # 静态资源（JS/CSS/图片）
    app.mount(
        "/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets"
    )

    # SPA catch-all: 所有非 /api 路径都返回 index.html（React Router 处理）
    @app.get("/{path:path}")
    async def spa_fallback(request: Request, path: str):
        # 如果是静态文件（有扩展名），尝试直接返回
        file_path = frontend_dist / path
        if file_path.is_file():
            return FileResponse(file_path)
        # 否则返回 index.html 让 React Router 处理
        return FileResponse(frontend_dist / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": settings.VERSION}
