from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.activity_log import ActivityLog


class ActivityLogService:
    """活动日志服务"""
    
    def __init__(self, db: Session):
        self.db = db

    def log_activity(
        self,
        action_type: str,
        description: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        status: str = "info",
        user_id: Optional[int] = None
    ) -> ActivityLog:
        """记录活动日志"""
        activity = ActivityLog(
            action_type=action_type,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            user_id=user_id
        )
        
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        
        return activity

    def get_recent_activities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近的活动日志"""
        activities = (
            self.db.query(ActivityLog)
            .order_by(desc(ActivityLog.created_at))
            .limit(limit)
            .all()
        )
        
        return [activity.to_dict() for activity in activities]

    def log_task_created(self, task_id: str, user_id: Optional[int] = None):
        """记录任务创建"""
        self.log_activity(
            action_type="task_created",
            description=f"新任务 #{task_id} 已创建，等待处理",
            entity_type="task",
            entity_id=task_id,
            status="info",
            user_id=user_id
        )

    def log_task_started(self, task_id: str, user_id: Optional[int] = None):
        """记录任务开始处理"""
        self.log_activity(
            action_type="task_started",
            description=f"任务 #{task_id} 开始处理，正在识别二维码",
            entity_type="task",
            entity_id=task_id,
            status="primary",
            user_id=user_id
        )

    def log_task_completed(self, task_id: str, user_id: Optional[int] = None):
        """记录任务完成"""
        self.log_activity(
            action_type="task_completed",
            description=f"任务 #{task_id} 处理完成，送达回证已生成",
            entity_type="task",
            entity_id=task_id,
            status="success",
            user_id=user_id
        )

    def log_task_failed(self, task_id: str, error_msg: str = "二维码识别异常", user_id: Optional[int] = None):
        """记录任务失败"""
        self.log_activity(
            action_type="task_failed",
            description=f"任务 #{task_id} 处理失败，{error_msg}",
            entity_type="task",
            entity_id=task_id,
            status="warning",
            user_id=user_id
        )

    def log_receipt_generated(self, receipt_id: str, tracking_number: str, user_id: Optional[int] = None):
        """记录送达回证生成"""
        self.log_activity(
            action_type="receipt_generated",
            description=f"送达回证已生成，快递单号: {tracking_number}",
            entity_type="delivery_receipt",
            entity_id=receipt_id,
            status="success",
            user_id=user_id
        )

    def log_receipt_downloaded(self, receipt_id: str, tracking_number: str, user_id: Optional[int] = None):
        """记录送达回证下载"""
        self.log_activity(
            action_type="receipt_downloaded",
            description=f"送达回证已下载，快递单号: {tracking_number}",
            entity_type="delivery_receipt",
            entity_id=receipt_id,
            status="info",
            user_id=user_id
        )

    def log_user_login(self, username: str, user_id: int):
        """记录用户登录"""
        self.log_activity(
            action_type="user_login",
            description=f"用户 {username} 登录系统",
            entity_type="user",
            entity_id=str(user_id),
            status="info",
            user_id=user_id
        )

    def log_user_logout(self, username: str, user_id: int):
        """记录用户注销"""
        self.log_activity(
            action_type="user_logout",
            description=f"用户 {username} 退出系统",
            entity_type="user",
            entity_id=str(user_id),
            status="info",
            user_id=user_id
        )

    def log_image_uploaded(self, filename: str, user_id: Optional[int] = None):
        """记录图片上传"""
        self.log_activity(
            action_type="image_uploaded",
            description=f"用户上传图片: {filename}",
            entity_type="file",
            entity_id=filename,
            status="info",
            user_id=user_id
        )