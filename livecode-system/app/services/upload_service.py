# -*- coding: utf-8 -*-
"""图片上传服务（支持本地存储和 Cloudflare R2）。"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


class UploadService:
    """图片上传处理。"""

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    @classmethod
    async def save_image(cls, file: UploadFile) -> str:
        """上传图片，返回 URL。"""
        # 校验文件类型
        ext = Path(file.filename or "").suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(f"不支持的图片格式：{ext}，仅支持 {cls.ALLOWED_EXTENSIONS}")

        content = await file.read()
        if len(content) > settings.MAX_IMAGE_SIZE:
            raise ValueError(f"图片过大（最大 {settings.MAX_IMAGE_SIZE // 1024 // 1024}MB）")

        filename = f"{uuid.uuid4().hex}{ext}"

        if settings.STORAGE_BACKEND == "r2":
            return await cls._save_r2(filename, content)
        return cls._save_local(filename, content)

    @classmethod
    def _save_local(cls, filename: str, content: bytes) -> str:
        """本地存储。"""
        dest = settings.IMAGE_DIR / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        return f"/uploads/images/{filename}"

    @classmethod
    async def _save_r2(cls, filename: str, content: bytes) -> str:
        """Cloudflare R2 存储。"""
        import boto3

        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        key = f"images/{filename}"
        s3.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType=f"image/{filename.rsplit('.', 1)[-1]}",
        )
        # 返回公网 URL
        public_url = settings.R2_PUBLIC_URL.rstrip("/")
        return f"{public_url}/{key}"

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
        if settings.STORAGE_BACKEND == "r2":
            url = await cls._save_r2_file(stored_name, content, file.content_type)
        else:
            dest = settings.UPLOAD_DIR / "files" / stored_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            url = f"/uploads/files/{stored_name}"
        return {
            "name": filename,
            "url": url,
            "size": len(content),
        }

    @classmethod
    async def _save_r2_file(
        cls,
        filename: str,
        content: bytes,
        content_type: str | None,
    ) -> str:
        """将附件保存到 Cloudflare R2 并返回公网地址。"""
        import boto3

        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        key = f"files/{filename}"
        s3.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType=content_type or "application/octet-stream",
        )
        return f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"