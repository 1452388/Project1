# -*- coding: utf-8 -*-
"""页面与 API 访问控制依赖。"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.services.session_service import SessionService


async def get_principal(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict | None:
    payload = SessionService.decode(request.cookies.get(SessionService.cookie_name))
    if not payload:
        return None
    if payload.get("role") == "guest":
        return payload
    user = await session.get(User, payload.get("user_id"))
    if not user or not user.is_active or user.is_deleted:
        return None
    payload["username"] = user.username
    return payload


async def require_login(request: Request, principal: dict | None = Depends(get_principal)) -> dict:
    if principal:
        return principal
    next_url = request.url.path
    if request.url.query:
        next_url += f"?{request.url.query}"
    raise HTTPException(
        status_code=307,
        headers={"Location": f"/auth/login?next={next_url}"},
    )


async def require_registered_user(principal: dict = Depends(require_login)) -> dict:
    if principal.get("role") == "guest":
        raise HTTPException(status_code=403, detail="游客只能查看当前活码页面")
    return principal


async def require_admin(principal: dict = Depends(require_login)) -> dict:
    """只允许管理员访问后台专用页面。"""
    if principal.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问后台")
    return principal


def require_guest_code(principal: dict, code: str) -> None:
    if principal.get("role") == "guest" and principal.get("guest_code") != code:
        raise HTTPException(status_code=403, detail="游客只能查看当前活码页面")