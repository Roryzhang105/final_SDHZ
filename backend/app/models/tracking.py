from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, JSON, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class TrackingInfo(BaseModel):
    __tablename__ = "tracking_info"
    
    # 关联的送达回证
    delivery_receipt_id = Column(Integer, ForeignKey("delivery_receipts.id"), unique=True)
    delivery_receipt = relationship("DeliveryReceipt", back_populates="tracking_info")
    
    # 物流状态
    current_status = Column(String(50), index=True)
    last_update = Column(DateTime, index=True)
    
    # 物流轨迹数据 (JSON格式存储)
    tracking_data = Column(JSON)
    
    # 截图相关字段
    screenshot_path = Column(String(500))  # 截图文件路径
    screenshot_filename = Column(String(255))  # 截图文件名
    screenshot_generated_at = Column(DateTime)  # 截图生成时间
    is_signed = Column(String(10), default="false")  # 是否已签收
    
    # 备注
    notes = Column(Text)
    
    # 表级索引定义
    __table_args__ = (
        Index('idx_tracking_info_status_update', 'current_status', 'last_update'),  # 状态和更新时间复合索引
        Index('idx_tracking_info_updated_at', 'updated_at'),  # 更新时间索引
        Index('idx_tracking_info_created_at', 'created_at'),  # 创建时间索引
        Index('idx_tracking_info_signed_update', 'is_signed', 'last_update'),  # 签收状态和时间复合索引
    )