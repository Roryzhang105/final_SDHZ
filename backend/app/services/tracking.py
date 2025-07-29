from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.tracking import TrackingInfo
from app.models.delivery_receipt import DeliveryReceipt


class TrackingService:
    def __init__(self, db: Session):
        self.db = db

    def get_tracking_by_receipt_id(self, receipt_id: int) -> Optional[TrackingInfo]:
        """根据送达回证ID获取物流信息"""
        return self.db.query(TrackingInfo).filter(
            TrackingInfo.delivery_receipt_id == receipt_id
        ).first()

    def get_tracking_by_number(self, tracking_number: str) -> Optional[TrackingInfo]:
        """根据快递单号获取物流信息"""
        receipt = self.db.query(DeliveryReceipt).filter(
            DeliveryReceipt.tracking_number == tracking_number
        ).first()
        
        if not receipt:
            return None
        
        return self.get_tracking_by_receipt_id(receipt.id)

    def get_receipt_by_tracking_number(self, tracking_number: str) -> Optional[DeliveryReceipt]:
        """根据快递单号获取送达回证"""
        return self.db.query(DeliveryReceipt).filter(
            DeliveryReceipt.tracking_number == tracking_number
        ).first()

    def create_or_update_tracking(
        self,
        receipt_id: int,
        current_status: str,
        tracking_data: dict,
        notes: str = None
    ) -> TrackingInfo:
        """创建或更新物流跟踪信息"""
        tracking = self.get_tracking_by_receipt_id(receipt_id)
        
        if tracking:
            # 更新现有记录
            tracking.current_status = current_status
            tracking.tracking_data = tracking_data
            tracking.last_update = datetime.utcnow()
            if notes:
                tracking.notes = notes
        else:
            # 创建新记录
            tracking = TrackingInfo(
                delivery_receipt_id=receipt_id,
                current_status=current_status,
                tracking_data=tracking_data,
                last_update=datetime.utcnow(),
                notes=notes
            )
            self.db.add(tracking)
        
        self.db.commit()
        self.db.refresh(tracking)
        return tracking