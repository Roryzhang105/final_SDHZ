#!/usr/bin/env python3
"""
脚本用于创建示例活动日志
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.activity_log import ActivityLogService


def seed_activities():
    """创建示例活动日志"""
    db: Session = SessionLocal()
    
    try:
        activity_service = ActivityLogService(db)
        
        # 创建一些示例活动
        activities = [
            {
                "action_type": "task_completed",
                "description": "任务 #1151242358360 处理完成，送达回证已生成",
                "entity_type": "task",
                "entity_id": "1151242358360",
                "status": "success"
            },
            {
                "action_type": "task_started",
                "description": "任务 #1151240728560 开始处理，正在识别二维码",
                "entity_type": "task",
                "entity_id": "1151240728560",
                "status": "primary"
            },
            {
                "action_type": "task_created",
                "description": "新任务 #1151238971060 已创建，等待处理",
                "entity_type": "task",
                "entity_id": "1151238971060",  
                "status": "info"
            },
            {
                "action_type": "task_failed",
                "description": "任务 #1151235647120 处理失败，二维码识别异常",
                "entity_type": "task",
                "entity_id": "1151235647120",
                "status": "warning"
            },
            {
                "action_type": "receipt_generated",
                "description": "送达回证已生成，快递单号: 1151242358360",
                "entity_type": "delivery_receipt",
                "entity_id": "1151242358360",
                "status": "success"
            },
            {
                "action_type": "system_start",
                "description": "系统启动完成，准备处理任务",
                "status": "info"
            }
        ]
        
        for activity_data in activities:
            activity_service.log_activity(**activity_data)
            
        print(f"Successfully created {len(activities)} sample activities")
        
    except Exception as e:
        print(f"Error creating sample activities: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_activities()