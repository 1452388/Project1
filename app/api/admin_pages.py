# -*- coding: utf-8 -*-
"""后台管理页面路由（HTML渲染）。"""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session, async_session
from app.api.dependencies import require_registered_user
from app.models.article import Article
from app.models.live_code import LiveCode

router = APIRouter(dependencies=[Depends(require_registered_user)])
templates = Jinja2Templates(directory="app/templates")


# ───────── 文章管理 ─────────

async def get_articles_with_stats(session: AsyncSession) -> list[dict]:
    """获取文章列表（含活码数和扫码量）。"""
    stmt = (
        select(Article)
        .where(Article.is_deleted == False)
        .options(selectinload(Article.live_codes))
        .order_by(Article.updated_at.desc())
    )
    result = await session.execute(stmt)
    articles = result.scalars().all()
    items = []
    for a in articles:
        lc_count = len([lc for lc in a.live_codes if not lc.is_deleted])
        scan_count = sum(lc.scan_count for lc in a.live_codes if not lc.is_deleted)
        items.append({
            "id": a.id, "title": a.title, "status": a.status,
            "created_at": a.created_at, "updated_at": a.updated_at,
            "live_code_count": lc_count, "total_scan_count": scan_count,
            "live_codes": a.live_codes,
        })
    return items


@router.get("/articles", response_class=HTMLResponse)
async def admin_articles(request: Request, session: AsyncSession = Depends(get_session)):
    """文章管理列表页。"""
    articles = await get_articles_with_stats(session)
    return templates.TemplateResponse(request, "admin/article_list.html", {"articles": articles})


@router.get("/article/create", response_class=HTMLResponse)
async def article_create_form(request: Request):
    """新建文章表单。"""
    return templates.TemplateResponse(request, "admin/article_edit.html", {"article": None})


@router.get("/article/edit/{article_id}", response_class=HTMLResponse)
async def article_edit_form(request: Request, article_id: int, session: AsyncSession = Depends(get_session)):
    """编辑文章表单。"""
    result = await session.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return templates.TemplateResponse(request, "admin/article_edit.html", {"article": article})


# ───────── 二维码配置页 ─────────

@router.get("/qr/generate/{live_code_id}", response_class=HTMLResponse)
async def qr_generate_page(
    request: Request,
    live_code_id: int,
    session: AsyncSession = Depends(get_session),
):
    """二维码配置页：预览 + 调配置 + 下载。"""
    from app.services.live_code_service import LiveCodeService
    lc_service = LiveCodeService(session)
    lc = await lc_service.get_by_id(live_code_id)
    if not lc:
        raise HTTPException(status_code=404, detail="活码不存在")
    # 关联文章
    article_stmt = select(Article).where(Article.id == lc.article_id)
    result = await session.execute(article_stmt)
    article = result.scalar_one_or_none()
    return templates.TemplateResponse(
        request,
        "admin/qr_generate.html",
        {
            "live_code": lc,
            "article": article,
            "sizes": {"small": "小 (200×200)", "medium": "中 (400×400)", "large": "大 (600×600)"},
        },
    )