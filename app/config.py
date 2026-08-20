# -*- coding: utf-8 -*-
"""应用配置。

环境变量（通过 .env 或系统环境变量）：
  DATABASE_URL    数据库连接字符串（默认 SQLite，生产用 MySQL）
  UPLOAD_DIR      上传文件根目录
  BASE_URL        站点基础 URL（生成二维码内容用 /l/{code} 前缀）
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（config.py 所在目录的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent


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
    # 开发用 SQLite；生产用 MySQL：
    #   mysql+asyncmy://user:password@localhost:3306/livecode_db
    DATABASE_URL: str = (
        f"sqlite+aiosqlite:///{(BASE_DIR / 'data' / 'livecode.db').as_posix()}"
    )

    # --- 上传 ---
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    IMAGE_DIR: Path = BASE_DIR / "uploads" / "images"
    LOGO_DIR: Path = BASE_DIR / "uploads" / "logo"
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp", "image/gif"}

    # --- 站点 ---
    # 扫码跳转时生成的二维码内容为 {BASE_URL}/l/{code}
    BASE_URL: str = "http://localhost:8000"

    # --- 二维码默认配置 ---
    QR_DEFAULT_SIZE: str = "medium"
    QR_SIZES: dict[str, int] = {"small": 200, "medium": 400, "large": 600}

    # --- 活码 ---
    LIVE_CODE_LENGTH: int = 8

    # 上传目录自动创建
    def ensure_dirs(self) -> None:
        try:
            self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            self.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            self.LOGO_DIR.mkdir(parents=True, exist_ok=True)
            (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
        except OSError:
            pass


settings = Settings()
settings.ensure_dirs()