# -*- coding: utf-8 -*-
"""后台专用项目编辑页面。"""

import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.database import get_session
from app.services.project_service import ProjectService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin-tools/project-editor/{project_id}", response_class=HTMLResponse)
async def project_editor(
    request: Request,
    project_id: int,
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_admin),
):
    service = ProjectService(session)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return templates.TemplateResponse(request, "admin/project_editor.html", {
        "request": request,
        "project": project,
        "username": principal.get("username", "管理员"),
    })


@router.post("/admin-tools/project-editor/{project_id}")
async def save_project_editor(
    project_id: int,
    title: str = Form(...),
    description: str = Form(""),
    content: str = Form(""),
    status: str = Form("active"),
    attachments: str = Form("[]"),
    session: AsyncSession = Depends(get_session),
    principal: dict = Depends(require_admin),
):
    if status not in {"active", "draft", "archived"}:
        raise HTTPException(status_code=400, detail="无效的项目状态")
    try:
        attachment_list = json.loads(attachments)
        if not isinstance(attachment_list, list):
            raise ValueError
    except (TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="附件数据格式错误")
    service = ProjectService(session)
    project = await service.update(project_id, {
        "title": title.strip(),
        "description": description.strip() or None,
        "content": content,
        "status": status,
        "attachments": attachment_list,
    })
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    await session.commit()
    return RedirectResponse(url="/admin/project/list?saved=1", status_code=303)