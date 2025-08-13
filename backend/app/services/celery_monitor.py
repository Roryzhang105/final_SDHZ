"""
Celery监控服务
用于收集、分析和展示Celery任务执行情况
"""

import json
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.celery_monitor import CeleryTaskMonitor, CeleryBeatHealth, RetryStatistics, WorkerStatistics
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


class CeleryMonitorService:
    """Celery监控服务"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self._should_close_db = db is None
    
    def __del__(self):
        if self._should_close_db and self.db:
            self.db.close()
    
    def record_task_event(self, task_id: str, event_type: str, event_data: Dict[str, Any]):
        """记录任务事件"""
        try:
            # 查找或创建任务监控记录
            task_monitor = self.db.query(CeleryTaskMonitor).filter(
                CeleryTaskMonitor.task_id == task_id
            ).first()
            
            if not task_monitor:
                task_monitor = CeleryTaskMonitor(task_id=task_id)
                self.db.add(task_monitor)
            
            # 根据事件类型更新记录
            if event_type == 'task-sent':
                task_monitor.task_name = event_data.get('name', '')
                task_monitor.queue_name = event_data.get('queue', 'default')
                task_monitor.args = event_data.get('args', [])
                task_monitor.kwargs = event_data.get('kwargs', {})
                task_monitor.eta = event_data.get('eta')
                
            elif event_type == 'task-received':
                task_monitor.received_at = datetime.fromtimestamp(event_data.get('timestamp', 0))
                task_monitor.worker_name = event_data.get('hostname', '')
                
            elif event_type == 'task-started':
                task_monitor.started_at = datetime.fromtimestamp(event_data.get('timestamp', 0))
                task_monitor.status = 'STARTED'
                
            elif event_type in ['task-succeeded', 'task-failed']:
                task_monitor.completed_at = datetime.fromtimestamp(event_data.get('timestamp', 0))
                task_monitor.status = 'SUCCESS' if event_type == 'task-succeeded' else 'FAILURE'
                task_monitor.result = event_data.get('result')
                
                if task_monitor.started_at:
                    task_monitor.runtime_seconds = (
                        task_monitor.completed_at - task_monitor.started_at
                    ).total_seconds()
                
                if event_type == 'task-failed':
                    task_monitor.traceback = event_data.get('traceback', '')
                    task_monitor.error_category = self._categorize_error(
                        event_data.get('exception', '')
                    )
                    
            elif event_type == 'task-retry':
                task_monitor.retries += 1
                task_monitor.status = 'RETRY'
                
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"记录任务事件失败: {e}")
            self.db.rollback()
    
    def _categorize_error(self, exception: str) -> str:
        """分类错误类型"""
        exception_lower = exception.lower()
        
        if any(keyword in exception_lower for keyword in ['connection', 'network', 'timeout']):
            return 'network_error'
        elif any(keyword in exception_lower for keyword in ['memory', 'disk', 'resource']):
            return 'resource_error'
        elif any(keyword in exception_lower for keyword in ['database', 'sql', 'query']):
            return 'database_error'
        elif any(keyword in exception_lower for keyword in ['permission', 'auth', 'forbidden']):
            return 'permission_error'
        else:
            return 'unknown_error'
    
    def update_beat_health(self):
        """更新Beat健康状态"""
        try:
            # 获取最新的健康记录
            health_record = self.db.query(CeleryBeatHealth).order_by(
                desc(CeleryBeatHealth.created_at)
            ).first()
            
            if not health_record or (
                datetime.now() - health_record.created_at
            ).total_seconds() > 300:  # 5分钟创建新记录
                health_record = CeleryBeatHealth()
                self.db.add(health_record)
            
            # 获取系统信息
            current_process = psutil.Process()
            health_record.beat_pid = current_process.pid
            health_record.last_heartbeat = datetime.now()
            health_record.cpu_percent = current_process.cpu_percent()
            health_record.memory_mb = current_process.memory_info().rss / 1024 / 1024
            health_record.is_alive = True
            
            # 获取任务统计
            recent_tasks = self.db.query(CeleryTaskMonitor).filter(
                CeleryTaskMonitor.created_at >= datetime.now() - timedelta(hours=1)
            )
            
            health_record.executed_tasks_count = recent_tasks.count()
            health_record.failed_tasks_count = recent_tasks.filter(
                CeleryTaskMonitor.status == 'FAILURE'
            ).count()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"更新Beat健康状态失败: {e}")
            self.db.rollback()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取监控仪表板统计数据"""
        try:
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days=1)
            
            # 基础统计
            total_tasks = self.db.query(CeleryTaskMonitor).count()
            
            today_tasks = self.db.query(CeleryTaskMonitor).filter(
                CeleryTaskMonitor.created_at >= today
            ).count()
            
            failed_today = self.db.query(CeleryTaskMonitor).filter(
                and_(
                    CeleryTaskMonitor.created_at >= today,
                    CeleryTaskMonitor.status == 'FAILURE'
                )
            ).count()
            
            success_today = self.db.query(CeleryTaskMonitor).filter(
                and_(
                    CeleryTaskMonitor.created_at >= today,
                    CeleryTaskMonitor.status == 'SUCCESS'
                )
            ).count()
            
            # 队列统计
            queue_stats = self.db.query(
                CeleryTaskMonitor.queue_name,
                func.count(CeleryTaskMonitor.id).label('count')
            ).filter(
                CeleryTaskMonitor.created_at >= today
            ).group_by(CeleryTaskMonitor.queue_name).all()
            
            # Worker统计
            worker_stats = self.db.query(
                CeleryTaskMonitor.worker_name,
                func.count(CeleryTaskMonitor.id).label('count'),
                func.avg(CeleryTaskMonitor.runtime_seconds).label('avg_runtime')
            ).filter(
                and_(
                    CeleryTaskMonitor.created_at >= today,
                    CeleryTaskMonitor.worker_name.isnot(None)
                )
            ).group_by(CeleryTaskMonitor.worker_name).all()
            
            # 错误分类统计
            error_stats = self.db.query(
                CeleryTaskMonitor.error_category,
                func.count(CeleryTaskMonitor.id).label('count')
            ).filter(
                and_(
                    CeleryTaskMonitor.created_at >= today,
                    CeleryTaskMonitor.status == 'FAILURE',
                    CeleryTaskMonitor.error_category.isnot(None)
                )
            ).group_by(CeleryTaskMonitor.error_category).all()
            
            # Beat健康状态
            beat_health = self.db.query(CeleryBeatHealth).order_by(
                desc(CeleryBeatHealth.created_at)
            ).first()
            
            return {
                'total_tasks': total_tasks,
                'today_tasks': today_tasks,
                'failed_today': failed_today,
                'success_today': success_today,
                'success_rate': (success_today / today_tasks * 100) if today_tasks > 0 else 0,
                'queue_stats': [
                    {'queue': stat.queue_name, 'count': stat.count}
                    for stat in queue_stats
                ],
                'worker_stats': [
                    {
                        'worker': stat.worker_name,
                        'count': stat.count,
                        'avg_runtime': round(stat.avg_runtime or 0, 2)
                    }
                    for stat in worker_stats
                ],
                'error_stats': [
                    {'category': stat.error_category, 'count': stat.count}
                    for stat in error_stats
                ],
                'beat_health': beat_health.to_dict() if beat_health else None
            }
            
        except Exception as e:
            logger.error(f"获取仪表板统计失败: {e}")
            return {}
    
    def get_task_history(self, hours: int = 24, task_name: str = None) -> List[Dict[str, Any]]:
        """获取任务历史记录"""
        try:
            query = self.db.query(CeleryTaskMonitor).filter(
                CeleryTaskMonitor.created_at >= datetime.now() - timedelta(hours=hours)
            )
            
            if task_name:
                query = query.filter(CeleryTaskMonitor.task_name == task_name)
            
            tasks = query.order_by(desc(CeleryTaskMonitor.created_at)).limit(1000).all()
            
            return [task.to_dict() for task in tasks]
            
        except Exception as e:
            logger.error(f"获取任务历史失败: {e}")
            return []
    
    def get_retry_statistics(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取重试统计数据"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            retry_stats = self.db.query(RetryStatistics).filter(
                RetryStatistics.date >= start_date
            ).order_by(desc(RetryStatistics.date)).all()
            
            return [stat.to_dict() for stat in retry_stats]
            
        except Exception as e:
            logger.error(f"获取重试统计失败: {e}")
            return []
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """获取正在执行的任务"""
        try:
            active_tasks = self.db.query(CeleryTaskMonitor).filter(
                CeleryTaskMonitor.status.in_(['PENDING', 'RECEIVED', 'STARTED'])
            ).order_by(desc(CeleryTaskMonitor.created_at)).all()
            
            return [task.to_dict() for task in active_tasks]
            
        except Exception as e:
            logger.error(f"获取活动任务失败: {e}")
            return []
    
    def retry_failed_task(self, task_id: str, force: bool = False) -> Dict[str, Any]:
        """重试失败的任务"""
        try:
            task_monitor = self.db.query(CeleryTaskMonitor).filter(
                CeleryTaskMonitor.task_id == task_id
            ).first()
            
            if not task_monitor:
                return {'success': False, 'message': '任务不存在'}
            
            if task_monitor.status != 'FAILURE' and not force:
                return {'success': False, 'message': '只能重试失败的任务'}
            
            # 创建新的任务
            new_task = celery_app.send_task(
                task_monitor.task_name,
                args=task_monitor.args or [],
                kwargs=task_monitor.kwargs or {}
            )
            
            return {
                'success': True,
                'message': '任务重试已提交',
                'new_task_id': new_task.id
            }
            
        except Exception as e:
            logger.error(f"重试任务失败: {e}")
            return {'success': False, 'message': f'重试失败: {str(e)}'}
    
    def cleanup_old_records(self, days: int = 30):
        """清理旧的监控记录"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理任务监控记录
            deleted_tasks = self.db.query(CeleryTaskMonitor).filter(
                CeleryTaskMonitor.created_at < cutoff_date
            ).delete()
            
            # 清理Beat健康记录
            deleted_health = self.db.query(CeleryBeatHealth).filter(
                CeleryBeatHealth.created_at < cutoff_date
            ).delete()
            
            # 清理重试统计（保留更久）
            stats_cutoff = datetime.now() - timedelta(days=days * 3)
            deleted_stats = self.db.query(RetryStatistics).filter(
                RetryStatistics.date < stats_cutoff
            ).delete()
            
            self.db.commit()
            
            logger.info(f"清理完成: 任务记录 {deleted_tasks}, 健康记录 {deleted_health}, 统计记录 {deleted_stats}")
            
        except Exception as e:
            logger.error(f"清理旧记录失败: {e}")
            self.db.rollback()


# 全局监控服务实例
monitor_service = CeleryMonitorService()


def get_monitor_service() -> CeleryMonitorService:
    """获取监控服务实例"""
    return monitor_service