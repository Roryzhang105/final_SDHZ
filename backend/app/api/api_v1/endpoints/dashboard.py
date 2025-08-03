from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import Dict, Any, List

from app.core.database import get_db
from app.models import DeliveryReceipt, Task, ActivityLog
from app.services.activity_log import ActivityLogService

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    获取仪表盘统计数据
    
    Returns:
        包含统计数据和最近活动的字典
    """
    try:
        # 获取送达回证统计
        from app.models.delivery_receipt import DeliveryStatusEnum
        
        receipt_stats = (
            db.query(
                func.count(DeliveryReceipt.id).label('total'),
                func.sum(case((DeliveryReceipt.status == DeliveryStatusEnum.DELIVERED, 1), else_=0)).label('completed'),
                func.sum(case((DeliveryReceipt.status == DeliveryStatusEnum.PROCESSING, 1), else_=0)).label('pending'),
                func.sum(case((DeliveryReceipt.status == DeliveryStatusEnum.FAILED, 1), else_=0)).label('failed')
            )
            .first()
        )
        
        # 获取任务统计（如果Task表有数据的话）
        task_stats = None
        try:
            from app.models.task import TaskStatusEnum
            
            task_stats = (
                db.query(
                    func.count(Task.id).label('total'),
                    func.sum(case((Task.status == TaskStatusEnum.COMPLETED, 1), else_=0)).label('completed'),
                    func.sum(case((Task.status.in_([TaskStatusEnum.PENDING, TaskStatusEnum.RECOGNIZING, TaskStatusEnum.TRACKING, TaskStatusEnum.GENERATING]), 1), else_=0)).label('pending'),
                    func.sum(case((Task.status == TaskStatusEnum.FAILED, 1), else_=0)).label('failed')
                )
                .first()
            )
        except Exception as e:
            # 如果Task表不存在或查询失败，忽略错误
            print(f"Task query error: {e}")
            pass
        
        # 优先使用任务统计，如果没有则使用送达回证统计
        stats = task_stats if task_stats and task_stats.total else receipt_stats
        
        # 获取最近活动
        activity_service = ActivityLogService(db)
        recent_activities = activity_service.get_recent_activities(limit=10)
        
        # 如果没有活动日志，创建一些示例活动
        if not recent_activities:
            # 创建一些示例活动日志
            activity_service.log_activity(
                action_type="system_start",
                description="系统启动完成，准备处理任务",
                status="info"
            )
            recent_activities = activity_service.get_recent_activities(limit=10)
        
        # 格式化活动数据以匹配前端期望的格式
        formatted_activities = []
        for activity in recent_activities:
            # 将status映射到前端期望的type
            activity_type = "info"
            if activity["status"] == "success":
                activity_type = "success"
            elif activity["status"] == "warning":
                activity_type = "warning"
            elif activity["status"] == "error":
                activity_type = "danger"
            elif activity["status"] == "primary":
                activity_type = "primary"
            
            formatted_activities.append({
                "id": activity["id"],
                "description": activity["description"],
                "time": activity["created_at"],
                "type": activity_type
            })
        
        return {
            "success": True,
            "data": {
                "statistics": {
                    "total_receipts": int(stats.total or 0),
                    "completed_receipts": int(stats.completed or 0),
                    "pending_receipts": int(stats.pending or 0),
                    "failed_receipts": int(stats.failed or 0)
                },
                "recent_activities": formatted_activities
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘数据失败: {str(e)}")


@router.get("/activities")
async def get_recent_activities(
    limit: int = 20,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取最近活动列表
    
    Args:
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        最近活动列表
    """
    try:
        activity_service = ActivityLogService(db)
        activities = activity_service.get_recent_activities(limit)
        
        return {
            "success": True,
            "data": {
                "activities": activities,
                "count": len(activities)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活动列表失败: {str(e)}")


@router.post("/activities/log")
async def log_activity(
    action_type: str,
    description: str,
    entity_type: str = None,
    entity_id: str = None,
    status: str = "info",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    记录活动日志
    
    Args:
        action_type: 动作类型
        description: 描述
        entity_type: 实体类型
        entity_id: 实体ID
        status: 状态
        db: 数据库会话
    
    Returns:
        操作结果
    """
    try:
        activity_service = ActivityLogService(db)
        activity = activity_service.log_activity(
            action_type=action_type,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status
        )
        
        return {
            "success": True,
            "data": activity.to_dict(),
            "message": "活动日志记录成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录活动日志失败: {str(e)}")