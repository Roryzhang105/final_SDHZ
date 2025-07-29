from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import uuid

from app.core.database import get_db
from app.services.qr_recognition import QRRecognitionService
from app.services.file import FileService
from app.core.config import settings

router = APIRouter()


@router.post("/recognize")
async def recognize_qr_code(
    file: UploadFile = File(...),
    save_file: bool = Form(default=False),
    db: Session = Depends(get_db)
):
    """
    识别单张图片中的二维码/条形码
    
    Args:
        file: 上传的图片文件
        save_file: 是否保存上传的文件到服务器
        db: 数据库会话
    
    Returns:
        识别结果，包含二维码内容、快递单号等信息
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    
    # 验证文件大小
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过限制")
    
    # 创建临时文件保存上传的图片
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    temp_file_path = None
    saved_file_path = None
    
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 如果需要保存文件，使用FileService保存
        if save_file:
            file_service = FileService(db)
            # 重置文件指针
            file.file.seek(0)
            file_info = await file_service.save_file(file)
            saved_file_path = file_info["file_path"]
        
        # 进行识别
        recognition_service = QRRecognitionService(db)
        result = recognition_service.recognize_single_image(temp_file_path)
        
        # 更新结果中的文件路径信息
        if saved_file_path:
            result["file_path"] = saved_file_path
            result["file_id"] = file_info.get("file_id")
        else:
            result["file_path"] = f"temp_file_{uuid.uuid4().hex}"
            result["file_id"] = None
        
        # 构造返回结果
        response = {
            "success": True,
            "message": "识别完成",
            "data": {
                "file_info": {
                    "filename": file.filename,
                    "size": file.size,
                    "content_type": file.content_type,
                    "saved": save_file,
                    "file_id": result.get("file_id")
                },
                "recognition_result": {
                    "detection_count": result["detection_count"],
                    "recognition_type": result["recognition_type"],
                    "confidence_score": result["confidence_score"],
                    "processing_time": result["processing_time"],
                    "is_success": result["is_success"] == "true"
                },
                "extracted_data": {
                    "tracking_numbers": result["tracking_numbers"],
                    "qr_contents": result["qr_contents"],
                    "barcode_contents": result["barcode_contents"]
                },
                "raw_results": result["raw_results"],
                "metadata": result["extra_metadata"]
            }
        }
        
        if result["error_message"]:
            response["data"]["error_message"] = result["error_message"]
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别过程中发生错误: {str(e)}")
    
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass


@router.post("/recognize-batch")
async def recognize_batch(
    files: List[UploadFile] = File(...),
    task_name: str = Form(...),
    description: str = Form(default=""),
    save_files: bool = Form(default=False),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    批量识别多张图片（异步处理）
    
    Args:
        files: 上传的图片文件列表
        task_name: 任务名称
        description: 任务描述
        save_files: 是否保存上传的文件
        background_tasks: 后台任务
        db: 数据库会话
    
    Returns:
        任务信息，可通过task_id查询处理进度和结果
    """
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个文件")
    
    if len(files) > 50:  # 限制批量处理文件数量
        raise HTTPException(status_code=400, detail="批量处理文件数量不能超过50个")
    
    # 验证所有文件
    for file in files:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail=f"文件 {file.filename} 不是图片格式"
            )
        
        if file.size and file.size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"文件 {file.filename} 大小超过限制"
            )
    
    try:
        # 创建识别任务
        recognition_service = QRRecognitionService(db)
        task = recognition_service.create_recognition_task(
            task_name=task_name,
            description=description
        )
        
        # 准备文件信息列表
        file_infos = []
        file_service = FileService(db) if save_files else None
        
        for file in files:
            file_info = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size
            }
            
            # 如果需要保存文件
            if save_files and file_service:
                saved_info = await file_service.save_file(file)
                file_info.update(saved_info)
            else:
                # 保存到临时目录供后台任务处理
                file_extension = os.path.splitext(file.filename)[1].lower()
                temp_filename = f"{uuid.uuid4().hex}{file_extension}"
                temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, temp_filename)
                
                content = await file.read()
                with open(temp_path, "wb") as f:
                    f.write(content)
                
                file_info["file_path"] = temp_path
                file_info["is_temp"] = True
            
            file_infos.append(file_info)
        
        # 添加后台任务进行批量识别
        from app.tasks.recognition_tasks import process_batch_recognition
        background_tasks.add_task(
            process_batch_recognition, 
            task.id, 
            file_infos, 
            save_files
        )
        
        return {
            "success": True,
            "message": "批量识别任务已创建，正在后台处理",
            "data": {
                "task_id": task.id,
                "task_name": task.task_name,
                "description": task.description,
                "total_files": len(file_infos),
                "status": task.status.value,
                "created_at": task.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建批量识别任务失败: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task_info(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取识别任务信息和统计
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        任务详细信息和处理统计
    """
    recognition_service = QRRecognitionService(db)
    stats = recognition_service.get_task_stats(task_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/tasks/{task_id}/results")
async def get_task_results(
    task_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取识别任务的详细结果
    
    Args:
        task_id: 任务ID
        skip: 跳过记录数
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        识别结果列表
    """
    recognition_service = QRRecognitionService(db)
    results = recognition_service.get_task_results(task_id, skip, limit)
    
    if not results and skip == 0:
        # 检查任务是否存在
        stats = recognition_service.get_task_stats(task_id)
        if not stats:
            raise HTTPException(status_code=404, detail="任务不存在")
    
    result_data = []
    for result in results:
        result_item = {
            "id": result.id,
            "file_name": result.file_name,
            "file_size": result.file_size,
            "recognition_type": result.recognition_type.value,
            "detection_count": result.detection_count,
            "confidence_score": result.confidence_score,
            "is_success": result.is_success == "true",
            "processing_time": result.processing_time,
            "tracking_numbers": result.tracking_numbers,
            "qr_contents": result.qr_contents,
            "barcode_contents": result.barcode_contents,
            "raw_results": result.raw_results,
            "created_at": result.created_at.isoformat()
        }
        
        if result.error_message:
            result_item["error_message"] = result.error_message
            
        result_data.append(result_item)
    
    return {
        "success": True,
        "data": {
            "results": result_data,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": len(results)
            }
        }
    }


@router.get("/test-image/{image_name}")
async def test_recognition(
    image_name: str,
    db: Session = Depends(get_db)
):
    """
    使用测试图片进行识别测试
    
    Args:
        image_name: 测试图片名称 (如: photo.png, photo2.jpg)
        db: 数据库会话
    
    Returns:
        识别结果
    """
    test_images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "tests")
    image_path = os.path.join(test_images_dir, image_name)
    
    if not os.path.exists(image_path):
        available_images = [f for f in os.listdir(test_images_dir) if f.startswith('photo')]
        raise HTTPException(
            status_code=404, 
            detail=f"测试图片不存在。可用的测试图片: {', '.join(available_images)}"
        )
    
    try:
        recognition_service = QRRecognitionService(db)
        result = recognition_service.recognize_single_image(image_path)
        
        return {
            "success": True,
            "message": f"测试图片 {image_name} 识别完成",
            "data": {
                "file_info": {
                    "filename": image_name,
                    "path": image_path,
                    "size": result["file_size"]
                },
                "recognition_result": {
                    "detection_count": result["detection_count"],
                    "recognition_type": result["recognition_type"],
                    "confidence_score": result["confidence_score"],
                    "processing_time": result["processing_time"],
                    "is_success": result["is_success"] == "true"
                },
                "extracted_data": {
                    "tracking_numbers": result["tracking_numbers"],
                    "qr_contents": result["qr_contents"],
                    "barcode_contents": result["barcode_contents"]
                },
                "raw_results": result["raw_results"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别测试图片失败: {str(e)}")