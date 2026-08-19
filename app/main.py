# -*- coding: utf-8 -*-
"""FastAPI 应用入口。"""

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.admin import AdminAuthBackend, ArticleAdmin, TeamMemberAdmin, ProjectAdmin
from app.api.pages import router as pages_router
from app.api.report_pages import router as report_pages_router
from app.api.router import api_router
from app.config import settings, IS_SERVERLESS
from app.database import engine, get_session
from app.api.dependencies import get_principal
from app.services.stats_service import StatsService

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# ── 静态文件（目录不存在时跳过挂载）──
_static_dir = Path("app/static")
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

_uploads_dir = Path(settings.UPLOAD_DIR)
if _uploads_dir.is_dir():
    app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

# ── SQLAdmin 后台管理 ──
admin = Admin(app, engine, authentication_backend=AdminAuthBackend(settings.SECRET_KEY))
admin.add_model_view(ArticleAdmin)
admin.add_model_view(TeamMemberAdmin)
admin.add_model_view(ProjectAdmin)

# ── API 路由 ──
app.include_router(api_router, prefix="/api/v1")

# ── 页面路由（扫码跳转入口等，不挂 /api/v1 前缀）──
app.include_router(pages_router)
app.include_router(report_pages_router)

# ── 后台管理页面路由（不挂 /api/v1 前缀）──
from app.api.admin_pages import router as admin_pages_router
app.include_router(admin_pages_router, prefix="/manage")

# ── 登录页面路由（不挂 /api/v1 前缀）──
from app.api.auth import router as auth_router
app.include_router(auth_router, prefix="/auth")

# ── 人员信息页面路由（不挂 /api/v1 前缀）──
from app.api.team_pages import router as team_pages_router
app.include_router(team_pages_router, prefix="/manage")

# ── 项目管理页面路由（不挂 /api/v1 前缀）──
from app.api.project_pages import router as project_pages_router
app.include_router(project_pages_router, prefix="/manage")

# ── 后台专用项目编辑页（不对前端网站开放）──
from app.api.project_admin_pages import router as project_admin_pages_router
app.include_router(project_admin_pages_router)


@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    session: AsyncSession = Depends(get_session),
    principal: dict | None = Depends(get_principal),
):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    stats = await StatsService(session).get_system_overview()
    return templates.TemplateResponse(
        request,
        "pages/index.html",
        {"request": request, "stats": stats, "principal": principal},
    )