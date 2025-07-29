from sqlalchemy import Column, String, Integer, ForeignKey, Text, Enum, DateTime, JSON, Float
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from .base import BaseModel


class RecognitionTypeEnum(enum.Enum):
    QRCODE = "qrcode"
    BARCODE = "barcode"
    MIXED = "mixed"


class RecognitionStatusEnum(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RecognitionTask(BaseModel):
    """识别任务表"""
    __tablename__ = "recognition_tasks"
    
    # 任务基本信息
    task_name = Column(String(100))
    description = Column(Text)
    
    # 任务状态
    status = Column(Enum(RecognitionStatusEnum), default=RecognitionStatusEnum.PENDING)
    recognition_type = Column(Enum(RecognitionTypeEnum), default=RecognitionTypeEnum.MIXED)
    
    # 处理统计
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # 处理时间
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 错误信息
    error_message = Column(Text)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")
    
    # 关联关系
    results = relationship("RecognitionResult", back_populates="task", cascade="all, delete-orphan")


class RecognitionResult(BaseModel):
    """识别结果表"""
    __tablename__ = "recognition_results"
    
    # 关联任务
    task_id = Column(Integer, ForeignKey("recognition_tasks.id"))
    task = relationship("RecognitionTask", back_populates="results")
    
    # 文件信息
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    # 识别结果
    recognition_type = Column(Enum(RecognitionTypeEnum))
    raw_results = Column(JSON)  # 原始识别结果
    
    # 解析后的结构化数据
    tracking_numbers = Column(JSON)  # 快递单号列表
    qr_contents = Column(JSON)       # 二维码内容列表
    barcode_contents = Column(JSON)  # 条形码内容列表
    
    # 识别质量评估
    confidence_score = Column(Float)  # 置信度分数
    detection_count = Column(Integer, default=0)  # 检测到的码数量
    
    # 处理状态
    is_success = Column(String(10), default="true")  # SQLite兼容的boolean
    error_message = Column(Text)
    processing_time = Column(Float)  # 处理耗时(秒)
    
    # 额外信息
    extra_metadata = Column(JSON)  # 其他元数据
    notes = Column(Text)           # 备注


class CourierPattern(BaseModel):
    """快递单号识别模式表"""
    __tablename__ = "courier_patterns"
    
    courier_name = Column(String(50), nullable=False)  # 快递公司名称
    courier_code = Column(String(20), nullable=False)  # 快递公司代码
    
    # 识别模式
    pattern_regex = Column(String(200))  # 正则表达式模式
    pattern_length = Column(Integer)     # 单号长度
    pattern_prefix = Column(String(10))  # 前缀模式
    
    # 模式描述
    description = Column(Text)
    examples = Column(JSON)  # 示例单号
    
    # 启用状态
    is_active = Column(String(10), default="true")
    priority = Column(Integer, default=1)  # 匹配优先级