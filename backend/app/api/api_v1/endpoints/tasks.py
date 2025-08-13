from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import mimetypes
import zipfile
import os
import tempfile
from datetime import datetime

from app.core.database import get_db
from app.services.task import TaskService
from app.core.config import settings
from app.models.task import TaskStatusEnum
from app.api.api_v1.endpoints.auth import get_admin_user
from app.models.user import User

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


@router.post("/batch-upload")
async def batch_upload_images_and_create_tasks(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    批量上传图片并创建处理任务（改进版）
    支持最多20个文件，并行处理，错误隔离
    """
    # 验证文件数量
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="最多支持同时上传20个文件")
    
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="请至少选择一个文件")
    
    service = TaskService(db)
    
    # 预验证所有文件
    validated_files = []
    validation_errors = []
    
    for i, file in enumerate(files):
        try:
            # 验证文件类型
            if not file.content_type or not file.content_type.startswith('image/'):
                validation_errors.append({
                    "index": i,
                    "filename": file.filename,
                    "error": "不是有效的图片格式"
                })
                continue
            
            # 验证文件大小
            if file.size and file.size > settings.MAX_UPLOAD_SIZE:
                validation_errors.append({
                    "index": i,
                    "filename": file.filename,
                    "error": f"文件大小超过限制({settings.MAX_UPLOAD_SIZE} bytes)"
                })
                continue
            
            # 验证文件格式
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
            if file.content_type not in allowed_types:
                validation_errors.append({
                    "index": i,
                    "filename": file.filename,
                    "error": "只支持 JPG、PNG 格式的图片"
                })
                continue
                
            # 在主线程中读取文件内容
            content = await file.read()
            file.file.seek(0)  # 重置文件指针，以防后续需要
            
            validated_files.append({
                "index": i,
                "filename": file.filename,
                "size": file.size,
                "content_type": file.content_type,
                "content": content  # 添加文件内容
            })
            
        except Exception as e:
            validation_errors.append({
                "index": i,
                "filename": file.filename,
                "error": f"文件验证失败: {str(e)}"
            })
    
    # 如果没有有效文件，返回错误
    if not validated_files:
        return {
            "success": False,
            "message": "没有有效的文件可以处理",
            "batch_id": None,
            "validation_errors": validation_errors,
            "tasks": []
        }
    
    # 批量创建任务
    batch_result = await service.batch_create_tasks_from_uploads(validated_files)
    
    return {
        "success": batch_result["success"],
        "message": batch_result["message"],
        "batch_id": batch_result.get("batch_id"),
        "validation_errors": validation_errors,
        "tasks": batch_result["tasks"],
        "summary": {
            "total_files": len(files),
            "valid_files": len(validated_files),
            "invalid_files": len(validation_errors),
            "created_tasks": len([t for t in batch_result["tasks"] if t["success"]])
        }
    }


@router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取任务状态（轻量级，用于前端轮询）
    """
    service = TaskService(db)
    task = service.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 计算处理进度
    progress_percentage = 0
    if task.status == TaskStatusEnum.PENDING:
        progress_percentage = 10
    elif task.status == TaskStatusEnum.RECOGNIZING:
        progress_percentage = 30
    elif task.status == TaskStatusEnum.TRACKING:
        progress_percentage = 50
    elif task.status == TaskStatusEnum.DELIVERED:
        progress_percentage = 70
    elif task.status == TaskStatusEnum.GENERATING:
        progress_percentage = 90
    elif task.status == TaskStatusEnum.COMPLETED:
        progress_percentage = 100
    elif task.status == TaskStatusEnum.FAILED:
        progress_percentage = task.progress_percentage or 0
    
    # 状态描述
    status_messages = {
        "PENDING": "任务已创建，等待处理",
        "RECOGNIZING": "正在识别二维码...",
        "TRACKING": "正在查询物流信息...",
        "DELIVERED": "快递已签收，正在生成文档...",
        "GENERATING": "正在生成送达回证...",
        "COMPLETED": "任务处理完成",
        "FAILED": f"处理失败: {task.error_message}" if task.error_message else "处理失败"
    }
    
    return {
        "success": True,
        "data": {
            "task_id": task.task_id,
            "status": task.status.value,
            "status_message": status_messages.get(task.status.value, "未知状态"),
            "progress": progress_percentage,
            "is_processing": task.status.value in ["RECOGNIZING", "TRACKING", "GENERATING"],
            "is_completed": task.status.value == "COMPLETED",
            "has_error": task.status.value == "FAILED",
            "error_message": task.error_message,
            "tracking_number": task.tracking_number,
            "courier_company": task.courier_company,
            "document_url": task.document_url if task.status.value == "COMPLETED" else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None
        }
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
    
    # 计算处理进度百分比
    progress_percentage = 0
    if task.status == TaskStatusEnum.PENDING:
        progress_percentage = 10
    elif task.status == TaskStatusEnum.RECOGNIZING:
        progress_percentage = 30
    elif task.status == TaskStatusEnum.TRACKING:
        progress_percentage = 50
    elif task.status == TaskStatusEnum.DELIVERED:
        progress_percentage = 70
    elif task.status == TaskStatusEnum.GENERATING:
        progress_percentage = 90
    elif task.status == TaskStatusEnum.COMPLETED:
        progress_percentage = 100
    elif task.status == TaskStatusEnum.FAILED:
        progress_percentage = task.progress_percentage or 0
    
    # 生成状态描述
    status_messages = {
        "PENDING": "任务已创建，等待处理",
        "RECOGNIZING": "正在识别二维码...",
        "TRACKING": "正在查询物流信息...",
        "DELIVERED": "快递已签收，正在生成文档...",
        "GENERATING": "正在生成送达回证...",
        "COMPLETED": "任务处理完成",
        "FAILED": f"处理失败: {task.error_message}" if task.error_message else "处理失败"
    }
    
    return {
        "success": True,
        "data": {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "status": task.status.value,
            "status_message": status_messages.get(task.status.value, "未知状态"),
            "progress": progress_percentage,
            "image_url": task.image_url,
            "qr_code": task.qr_code,
            "tracking_number": task.tracking_number,
            "courier_company": task.courier_company,
            "delivery_status": task.delivery_status,
            "delivery_time": task.delivery_time.isoformat() if task.delivery_time else None,
            "tracking_data": task.tracking_data,
            "document_url": task.document_url,
            "screenshot_url": task.screenshot_url,
            "extra_metadata": task.extra_metadata,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "processing_time": task.processing_time,
            "is_processing": task.status.value in ["RECOGNIZING", "TRACKING", "GENERATING"]
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
    
    # 过滤空状态参数
    status_filter = status.strip() if status and status.strip() else None
    
    # 在数据库查询层面进行过滤，而不是在Python层面
    tasks = service.get_all_tasks(limit=limit, offset=offset, status_filter=status_filter)
    
    def parse_doc_title(doc_title):
        """解析doc_title，提取文书类型和案号"""
        if not doc_title:
            return None, None
            
        lines = doc_title.strip().split('\n')
        if len(lines) >= 2:
            # 第一行：行政复议+文书类型
            first_line = lines[0].strip()
            if first_line.startswith('行政复议'):
                document_type = first_line[4:]  # 去掉"行政复议"前缀
            else:
                document_type = first_line
                
            # 第二行：案号
            case_number = lines[1].strip()
            return document_type, case_number
        elif len(lines) == 1:
            # 只有一行，尝试解析
            line = lines[0].strip()
            if line.startswith('行政复议'):
                document_type = line[4:]
                return document_type, None
            else:
                return line, None
        
        return None, None
    
    task_list = []
    for task in tasks:
        # 解析doc_title
        document_type, case_number = parse_doc_title(getattr(task, 'delivery_doc_title', None))
        
        task_list.append({
            "task_id": task.task_id,
            "task_name": task.task_name,
            "status": task.status.value,
            "progress": task.progress_percentage,
            "image_url": task.image_url,
            "qr_code": task.qr_code,
            "tracking_number": task.tracking_number,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            # 新增的delivery receipt信息
            "document_type": document_type,
            "case_number": case_number,
            "receiver": getattr(task, 'delivery_receiver', None)
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
    
    # 让FastAPI的依赖注入系统自动提交事务
    
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


@router.post("/{task_id}/check-progress")
async def check_task_progress(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    检查并更新任务进度
    """
    service = TaskService(db)
    updated = await service.check_and_update_task_progress(task_id)
    
    if updated:
        return {
            "success": True,
            "message": "任务进度已更新"
        }
    else:
        return {
            "success": True,
            "message": "任务进度无需更新"
        }


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    删除任务（仅管理员）
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        admin_user: 管理员用户（自动验证权限）
    
    Returns:
        删除结果
    """
    service = TaskService(db)
    success = service.delete_task(task_id, admin_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在或删除失败")
    
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


@router.post("/batch-status")
async def get_batch_task_status(
    task_ids: List[str],
    db: Session = Depends(get_db)
):
    """
    批量获取任务状态
    """
    if len(task_ids) > 50:
        raise HTTPException(status_code=400, detail="一次最多查询50个任务状态")
    
    service = TaskService(db)
    results = []
    
    for task_id in task_ids:
        task = service.get_task_by_id(task_id)
        if task:
            # 计算进度
            progress = service._calculate_progress(task.status)
            
            results.append({
                "task_id": task.task_id,
                "status": task.status.value,
                "progress": progress,
                "message": service._get_status_message(task.status),
                "error_message": task.error_message,
                "tracking_number": task.tracking_number,
                "document_url": task.document_url,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            })
        else:
            results.append({
                "task_id": task_id,
                "status": "not_found",
                "progress": 0,
                "message": "任务不存在",
                "error_message": "任务不存在"
            })
    
    # 统计各状态数量
    status_counts = {}
    for result in results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "success": True,
        "data": {
            "tasks": results,
            "summary": {
                "total": len(results),
                "status_counts": status_counts,
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
                "processing": sum(status_counts.get(s, 0) for s in ["pending", "recognizing", "tracking", "generating"])
            }
        }
    }


@router.post("/batch-download")
async def batch_download_tasks(
    task_ids: List[str],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量下载任务文件，打包为ZIP
    """
    if len(task_ids) > 20:
        raise HTTPException(status_code=400, detail="一次最多下载20个任务的文件")
    
    service = TaskService(db)
    
    # 获取任务并验证
    tasks = []
    for task_id in task_ids:
        task = service.get_task_by_id(task_id)
        if task and task.status == TaskStatusEnum.COMPLETED:
            tasks.append(task)
    
    if not tasks:
        raise HTTPException(status_code=400, detail="没有可下载的已完成任务")
    
    # 创建临时ZIP文件
    temp_dir = tempfile.mkdtemp()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"batch_download_{timestamp}.zip"
    zip_path = os.path.join(temp_dir, zip_filename)
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for task in tasks:
                task_folder = f"task_{task.task_id}_{task.tracking_number or 'unknown'}"
                
                # 添加任务信息文件
                task_info = f"""任务信息
任务ID: {task.task_id}
快递单号: {task.tracking_number or '未知'}
创建时间: {task.created_at}
完成时间: {task.completed_at}
状态: {task.status.value}
"""
                zipf.writestr(f"{task_folder}/task_info.txt", task_info.encode('utf-8'))
                
                # 添加原图
                if task.image_path and os.path.exists(task.image_path):
                    zipf.write(
                        task.image_path,
                        f"{task_folder}/original_image{os.path.splitext(task.image_path)[1]}"
                    )
                
                # 添加送达回证
                if task.document_path and os.path.exists(task.document_path):
                    zipf.write(
                        task.document_path,
                        f"{task_folder}/delivery_receipt.docx"
                    )
                
                # 添加物流截图
                if task.screenshot_path and os.path.exists(task.screenshot_path):
                    zipf.write(
                        task.screenshot_path,
                        f"{task_folder}/tracking_screenshot.png"
                    )
                
                # 添加二维码标签
                if task.extra_metadata and task.extra_metadata.get("qr_label_path"):
                    qr_label_path = task.extra_metadata["qr_label_path"]
                    if os.path.exists(qr_label_path):
                        zipf.write(
                            qr_label_path,
                            f"{task_folder}/qr_label.png"
                        )
        
        # 添加清理任务
        def cleanup_temp_file():
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                print(f"清理临时文件失败: {e}")
        
        background_tasks.add_task(cleanup_temp_file)
        
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type='application/zip',
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        # 清理临时文件
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"创建ZIP文件失败: {str(e)}")


@router.get("/batch/{batch_id}/status")
async def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    获取批量任务的整体状态
    """
    service = TaskService(db)
    batch_status = await service.get_batch_status(batch_id)
    
    if not batch_status:
        raise HTTPException(status_code=404, detail="批量任务不存在")
    
    return {
        "success": True,
        "data": batch_status
    }