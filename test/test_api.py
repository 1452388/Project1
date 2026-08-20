# -*- coding: utf-8 -*-
"""项目管理 API 测试（带认证）。"""

import pytest
import httpx
from httpx import ASGITransport

from app.main import app

_transport = ASGITransport(app=app)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client():
    """登录后的测试客户端，session 级别不关闭。"""
    c = httpx.AsyncClient(transport=_transport, base_url="http://test")
    # 注册
    await c.post("/api/v1/auth/register", json={
        "username": "testuser", "password": "admin123",
    })
    # 登录
    await c.post("/api/v1/auth/login", json={
        "username": "testuser", "password": "admin123",
    })
    return c


# ===== 人员管理 =====


@pytest.mark.anyio
async def test_create_member(client):
    resp = await client.post("/api/v1/team", json={
        "name": "张三", "position": "工程师", "department": "技术部",
        "email": "zhangsan@example.com", "phone": "13800000001", "wechat": "wx001",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["姓名"] == "张三"
    assert data["职位"] == "工程师"
    assert data["状态"] == "active"


@pytest.mark.anyio
async def test_list_members(client):
    resp = await client.get("/api/v1/team")
    assert resp.status_code == 200
    assert "列表" in resp.json()


@pytest.mark.anyio
async def test_update_member(client):
    r1 = await client.post("/api/v1/team", json={"name": "原名"})
    mid = r1.json()["会员编号"]
    r2 = await client.put(f"/api/v1/team/{mid}", json={"name": "新名"})
    assert r2.status_code == 200
    assert r2.json()["姓名"] == "新名"


@pytest.mark.anyio
async def test_toggle_status(client):
    r1 = await client.post("/api/v1/team", json={"name": "状态测试"})
    mid = r1.json()["会员编号"]
    r2 = await client.post(f"/api/v1/team/{mid}/toggle-status")
    assert r2.json()["状态"] == "inactive"
    r3 = await client.post(f"/api/v1/team/{mid}/toggle-status")
    assert r3.json()["状态"] == "active"


@pytest.mark.anyio
async def test_delete_member(client):
    r1 = await client.post("/api/v1/team", json={"name": "删除测试"})
    mid = r1.json()["会员编号"]
    r2 = await client.delete(f"/api/v1/team/{mid}")
    assert r2.status_code == 200
    r3 = await client.get(f"/api/v1/team/{mid}")
    assert r3.status_code == 404


# ===== 项目管理 =====


@pytest.mark.anyio
async def test_create_project(client):
    resp = await client.post("/api/v1/projects", json={
        "title": "测试项目", "description": "项目描述", "status": "draft",
    })
    assert resp.status_code == 200
    assert resp.json()["项目名称"] == "测试项目"


@pytest.mark.anyio
async def test_list_projects(client):
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    assert "列表" in resp.json()


@pytest.mark.anyio
async def test_update_project(client):
    r1 = await client.post("/api/v1/projects", json={"title": "原名"})
    pid = r1.json()["项目编号"]
    r2 = await client.put(f"/api/v1/projects/{pid}", json={"title": "新名"})
    assert r2.status_code == 200
    assert r2.json()["项目名称"] == "新名"


@pytest.mark.anyio
async def test_delete_project(client):
    r1 = await client.post("/api/v1/projects", json={"title": "删除测试"})
    pid = r1.json()["项目编号"]
    r2 = await client.delete(f"/api/v1/projects/{pid}")
    assert r2.status_code == 200
    r3 = await client.get(f"/api/v1/projects/{pid}")
    assert r3.status_code == 404
