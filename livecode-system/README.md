# 活码管理系统

一个可编辑内容的二维码（活码）管理系统，使用 FastAPI + Tailwind CSS 构建。

## 访问地址

- **首页**：http://localhost:8000
- **管理后台**：http://localhost:8000/admin
- **API 文档**：http://localhost:8000/docs
- **扫码演示**：http://localhost:8000/l/BNnSmWkL

## 功能特性

### 已完成 ✅

| 功能 | 说明 |
|------|------|
| 文章管理 | 创建/编辑/删除文章，支持富文本和图片 |
| 活码管理 | 为文章生成活码，支持启用/停用/删除 |
| 二维码生成 | 支持尺寸选择、Logo嵌入、边框文字 |
| 扫码跳转 | 固定二维码，内容随时可改 |
| 数据统计 | 扫码总量、按天趋势、Excel导出 |
| 图片上传 | 支持JPG/PNG/WebP，本地存储 |
| 批量生成 | 多活码批量生成ZIP |
| 管理后台 | SQLAdmin + Tailwind现代化界面，支持人员信息编辑和删除 |

### 待实现

| 功能 | 优先级 |
|------|--------|
| 文章列表管理页面 | 中 |
| 统计图表页面 | 中 |
| 批量生成二维码页面 | 低 |
| 单元测试 | 低 |
| 多用户登录 | 后续 |

## 快速开始

```bash
# 进入项目目录
cd F:\TJ Petroleum\livecode-system

# 激活虚拟环境
.venv\Scripts\activate

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 项目结构

```
livecode-system/
├── app/
│   ├── api/          # API路由 (articles, live_codes, qr, stats, upload)
│   ├── models/       # SQLAlchemy模型 (Article, LiveCode, ScanLog, User)
│   ├── services/     # 业务逻辑层
│   ├── templates/    # Jinja2模板
│   └── static/       # 静态文件
├── data/             # SQLite数据库
├── uploads/          # 上传文件
└── test/             # 测试代码
```

## 技术栈

- **后端**：FastAPI + SQLAlchemy (async)
- **数据库**：SQLite（第一版）/ PostgreSQL（可升级）
- **前端**：Tailwind CSS + HTMX + Quill
- **后台管理**：SQLAdmin
- **二维码**：qrcode + Pillow

## 项目统计

- 28 个 Python 文件
- 6 个 HTML 模板
- 10 个核心 API 端点已验证通过

## 后续扩展提醒

1. 多用户登录 + 权限角色
2. 前后端分离升级（Vue/React）
3. 文件上传下载插件
4. 地图插件
5. 二维码颜色自定义
6. 设备/来源/地域分析
7. 公网部署

## 开发说明

- 数据库：SQLite 单文件，切换 PostgreSQL 只需修改 `config.py` 中的 DATABASE_URL
- 模型扩展：文章和活码都支持 `extra_fields` JSON 字段，方便后续插件扩展
- 图片存储：本地 `uploads/images/`，后续可改为 OSS/S3

---

> 当前版本：v1.0.0
> 数据库：SQLite（data/livecode.db）
> 最后更新：2026-08-18