# -*- coding: utf-8 -*-
"""图片上传 API 路由。"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.api.dependencies import require_admin, require_registered_user

from app.services.upload_service import UploadService

router = APIRouter(dependencies=[Depends(require_registered_user)])


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """上传图片，返回 URL。"""
    try:
        url = await UploadService.save_image(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"url": url}


@router.post("/file", dependencies=[Depends(require_admin)])
async def upload_file(file: UploadFile = File(...)):
    """上传项目附件，返回附件信息。"""
    try:
        return await UploadService.save_file(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))