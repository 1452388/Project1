# -*- coding: utf-8 -*-
"""错误汇报页面路由。"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/report", response_class=HTMLResponse)
async def report_page(request: Request):
    """错误汇报页面。"""
    return templates.TemplateResponse(request, "pages/report.html", {
        "request": request,
        "github_url": settings.GITHUB_REPOSITORY_URL,
        "support_email": settings.SUPPORT_EMAIL,
    })
