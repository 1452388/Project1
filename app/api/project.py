# -*- coding: utf-8 -*-
"""项目 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.api.dependencies import require_registered_user
from app.services.project_service import ProjectService

router = APIRouter(dependencies=[Depends(require_registered_user)])


# ===== Pydantic 模型 =====


class ProjectCreate(BaseModel):
    """创建项目请求体。"""

    title: str = Field(..., description="项目名称")
    description: str | None = Field(None, description="简短描述")
    content: str | None = Field(None, description="富文本内容（HTML）")
    content_style: dict = Field(default={}, description="内容样式配置")
    status: str = Field(default="active", description="状态（active/draft/archived）")
    cover_image: str | None = Field(None, description="封面图 URL")
    attachments: list = Field(default=[], description="附件列表")
    extra_data: dict = Field(default={}, description="扩展字段")


class ProjectUpdate(BaseModel):
    """编辑项目请求体（所有字段可选）。"""

    title: str | None = Field(None, description="项目名称")
    description: str | None = Field(None, description="简短描述")
    content: str | None = Field(None, description="富文本内容（HTML）")
    content_style: dict | None = Field(None, description="内容样式配置")
    status: str | None = Field(None, description="状态（active/draft/archived）")
    cover_image: str | None = Field(None, description="封面图 URL")
    attachments: list | None = Field(None, description="附件列表")
    extra_data: dict | None = Field(None, description="扩展字段")


# ===== 辅助函数 =====


def project_to_dict(p) -> dict:
    """将项目对象转为中文字段名的字典。"""
    return {
        "项目编号": p.id,
        "项目名称": p.title,
        "简短描述": p.description,
        "内容": p.content,
        "内容样式": p.content_style,
        "状态": p.status,
        "封面图": p.cover_image,
        "附件列表": p.attachments,
        "扩展字段": p.extra_data,
        "创建时间": p.created_at.isoformat(),
        "更新时间": p.updated_at.isoformat(),
    }


# ===== 查询端点 =====


@router.get("")
async def list_projects(
    search: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """项目列表（支持搜索、状态筛选）。"""
    service = ProjectService(session)
    projects, total = await service.list(
        search=search, status=status, page=page, page_size=page_size,
    )
    return {
        "列表": [project_to_dict(p) for p in projects],
        "总数": total, "当前页": page, "每页条数": page_size,
    }


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    session: AsyncSession = Depends(get_session),
):
    """项目详情。"""
    service = ProjectService(session)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project_to_dict(project)


# ===== 写入端点 =====


@router.post("")
async def create_project(
    data: ProjectCreate,
    session: AsyncSession = Depends(get_session),
):
    """创建项目。"""
    service = ProjectService(session)
    project = await service.create(data.model_dump())
    await session.commit()
    return project_to_dict(project)


@router.put("/{project_id}")
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
):
    """编辑项目（内容、样式等）。"""
    service = ProjectService(session)
    project = await service.update(project_id, data.model_dump(exclude_unset=True))
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    await session.commit()
    return project_to_dict(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_session),
):
    """删除项目（软删除）。"""
    service = ProjectService(session)
    ok = await service.delete(project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="项目不存在")
    await session.commit()
    return {"消息": "删除成功"}
