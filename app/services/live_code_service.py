# -*- coding: utf-8 -*-
"""活码业务逻辑层。"""

import secrets
import string

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.live_code import LiveCode


class LiveCodeService:
    """活码 CRUD 与状态管理。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _generate_code(length: int | None = None) -> str:
        """生成随机活码ID（大小写字母+数字，避免易混淆字符）。"""
        length = length or settings.LIVE_CODE_LENGTH
        alphabet = string.ascii_letters + string.digits
        # 排除易混淆字符 0/O/1/l/I
        alphabet = alphabet.replace("0", "").replace("O", "").replace("1", "").replace("l", "").replace("I", "")
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def create(
        self,
        article_id: int | None = None,
        project_id: int | None = None,
        qr_config: dict | None = None,
    ) -> LiveCode:
        """为文章或项目生成一个活码。"""
        if (article_id is None) == (project_id is None):
            raise ValueError("活码必须且只能关联文章或项目")
        if project_id is not None:
            existing = await self.get_by_project(project_id)
            if existing:
                return existing
        # 碰撞检测：最多重试 5 次
        for _ in range(5):
            code = self._generate_code()
            exists = await self.session.execute(
                select(LiveCode.id).where(LiveCode.code == code)
            )
            if exists.scalar_one_or_none() is None:
                break
        else:
            raise RuntimeError("活码生成失败：多次碰撞")

        live_code = LiveCode(
            code=code,
            article_id=article_id,
            project_id=project_id,
            qr_config=qr_config or {},
        )
        self.session.add(live_code)
        await self.session.flush()
        return live_code

    async def get_by_id(self, live_code_id: int) -> LiveCode | None:
        stmt = select(LiveCode).where(
            LiveCode.id == live_code_id, LiveCode.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> LiveCode | None:
        stmt = select(LiveCode).where(
            LiveCode.code == code, LiveCode.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: int) -> LiveCode | None:
        """获取项目当前唯一有效活码。"""
        stmt = (
            select(LiveCode)
            .where(LiveCode.project_id == project_id, LiveCode.is_deleted == False)
            .order_by(LiveCode.id.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        article_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LiveCode], int]:
        query = select(LiveCode).where(LiveCode.is_deleted == False)
        count_query = select(func.count(LiveCode.id)).where(LiveCode.is_deleted == False)

        if article_id:
            query = query.where(LiveCode.article_id == article_id)
            count_query = count_query.where(LiveCode.article_id == article_id)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            query
            .order_by(LiveCode.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def set_active(self, live_code_id: int, is_active: bool) -> LiveCode | None:
        live_code = await self.get_by_id(live_code_id)
        if not live_code:
            return None
        stmt = (
            update(LiveCode)
            .where(LiveCode.id == live_code_id)
            .values(is_active=is_active)
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get_by_id(live_code_id)

    async def update_qr_config(self, live_code_id: int, qr_config: dict) -> LiveCode | None:
        live_code = await self.get_by_id(live_code_id)
        if not live_code:
            return None
        stmt = (
            update(LiveCode)
            .where(LiveCode.id == live_code_id)
            .values(qr_config=qr_config)
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get_by_id(live_code_id)

    async def soft_delete(self, live_code_id: int) -> bool:
        live_code = await self.get_by_id(live_code_id)
        if not live_code:
            return False
        stmt = (
            update(LiveCode)
            .where(LiveCode.id == live_code_id)
            .values(is_deleted=True)
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return True

    async def increment_scan_count(self, live_code_id: int) -> None:
        """扫码计数 +1（统计缓存字段）。"""
        stmt = (
            update(LiveCode)
            .where(LiveCode.id == live_code_id)
            .values(scan_count=LiveCode.scan_count + 1)
        )
        await self.session.execute(stmt)
        await self.session.flush()