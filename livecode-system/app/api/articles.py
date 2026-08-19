# -*- coding: utf-8 -*-
"""文章 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.api.dependencies import require_registered_user
from app.schemas import ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListResponse, PaginatedResponse
from app.services.article_service import ArticleService

router = APIRouter(dependencies=[Depends(require_registered_user)])


def get_article_service(session: AsyncSession = Depends(get_session)) -> ArticleService:
    return ArticleService(session)


@router.post("", response_model=ArticleResponse, status_code=201)
async def create_article(
    data: ArticleCreate,
    service: ArticleService = Depends(get_article_service),
):
    """创建文章。"""
    article = await service.create(data)
    live_code_count = await service.get_live_code_count(article.id)
    total_scan = await service.get_total_scan_count(article.id)
    return ArticleResponse(
        id=article.id,
        title=article.title,
        content=article.content,
        images=article.images,
        status=article.status,
        extra_fields=article.extra_fields,
        author_id=article.author_id,
        created_at=article.created_at,
        updated_at=article.updated_at,
        is_published=article.is_published,
    )


@router.get("", response_model=PaginatedResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern=r"^(draft|published)$"),
    search: str | None = Query(None, max_length=100),
    service: ArticleService = Depends(get_article_service),
):
    """文章列表（分页、搜索、筛选）。"""
    articles, total = await service.list(page=page, page_size=page_size, status=status, search=search)
    items = []
    for a in articles:
        lc_count = await service.get_live_code_count(a.id)
        scan_count = await service.get_total_scan_count(a.id)
        items.append(ArticleListResponse(
            id=a.id, title=a.title, status=a.status,
            created_at=a.created_at, updated_at=a.updated_at,
            live_code_count=lc_count, total_scan_count=scan_count,
        ).model_dump())
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
):
    """文章详情。"""
    article = await service.get(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return ArticleResponse(
        id=article.id, title=article.title, content=article.content,
        images=article.images, status=article.status,
        extra_fields=article.extra_fields, author_id=article.author_id,
        created_at=article.created_at, updated_at=article.updated_at,
        is_published=article.is_published,
    )


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    service: ArticleService = Depends(get_article_service),
):
    """更新文章。"""
    article = await service.update(article_id, data)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return ArticleResponse(
        id=article.id, title=article.title, content=article.content,
        images=article.images, status=article.status,
        extra_fields=article.extra_fields, author_id=article.author_id,
        created_at=article.created_at, updated_at=article.updated_at,
        is_published=article.is_published,
    )


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
):
    """删除文章（软删除）。"""
    ok = await service.soft_delete(article_id)
    if not ok:
        raise HTTPException(status_code=404, detail="文章不存在")


@router.post("/{article_id}/publish", response_model=ArticleResponse)
async def publish_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
):
    """发布文章。"""
    article = await service.set_status(article_id, "published")
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return ArticleResponse(
        id=article.id, title=article.title, content=article.content,
        images=article.images, status=article.status,
        extra_fields=article.extra_fields, author_id=article.author_id,
        created_at=article.created_at, updated_at=article.updated_at,
        is_published=article.is_published,
    )


@router.post("/{article_id}/draft", response_model=ArticleResponse)
async def draft_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
):
    """转为草稿。"""
    article = await service.set_status(article_id, "draft")
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return ArticleResponse(
        id=article.id, title=article.title, content=article.content,
        images=article.images, status=article.status,
        extra_fields=article.extra_fields, author_id=article.author_id,
        created_at=article.created_at, updated_at=article.updated_at,
        is_published=article.is_published,
    )