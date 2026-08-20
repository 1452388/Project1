# -*- coding: utf-8 -*-
"""图片上传服务（本地存储）。"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


class UploadService:
    """图片上传处理。"""

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    @classmethod
    async def save_image(cls, file: UploadFile) -> str:
        """上传图片，返回相对路径（如 /uploads/images/uuid.jpg）。"""
        # 校验文件类型
        ext = Path(file.filename or "").suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(f"不支持的图片格式：{ext}，仅支持 {cls.ALLOWED_EXTENSIONS}")

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}{ext}"
        dest = settings.IMAGE_DIR / filename

        # 写入文件
        content = await file.read()
        if len(content) > settings.MAX_IMAGE_SIZE:
            raise ValueError(f"图片过大（最大 {settings.MAX_IMAGE_SIZE // 1024 // 1024}MB）")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

        return f"/uploads/images/{filename}"

    @classmethod
    async def save_file(cls, file: UploadFile) -> dict:
        """保存项目附件，返回文件名、地址和大小。"""
        filename = Path(file.filename or "未命名文件").name
        if not filename:
            raise ValueError("文件名不能为空")
        content = await file.read()
        max_size = getattr(settings, "MAX_FILE_SIZE", 50 * 1024 * 1024)
        if len(content) > max_size:
            raise ValueError(f"文件过大（最大 {max_size // 1024 // 1024}MB）")

        stored_name = f"{uuid.uuid4().hex}_{filename}"
        dest = settings.UPLOAD_DIR / "files" / stored_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

        return {
            "name": filename,
            "url": f"/uploads/files/{stored_name}",
            "size": len(content),
        }