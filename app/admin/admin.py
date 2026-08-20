# -*- coding: utf-8 -*-
"""SQLAdmin 后台管理视图配置。"""

from fastapi import Request
from fastapi.responses import RedirectResponse, Response
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from wtforms import BooleanField
from markupsafe import Markup, escape

from app.models.article import Article
from app.models.project import Project
from app.models.team_member import TeamMember
from app.services.session_service import SessionService


class AdminAuthBackend(AuthenticationBackend):
    """复用系统登录会话保护 SQLAdmin。"""

    async def login(self, request: Request) -> Response:
        return RedirectResponse("/auth/login?next=/admin", status_code=303)

    async def logout(self, request: Request) -> Response:
        response = RedirectResponse("/auth/login", status_code=303)
        response.delete_cookie(SessionService.cookie_name)
        return response

    async def authenticate(self, request: Request) -> bool:
        payload = SessionService.decode(request.cookies.get(SessionService.cookie_name))
        return bool(payload and payload.get("role") == "admin")


class ArticleAdmin(ModelView, model=Article):
    """文章管理后台视图。"""

    name = "文章"
    name_plural = "文章管理"
    icon = "fa-solid fa-newspaper"
    column_list = [
        Article.id, Article.title, Article.status,
        Article.created_at, Article.updated_at,
    ]
    column_searchable_list = [Article.title]
    column_sortable_list = [Article.id, Article.created_at, Article.updated_at]
    column_default_sort = (Article.created_at, True)
    column_formatters = {
        Article.status: lambda m, a: "✅ 已发布" if m.is_published else "📝 草稿",
    }
    # 详情页展示
    column_details_list = [
        Article.id, Article.title, Article.content, Article.images,
        Article.status, Article.extra_fields,
        Article.created_at, Article.updated_at,
    ]
    form_excluded_columns = {
        Article.created_at, Article.updated_at, Article.is_deleted,
        Article.author_id, Article.live_codes,
    }


    async def delete_model(self, request, pk):
        """重写删除方法，使用软删除。"""
        from app.services.project_service import ProjectService
        from app.database import async_session
        async with async_session() as session:
            service = ProjectService(session)
            await service.delete(int(pk))
            await session.commit()
    can_delete = True
    can_export = True


class TeamMemberAdmin(ModelView, model=TeamMember):
    """人员信息后台管理视图。"""

    name = "人员"
    name_plural = "人员管理"
    icon = "fa-solid fa-users"
    column_labels = {
        TeamMember.id: "编号",
        TeamMember.name: "姓名",
        TeamMember.position: "职位",
        TeamMember.department: "部门",
        TeamMember.email: "邮箱",
        TeamMember.phone: "电话",
        TeamMember.wechat: "微信",
        TeamMember.avatar_url: "头像地址",
        TeamMember.bio: "个人简介",
        TeamMember.code: "名片活码",
        TeamMember.status: "人员状态",
        TeamMember.extra_data: "扩展信息",
        TeamMember.created_at: "创建时间",
        TeamMember.updated_at: "更新时间",
    }
    column_list = [
        TeamMember.id, TeamMember.name, TeamMember.position,
        TeamMember.department, TeamMember.phone, TeamMember.status,
        TeamMember.created_at, TeamMember.updated_at,
    ]
    column_searchable_list = [
        TeamMember.name, TeamMember.position, TeamMember.department,
        TeamMember.email, TeamMember.phone,
    ]
    column_sortable_list = [TeamMember.id, TeamMember.created_at, TeamMember.updated_at]
    column_default_sort = (TeamMember.created_at, True)
    column_formatters = {
        TeamMember.status: lambda m, a: "✅ 在职" if m.status == "active" else "⛔ 离职",
        TeamMember.code: lambda m, a: Markup(
            '<div class="flex items-center gap-2">'
            '<img src="/api/v1/qr/team/{0}?size=small&caption=扫一扫查看" '
            'alt="名片二维码" width="64" height="64" class="rounded border">'
            '<a href="/manage/member/{0}" target="_blank" '
            'class="text-primary-600 hover:text-primary-800">{0}</a>'
            '</div>'.format(escape(m.code))
        ),
    }
    column_details_list = [
        TeamMember.id, TeamMember.name, TeamMember.position,
        TeamMember.department, TeamMember.email, TeamMember.phone,
        TeamMember.wechat, TeamMember.avatar_url, TeamMember.bio,
        TeamMember.code, TeamMember.status, TeamMember.extra_data,
        TeamMember.created_at, TeamMember.updated_at,
    ]
    form_excluded_columns = {
        TeamMember.created_at, TeamMember.updated_at,
        TeamMember.code, TeamMember.edit_password_hash,
    }
    form_args = {
        "name": {"label": "姓名", "description": "请输入人员姓名"},
        "position": {"label": "职位", "description": "例如：项目经理"},
        "department": {"label": "部门", "description": "例如：项目部"},
        "email": {"label": "邮箱", "description": "用于联系人员的邮箱地址"},
        "phone": {"label": "电话", "description": "用于联系人员的电话号码"},
        "wechat": {"label": "微信", "description": "微信号或企业微信号"},
        "avatar_url": {"label": "头像地址", "description": "填写已上传头像的图片地址"},
        "bio": {"label": "个人简介", "description": "支持填写人员介绍内容"},
        "status": {
            "label": "人员状态",
            "description": "active=在职，inactive=离职",
        },
        "extra_data": {"label": "扩展信息", "description": "JSON 格式的附加信息，可留空"},
    }

    async def on_model_change(self, data, model, is_created, request):
        """将后台输入的中文状态统一保存为系统状态值。"""
        status_map = {"在职": "active", "离职": "inactive"}
        data["status"] = status_map.get(data.get("status"), data.get("status", "active"))



    async def delete_model(self, request, pk):
        """重写删除方法，使用软删除。"""
        from app.services.project_service import ProjectService
        from app.database import async_session
        async with async_session() as session:
            service = ProjectService(session)
            await service.delete(int(pk))
            await session.commit()
    can_delete = True


