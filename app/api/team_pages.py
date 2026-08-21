# -*- coding: utf-8 -*-
"""人员信息管理页面路由（HTML渲染）。"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.api.dependencies import get_principal, require_guest_code, require_registered_user
from app.services.team_service import TeamMemberService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/team", response_class=HTMLResponse)
async def team_list(
    request: Request,
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """人员列表页。"""
    service = TeamMemberService(session)
    members, total = await service.list(search=search, status=status, page=page, page_size=10)
    return templates.TemplateResponse(request, "admin/team_list.html", {
        "members": members, "total": total, "page": page,
        "search": search or "", "status": status,
    })


@router.get("/team/{member_key}", response_class=HTMLResponse)
async def team_detail(
    request: Request,
    member_key: str,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """成员详情页，使用随机活码后缀。"""
    service = TeamMemberService(session)
    member = await service.get_by_code_for_manage(member_key)
    if not member and member_key.isdigit():
        member = await service.get(int(member_key))
    if not member:
        return templates.TemplateResponse(request, "pages/notice.html", {
            "request": request, "title": "成员不存在", "icon": "❓",
        })
    return templates.TemplateResponse(request, "admin/team_detail.html", {
        "member": member, "page_url": f"{request.base_url}team/{member.code}",
        "member_id": member.id,
    })


@router.get("/team/{member_key}/upload-photo", response_class=HTMLResponse)
async def team_upload_photo(
    request: Request,
    member_key: str,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """成员照片上传页。"""
    service = TeamMemberService(session)
    member = await service.get_by_code_for_manage(member_key)
    if not member and member_key.isdigit():
        member = await service.get(int(member_key))
    if not member:
        return templates.TemplateResponse(request, "pages/notice.html", {
            "request": request, "title": "成员不存在", "icon": "❓",
        })
    return templates.TemplateResponse(request, "admin/team_upload_photo.html", {
        "member": member,
    })


# ===== 扫码跳转的公开名片页 =====

@router.get("/member/{code}", response_class=HTMLResponse)
async def team_card_public(
    request: Request,
    code: str,
    session: AsyncSession = Depends(get_session),
    principal: dict | None = Depends(get_principal),
):
    """公开名片页（扫码跳转）。"""
    if not principal:
        raise HTTPException(
            status_code=307,
            headers={"Location": f"/auth/login?next=/manage/member/{code}"},
        )
    require_guest_code(principal, code)
    service = TeamMemberService(session)
    member = await service.get_by_code(code)
    if not member:
        return templates.TemplateResponse(request, "pages/notice.html", {
            "request": request, "title": "成员不存在", "icon": "❓",
        })
    return templates.TemplateResponse(request, "team/card.html", {"member": member})