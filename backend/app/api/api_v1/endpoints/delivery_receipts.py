from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.delivery_receipt import DeliveryReceiptService
from app.tasks.receipt_tasks import process_delivery_receipt

router = APIRouter()


@router.post("/")
async def create_delivery_receipt(
    tracking_number: str,
    recipient_name: str,
    recipient_address: str,
    sender_name: str,
    courier_company: str,
    background_tasks: BackgroundTasks,
    recipient_phone: str = None,
    sender_address: str = None,
    courier_code: str = None,
    db: Session = Depends(get_db)
):
    """
    创建送达回证
    """
    service = DeliveryReceiptService(db)
    receipt = service.create_delivery_receipt(
        tracking_number=tracking_number,
        recipient_name=recipient_name,
        recipient_address=recipient_address,
        sender_name=sender_name,
        courier_company=courier_company,
        recipient_phone=recipient_phone,
        sender_address=sender_address,
        courier_code=courier_code
    )
    
    # 异步处理送达回证
    background_tasks.add_task(process_delivery_receipt, receipt.id)
    
    return {"message": "送达回证创建成功", "receipt_id": receipt.id}


@router.get("/")
async def get_delivery_receipts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取送达回证列表
    """
    service = DeliveryReceiptService(db)
    receipts = service.get_delivery_receipts(skip=skip, limit=limit)
    return receipts


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