# -*- coding: utf-8 -*-
"""二维码 API 路由。"""

import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.api.dependencies import get_principal, require_guest_code, require_registered_user
from app.schemas import QRBatchRequest, QRConfig
from app.services.live_code_service import LiveCodeService
from app.services.team_service import TeamMemberService
from app.services.qr_service import QRService

router = APIRouter()


@router.get("/{live_code_id}")
async def get_qr_image(
    live_code_id: int,
    size: str = "medium",
    caption: str | None = None,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """获取二维码图片（PNG）。"""
    lc_service = LiveCodeService(session)
    lc = await lc_service.get_by_id(live_code_id)
    if not lc or not lc.is_active:
        raise HTTPException(status_code=404, detail="活码不存在或已停用")

    content = f"{settings.BASE_URL}/l/{lc.code}"
    config = QRConfig(size=size, caption=caption, logo_path=None)
    img = QRService.generate(content, config)
    png_bytes = QRService.to_png_bytes(img)

    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={lc.code}.png"},
    )


@router.get("/{live_code_id}/download")
async def download_qr(
    live_code_id: int,
    size: str = "medium",
    caption: str | None = None,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """下载二维码 PNG。"""
    lc_service = LiveCodeService(session)
    lc = await lc_service.get_by_id(live_code_id)
    if not lc or not lc.is_active:
        raise HTTPException(status_code=404, detail="活码不存在或已停用")

    content = f"{settings.BASE_URL}/l/{lc.code}"
    config = QRConfig(size=size, caption=caption, logo_path=None)
    img = QRService.generate(content, config)
    png_bytes = QRService.to_png_bytes(img)

    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={lc.code}.png"},
    )


@router.post("/batch")
async def batch_generate_qr(
    data: QRBatchRequest,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """批量生成二维码，返回 ZIP。"""
    lc_service = LiveCodeService(session)
    items = []

    for lc_id in data.live_code_ids:
        lc = await lc_service.get_by_id(lc_id)
        if not lc or not lc.is_active:
            continue
        content = f"{settings.BASE_URL}/l/{lc.code}"
        items.append((f"{lc.code}.png", content, data.config))

    if not items:
        raise HTTPException(status_code=400, detail="没有有效的活码可生成")

    zip_bytes = QRService.batch_generate_zip(items)

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=qrcodes.zip"},
    )


@router.get("/team/{code}")
async def get_team_qr_image(
    code: str,
    size: str = "medium",
    caption: str | None = None,
    session: AsyncSession = Depends(get_session),
    principal: dict | None = Depends(get_principal),
):
    """获取团队成员名片二维码（PNG）。"""
    team_service = TeamMemberService(session)
    member = await team_service.get_by_code(code)
    if not principal:
        raise HTTPException(status_code=401, detail="请先登录")
    require_guest_code(principal, code)
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")

    content = f"{settings.BASE_URL}/manage/member/{code}"
    config = QRConfig(size=size, caption=caption, logo_path=member.avatar_url if member.avatar_url else None)
    img = QRService.generate(content, config)
    png_bytes = QRService.to_png_bytes(img)

    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={code}.png"},
    )


@router.get("/team/{code}/download")
async def download_team_qr(
    code: str,
    size: str = "medium",
    caption: str | None = None,
    session: AsyncSession = Depends(get_session),
    principal: dict | None = Depends(get_principal),
):
    """下载团队成员名片二维码 PNG。"""
    team_service = TeamMemberService(session)
    member = await team_service.get_by_code(code)
    if not principal:
        raise HTTPException(status_code=401, detail="请先登录")
    require_guest_code(principal, code)
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")

    content = f"{settings.BASE_URL}/manage/member/{code}"
    config = QRConfig(size=size, caption=caption, logo_path=member.avatar_url if member.avatar_url else None)
    img = QRService.generate(content, config)
    png_bytes = QRService.to_png_bytes(img)

    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={code}.png"},
    )