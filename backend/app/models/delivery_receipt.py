from sqlalchemy import Column, String, Integer, ForeignKey, Text, Enum, DateTime
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
    
    # 基本信息
    tracking_number = Column(String(50), unique=True, index=True, nullable=False)
    recipient_name = Column(String(100), nullable=False)
    recipient_phone = Column(String(20))
    recipient_address = Column(Text, nullable=False)
    
    # 发件人信息
    sender_name = Column(String(100), nullable=False)
    sender_address = Column(Text)
    
    # 快递公司信息
    courier_company = Column(String(50), nullable=False)
    courier_code = Column(String(20))
    
    # 状态信息
    status = Column(Enum(DeliveryStatusEnum), default=DeliveryStatusEnum.CREATED)
    
    # 文件路径
    qr_code_path = Column(String(255))
    barcode_path = Column(String(255))
    receipt_file_path = Column(String(255))
    tracking_screenshot_path = Column(String(255))
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="delivery_receipts")
    
    # 关联关系
    tracking_info = relationship("TrackingInfo", back_populates="delivery_receipt", uselist=False)