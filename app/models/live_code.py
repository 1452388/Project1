# -*- coding: utf-8 -*-
"""活码模型。"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LiveCode(BaseModel):
    """指向一篇文章的固定标识符（活码）。"""

    __tablename__ = "live_codes"

    # 随机字符串，如 a3kF9qXz
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("articles.id"), nullable=True, index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # 二维码生成配置：{size, logo_path, caption}
    qr_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # 扫码总量缓存
    scan_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )
    # 预留扩展
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    article = relationship("Article", back_populates="live_codes")
    project = relationship("Project")
    scan_logs = relationship(
        "ScanLog", back_populates="live_code", cascade="all, delete-orphan"
    )