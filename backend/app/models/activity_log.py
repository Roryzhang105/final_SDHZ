from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class ActivityLog(Base):
    """活动日志模型"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(50), nullable=False, comment="动作类型")
    description = Column(Text, nullable=False, comment="动作描述")
    entity_type = Column(String(50), nullable=True, comment="实体类型")
    entity_id = Column(String(100), nullable=True, comment="实体ID")
    status = Column(String(20), default="info", comment="状态: success, info, warning, error")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关联关系
    user = relationship("User", back_populates="activity_logs")

    def to_dict(self):
        """转换为字典格式"""
        user_info = None
        try:
            if self.user:
                user_info = {
                    "id": self.user.id,
                    "username": self.user.username
                }
        except Exception:
            # 如果user关系未加载或出错，忽略
            pass
            
        return {
            "id": self.id,
            "action_type": self.action_type,
            "description": self.description,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "status": self.status,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user": user_info
        }