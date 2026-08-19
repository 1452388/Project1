# -*- coding: utf-8 -*-
"""团队成员业务逻辑层。"""

import hashlib
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_member import TeamMember, generate_team_member_code


class TeamMemberService:
    """团队成员 CRUD 与状态管理。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> TeamMember:
        """创建团队成员。"""
        # 生成活码ID
        code = generate_team_member_code()
        # 处理编辑密码
        edit_password_hash = None
        if data.get("edit_password"):
            edit_password_hash = hashlib.sha256(data["edit_password"].encode()).hexdigest()

        member = TeamMember(
            name=data["name"],
            position=data.get("position"),
            department=data.get("department"),
            email=data.get("email"),
            phone=data.get("phone"),
            wechat=data.get("wechat"),
            avatar_url=data.get("avatar_url"),
            bio=data.get("bio"),
            code=code,
            status=data.get("status", "active"),
            edit_password_hash=edit_password_hash,
            extra_data=data.get("extra_data", {}),
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def get(self, member_id: int) -> TeamMember | None:
        """获取成员详情。"""
        stmt = select(TeamMember).where(TeamMember.id == member_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> TeamMember | None:
        """通过活码ID获取成员（公开）。"""
        stmt = select(TeamMember).where(TeamMember.code == code, TeamMember.status == "active")
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code_for_manage(self, code: str) -> TeamMember | None:
        """通过活码ID获取管理详情，包含离职人员。"""
        stmt = select(TeamMember).where(TeamMember.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        search: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TeamMember], int]:
        """成员列表（支持搜索、状态筛选）。"""
        query = select(TeamMember)
        count_query = select(func.count(TeamMember.id))

        # 搜索
        if search:
            like = f"%{search}%"
            query = query.where(
                (TeamMember.name.like(like)) |
                (TeamMember.position.like(like)) |
                (TeamMember.department.like(like)) |
                (TeamMember.email.like(like))
            )
            count_query = count_query.where(
                (TeamMember.name.like(like)) |
                (TeamMember.position.like(like)) |
                (TeamMember.department.like(like)) |
                (TeamMember.email.like(like))
            )

        # 状态筛选
        if status:
            query = query.where(TeamMember.status == status)
            count_query = count_query.where(TeamMember.status == status)

        # 总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(TeamMember.created_at.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        members = list(result.scalars().all())
        return members, total

    async def update(self, member_id: int, data: dict) -> TeamMember | None:
        """更新成员信息。"""
        member = await self.get(member_id)
        if not member:
            return None

        update_data = {k: v for k, v in data.items() if k != "edit_password"}

        # 处理编辑密码
        if data.get("edit_password"):
            update_data["edit_password_hash"] = hashlib.sha256(data["edit_password"].encode()).hexdigest()

        if update_data:
            stmt = update(TeamMember).where(TeamMember.id == member_id).values(**update_data)
            await self.session.execute(stmt)
            await self.session.flush()
            return await self.get(member_id)
        return member

    async def verify_edit_password(self, member_id: int, password: str) -> bool:
        """验证编辑密码。"""
        member = await self.get(member_id)
        if not member:
            return False
        if not member.edit_password_hash:
            return True  # 无密码保护
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return member.edit_password_hash == password_hash

    async def delete(self, member_id: int) -> bool:
        """删除成员。"""
        member = await self.get(member_id)
        if not member:
            return False
        from sqlalchemy import delete
        stmt = delete(TeamMember).where(TeamMember.id == member_id)
        await self.session.execute(stmt)
        await self.session.flush()
        return True

    async def toggle_status(self, member_id: int) -> TeamMember | None:
        """切换成员状态（active/inactive）。"""
        member = await self.get(member_id)
        if not member:
            return None
        new_status = "inactive" if member.status == "active" else "active"
        stmt = update(TeamMember).where(TeamMember.id == member_id).values(status=new_status)
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get(member_id)