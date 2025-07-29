import os
import uuid
from typing import Dict, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings


class FileService:
    def __init__(self, db: Session):
        self.db = db

    async def save_file(self, file: UploadFile) -> Dict[str, str]:
        """保存上传的文件"""
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1]
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_extension}"
        
        # 确保上传目录存在
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "file_path": file_path,
            "size": len(content)
        }

    def get_file_info(self, file_id: str) -> Optional[Dict[str, str]]:
        """获取文件信息"""
        # 这里应该从数据库查询文件信息
        # 暂时返回简单的文件路径信息
        file_path = None
        for ext in [".jpg", ".png", ".pdf", ".docx"]:
            potential_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
            if os.path.exists(potential_path):
                file_path = potential_path
                break
        
        if not file_path:
            return None
        
        return {
            "file_id": file_id,
            "file_path": file_path,
            "size": os.path.getsize(file_path)
        }

    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        file_info = self.get_file_info(file_id)
        if not file_info:
            return False
        
        try:
            os.remove(file_info["file_path"])
            return True
        except OSError:
            return False