# -*- coding: utf-8 -*-
"""登录/认证相关API。"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService
from app.services.session_service import SessionService

router = APIRouter()


def safe_next_url(value: str | None, default: str = "/") -> str:
    """只允许回跳到站内绝对路径。"""
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return default


# ===== 注册请求模型 =====

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)


# ===== 登录日志模型 =====

class LoginLogRequest(BaseModel):
    user_id: int
    username: str
    role: str


# ===== 页面路由 =====

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str | None = Query(None)):
    """登录页面。"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(request, "pages/login.html", {
        "request": request, "next_url": safe_next_url(next),
    })


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """注册页面。"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(request, "pages/register.html", {"request": request})


# ===== API 路由 =====

@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """用户登录。"""
    auth_service = AuthService(session)
    user = await auth_service.authenticate(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = SessionService.create(user.id, user.role)
    response.set_cookie(
        SessionService.cookie_name, token, max_age=SessionService.max_age,
        httponly=True, samesite="lax",
    )
    next_url = safe_next_url(request.query_params.get("next"))
    return LoginResponse(
        user_id=user.id,
        username=user.username,
        token=token,
        role=user.role,
        redirect_to=next_url,
    )


@router.post("/register")
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    """用户注册。"""
    auth_service = AuthService(session)
    # 检查用户名是否已存在
    existing = await auth_service.get_user_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    # 创建用户
    user = await auth_service.register_user(data.username, data.password)
    await session.commit()
    return {"message": "注册成功", "user_id": user.id}


@router.post("/login/guest", response_model=LoginResponse)
async def guest_login(
    request: Request,
    response: Response,
):
    """游客登录。"""
    next_url = safe_next_url(request.query_params.get("next"))
    guest_code = None
    for prefix in ("/l/", "/manage/member/"):
        if next_url.startswith(prefix):
            guest_code = next_url.removeprefix(prefix).split("?", 1)[0].strip("/")
            break
    token = SessionService.create(0, "guest", guest_code=guest_code)
    response.set_cookie(
        SessionService.cookie_name, token, max_age=SessionService.max_age,
        httponly=True, samesite="lax",
    )
    return LoginResponse(
        user_id=0,
        username="guest",
        token=token,
        role="guest",
        redirect_to=next_url if guest_code else "/",
    )


@router.post("/log-login")
async def log_login(data: LoginLogRequest):
    """记录登录日志（简单实现，写入文件）。"""
    import json
    import os
    from datetime import datetime
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "login.log")
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": data.user_id,
        "username": data.username,
        "role": data.role,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    return {"message": "日志已记录"}


@router.post("/logout")
async def logout(response: Response):
    """用户登出。"""
    response.delete_cookie(SessionService.cookie_name)
    return {"message": "已登出"}


@router.get("/me")
async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)):
    """获取当前用户信息。"""
    payload = SessionService.decode(request.cookies.get(SessionService.cookie_name))
    if not payload:
        raise HTTPException(status_code=401, detail="未登录")
    if payload.get("role") == "guest":
        return {"id": 0, "username": "游客", "role": "guest", "guest_code": payload.get("guest_code")}
    from app.models.user import User
    user = await session.get(User, payload.get("user_id"))
    if not user or not user.is_active or user.is_deleted:
        raise HTTPException(status_code=401, detail="无效会话")
    return {"id": user.id, "username": user.username, "role": user.role}