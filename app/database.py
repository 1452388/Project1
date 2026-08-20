# -*- coding: utf-8 -*-
"""数据库引擎与 Session 管理（SQLAlchemy 2.0 异步）。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 根据数据库类型配置连接池
_is_postgres = settings.DATABASE_URL.startswith("postgresql+")
_is_mysql = settings.DATABASE_URL.startswith("mysql+")

_engine_kwargs: dict = {}
if _is_postgres or _is_mysql:
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10
elif settings.DATABASE_URL.startswith("sqlite"):
    from sqlalchemy.pool import StaticPool
    _engine_kwargs["poolclass"] = StaticPool

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    **_engine_kwargs,
)

# Session 工厂
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：请求级 Session。"""
    async with async_session() as session:
        yield session


async def create_all() -> None:
    """开发辅助：直接建表（正式用 Alembic 迁移）。"""
    from app import models  # noqa: F401  确保模型已导入

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)