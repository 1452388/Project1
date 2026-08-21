# -*- coding: utf-8 -*-
"""人员信息 Pydantic 模型。"""

from pydantic import BaseModel, Field


class TeamMemberCreate(BaseModel):
    """创建人员请求体。"""

    name: str = Field(..., description="姓名")
    position: str | None = Field(None, description="职位")
    department: str | None = Field(None, description="部门")
    email: str | None = Field(None, description="邮箱")
    phone: str | None = Field(None, description="电话")
    wechat: str | None = Field(None, description="微信号")
    avatar_url: str | None = Field(None, description="头像地址")
    bio: str | None = Field(None, description="个人简介")
    # 名片扩展字段
    age: str | None = Field(None, description="年龄")
    section: str | None = Field(None, description="标段")
    post: str | None = Field(None, description="岗位")
    id_card: str | None = Field(None, description="身份证号")
    # 编辑密码
    edit_password: str | None = Field(None, description="编辑密码（可选，设置后编辑需验证）")
    extra_data: dict = Field(default={}, description="扩展字段")


class TeamMemberUpdate(BaseModel):
    """编辑人员请求体（所有字段可选）。"""

    name: str | None = Field(None, description="姓名")
    position: str | None = Field(None, description="职位")
    department: str | None = Field(None, description="部门")
    email: str | None = Field(None, description="邮箱")
    phone: str | None = Field(None, description="电话")
    wechat: str | None = Field(None, description="微信号")
    avatar_url: str | None = Field(None, description="头像地址")
    bio: str | None = Field(None, description="个人简介")
    # 名片扩展字段
    age: str | None = Field(None, description="年龄")
    section: str | None = Field(None, description="标段")
    post: str | None = Field(None, description="岗位")
    id_card: str | None = Field(None, description="身份证号")
    # 编辑密码
    edit_password: str | None = Field(None, description="编辑密码")
    status: str | None = Field(None, description="状态（active=在职, inactive=离职）")
    extra_data: dict | None = Field(None, description="扩展字段")
