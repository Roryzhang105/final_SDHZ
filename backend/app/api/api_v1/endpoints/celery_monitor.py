"""
Celery监控API端点
提供任务监控、统计和管理功能
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.celery_monitor import CeleryMonitorService
from app.models.user import User
from app.api.api_v1.endpoints.auth import get_current_user
from app.tasks.celery_app import celery_app

router = APIRouter()


class RetryTaskRequest(BaseModel):
    """重试任务请求"""
    task_id: str
    force: bool = False


@router.get("/dashboard")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取监控仪表板统计数据"""
    monitor_service = CeleryMonitorService(db)
    stats = monitor_service.get_dashboard_stats()
    
    return {
        "success": True,
        "message": "获取仪表板统计成功",
        "data": stats
    }


@router.get("/tasks")
async def get_task_history(
    hours: int = Query(24, ge=1, le=168, description="查询最近几小时的任务"),
    task_name: Optional[str] = Query(None, description="任务名称筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务历史记录"""
    monitor_service = CeleryMonitorService(db)
    
    all_tasks = monitor_service.get_task_history(hours, task_name)
    
    # 手动分页
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    tasks = all_tasks[start_idx:end_idx]
    
    return {
        "success": True,
        "message": "获取任务历史成功",
        "data": {
            "tasks": tasks,
            "pagination": {
                "page": page,
                "size": size,
                "total": len(all_tasks),
                "pages": (len(all_tasks) + size - 1) // size
            }
        }
    }


@router.get("/tasks/active")
async def get_active_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取正在执行的任务"""
    monitor_service = CeleryMonitorService(db)
    active_tasks = monitor_service.get_active_tasks()
    
    return {
        "success": True,
        "message": "获取活动任务成功",
        "data": active_tasks
    }


@router.get("/workers")
async def get_worker_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Worker统计信息"""
    try:
        # 获取Celery活动的Worker信息
        inspect = celery_app.control.inspect()
        
        # 获取活动的worker
        active_workers = inspect.active()
        reserved_tasks = inspect.reserved()
        worker_stats = inspect.stats()
        
        workers_info = []
        
        if active_workers:
            for worker_name, tasks in active_workers.items():
                worker_info = {
                    'name': worker_name,
                    'active_tasks': len(tasks),
                    'reserved_tasks': len(reserved_tasks.get(worker_name, [])) if reserved_tasks else 0,
                    'stats': worker_stats.get(worker_name, {}) if worker_stats else {},
                    'tasks': tasks
                }
                workers_info.append(worker_info)
        
        return {
            "success": True,
            "message": "获取Worker统计成功",
            "data": {
                "workers": workers_info,
                "total_workers": len(workers_info)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"获取Worker统计失败: {str(e)}",
            "data": {"workers": [], "total_workers": 0}
        }


@router.get("/queues")
async def get_queue_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取队列统计信息"""
    try:
        # 获取队列长度信息
        inspect = celery_app.control.inspect()
        active_queues = inspect.active_queues()
        
        queue_info = []
        if active_queues:
            for worker_name, queues in active_queues.items():
                for queue in queues:
                    queue_info.append({
                        'worker': worker_name,
                        'name': queue['name'],
                        'exchange': queue.get('exchange', {}),
                        'routing_key': queue.get('routing_key', ''),
                    })
        
        return {
            "success": True,
            "message": "获取队列统计成功",
            "data": queue_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"获取队列统计失败: {str(e)}",
            "data": []
        }


@router.get("/retry-stats")
async def get_retry_statistics(
    days: int = Query(7, ge=1, le=30, description="查询最近几天的重试统计"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取重试统计数据"""
    monitor_service = CeleryMonitorService(db)
    retry_stats = monitor_service.get_retry_statistics(days)
    
    return {
        "success": True,
        "message": "获取重试统计成功",
        "data": retry_stats
    }


@router.post("/tasks/retry")
async def retry_task(
    request: RetryTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重试失败的任务"""
    monitor_service = CeleryMonitorService(db)
    result = monitor_service.retry_failed_task(request.task_id, request.force)
    
    if result['success']:
        return {
            "success": True,
            "message": result['message'],
            "data": {"new_task_id": result.get('new_task_id')}
        }
    else:
        raise HTTPException(status_code=400, detail=result['message'])


@router.post("/tasks/{task_id}/revoke")
async def revoke_task(
    task_id: str,
    terminate: bool = Query(False, description="是否强制终止任务"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """撤销/停止任务"""
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        
        return {
            "success": True,
            "message": f"任务 {task_id} 已{'强制终止' if terminate else '撤销'}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"撤销任务失败: {str(e)}")


@router.get("/beat/health")
async def get_beat_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Beat健康状态"""
    monitor_service = CeleryMonitorService(db)
    
    # 更新Beat健康状态
    monitor_service.update_beat_health()
    
    # 获取最新的健康数据
    stats = monitor_service.get_dashboard_stats()
    beat_health = stats.get('beat_health')
    
    if not beat_health:
        raise HTTPException(status_code=404, detail="Beat健康状态不可用")
    
    # 检查Beat是否健康
    last_heartbeat = datetime.fromisoformat(beat_health['last_heartbeat'].replace('Z', '+00:00'))
    is_healthy = (datetime.now() - last_heartbeat.replace(tzinfo=None)).total_seconds() < 300  # 5分钟内
    
    return {
        "success": True,
        "message": "获取Beat健康状态成功",
        "data": {
            **beat_health,
            "is_healthy": is_healthy,
            "status": "healthy" if is_healthy else "unhealthy"
        }
    }


@router.post("/cleanup")
async def cleanup_old_records(
    background_tasks: BackgroundTasks,
    days: int = Query(30, ge=7, le=365, description="清理多少天前的记录"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清理旧的监控记录"""
    def cleanup_task():
        monitor_service = CeleryMonitorService()
        monitor_service.cleanup_old_records(days)
    
    background_tasks.add_task(cleanup_task)
    
    return {
        "success": True,
        "message": f"已启动清理 {days} 天前的监控记录"
    }


@router.get("/scheduled-tasks")
async def get_scheduled_tasks(
    current_user: User = Depends(get_current_user)
):
    """获取定时任务配置"""
    try:
        # 获取Beat调度配置
        from app.tasks.beat_schedules import BEAT_SCHEDULE
        
        scheduled_tasks = []
        for task_name, config in BEAT_SCHEDULE.items():
            scheduled_tasks.append({
                'name': task_name,
                'task': config['task'],
                'schedule': str(config['schedule']),
                'queue': config.get('options', {}).get('queue', 'default'),
                'description': config.get('description', '无描述')
            })
        
        return {
            "success": True,
            "message": "获取定时任务配置成功",
            "data": scheduled_tasks
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取定时任务配置失败: {str(e)}")


@router.get("/system-status")
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """获取系统状态概览"""
    try:
        inspect = celery_app.control.inspect()
        
        # 获取各种系统状态
        ping_results = inspect.ping()
        active_workers = inspect.active()
        reserved_tasks = inspect.reserved()
        
        # 统计信息
        total_workers = len(ping_results) if ping_results else 0
        total_active_tasks = sum(len(tasks) for tasks in active_workers.values()) if active_workers else 0
        total_reserved_tasks = sum(len(tasks) for tasks in reserved_tasks.values()) if reserved_tasks else 0
        
        return {
            "success": True,
            "message": "获取系统状态成功",
            "data": {
                "broker_connected": bool(ping_results),
                "total_workers": total_workers,
                "total_active_tasks": total_active_tasks,
                "total_reserved_tasks": total_reserved_tasks,
                "ping_results": ping_results or {},
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"获取系统状态失败: {str(e)}",
            "data": {
                "broker_connected": False,
                "total_workers": 0,
                "total_active_tasks": 0,
                "total_reserved_tasks": 0,
                "timestamp": datetime.now().isoformat()
            }
        }