from sqlalchemy import Column, String, Integer, ForeignKey, Text, Enum, DateTime, JSON, Float, Index
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
import uuid

from .base import BaseModel


class TaskStatusEnum(enum.Enum):
    PENDING = "pending"
    RECOGNIZING = "recognizing"
    TRACKING = "tracking"
    DELIVERED = "delivered"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    RETURNED = "returned"


class Task(BaseModel):
    """主任务表"""
    __tablename__ = "tasks"
    
    # 任务基本信息
    task_id = Column(String(50), unique=True, nullable=False)  # 唯一任务ID
    task_name = Column(String(100))
    description = Column(Text)
    
    # 任务状态
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.PENDING, index=True)
    
    # 文件信息
    image_path = Column(String(500))  # 原始图片路径
    image_url = Column(String(500))   # 图片访问URL
    file_size = Column(Integer)
    
    # 识别结果
    qr_code = Column(Text)  # 识别到的二维码内容
    tracking_number = Column(String(100))  # 快递单号
    courier_company = Column(String(50))   # 快递公司
    
    # 物流信息
    tracking_data = Column(JSON)  # 物流跟踪数据
    delivery_status = Column(String(50))  # 配送状态
    delivery_time = Column(DateTime)  # 签收时间
    
    # 生成的文档
    document_url = Column(String(500))    # 回证文档URL
    document_path = Column(String(500))   # 回证文档路径
    screenshot_url = Column(String(500))  # 截图URL
    screenshot_path = Column(String(500)) # 截图路径
    
    # 处理时间
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_time = Column(Float)  # 总处理耗时(秒)
    
    # 错误信息
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")
    
    # 额外信息
    extra_metadata = Column(JSON)  # 其他元数据
    remarks = Column(Text)         # 备注
    
    # 表级索引定义
    __table_args__ = (
        Index('idx_tasks_status_created', 'status', 'created_at'),  # 状态和创建时间复合索引
        Index('idx_tasks_created_at', 'created_at'),  # 创建时间索引
        Index('idx_tasks_user_status', 'user_id', 'status'),  # 用户和状态复合索引
        Index('idx_tasks_tracking_number', 'tracking_number'),  # 快递单号索引
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.task_id:
            self.task_id = f"task_{uuid.uuid4().hex[:12]}"
    
    @property
    def progress_percentage(self):
        """获取任务进度百分比"""
        # 如果任务失败，根据已完成的步骤计算进度
        if self.status == TaskStatusEnum.FAILED:
            # 根据已有数据判断任务进行到了哪一步
            if self.document_url:  # 如果有文档，说明接近完成
                return 90
            elif self.tracking_data:  # 如果有物流数据，说明至少完成了跟踪
                return 50
            elif self.tracking_number:  # 如果有快递单号，说明完成了识别
                return 30
            elif self.qr_code:  # 如果有二维码内容，说明部分识别成功
                return 15
            else:
                return 0
        
        # 正常状态的进度映射
        progress_map = {
            TaskStatusEnum.PENDING: 0,
            TaskStatusEnum.RECOGNIZING: 20,
            TaskStatusEnum.TRACKING: 40,
            TaskStatusEnum.DELIVERED: 60,
            TaskStatusEnum.GENERATING: 80,
            TaskStatusEnum.COMPLETED: 100
        }
        return progress_map.get(self.status, 0)
    
    @property
    def is_processing(self):
        """判断任务是否正在处理中"""
        return self.status in [
            TaskStatusEnum.PENDING,
            TaskStatusEnum.RECOGNIZING,
            TaskStatusEnum.TRACKING,
            TaskStatusEnum.GENERATING
        ]
    
    @property
    def is_completed(self):
        """判断任务是否已完成"""
        return self.status == TaskStatusEnum.COMPLETED
    
    @property
    def is_failed(self):
        """判断任务是否失败"""
        return self.status == TaskStatusEnum.FAILED