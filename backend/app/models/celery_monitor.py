"""
Celery监控相关数据模型
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, Index
from sqlalchemy.sql import func
from enum import Enum
import json
from datetime import datetime

from .base import BaseModel


class TaskStatusEnum(Enum):
    """Celery任务状态枚举"""
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class CeleryTaskMonitor(BaseModel):
    """Celery任务执行监控"""
    __tablename__ = "celery_task_monitor"
    
    # 任务基本信息
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    task_name = Column(String(255), nullable=False, index=True)
    
    # 执行状态
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    result = Column(JSON, nullable=True)  # 任务结果或错误信息
    
    # 时间信息
    received_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 执行信息
    worker_name = Column(String(255), nullable=True)
    queue_name = Column(String(100), nullable=True, index=True)
    runtime_seconds = Column(Float, nullable=True)  # 执行时长(秒)
    
    # 重试信息
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 错误信息
    traceback = Column(Text, nullable=True)
    error_category = Column(String(100), nullable=True, index=True)
    
    # 元数据
    args = Column(JSON, nullable=True)  # 任务参数
    kwargs = Column(JSON, nullable=True)  # 任务关键字参数
    eta = Column(DateTime, nullable=True)  # 预计执行时间
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'status': self.status,
            'result': self.result,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'worker_name': self.worker_name,
            'queue_name': self.queue_name,
            'runtime_seconds': self.runtime_seconds,
            'retries': self.retries,
            'max_retries': self.max_retries,
            'error_category': self.error_category,
            'args': self.args,
            'kwargs': self.kwargs,
            'eta': self.eta.isoformat() if self.eta else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    # 创建索引优化查询性能
    __table_args__ = (
        Index('idx_task_status_created', 'status', 'created_at'),
        Index('idx_task_name_created', 'task_name', 'created_at'),
        Index('idx_queue_status', 'queue_name', 'status'),
        Index('idx_worker_completed', 'worker_name', 'completed_at'),
    )


class CeleryBeatHealth(BaseModel):
    """Celery Beat健康状态记录"""
    __tablename__ = "celery_beat_health"
    
    # Beat基本信息
    beat_pid = Column(Integer, nullable=True)
    beat_version = Column(String(50), nullable=True)
    
    # 健康状态
    is_alive = Column(Boolean, default=True, nullable=False, index=True)
    last_heartbeat = Column(DateTime, default=func.now(), nullable=False)
    
    # 性能指标
    cpu_percent = Column(Float, nullable=True)  # CPU使用率
    memory_mb = Column(Float, nullable=True)    # 内存使用(MB)
    
    # 调度信息
    scheduled_tasks_count = Column(Integer, default=0)
    executed_tasks_count = Column(Integer, default=0)
    failed_tasks_count = Column(Integer, default=0)
    
    # 错误信息
    errors = Column(JSON, nullable=True)  # 最近的错误记录
    warnings = Column(JSON, nullable=True)  # 警告信息
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'beat_pid': self.beat_pid,
            'beat_version': self.beat_version,
            'is_alive': self.is_alive,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'scheduled_tasks_count': self.scheduled_tasks_count,
            'executed_tasks_count': self.executed_tasks_count,
            'failed_tasks_count': self.failed_tasks_count,
            'errors': self.errors,
            'warnings': self.warnings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    __table_args__ = (
        Index('idx_beat_alive_heartbeat', 'is_alive', 'last_heartbeat'),
    )


class RetryStatistics(BaseModel):
    """重试统计数据"""
    __tablename__ = "retry_statistics"
    
    # 统计维度
    date = Column(DateTime, nullable=False, index=True)  # 统计日期
    task_name = Column(String(255), nullable=False, index=True)  # 任务名称
    error_category = Column(String(100), nullable=False, index=True)  # 错误类别
    
    # 统计数据
    total_tasks = Column(Integer, default=0)      # 总任务数
    failed_tasks = Column(Integer, default=0)     # 失败任务数
    retry_tasks = Column(Integer, default=0)      # 重试任务数
    success_after_retry = Column(Integer, default=0)  # 重试后成功数
    
    # 计算字段
    failure_rate = Column(Float, nullable=True)   # 失败率
    retry_success_rate = Column(Float, nullable=True)  # 重试成功率
    
    # 性能数据
    avg_runtime_seconds = Column(Float, nullable=True)  # 平均执行时间
    avg_retry_delay = Column(Float, nullable=True)      # 平均重试间隔
    
    def calculate_rates(self):
        """计算失败率和重试成功率"""
        if self.total_tasks > 0:
            self.failure_rate = self.failed_tasks / self.total_tasks
        
        if self.retry_tasks > 0:
            self.retry_success_rate = self.success_after_retry / self.retry_tasks

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'task_name': self.task_name,
            'error_category': self.error_category,
            'total_tasks': self.total_tasks,
            'failed_tasks': self.failed_tasks,
            'retry_tasks': self.retry_tasks,
            'success_after_retry': self.success_after_retry,
            'failure_rate': self.failure_rate,
            'retry_success_rate': self.retry_success_rate,
            'avg_runtime_seconds': self.avg_runtime_seconds,
            'avg_retry_delay': self.avg_retry_delay,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    __table_args__ = (
        Index('idx_date_task_category', 'date', 'task_name', 'error_category'),
    )


class WorkerStatistics(BaseModel):
    """Worker统计数据"""
    __tablename__ = "worker_statistics"
    
    # Worker信息
    worker_name = Column(String(255), nullable=False, index=True)
    
    # 时间维度
    date = Column(DateTime, nullable=False, index=True)
    
    # 性能统计
    processed_tasks = Column(Integer, default=0)
    successful_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    # 资源使用
    avg_cpu_percent = Column(Float, nullable=True)
    avg_memory_mb = Column(Float, nullable=True)
    peak_memory_mb = Column(Float, nullable=True)
    
    # 时间统计
    total_runtime_seconds = Column(Float, nullable=True)
    avg_task_runtime = Column(Float, nullable=True)
    
    # 健康状态
    uptime_seconds = Column(Float, nullable=True)
    restart_count = Column(Integer, default=0)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'worker_name': self.worker_name,
            'date': self.date.isoformat() if self.date else None,
            'processed_tasks': self.processed_tasks,
            'successful_tasks': self.successful_tasks,
            'failed_tasks': self.failed_tasks,
            'avg_cpu_percent': self.avg_cpu_percent,
            'avg_memory_mb': self.avg_memory_mb,
            'peak_memory_mb': self.peak_memory_mb,
            'total_runtime_seconds': self.total_runtime_seconds,
            'avg_task_runtime': self.avg_task_runtime,
            'uptime_seconds': self.uptime_seconds,
            'restart_count': self.restart_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    __table_args__ = (
        Index('idx_worker_date', 'worker_name', 'date'),
    )