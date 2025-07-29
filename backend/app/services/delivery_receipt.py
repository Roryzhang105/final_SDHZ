from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.delivery_receipt import DeliveryReceipt, DeliveryStatusEnum


class DeliveryReceiptService:
    def __init__(self, db: Session):
        self.db = db

    def create_delivery_receipt(
        self,
        tracking_number: str,
        recipient_name: str,
        recipient_address: str,
        sender_name: str,
        courier_company: str,
        **kwargs
    ) -> DeliveryReceipt:
        """创建送达回证"""
        receipt = DeliveryReceipt(
            tracking_number=tracking_number,
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            sender_name=sender_name,
            courier_company=courier_company,
            **kwargs
        )
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def get_delivery_receipt(self, receipt_id: int) -> Optional[DeliveryReceipt]:
        """获取送达回证"""
        return self.db.query(DeliveryReceipt).filter(DeliveryReceipt.id == receipt_id).first()

    def get_delivery_receipt_by_tracking(self, tracking_number: str) -> Optional[DeliveryReceipt]:
        """根据快递单号获取送达回证"""
        return self.db.query(DeliveryReceipt).filter(
            DeliveryReceipt.tracking_number == tracking_number
        ).first()

    def get_delivery_receipts(self, skip: int = 0, limit: int = 100) -> List[DeliveryReceipt]:
        """获取送达回证列表"""
        return self.db.query(DeliveryReceipt).offset(skip).limit(limit).all()

    def update_receipt_status(self, receipt_id: int, status: str) -> Optional[DeliveryReceipt]:
        """更新送达回证状态"""
        receipt = self.get_delivery_receipt(receipt_id)
        if not receipt:
            return None
        
        # 验证状态值
        try:
            status_enum = DeliveryStatusEnum(status)
            receipt.status = status_enum
            self.db.commit()
            self.db.refresh(receipt)
            return receipt
        except ValueError:
            return None

    def update_receipt_files(
        self,
        receipt_id: int,
        qr_code_path: str = None,
        barcode_path: str = None,
        receipt_file_path: str = None,
        tracking_screenshot_path: str = None
    ) -> Optional[DeliveryReceipt]:
        """更新送达回证文件路径"""
        receipt = self.get_delivery_receipt(receipt_id)
        if not receipt:
            return None
        
        if qr_code_path:
            receipt.qr_code_path = qr_code_path
        if barcode_path:
            receipt.barcode_path = barcode_path
        if receipt_file_path:
            receipt.receipt_file_path = receipt_file_path
        if tracking_screenshot_path:
            receipt.tracking_screenshot_path = tracking_screenshot_path
        
        self.db.commit()
        self.db.refresh(receipt)
        return receipt