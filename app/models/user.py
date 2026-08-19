# -*- coding: utf-8 -*-
"""用户模型（预留多用户）。"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    """用户（第一版预留，后续多用户时启用）。"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=""
    )
    role: Mapped[str] = mapped_column(
        String(20), default="admin", nullable=False, server_default="admin"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default="1"
    )
    # 预留字段
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)