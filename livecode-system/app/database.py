# -*- coding: utf-8 -*-
"""数据库引擎与 Session 管理（SQLAlchemy 2.0 异步）。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 根据数据库类型配置连接池
_is_postgres = settings.DATABASE_URL.startswith("postgresql")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"ssl": True} if settings.DATABASE_SSL else {},
    # PostgreSQL 连接池参数
    **(
        {"pool_size": 5, "max_overflow": 10}
        if _is_postgres
        else {}
    ),
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