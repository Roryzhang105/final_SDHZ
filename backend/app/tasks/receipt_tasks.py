from celery import current_app as celery_app
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.delivery_receipt import DeliveryReceiptService
from app.models.delivery_receipt import DeliveryStatusEnum


@celery_app.task
def process_delivery_receipt(receipt_id: int):
    """
    处理送达回证的异步任务
    包括生成二维码、条形码、填充模板文档等
    """
    db: Session = SessionLocal()
    try:
        service = DeliveryReceiptService(db)
        receipt = service.get_delivery_receipt(receipt_id)
        
        if not receipt:
            return {"error": "送达回证不存在"}
        
        # 更新状态为处理中
        service.update_receipt_status(receipt_id, DeliveryStatusEnum.PROCESSING.value)
        
        # 1. 生成二维码和条形码
        from app.tasks.file_tasks import generate_qr_and_barcode
        generate_qr_and_barcode.delay(receipt_id)
        
        # 2. 填充文档模板
        from app.tasks.file_tasks import fill_receipt_template
        fill_receipt_template.delay(receipt_id)
        
        # 3. 查询物流信息
        from app.tasks.tracking_tasks import update_tracking_info
        update_tracking_info.delay(receipt.tracking_number)
        
        return {"message": "送达回证处理完成", "receipt_id": receipt_id}
        
    except Exception as e:
        # 更新状态为失败
        service = DeliveryReceiptService(db)
        service.update_receipt_status(receipt_id, DeliveryStatusEnum.FAILED.value)
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def batch_process_receipts(receipt_ids: list):
    """
    批量处理送达回证
    """
    results = []
    for receipt_id in receipt_ids:
        result = process_delivery_receipt.delay(receipt_id)
        results.append({"receipt_id": receipt_id, "task_id": result.id})
    
    return {"message": f"批量处理 {len(receipt_ids)} 个送达回证", "tasks": results}