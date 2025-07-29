from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.file import FileService
from app.core.config import settings

router = APIRouter()


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传文件
    """
    if file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过限制")
    
    service = FileService(db)
    file_info = await service.save_file(file)
    
    return {
        "message": "文件上传成功",
        "file_id": file_info.get("file_id"),
        "file_path": file_info.get("file_path")
    }


@router.post("/files")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    批量上传文件
    """
    service = FileService(db)
    uploaded_files = []
    
    for file in files:
        if file.size > settings.MAX_UPLOAD_SIZE:
            continue
        
        file_info = await service.save_file(file)
        uploaded_files.append(file_info)
    
    return {
        "message": f"成功上传 {len(uploaded_files)} 个文件",
        "files": uploaded_files
    }


@router.get("/files/{file_id}")
async def get_file_info(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文件信息
    """
    service = FileService(db)
    file_info = service.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    return file_info