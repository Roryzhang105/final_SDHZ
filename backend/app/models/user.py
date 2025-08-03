from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 关联关系
    delivery_receipts = relationship("DeliveryReceipt", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")