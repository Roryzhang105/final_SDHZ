"""
健康检查和告警任务
定期检查系统健康状态并发送告警
"""

import psutil
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from celery import current_app as celery_app
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.celery_monitor import CeleryTaskMonitor, CeleryBeatHealth, WorkerStatistics
from app.services.celery_monitor import CeleryMonitorService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def monitor_system_health(self) -> Dict[str, Any]:
    """监控系统健康状态"""
    db: Session = SessionLocal()
    
    try:
        monitor_service = CeleryMonitorService(db)
        
        # 更新Beat健康状态
        monitor_service.update_beat_health()
        
        # 收集系统指标
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 检查Celery连接状态
        try:
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            ping_results = inspect.ping()
            broker_connected = bool(ping_results)
            worker_count = len(ping_results) if ping_results else 0
        except Exception as e:
            logger.error(f"检查Celery状态失败: {e}")
            broker_connected = False
            worker_count = 0
            active_workers = {}
        
        # 获取任务统计
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_tasks_today = db.query(CeleryTaskMonitor).filter(
            CeleryTaskMonitor.created_at >= today
        ).count()
        
        failed_tasks_today = db.query(CeleryTaskMonitor).filter(
            and_(
                CeleryTaskMonitor.created_at >= today,
                CeleryTaskMonitor.status == 'FAILURE'
            )
        ).count()
        
        # 计算失败率
        failure_rate = (failed_tasks_today / total_tasks_today * 100) if total_tasks_today > 0 else 0
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / 1024**3,
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / 1024**3
            },
            'celery': {
                'broker_connected': broker_connected,
                'worker_count': worker_count,
                'active_tasks': sum(len(tasks) for tasks in active_workers.values()) if active_workers else 0
            },
            'tasks': {
                'total_today': total_tasks_today,
                'failed_today': failed_tasks_today,
                'failure_rate': failure_rate
            }
        }
        
        # 检查告警条件
        alerts = check_alert_conditions(health_data)
        
        if alerts:
            logger.warning(f"检测到健康告警: {alerts}")
            # 这里可以集成邮件、短信等告警通知
            
        return {
            'success': True,
            'message': '系统健康检查完成',
            'data': health_data,
            'alerts': alerts
        }
        
    except Exception as e:
        logger.error(f"系统健康检查失败: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()


def check_alert_conditions(health_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """检查告警条件"""
    alerts = []
    
    # 系统资源告警阈值
    ALERT_THRESHOLDS = {
        'cpu_percent': 80.0,           # CPU使用率 > 80%
        'memory_percent': 85.0,        # 内存使用率 > 85%
        'disk_percent': 90.0,          # 磁盘使用率 > 90%
        'failure_rate': 20.0,          # 失败率 > 20%
        'memory_available_gb': 1.0,    # 可用内存 < 1GB
        'disk_free_gb': 5.0            # 剩余磁盘 < 5GB
    }
    
    system = health_data.get('system', {})
    celery_info = health_data.get('celery', {})
    tasks = health_data.get('tasks', {})
    
    # CPU告警
    if system.get('cpu_percent', 0) > ALERT_THRESHOLDS['cpu_percent']:
        alerts.append({
            'type': 'cpu_high',
            'severity': 'warning',
            'message': f"CPU使用率过高: {system['cpu_percent']:.1f}%",
            'threshold': ALERT_THRESHOLDS['cpu_percent'],
            'current_value': system['cpu_percent']
        })
    
    # 内存告警
    if system.get('memory_percent', 0) > ALERT_THRESHOLDS['memory_percent']:
        alerts.append({
            'type': 'memory_high',
            'severity': 'warning',
            'message': f"内存使用率过高: {system['memory_percent']:.1f}%",
            'threshold': ALERT_THRESHOLDS['memory_percent'],
            'current_value': system['memory_percent']
        })
    
    if system.get('memory_available_gb', 0) < ALERT_THRESHOLDS['memory_available_gb']:
        alerts.append({
            'type': 'memory_low',
            'severity': 'critical',
            'message': f"可用内存不足: {system['memory_available_gb']:.2f}GB",
            'threshold': ALERT_THRESHOLDS['memory_available_gb'],
            'current_value': system['memory_available_gb']
        })
    
    # 磁盘告警
    if system.get('disk_percent', 0) > ALERT_THRESHOLDS['disk_percent']:
        alerts.append({
            'type': 'disk_high',
            'severity': 'critical',
            'message': f"磁盘使用率过高: {system['disk_percent']:.1f}%",
            'threshold': ALERT_THRESHOLDS['disk_percent'],
            'current_value': system['disk_percent']
        })
    
    if system.get('disk_free_gb', 0) < ALERT_THRESHOLDS['disk_free_gb']:
        alerts.append({
            'type': 'disk_low',
            'severity': 'critical',
            'message': f"剩余磁盘空间不足: {system['disk_free_gb']:.2f}GB",
            'threshold': ALERT_THRESHOLDS['disk_free_gb'],
            'current_value': system['disk_free_gb']
        })
    
    # Celery告警
    if not celery_info.get('broker_connected', False):
        alerts.append({
            'type': 'broker_disconnected',
            'severity': 'critical',
            'message': 'Celery消息代理连接断开',
            'current_value': False
        })
    
    if celery_info.get('worker_count', 0) == 0:
        alerts.append({
            'type': 'no_workers',
            'severity': 'critical',
            'message': '没有可用的Celery Worker',
            'current_value': 0
        })
    
    # 任务失败率告警
    failure_rate = tasks.get('failure_rate', 0)
    if failure_rate > ALERT_THRESHOLDS['failure_rate']:
        alerts.append({
            'type': 'high_failure_rate',
            'severity': 'warning',
            'message': f"任务失败率过高: {failure_rate:.1f}%",
            'threshold': ALERT_THRESHOLDS['failure_rate'],
            'current_value': failure_rate
        })
    
    return alerts


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 300})
def cleanup_monitoring_data(self) -> Dict[str, Any]:
    """清理监控数据"""
    db: Session = SessionLocal()
    
    try:
        monitor_service = CeleryMonitorService(db)
        
        # 清理30天前的任务监控记录
        monitor_service.cleanup_old_records(days=30)
        
        return {
            'success': True,
            'message': '监控数据清理完成'
        }
        
    except Exception as e:
        logger.error(f"清理监控数据失败: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def collect_worker_statistics(self) -> Dict[str, Any]:
    """收集Worker统计数据"""
    db: Session = SessionLocal()
    
    try:
        # 获取Worker信息
        inspect = celery_app.control.inspect()
        worker_stats = inspect.stats()
        ping_results = inspect.ping()
        
        if not worker_stats:
            logger.warning("无法获取Worker统计信息")
            return {'success': False, 'message': '无法获取Worker统计信息'}
        
        current_time = datetime.now()
        today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for worker_name, stats in worker_stats.items():
            # 查找或创建Worker统计记录
            worker_stat = db.query(WorkerStatistics).filter(
                and_(
                    WorkerStatistics.worker_name == worker_name,
                    WorkerStatistics.date >= today
                )
            ).first()
            
            if not worker_stat:
                worker_stat = WorkerStatistics(
                    worker_name=worker_name,
                    date=today
                )
                db.add(worker_stat)
            
            # 更新统计数据
            pool_stats = stats.get('pool', {})
            rusage = stats.get('rusage', {})
            
            worker_stat.processed_tasks = pool_stats.get('processes', [0])[0] if pool_stats.get('processes') else 0
            worker_stat.total_runtime_seconds = rusage.get('utime', 0) + rusage.get('stime', 0)
            
            # 获取系统资源使用情况（如果可用）
            try:
                current_process = psutil.Process()
                worker_stat.avg_cpu_percent = current_process.cpu_percent()
                worker_stat.avg_memory_mb = current_process.memory_info().rss / 1024 / 1024
            except Exception as e:
                logger.debug(f"无法获取进程资源信息: {e}")
        
        db.commit()
        
        return {
            'success': True,
            'message': 'Worker统计数据收集完成',
            'workers_processed': len(worker_stats)
        }
        
    except Exception as e:
        logger.error(f"收集Worker统计数据失败: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()


@celery_app.task(bind=True)
def generate_health_report(self, days: int = 7) -> Dict[str, Any]:
    """生成健康报告"""
    db: Session = SessionLocal()
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # 获取Beat健康记录
        beat_health_records = db.query(CeleryBeatHealth).filter(
            CeleryBeatHealth.created_at >= start_date
        ).order_by(desc(CeleryBeatHealth.created_at)).limit(1000).all()
        
        # 获取任务统计
        task_stats = db.query(
            func.date(CeleryTaskMonitor.created_at).label('date'),
            func.count(CeleryTaskMonitor.id).label('total'),
            func.sum(
                func.case([(CeleryTaskMonitor.status == 'SUCCESS', 1)], else_=0)
            ).label('success'),
            func.sum(
                func.case([(CeleryTaskMonitor.status == 'FAILURE', 1)], else_=0)
            ).label('failed'),
            func.avg(CeleryTaskMonitor.runtime_seconds).label('avg_runtime')
        ).filter(
            CeleryTaskMonitor.created_at >= start_date
        ).group_by(
            func.date(CeleryTaskMonitor.created_at)
        ).all()
        
        # 生成报告
        report = {
            'period': f'{days}天',
            'generated_at': datetime.now().isoformat(),
            'beat_health': {
                'total_records': len(beat_health_records),
                'avg_cpu_percent': sum(r.cpu_percent or 0 for r in beat_health_records) / len(beat_health_records) if beat_health_records else 0,
                'avg_memory_mb': sum(r.memory_mb or 0 for r in beat_health_records) / len(beat_health_records) if beat_health_records else 0,
                'uptime_percentage': sum(1 for r in beat_health_records if r.is_alive) / len(beat_health_records) * 100 if beat_health_records else 0
            },
            'task_statistics': [
                {
                    'date': stat.date.isoformat() if stat.date else None,
                    'total': stat.total,
                    'success': stat.success,
                    'failed': stat.failed,
                    'success_rate': (stat.success / stat.total * 100) if stat.total > 0 else 0,
                    'avg_runtime': round(stat.avg_runtime or 0, 2)
                }
                for stat in task_stats
            ]
        }
        
        # 生成总结和建议
        total_tasks = sum(stat.total for stat in task_stats)
        total_success = sum(stat.success for stat in task_stats)
        overall_success_rate = (total_success / total_tasks * 100) if total_tasks > 0 else 0
        
        report['summary'] = {
            'total_tasks': total_tasks,
            'overall_success_rate': round(overall_success_rate, 2),
            'recommendations': generate_recommendations(report)
        }
        
        return {
            'success': True,
            'message': '健康报告生成完成',
            'data': report
        }
        
    except Exception as e:
        logger.error(f"生成健康报告失败: {e}")
        return {
            'success': False,
            'message': f'生成健康报告失败: {str(e)}'
        }
        
    finally:
        db.close()


def generate_recommendations(report: Dict[str, Any]) -> List[str]:
    """生成优化建议"""
    recommendations = []
    
    beat_health = report.get('beat_health', {})
    task_stats = report.get('task_statistics', [])
    
    # Beat健康检查建议
    avg_cpu = beat_health.get('avg_cpu_percent', 0)
    if avg_cpu > 50:
        recommendations.append(f"Beat进程CPU使用率较高({avg_cpu:.1f}%)，建议优化定时任务频率")
    
    avg_memory = beat_health.get('avg_memory_mb', 0)
    if avg_memory > 200:
        recommendations.append(f"Beat进程内存使用较高({avg_memory:.1f}MB)，建议检查内存泄漏")
    
    uptime = beat_health.get('uptime_percentage', 0)
    if uptime < 95:
        recommendations.append(f"Beat进程稳定性较低({uptime:.1f}%)，建议检查重启原因")
    
    # 任务执行建议
    if task_stats:
        avg_success_rate = sum(stat['success_rate'] for stat in task_stats) / len(task_stats)
        if avg_success_rate < 90:
            recommendations.append(f"任务成功率偏低({avg_success_rate:.1f}%)，建议检查失败原因")
        
        avg_runtime = sum(stat['avg_runtime'] for stat in task_stats) / len(task_stats)
        if avg_runtime > 60:
            recommendations.append(f"平均任务执行时间较长({avg_runtime:.1f}s)，建议优化任务逻辑")
    
    if not recommendations:
        recommendations.append("系统运行状态良好，无需特殊优化")
    
    return recommendations