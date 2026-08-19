# -*- coding: utf-8 -*-
"""Pydantic 请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ─── 文章 ───


class ArticleCreate(BaseModel):
    title: str = Field(..., max_length=200, min_length=1)
    content: str = ""
    images: list[str] = []
    extra_fields: dict = {}


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    content: str | None = None
    images: list[str] | None = None
    extra_fields: dict | None = None


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    images: list
    status: str
    extra_fields: dict
    author_id: int | None
    created_at: datetime
    updated_at: datetime
    is_published: bool


class ArticleListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    live_code_count: int = 0
    total_scan_count: int = 0


# ─── 活码 ───


class LiveCodeCreate(BaseModel):
    article_id: int | None = Field(None, gt=0)
    project_id: int | None = Field(None, gt=0)


class LiveCodeUpdate(BaseModel):
    is_active: bool | None = None
    qr_config: dict | None = None


class LiveCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    article_id: int | None
    project_id: int | None = None
    is_active: bool
    qr_config: dict
    scan_count: int
    created_at: datetime


# ─── 二维码 ───


class QRConfig(BaseModel):
    size: str = Field(default="medium", pattern=r"^(small|medium|large)$")
    caption: str | None = None
    logo_path: str | None = None


class QRBatchRequest(BaseModel):
    live_code_ids: list[int] = Field(..., min_length=1, max_length=100)
    config: QRConfig = QRConfig()


# ─── 统计 ───


class StatsResponse(BaseModel):
    total: int
    today: int
    yesterday: int
    trend: list[dict]  # [{"date": "2026-08-17", "count": 10}, ...]


# ─── 通用 ───


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int