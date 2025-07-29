from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

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
        
        # 从tracking_data中提取签收状态
        is_signed = "true" if tracking_data.get("is_signed", False) else "false"
        sign_time = tracking_data.get("sign_time", "")
        
        current_time = datetime.utcnow()
        
        if tracking:
            # 更新现有记录
            tracking.current_status = current_status
            tracking.tracking_data = tracking_data
            tracking.last_update = current_time
            tracking.is_signed = is_signed
            if notes:
                tracking.notes = notes
        else:
            # 创建新记录
            tracking = TrackingInfo(
                delivery_receipt_id=receipt_id,
                current_status=current_status,
                tracking_data=tracking_data,
                last_update=current_time,
                is_signed=is_signed,
                notes=notes
            )
            self.db.add(tracking)
        
        self.db.commit()
        self.db.refresh(tracking)
        return tracking
    
    def update_screenshot_info(
        self,
        tracking_number: str,
        screenshot_path: str,
        screenshot_filename: str
    ) -> bool:
        """
        更新物流记录的截图信息
        
        Args:
            tracking_number: 快递单号
            screenshot_path: 截图文件路径
            screenshot_filename: 截图文件名
            
        Returns:
            更新是否成功
        """
        try:
            tracking_info = self.get_tracking_by_number(tracking_number)
            if tracking_info:
                tracking_info.screenshot_path = screenshot_path
                tracking_info.screenshot_filename = screenshot_filename
                tracking_info.screenshot_generated_at = datetime.utcnow()
                self.db.commit()
                return True
            return False
        except Exception:
            self.db.rollback()
            return False
    
    def should_refresh_tracking(self, tracking_info: TrackingInfo, refresh_threshold_minutes: int = 30) -> bool:
        """
        判断是否需要重新查询物流信息
        
        Args:
            tracking_info: 现有的物流信息记录
            refresh_threshold_minutes: 刷新阈值（分钟），默认30分钟
            
        Returns:
            True: 需要重新查询, False: 使用现有缓存
        """
        if not tracking_info:
            return True
        
        # 1. 检查是否已签收
        is_signed = tracking_info.is_signed == "true"
        if is_signed:
            # 已签收的快递状态不会再变化，不需要重新查询
            return False
        
        # 2. 未签收的快递需要检查上次查询时间
        if not tracking_info.last_update:
            # 没有记录查询时间，需要重新查询
            return True
        
        # 3. 计算时间差
        current_time = datetime.utcnow()
        time_diff = current_time - tracking_info.last_update
        threshold = timedelta(minutes=refresh_threshold_minutes)
        
        # 4. 如果超过阈值时间，需要重新查询
        return time_diff > threshold
    
    def is_tracking_data_fresh(self, tracking_info: TrackingInfo, threshold_minutes: int = 30) -> bool:
        """
        检查物流数据是否新鲜（在阈值时间内）
        
        Args:
            tracking_info: 物流信息记录
            threshold_minutes: 时间阈值（分钟）
            
        Returns:
            True: 数据新鲜, False: 数据过时
        """
        return not self.should_refresh_tracking(tracking_info, threshold_minutes)