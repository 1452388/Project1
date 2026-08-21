# -*- coding: utf-8 -*-
"""人员信息 API 路由。"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.api.dependencies import require_registered_user
from app.schemas.team import TeamMemberCreate, TeamMemberUpdate
from app.services.team_service import TeamMemberService
from app.services.upload_service import UploadService

router = APIRouter(dependencies=[Depends(require_registered_user)])


# ===== 查询端点 =====


@router.get("/search")
async def search_members_by_name(
    name: str = Query(..., description="按姓名查询（支持模糊搜索）"),
    status: str | None = Query(None, description="状态（active/inactive）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """按姓名搜索人员（模糊匹配）。"""
    service = TeamMemberService(session)
    # 复用 list 的 search 参数搜索所有可用字段（含姓名）
    members, total = await service.list(
        search=name, status=status, page=page, page_size=page_size,
    )
    return {
        "列表": [
            {
                "会员编号": m.id, "姓名": m.name, "职位": m.position,
                "部门": m.department, "邮箱": m.email, "电话": m.phone,
                "微信": m.wechat, "头像地址": m.avatar_url, "活码ID": m.code,
                "状态": m.status,
            }
            for m in members
        ],
        "总数": total, "当前页": page, "每页条数": page_size,
    }


@router.get("")
async def list_members(
    search: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """人员列表（支持搜索、状态筛选）。"""
    service = TeamMemberService(session)
    members, total = await service.list(
        search=search, status=status, page=page, page_size=page_size,
    )
    return {
        "列表": [
            {
                "会员编号": m.id, "姓名": m.name, "职位": m.position,
                "部门": m.department, "邮箱": m.email, "电话": m.phone,
                "微信": m.wechat, "头像地址": m.avatar_url, "个人简介": m.bio,
                "活码ID": m.code, "状态": m.status,
                "创建时间": m.created_at.isoformat(),
                "更新时间": m.updated_at.isoformat(),
                "设置了编辑密码": m.edit_password_hash is not None,
            }
            for m in members
        ],
        "总数": total, "当前页": page, "每页条数": page_size,
    }


@router.get("/{member_id}")
async def get_member(
    member_id: int,
    session: AsyncSession = Depends(get_session),
):
    """成员详情。"""
    service = TeamMemberService(session)
    member = await service.get(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    return {
        "会员编号": member.id, "姓名": member.name, "职位": member.position,
        "部门": member.department, "邮箱": member.email, "电话": member.phone,
        "微信": member.wechat, "头像地址": member.avatar_url, "个人简介": member.bio,
        "活码ID": member.code, "状态": member.status,
        "设置了编辑密码": member.edit_password_hash is not None,
        "创建时间": member.created_at.isoformat(),
        "更新时间": member.updated_at.isoformat(),
    }


@router.get("/by-code/{code}")
async def get_member_by_code(
    code: str,
    session: AsyncSession = Depends(get_session),
):
    """通过活码ID获取成员（公开）。"""
    service = TeamMemberService(session)
    member = await service.get_by_code(code)
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在或已停用")
    return {
        "会员编号": member.id, "姓名": member.name, "职位": member.position,
        "部门": member.department, "邮箱": member.email, "电话": member.phone,
        "微信": member.wechat, "头像地址": member.avatar_url, "个人简介": member.bio,
        "活码ID": member.code, "状态": member.status,
    }


# ===== 写入端点 =====


@router.post("")
async def create_member(
    data: TeamMemberCreate,
    session: AsyncSession = Depends(get_session),
):
    """创建人员。"""
    service = TeamMemberService(session)
    member = await service.create(data.model_dump())
    await session.commit()
    return {
        "会员编号": member.id, "姓名": member.name, "职位": member.position,
        "部门": member.department, "邮箱": member.email, "电话": member.phone,
        "微信": member.wechat, "头像地址": member.avatar_url, "个人简介": member.bio,
        "活码ID": member.code, "状态": member.status,
        "创建时间": member.created_at.isoformat(),
        "更新时间": member.updated_at.isoformat(),
    }


@router.put("/{member_id}")
async def update_member(
    member_id: int,
    data: TeamMemberUpdate,
    session: AsyncSession = Depends(get_session),
):
    """编辑人员信息。"""
    service = TeamMemberService(session)
    member = await service.update(member_id, data.model_dump(exclude_unset=True))
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    await session.commit()
    return {
        "会员编号": member.id, "姓名": member.name, "职位": member.position,
        "部门": member.department, "邮箱": member.email, "电话": member.phone,
        "微信": member.wechat, "头像地址": member.avatar_url, "个人简介": member.bio,
        "活码ID": member.code, "状态": member.status,
        "创建时间": member.created_at.isoformat(),
        "更新时间": member.updated_at.isoformat(),
    }


@router.delete("/{member_id}")
async def delete_member(
    member_id: int,
    session: AsyncSession = Depends(get_session),
):
    """删除人员。"""
    service = TeamMemberService(session)
    ok = await service.delete(member_id)
    if not ok:
        raise HTTPException(status_code=404, detail="成员不存在")
    await session.commit()
    return {"消息": "删除成功"}


@router.post("/{member_id}/toggle-status")
async def toggle_member_status(
    member_id: int,
    session: AsyncSession = Depends(get_session),
):
    """切换成员状态（在职/离职）。"""
    service = TeamMemberService(session)
    member = await service.toggle_status(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    await session.commit()
    return {
        "会员编号": member.id, "姓名": member.name, "状态": member.status,
        "消息": f"已切换为{'在职' if member.status == 'active' else '离职'}",
    }


@router.post("/{member_id}/avatar")
async def upload_member_avatar(
    member_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """上传人员头像。"""
    try:
        url = await UploadService.save_image(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = TeamMemberService(session)
    member = await service.update(member_id, {"avatar_url": url})
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    await session.commit()
    return {"消息": "头像上传成功", "头像地址": url}
