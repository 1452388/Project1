# -*- coding: utf-8 -*-
"""文章模型。"""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ArticleStatus(str, Enum):
    """文章状态。"""

    DRAFT = "draft"
    PUBLISHED = "published"


class Article(BaseModel):
    """可编辑的文章内容单元。"""

    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # 图片 URL 列表，第一张为封面
    images: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ArticleStatus.DRAFT.value, nullable=False
    )
    # 扩展字段：{plugin_type: data}，后续加地图/商品/文件等不改表结构
    extra_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # 预留多用户
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    live_codes = relationship(
        "LiveCode", back_populates="article", cascade="all, delete-orphan"
    )

    @property
    def is_published(self) -> bool:
        return self.status == ArticleStatus.PUBLISHED.value

    @property
    def cover_url(self) -> str | None:
        return self.images[0] if self.images else None