class ProjectAdmin(ModelView, model=Project):
    """项目管理后台视图。"""

    name = "项目"
    name_plural = "项目管理"
    icon = "fa-solid fa-folder"
    column_labels = {
        Project.id: "编号",
        Project.title: "项目名称",
        Project.description: "简短描述",
        Project.content: "项目内容",
        Project.content_style: "内容样式",
        Project.status: "状态",
        Project.cover_image: "封面图",
        Project.attachments: "附件列表",
        Project.extra_data: "扩展信息",
        Project.created_at: "创建时间",
        Project.updated_at: "更新时间",
    }
    column_list = [
        Project.id, Project.title, Project.description,
        Project.status, Project.created_at, Project.updated_at,
    ]
    column_searchable_list = [Project.title, Project.description]
    column_sortable_list = [Project.id, Project.created_at, Project.updated_at]
    column_default_sort = (Project.updated_at, True)
    column_formatters = {
        Project.title: lambda m, a: Markup(
            '<a href="/admin-tools/project-editor/{0}" class="font-medium text-primary-600 hover:text-primary-800">编辑项目：{1}</a>'.format(
                m.id, escape(m.title)
            )
        ),
        Project.status: lambda m, a: {"active": "✅ 进行中", "draft": "📝 草稿", "archived": "📁 已归档"}.get(m.status, m.status),
    }
    column_details_list = [
        Project.id, Project.title, Project.description, Project.content,
        Project.content_style, Project.status, Project.cover_image,
        Project.attachments, Project.extra_data,
        Project.created_at, Project.updated_at,
    ]
    form_excluded_columns = {
        Project.created_at, Project.updated_at,
    }
    form_args = {
        "title": {"label": "项目名称", "description": "请输入项目名称"},
        "description": {"label": "简短描述", "description": "项目的简短描述"},
        "content": {"label": "项目内容", "description": "支持 HTML 富文本内容"},
        "content_style": {"label": "内容样式", "description": "JSON 格式的样式配置"},
        "cover_image": {"label": "封面图", "description": "封面图片的 URL 地址"},
        "attachments": {"label": "附件列表", "description": "JSON 格式的附件列表"},
        "extra_data": {"label": "扩展信息", "description": "JSON 格式的附加信息"},
        "status": {
            "label": "状态",
            "description": "active=进行中, draft=草稿, archived=已归档",
            "default": True,
        },
    }
    form_overrides = {
        "status": BooleanField,
    }

    async def get_form_data_for_edit(self, obj):
        """将数据库状态转换为表单状态。"""
        data = await super().get_form_data_for_edit(obj)
        data["status"] = obj.status == "active"
        return data

    async def on_model_change(self, data, model, is_created, request):
        """将表单状态转换为数据库状态。"""
        data["status"] = "active" if data.get("status") else "draft"



    async def delete_model(self, request, pk):
        """重写删除方法，使用软删除。"""
        from app.services.project_service import ProjectService
        from app.database import async_session
        async with async_session() as session:
            service = ProjectService(session)
            await service.delete(int(pk))
            await session.commit()
    can_delete = True

    def list_query(self, request):
        """过滤已删除的项目。"""
        return super().list_query(request).where(Project.is_deleted == False)