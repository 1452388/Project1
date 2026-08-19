# -*- coding: utf-8 -*-
"""应用配置。

环境变量（通过 .env 或系统环境变量）：
  DATABASE_URL    数据库连接字符串（默认 SQLite）
  STORAGE_BACKEND 存储后端：local / r2
  UPLOAD_DIR      上传文件根目录（local 模式）
  BASE_URL        站点基础 URL（生成二维码内容用 /l/{code} 前缀）
"""

import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（config.py 所在目录的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent

# 判断是否在 Vercel 等只读环境
IS_SERVERLESS = os.environ.get("VERCEL", "") != ""


def normalize_database_url(value: str) -> tuple[str, bool]:
    """兼容 Neon/Supabase 提供的 PostgreSQL 连接串。"""
    if value.startswith("postgres://"):
        value = "postgresql+asyncpg://" + value[len("postgres://"):]
    elif value.startswith("postgresql://"):
        value = "postgresql+asyncpg://" + value[len("postgresql://"):]

    parts = urlsplit(value)
    if parts.scheme != "postgresql+asyncpg":
        return value, False

    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    sslmode = query.pop("sslmode", "")
    query.pop("channel_binding", None)
    normalized = urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(query),
        parts.fragment,
    ))
    return normalized, sslmode not in ("", "disable", "allow", "prefer")


class Settings(BaseSettings):
    """应用配置。"""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    # --- 应用 ---
    APP_NAME: str = "活码管理系统"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key-in-production"
    GITHUB_REPOSITORY_URL: str = "https://github.com/1452388/Project1"
    SUPPORT_EMAIL: str = "xich19003@gmail.com"

    # --- 数据库 ---
    DATABASE_URL: str = (
        f"sqlite+aiosqlite:///{(BASE_DIR / 'data' / 'livecode.db').as_posix()}"
    )
    DATABASE_SSL: bool = False

    # --- 存储后端：local / r2 ---
    STORAGE_BACKEND: str = "local"

    # --- 本地上传（STORAGE_BACKEND=local 时使用）---
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    IMAGE_DIR: Path = BASE_DIR / "uploads" / "images"
    LOGO_DIR: Path = BASE_DIR / "uploads" / "logo"
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp", "image/gif"}

    # --- Cloudflare R2（STORAGE_BACKEND=r2 时使用）---
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""  # 自定义域名，如 https://cdn.example.com

    # --- 站点 ---
    BASE_URL: str = "https://www.hxy820.uno"

    # --- 二维码默认配置 ---
    QR_DEFAULT_SIZE: str = "medium"
    QR_SIZES: dict[str, int] = {"small": 200, "medium": 400, "large": 600}

    # --- 活码 ---
    LIVE_CODE_LENGTH: int = 8

    # 上传目录自动创建（只读环境下跳过）
    def ensure_dirs(self) -> None:
        if IS_SERVERLESS:
            return
        try:
            self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            self.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            self.LOGO_DIR.mkdir(parents=True, exist_ok=True)
            (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
        except OSError:
            pass  # 只读文件系统，忽略


settings = Settings()
settings.DATABASE_URL, settings.DATABASE_SSL = normalize_database_url(settings.DATABASE_URL)

# Vercel 的项目目录是只读的，SQLite 无法用于生产写入。
if IS_SERVERLESS and settings.DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "生产环境必须配置 PostgreSQL：请设置 DATABASE_URL，"
        "不能在 Vercel 上使用 SQLite。"
    )

settings.ensure_dirs()