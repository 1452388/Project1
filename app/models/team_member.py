# -*- coding: utf-8 -*-
"""团队成员模型。"""

from datetime import datetime
import secrets
import string

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


def generate_team_member_code(length: int = 8) -> str:
    """生成用于人员名片页的随机活码 ID。"""
    alphabet = string.ascii_letters + string.digits
    alphabet = alphabet.replace("0", "").replace("O", "").replace("1", "").replace("l", "").replace("I", "")
    return "".join(secrets.choice(alphabet) for _ in range(length))


class TeamMember(BaseModel):
    """团队成员信息。"""

    __tablename__ = "team_members"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    wechat: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 活码ID（用于名片页跳转）
    code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, index=True,
        default=generate_team_member_code,
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    # 编辑密码（哈希存储）
    edit_password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 扩展字段
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )