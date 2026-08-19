# -*- coding: utf-8 -*-
"""通用 Mixin 与 Base 模型。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.database import Base


class TimestampMixin:
    """创建/更新时间戳。"""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


class SoftDeleteMixin:
    """软删除标记。"""

    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        return mapped_column(Boolean, default=False, nullable=False, server_default="0")


class IDMixin:
    """自增主键。"""

    @declared_attr
    def id(cls) -> Mapped[int]:
        return mapped_column(Integer, primary_key=True, autoincrement=True)


class BaseModel(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """整合了主键、时间戳、软删除的基类（抽象）。"""

    __abstract__ = True


__all__ = ["Base", "BaseModel", "IDMixin", "TimestampMixin", "SoftDeleteMixin"]