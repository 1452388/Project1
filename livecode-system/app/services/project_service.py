# -*- coding: utf-8 -*-
"""项目业务逻辑层。"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectService:
    """项目 CRUD 与状态管理。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Project:
        """创建项目。"""
        project = Project(
            title=data["title"],
            description=data.get("description"),
            content=data.get("content"),
            content_style=data.get("content_style", {}),
            status=data.get("status", "active"),
            cover_image=data.get("cover_image"),
            attachments=data.get("attachments", []),
            extra_data=data.get("extra_data", {}),
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def get(self, project_id: int) -> Project | None:
        """获取项目详情。"""
        stmt = select(Project).where(
            Project.id == project_id,
            Project.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        search: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Project], int]:
        """项目列表（支持搜索、状态筛选）。"""
        query = select(Project).where(Project.is_deleted == False)
        count_query = select(func.count(Project.id)).where(Project.is_deleted == False)

        # 搜索
        if search:
            like = f"%{search}%"
            query = query.where(
                (Project.title.like(like)) |
                (Project.description.like(like))
            )
            count_query = count_query.where(
                (Project.title.like(like)) |
                (Project.description.like(like))
            )

        # 状态筛选
        if status:
            query = query.where(Project.status == status)
            count_query = count_query.where(Project.status == status)

        # 总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(Project.updated_at.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        projects = list(result.scalars().all())
        return projects, total

    async def update(self, project_id: int, data: dict) -> Project | None:
        """更新项目信息。"""
        project = await self.get(project_id)
        if not project:
            return None

        if data:
            stmt = update(Project).where(Project.id == project_id).values(**data)
            await self.session.execute(stmt)
            await self.session.flush()
            return await self.get(project_id)
        return project

    async def delete(self, project_id: int) -> bool:
        """软删除项目。"""
        project = await self.get(project_id)
        if not project:
            return False
        stmt = update(Project).where(Project.id == project_id).values(is_deleted=True)
        await self.session.execute(stmt)
        await self.session.flush()
        return True
