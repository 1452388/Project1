# -*- coding: utf-8 -*-
"""项目管理页面路由（HTML渲染）。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.api.dependencies import require_registered_user
from app.services.project_service import ProjectService
from app.services.live_code_service import LiveCodeService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/projects", response_class=HTMLResponse)
async def project_list(
    request: Request,
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """项目列表页。"""
    service = ProjectService(session)
    projects, total = await service.list(search=search, status=status, page=page, page_size=10)
    return templates.TemplateResponse(request, "admin/project_list.html", {
        "projects": projects, "total": total, "page": page,
        "search": search or "", "status": status,
    })


@router.get("/project/create", response_class=HTMLResponse)
async def project_create_form(
    request: Request,
    principal: dict = Depends(require_registered_user),
):
    """新建项目表单。"""
    return templates.TemplateResponse(request, "admin/project_form.html", {"project": None})


@router.get("/project/edit/{project_id}", response_class=HTMLResponse)
async def project_edit_form(
    request: Request,
    project_id: int,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """编辑项目表单。"""
    service = ProjectService(session)
    project = await service.get(project_id)
    if not project:
        return templates.TemplateResponse(request, "pages/notice.html", {
            "request": request, "title": "项目不存在", "icon": "❓",
        })
    return templates.TemplateResponse(request, "admin/project_form.html", {"project": project})


@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(
    request: Request,
    project_id: int,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """项目详情页。"""
    service = ProjectService(session)
    project = await service.get(project_id)
    if not project:
        return templates.TemplateResponse(request, "pages/notice.html", {
            "request": request, "title": "项目不存在", "icon": "❓",
        })
    live_code = None
    if request.query_params.get("live_code"):
        live_code = await LiveCodeService(session).get_by_id(int(request.query_params["live_code"]))
    return templates.TemplateResponse(request, "admin/project_detail.html", {
        "project": project, "live_code": live_code,
    })


@router.post("/projects/{project_id}/live-code")
async def create_project_live_code(
    request: Request,
    project_id: int,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """为项目生成二维码活码。"""
    project = await ProjectService(session).get(project_id)
    if not project:
        return templates.TemplateResponse(request, "pages/notice.html", {
            "request": request, "title": "项目不存在", "icon": "❓",
        }, status_code=404)
    live_code = await LiveCodeService(session).create(project_id=project_id)
    await session.commit()
    return RedirectResponse(
        url=f"/manage/projects/{project_id}?live_code={live_code.id}",
        status_code=303,
    )


@router.get("/project/delete/{project_id}")
async def project_delete(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_registered_user),
):
    """删除项目（软删除）。"""
    service = ProjectService(session)
    await service.delete(project_id)
    await session.commit()
    return RedirectResponse(url="/manage/projects", status_code=303)
