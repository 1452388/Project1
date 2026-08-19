# -*- coding: utf-8 -*-
"""API 路由聚合。"""

from fastapi import APIRouter

from app.api.articles import router as articles_router
from app.api.live_codes import router as live_codes_router
from app.api.qr import router as qr_router
from app.api.stats import router as stats_router
from app.api.upload import router as upload_router
from app.api.pages import router as pages_router
from app.api.auth import router as auth_router
from app.api.team import router as team_router
from app.api.project import router as project_router

api_router = APIRouter()
api_router.include_router(articles_router, prefix="/articles", tags=["文章"])
api_router.include_router(live_codes_router, prefix="/live-codes", tags=["活码"])
api_router.include_router(qr_router, prefix="/qr", tags=["二维码"])
api_router.include_router(stats_router, prefix="/stats", tags=["统计"])
api_router.include_router(upload_router, prefix="/upload", tags=["上传"])
api_router.include_router(pages_router)
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(team_router, prefix="/team", tags=["人员"])
api_router.include_router(project_router, prefix="/projects", tags=["项目"])