from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import os

from app.core.database import get_db
from app.services.delivery_receipt import DeliveryReceiptService
from app.services.delivery_receipt_generator import DeliveryReceiptGeneratorService
from app.tasks.receipt_tasks import process_delivery_receipt


class DeliveryReceiptGenerateRequest(BaseModel):
    tracking_number: str
    doc_title: str = "送达回证"
    sender: Optional[str] = None
    send_time: Optional[str] = None
    send_location: Optional[str] = None
    receiver: Optional[str] = None

router = APIRouter()


@router.post("/generate")
async def generate_delivery_receipt(
    request: DeliveryReceiptGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    生成送达回证Word文档
    
    Args:
        request: 生成请求参数
        db: 数据库会话
    
    Returns:
        生成结果，包含文档路径等信息
    """
    try:
        generator_service = DeliveryReceiptGeneratorService(db)
        result = generator_service.generate_delivery_receipt(
            tracking_number=request.tracking_number,
            doc_title=request.doc_title,
            sender=request.sender,
            send_time=request.send_time,
            send_location=request.send_location,
            receiver=request.receiver
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "data": {
                    "tracking_number": result["tracking_number"],
                    "receipt_id": result["receipt_id"],
                    "doc_filename": result["doc_filename"],
                    "file_size": result["file_size"],
                    "download_url": f"/api/v1/delivery-receipts/{request.tracking_number}/download"
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成送达回证失败: {str(e)}")


@router.post("/")
async def create_delivery_receipt_legacy(
    tracking_number: str = Form(...),
    recipient_name: str = Form(None),
    recipient_address: str = Form(None),
    sender_name: str = Form(None),
    courier_company: str = Form(None),
    background_tasks: BackgroundTasks = None,
    recipient_phone: str = Form(None),
    sender_address: str = Form(None),
    courier_code: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    创建送达回证（兼容旧版API）
    现在只需要tracking_number，其他字段都是可选的
    """
    service = DeliveryReceiptService(db)
    
    # 使用新的可选字段创建方式
    from app.models.delivery_receipt import DeliveryReceipt
    receipt = DeliveryReceipt(
        tracking_number=tracking_number,
        recipient_name=recipient_name,
        recipient_address=recipient_address,
        sender_name=sender_name,
        courier_company=courier_company,
        recipient_phone=recipient_phone,
        sender_address=sender_address,
        courier_code=courier_code
    )
    
    service.db.add(receipt)
    service.db.commit()
    service.db.refresh(receipt)
    
    # 可选：异步处理送达回证
    if background_tasks:
        background_tasks.add_task(process_delivery_receipt, receipt.id)
    
    return {"message": "送达回证创建成功", "receipt_id": receipt.id}


@router.get("/")
async def get_delivery_receipts(
    limit: int = Query(50, description="返回记录数限制", ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    获取送达回证列表
    """
    try:
        generator_service = DeliveryReceiptGeneratorService(db)
        result = generator_service.list_delivery_receipts(limit)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "data": {
                    "receipts": result["receipts"],
                    "count": result["count"],
                    "limit": result["limit"]
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取送达回证列表失败: {str(e)}")


@router.get("/tracking/{tracking_number}")
async def get_delivery_receipt_by_tracking(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """
    根据快递单号获取送达回证信息
    
    Args:
        tracking_number: 快递单号
        db: 数据库会话
    
    Returns:
        送达回证详细信息
    """
    try:
        generator_service = DeliveryReceiptGeneratorService(db)
        result = generator_service.get_receipt_info(tracking_number)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "data": result
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("message", "未找到送达回证"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取送达回证信息失败: {str(e)}")


@router.get("/{receipt_id}")
async def get_delivery_receipt(
    receipt_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定送达回证
    """
    service = DeliveryReceiptService(db)
    receipt = service.get_delivery_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="送达回证不存在")
    return receipt


@router.put("/{receipt_id}/status")
async def update_receipt_status(
    receipt_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    更新送达回证状态
    """
    service = DeliveryReceiptService(db)
    receipt = service.update_receipt_status(receipt_id, status)
    if not receipt:
        raise HTTPException(status_code=404, detail="送达回证不存在")
    return {"message": "状态更新成功"}


@router.get("/{tracking_number}/download")
async def download_delivery_receipt(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """
    下载送达回证Word文档
    
    Args:
        tracking_number: 快递单号
        db: 数据库会话
    
    Returns:
        Word文档下载响应
    """
    try:
        service = DeliveryReceiptService(db)
        receipt = service.get_delivery_receipt_by_tracking(tracking_number)
        
        if not receipt:
            raise HTTPException(
                status_code=404,
                detail=f"未找到快递单号 {tracking_number} 的送达回证记录"
            )
        
        if not receipt.delivery_receipt_doc_path:
            raise HTTPException(
                status_code=404,
                detail="该送达回证暂无Word文档，请先生成"
            )
        
        # 检查文件是否存在
        if not os.path.exists(receipt.delivery_receipt_doc_path):
            raise HTTPException(
                status_code=404,
                detail="送达回证文档不存在，可能已被删除"
            )
        
        # 安全检查：确保文件在允许的目录内
        from app.core.config import settings
        if not os.path.abspath(receipt.delivery_receipt_doc_path).startswith(os.path.abspath(settings.UPLOAD_DIR)):
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        # 确定文件名
        filename = f"delivery_receipt_{tracking_number}.docx"
        
        return FileResponse(
            path=receipt.delivery_receipt_doc_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载送达回证失败: {str(e)}")