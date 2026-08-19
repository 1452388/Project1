# -*- coding: utf-8 -*-
"""Pydantic 请求/响应模型（登录相关）。"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class LoginResponse(BaseModel):
    user_id: int
    username: str
    token: str
    role: str
    redirect_to: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"