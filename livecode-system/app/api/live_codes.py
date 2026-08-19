# -*- coding: utf-8 -*-
"""活码 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.api.dependencies import require_registered_user
from app.schemas import LiveCodeCreate, LiveCodeResponse, PaginatedResponse
from app.services.live_code_service import LiveCodeService

router = APIRouter(dependencies=[Depends(require_registered_user)])


def get_service(session: AsyncSession = Depends(get_session)) -> LiveCodeService:
    return LiveCodeService(session)


@router.post("", response_model=LiveCodeResponse, status_code=201)
async def create_live_code(
    data: LiveCodeCreate,
    service: LiveCodeService = Depends(get_service),
):
    """为文章或项目生成活码。"""
    try:
        live_code = await service.create(
            article_id=data.article_id,
            project_id=data.project_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return LiveCodeResponse(
        id=live_code.id, code=live_code.code,
        article_id=live_code.article_id, project_id=live_code.project_id,
        is_active=live_code.is_active,
        qr_config=live_code.qr_config, scan_count=live_code.scan_count,
        created_at=live_code.created_at,
    )


@router.get("", response_model=PaginatedResponse)
async def list_live_codes(
    article_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: LiveCodeService = Depends(get_service),
):
    """活码列表。"""
    items, total = await service.list(
        article_id=article_id, page=page, page_size=page_size,
    )
    return PaginatedResponse(
        items=[
            LiveCodeResponse(
                id=lc.id, code=lc.code, article_id=lc.article_id,
                project_id=lc.project_id,
                is_active=lc.is_active, qr_config=lc.qr_config,
                scan_count=lc.scan_count, created_at=lc.created_at,
            ).model_dump()
            for lc in items
        ],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{live_code_id}", response_model=LiveCodeResponse)
async def get_live_code(
    live_code_id: int,
    service: LiveCodeService = Depends(get_service),
):
    """活码详情。"""
    lc = await service.get_by_id(live_code_id)
    if not lc:
        raise HTTPException(status_code=404, detail="活码不存在")
    return LiveCodeResponse(
        id=lc.id, code=lc.code, article_id=lc.article_id,
        project_id=lc.project_id,
        is_active=lc.is_active, qr_config=lc.qr_config,
        scan_count=lc.scan_count, created_at=lc.created_at,
    )


@router.put("/{live_code_id}/toggle", response_model=LiveCodeResponse)
async def toggle_live_code(
    live_code_id: int,
    is_active: bool = Query(...),
    service: LiveCodeService = Depends(get_service),
):
    """停用/启用活码。"""
    lc = await service.set_active(live_code_id, is_active)
    if not lc:
        raise HTTPException(status_code=404, detail="活码不存在")
    return LiveCodeResponse(
        id=lc.id, code=lc.code, article_id=lc.article_id,
        project_id=lc.project_id,
        is_active=lc.is_active, qr_config=lc.qr_config,
        scan_count=lc.scan_count, created_at=lc.created_at,
    )


@router.delete("/{live_code_id}", status_code=204)
async def delete_live_code(
    live_code_id: int,
    service: LiveCodeService = Depends(get_service),
):
    """删除活码。"""
    ok = await service.soft_delete(live_code_id)
    if not ok:
        raise HTTPException(status_code=404, detail="活码不存在")