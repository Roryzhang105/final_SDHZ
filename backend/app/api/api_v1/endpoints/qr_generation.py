from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import uuid

from app.core.database import get_db
from app.services.qr_generation import QRGenerationService
from app.services.qr_recognition import QRRecognitionService
from app.core.config import settings

router = APIRouter()


@router.post("/generate-from-url")
async def generate_from_url(
    url: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    直接基于URL生成二维码条形码标签
    
    Args:
        url: 要生成二维码的URL
        db: 数据库会话
    
    Returns:
        生成结果，包含标签文件路径等信息
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL参数不能为空")
    
    # 验证URL格式
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="无效的URL格式，必须以http://或https://开头")
    
    try:
        generation_service = QRGenerationService(db)
        result = generation_service.generate_qr_barcode_label(url)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "data": result["data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成二维码条形码标签失败: {str(e)}")


@router.post("/generate-from-recognition")
async def generate_from_recognition(
    qr_contents: List[str] = Form(...),
    db: Session = Depends(get_db)
):
    """
    基于识别结果生成二维码条形码标签
    
    Args:
        qr_contents: 二维码识别结果列表，如 ["https://mini.ems.com.cn/youzheng/mini/1151240728560"]
        db: 数据库会话
    
    Returns:
        生成结果，包含标签文件路径等信息
    """
    if not qr_contents or len(qr_contents) == 0:
        raise HTTPException(status_code=400, detail="qr_contents参数不能为空")
    
    try:
        generation_service = QRGenerationService(db)
        result = generation_service.generate_from_recognition_result(qr_contents)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "data": result["data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成二维码条形码标签失败: {str(e)}")


@router.post("/recognize-and-generate")
async def recognize_and_generate(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传图片识别二维码，然后生成新的二维码条形码标签（一站式服务）
    
    Args:
        file: 上传的图片文件
        db: 数据库会话
    
    Returns:
        识别结果和生成结果
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    
    # 验证文件大小
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过限制")
    
    # 验证文件格式
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    temp_file_path = None
    
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 进行二维码识别
        recognition_service = QRRecognitionService(db)
        recognition_result = recognition_service.recognize_single_image(temp_file_path)
        
        # 检查是否识别到二维码
        qr_contents = recognition_result.get("qr_contents", [])
        if not qr_contents or len(qr_contents) == 0:
            return {
                "success": False,
                "message": "未能从上传的图片中识别到二维码内容",
                "data": {
                    "recognition_result": {
                        "detection_count": recognition_result["detection_count"],
                        "recognition_type": recognition_result["recognition_type"],
                        "confidence_score": recognition_result["confidence_score"],
                        "processing_time": recognition_result["processing_time"],
                        "is_success": recognition_result["is_success"] == "true"
                    },
                    "extracted_data": {
                        "tracking_numbers": recognition_result["tracking_numbers"],
                        "qr_contents": qr_contents,
                        "barcode_contents": recognition_result["barcode_contents"]
                    }
                }
            }
        
        # 生成二维码条形码标签
        generation_service = QRGenerationService(db)
        generation_result = generation_service.generate_from_recognition_result(qr_contents)
        
        # 组合返回结果
        response = {
            "success": generation_result["success"],
            "message": "识别和生成完成" if generation_result["success"] else "生成失败",
            "data": {
                "recognition_result": {
                    "detection_count": recognition_result["detection_count"],
                    "recognition_type": recognition_result["recognition_type"],
                    "confidence_score": recognition_result["confidence_score"],
                    "processing_time": recognition_result["processing_time"],
                    "is_success": recognition_result["is_success"] == "true"
                },
                "extracted_data": {
                    "tracking_numbers": recognition_result["tracking_numbers"],
                    "qr_contents": qr_contents,
                    "barcode_contents": recognition_result["barcode_contents"]
                }
            }
        }
        
        if generation_result["success"]:
            response["data"]["generation_result"] = generation_result["data"]
        else:
            response["data"]["generation_error"] = generation_result["error"]
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别和生成过程中发生错误: {str(e)}")
    
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass


@router.get("/download/{file_name}")
async def download_generated_file(file_name: str):
    """
    下载生成的标签文件
    
    Args:
        file_name: 文件名
    
    Returns:
        文件下载响应
    """
    file_path = os.path.join(settings.UPLOAD_DIR, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 安全检查：确保文件在允许的目录内
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.UPLOAD_DIR)):
        raise HTTPException(status_code=403, detail="访问被拒绝")
    
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type='image/png'
    )


@router.post("/test-generation")
async def test_generation(
    test_url: str = Form(default="https://mini.ems.com.cn/youzheng/mini/1151240728560"),
    db: Session = Depends(get_db)
):
    """
    测试二维码条形码生成功能
    
    Args:
        test_url: 测试URL，默认为示例URL
        db: 数据库会话
    
    Returns:
        测试结果
    """
    try:
        generation_service = QRGenerationService(db)
        result = generation_service.generate_qr_barcode_label(test_url)
        
        return {
            "success": True,
            "message": f"测试生成完成，使用URL: {test_url}",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试生成失败: {str(e)}")