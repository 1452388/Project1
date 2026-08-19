# -*- coding: utf-8 -*-
"""用户认证服务。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class AuthService:
    """用户认证服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username, User.is_deleted == False)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(self, username: str, password: str) -> User | None:
        """验证用户名密码（第一版用简单哈希，后续可升级bcrypt）。"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        # 简单哈希对比（后续可升级）
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.password_hash == password_hash:
            return user
        return None

    async def create_admin_user(self, username: str, password: str) -> User:
        """创建管理员用户（第一版默认账号）。"""
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(
            username=username,
            password_hash=password_hash,
            role="admin",
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_password(self, user_id: int, new_password: str) -> bool:
        """修改密码。"""
        import hashlib
        from sqlalchemy import update
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(password_hash=new_hash)
        )
        await self.session.execute(stmt)
        return True

    async def register_user(self, username: str, password: str) -> User:
        """注册普通用户。"""
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(
            username=username,
            password_hash=password_hash,
            role="user",
        )
        self.session.add(user)
        await self.session.flush()
        return user