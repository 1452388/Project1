# -*- coding: utf-8 -*-
"""文章展示页（扫码用户）、扫码跳转入口等页面路由。"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.api.dependencies import get_principal, require_guest_code, require_login
from app.models.live_code import LiveCode
from app.services.article_service import ArticleService
from app.services.live_code_service import LiveCodeService
from app.services.stats_service import StatsService
from app.services.project_service import ProjectService
from app.services.session_service import SessionService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def record_scan(
    session: AsyncSession,
    live_code: LiveCode,
    request: Request,
) -> None:
    """记录一次扫码（写入 ScanLog 并更新计数缓存）。"""
    stats = StatsService(session)
    await stats.record_scan(
        live_code_id=live_code.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer"),
    )
    lc_service = LiveCodeService(session)
    await lc_service.increment_scan_count(live_code.id)


@router.get("/l/{code}", response_class=HTMLResponse)
async def live_code_page(
    code: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    principal: dict | None = Depends(get_principal),
):
    """扫码跳转入口：活码 → 文章展示页。"""
    lc_service = LiveCodeService(session)
    live_code = await lc_service.get_by_code(code)

    # 1. 活码不存在
    if not live_code:
        return templates.TemplateResponse(
            request,
            "pages/notice.html",
            {
                "request": request,
                "title": "活码不存在",
                "message": "该活码不存在或已被删除，请联系管理员。",
                "icon": "❓",
            },
        )

    # 2. 活码已停用
    if not live_code.is_active:
        return templates.TemplateResponse(
            request,
            "pages/notice.html",
            {
                "request": request,
                "title": "活码已停用",
                "message": "该活码已被停用，如有疑问请联系管理员。",
                "icon": "⛔",
            },
        )

    # 3. 关联文章或项目
    article = None
    project = None
    if live_code.project_id:
        project = await ProjectService(session).get(live_code.project_id)
    elif live_code.article_id:
        article = await ArticleService(session).get_published(live_code.article_id)

    # 4. 目标内容未发布或被删除
    if not article and not project:
        return templates.TemplateResponse(
            request,
            "pages/notice.html",
            {
                "request": request,
                "title": "内容暂未发布",
                "message": "该内容仍在准备中，请稍后再试。",
                "icon": "📝",
            },
        )

    # 扫码页面对访客开放；后台和管理页面仍需要登录。
    guest_token = None
    if not principal:
        guest_token = SessionService.create(0, "guest", guest_code=code)
        principal = {"role": "guest", "guest_code": code}
    require_guest_code(principal, code)

    # 5. 记录扫码
    await record_scan(session, live_code, request)
    await session.commit()

    # 6. 渲染目标展示页
    if project:
        response = templates.TemplateResponse(
            request,
            "admin/project_detail.html",
            {"request": request, "project": project, "live_code": live_code},
        )
    else:
        response = templates.TemplateResponse(
        request,
        "article/view.html",
        {
            "request": request,
            "article": article,
            "live_code": live_code,
            "page_url": f"{settings.BASE_URL}/l/{live_code.code}",
        },
    )
    if guest_token:
        response.set_cookie(
            SessionService.cookie_name,
            guest_token,
            max_age=SessionService.max_age,
            httponly=True,
            samesite="lax",
        )
    return response