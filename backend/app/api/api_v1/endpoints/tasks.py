from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import mimetypes

from app.core.database import get_db
from app.services.task import TaskService
from app.core.config import settings

router = APIRouter()


@router.post("/upload")
async def upload_image_and_create_task(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传图片并创建处理任务
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只支持图片文件")
    
    # 验证文件大小
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过限制")
    
    # 验证文件格式
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 JPG、PNG 格式的图片")
    
    service = TaskService(db)
    result = await service.create_task_from_upload(file)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result["message"])


@router.post("/upload/batch")
async def upload_images_and_create_tasks(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    批量上传图片并创建处理任务
    """
    service = TaskService(db)
    results = []
    
    for file in files:
        # 跳过无效文件
        if not file.content_type or not file.content_type.startswith('image/'):
            results.append({
                "success": False,
                "message": f"文件 {file.filename} 不是有效的图片格式",
                "filename": file.filename
            })
            continue
            
        if file.size and file.size > settings.MAX_UPLOAD_SIZE:
            results.append({
                "success": False,
                "message": f"文件 {file.filename} 大小超过限制",
                "filename": file.filename
            })
            continue
        
        # 处理有效文件
        result = await service.create_task_from_upload(file)
        result["filename"] = file.filename
        results.append(result)
    
    success_count = len([r for r in results if r["success"]])
    total_count = len(results)
    
    return {
        "success": success_count > 0,
        "message": f"成功处理 {success_count}/{total_count} 个文件",
        "results": results
    }


@router.get("/{task_id}")
async def get_task_detail(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取任务详情
    """
    service = TaskService(db)
    task = service.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "success": True,
        "data": {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "status": task.status.value,
            "progress": task.progress_percentage,
            "image_url": task.image_url,
            "qr_code": task.qr_code,
            "tracking_number": task.tracking_number,
            "courier_company": task.courier_company,
            "delivery_status": task.delivery_status,
            "delivery_time": task.delivery_time.isoformat() if task.delivery_time else None,
            "tracking_data": task.tracking_data,
            "document_url": task.document_url,
            "screenshot_url": task.screenshot_url,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "processing_time": task.processing_time
        }
    }


@router.get("/")
async def get_task_list(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    获取任务列表
    """
    service = TaskService(db)
    tasks = service.get_all_tasks(limit=limit, offset=offset)
    
    task_list = []
    for task in tasks:
        # 状态过滤
        if status and task.status.value != status:
            continue
            
        task_list.append({
            "task_id": task.task_id,
            "task_name": task.task_name,
            "status": task.status.value,
            "progress": task.progress_percentage,
            "image_url": task.image_url,
            "qr_code": task.qr_code,
            "tracking_number": task.tracking_number,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        })
    
    return {
        "success": True,
        "data": {
            "items": task_list,
            "total": len(task_list),
            "limit": limit,
            "offset": offset
        }
    }


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    task_name: Optional[str] = None,
    remarks: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    更新任务信息
    """
    service = TaskService(db)
    task = service.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新字段
    if task_name is not None:
        task.task_name = task_name
    if remarks is not None:
        task.remarks = remarks
    
    service.db.commit()
    
    return {
        "success": True,
        "message": "任务更新成功",
        "data": {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "status": task.status.value
        }
    }


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    重试失败的任务
    """
    service = TaskService(db)
    success = service.retry_task(task_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="任务无法重试或不存在")
    
    return {
        "success": True,
        "message": "任务重试成功"
    }


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    删除任务
    """
    service = TaskService(db)
    success = service.delete_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "success": True,
        "message": "任务删除成功"
    }


@router.get("/stats/summary")
async def get_task_statistics(
    db: Session = Depends(get_db)
):
    """
    获取任务统计信息
    """
    service = TaskService(db)
    stats = service.get_task_statistics()
    
    return {
        "success": True,
        "data": stats
    }