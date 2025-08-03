from sqlalchemy import Column, String, Integer, ForeignKey, Text, Enum, DateTime, Index
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class DeliveryStatusEnum(enum.Enum):
    CREATED = "created"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class DeliveryReceipt(BaseModel):
    __tablename__ = "delivery_receipts"
    
    # 基本信息 - 只有tracking_number是必填的
    tracking_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # 送达回证相关信息（严格对应insert_imgs_delivery_receipt.py的参数）
    doc_title = Column(String(200), default="送达回证")  # 送达文书名称及文号
    sender = Column(String(100))        # 送达人
    send_time = Column(String(50))      # 送达时间
    send_location = Column(String(200)) # 送达地点
    receiver = Column(String(100))      # 受送达人
    
    # 状态信息
    status = Column(Enum(DeliveryStatusEnum), default=DeliveryStatusEnum.CREATED, index=True)
    
    # 文件路径
    qr_code_path = Column(String(255))              # 二维码文件路径
    barcode_path = Column(String(255))              # 条形码文件路径  
    receipt_file_path = Column(String(255))         # 二维码条形码标签文件路径
    tracking_screenshot_path = Column(String(255))  # 物流截图路径
    delivery_receipt_doc_path = Column(String(255)) # 送达回证Word文档路径
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="delivery_receipts")
    
    # 关联关系
    tracking_info = relationship("TrackingInfo", back_populates="delivery_receipt", uselist=False)
    
    # 表级索引定义
    __table_args__ = (
        Index('idx_delivery_receipts_user_status', 'user_id', 'status'),  # 用户和状态复合索引
        Index('idx_delivery_receipts_status_created', 'status', 'created_at'),  # 状态和创建时间复合索引
        Index('idx_delivery_receipts_created_at', 'created_at'),  # 创建时间索引
    )