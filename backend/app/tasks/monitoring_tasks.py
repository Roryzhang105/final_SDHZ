"""
监控和清理任务模块
用于监控系统运行状态、清理过期数据、生成统计报告和发送告警
"""

import os
import logging
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import current_app as celery_app
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.task import Task, TaskStatusEnum
from app.models.delivery_receipt import DeliveryReceipt, DeliveryStatusEnum
from app.models.tracking import TrackingInfo

# 设置日志
logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 300})
def cleanup_expired_tasks(self) -> Dict[str, Any]:
    """
    清理过期任务和相关数据
    每天凌晨4点执行，清理超过保留期限的已完成任务
    """
    start_time = datetime.now()
    logger.info(f"开始执行过期任务清理 - {start_time}")
    
    db: Session = SessionLocal()
    
    try:
        # 配置清理策略
        cleanup_config = {
            "completed_tasks_days": 30,    # 完成任务保留30天
            "failed_tasks_days": 7,        # 失败任务保留7天
            "temp_files_hours": 24,        # 临时文件保留24小时
            "log_files_days": 30           # 日志文件保留30天
        }
        
        stats = {
            "tasks_cleaned": 0,
            "files_cleaned": 0,
            "receipts_cleaned": 0,
            "logs_cleaned": 0,
            "disk_space_freed_mb": 0,
            "errors": []
        }
        
        # 1. 清理过期的已完成任务
        completed_threshold = datetime.now() - timedelta(days=cleanup_config["completed_tasks_days"])
        completed_tasks = db.query(Task).filter(
            and_(
                Task.status == TaskStatusEnum.COMPLETED,
                Task.completed_at < completed_threshold
            )
        ).all()
        
        for task in completed_tasks:
            try:
                # 清理任务相关文件
                files_freed = cleanup_task_files(task)
                stats["disk_space_freed_mb"] += files_freed
                
                # 删除任务记录
                db.delete(task)
                stats["tasks_cleaned"] += 1
                
            except Exception as e:
                error_msg = f"清理完成任务 {task.task_id} 失败: {str(e)}"
                stats["errors"].append(error_msg)
                logger.error(error_msg)
        
        # 2. 清理过期的失败任务
        failed_threshold = datetime.now() - timedelta(days=cleanup_config["failed_tasks_days"])
        failed_tasks = db.query(Task).filter(
            and_(
                Task.status == TaskStatusEnum.FAILED,
                Task.updated_at < failed_threshold
            )
        ).all()
        
        for task in failed_tasks:
            try:
                # 清理任务相关文件
                files_freed = cleanup_task_files(task)
                stats["disk_space_freed_mb"] += files_freed
                
                # 删除任务记录
                db.delete(task)
                stats["tasks_cleaned"] += 1
                
            except Exception as e:
                error_msg = f"清理失败任务 {task.task_id} 失败: {str(e)}"
                stats["errors"].append(error_msg)
                logger.error(error_msg)
        
        # 3. 清理过期的回证记录（没有关联任务的）
        orphan_receipts = db.query(DeliveryReceipt).filter(
            and_(
                DeliveryReceipt.created_at < completed_threshold,
                ~DeliveryReceipt.tracking_number.in_(
                    db.query(Task.tracking_number).filter(Task.tracking_number.isnot(None))
                )
            )
        ).all()
        
        for receipt in orphan_receipts:
            try:
                # 清理回证相关文件
                files_freed = cleanup_receipt_files(receipt)
                stats["disk_space_freed_mb"] += files_freed
                
                # 删除关联的跟踪信息
                if receipt.tracking_info:
                    db.delete(receipt.tracking_info)
                
                # 删除回证记录
                db.delete(receipt)
                stats["receipts_cleaned"] += 1
                
            except Exception as e:
                error_msg = f"清理回证记录 {receipt.id} 失败: {str(e)}"
                stats["errors"].append(error_msg)
                logger.error(error_msg)
        
        # 4. 清理临时文件
        temp_freed = cleanup_temp_files(cleanup_config["temp_files_hours"])
        stats["disk_space_freed_mb"] += temp_freed
        stats["files_cleaned"] = temp_freed
        
        # 5. 清理过期日志文件
        logs_freed = cleanup_log_files(cleanup_config["log_files_days"])
        stats["disk_space_freed_mb"] += logs_freed
        stats["logs_cleaned"] = logs_freed
        
        # 提交数据库更改
        db.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"过期任务清理完成 - 耗时: {execution_time:.2f}秒, 统计: {stats}")
        
        return {
            "success": True,
            "message": "过期任务清理完成",
            "stats": stats,
            "execution_time": execution_time
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"过期任务清理失败: {str(e)}", exc_info=True)
        raise self.retry(exc=e)
        
    finally:
        db.close()


def cleanup_task_files(task: Task) -> float:
    """
    清理任务相关的文件，返回释放的磁盘空间(MB)
    """
    freed_space = 0.0
    
    files_to_clean = [
        task.image_path,
        task.document_path,
        task.screenshot_path
    ]
    
    for file_path in files_to_clean:
        if file_path and os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                freed_space += file_size / (1024 * 1024)  # 转换为MB
                logger.debug(f"删除文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败 {file_path}: {e}")
    
    return freed_space


def cleanup_receipt_files(receipt: DeliveryReceipt) -> float:
    """
    清理回证相关的文件，返回释放的磁盘空间(MB)
    """
    freed_space = 0.0
    
    files_to_clean = [
        receipt.qr_code_path,
        receipt.barcode_path,
        receipt.receipt_file_path,
        receipt.tracking_screenshot_path,
        receipt.delivery_receipt_doc_path
    ]
    
    if receipt.tracking_info:
        files_to_clean.append(receipt.tracking_info.screenshot_path)
    
    for file_path in files_to_clean:
        if file_path and os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                freed_space += file_size / (1024 * 1024)
                logger.debug(f"删除回证文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除回证文件失败 {file_path}: {e}")
    
    return freed_space


def cleanup_temp_files(hours_threshold: int) -> float:
    """
    清理临时文件，返回释放的磁盘空间(MB)
    """
    freed_space = 0.0
    temp_dirs = [
        "/tmp",
        "uploads/temp",
        "static/temp"
    ]
    
    cutoff_time = datetime.now() - timedelta(hours=hours_threshold)
    
    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            continue
            
        try:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # 检查文件修改时间
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_mtime < cutoff_time:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            freed_space += file_size / (1024 * 1024)
                    except Exception as e:
                        logger.warning(f"清理临时文件失败 {file_path}: {e}")
                        
        except Exception as e:
            logger.warning(f"清理临时目录失败 {temp_dir}: {e}")
    
    return freed_space


def cleanup_log_files(days_threshold: int) -> float:
    """
    清理过期日志文件，返回释放的磁盘空间(MB)
    """
    freed_space = 0.0
    log_dirs = [
        "logs",
        "/var/log/celery",
        "/var/log/delivery_receipt"
    ]
    
    cutoff_time = datetime.now() - timedelta(days=days_threshold)
    
    for log_dir in log_dirs:
        if not os.path.exists(log_dir):
            continue
            
        try:
            for file in os.listdir(log_dir):
                file_path = os.path.join(log_dir, file)
                if os.path.isfile(file_path):
                    try:
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_mtime < cutoff_time and file.endswith('.log'):
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            freed_space += file_size / (1024 * 1024)
                            logger.debug(f"删除日志文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"删除日志文件失败 {file_path}: {e}")
                        
        except Exception as e:
            logger.warning(f"清理日志目录失败 {log_dir}: {e}")
    
    return freed_space


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 180})
def generate_daily_statistics(self) -> Dict[str, Any]:
    """
    生成每日任务执行统计报告
    每天凌晨2点执行
    """
    start_time = datetime.now()
    logger.info(f"开始生成每日统计报告 - {start_time}")
    
    db: Session = SessionLocal()
    
    try:
        # 统计昨天的数据
        yesterday = (datetime.now() - timedelta(days=1)).date()
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_end = datetime.combine(yesterday, datetime.max.time())
        
        # 基础任务统计
        task_stats = generate_task_statistics(db, yesterday_start, yesterday_end)
        
        # 性能统计
        performance_stats = generate_performance_statistics(db, yesterday_start, yesterday_end)
        
        # 错误统计
        error_stats = generate_error_statistics(db, yesterday_start, yesterday_end)
        
        # 系统资源统计
        system_stats = generate_system_statistics()
        
        # 趋势分析
        trend_stats = generate_trend_analysis(db, yesterday)
        
        daily_report = {
            "date": yesterday.isoformat(),
            "task_statistics": task_stats,
            "performance_statistics": performance_stats,
            "error_statistics": error_stats,
            "system_statistics": system_stats,
            "trend_analysis": trend_stats,
            "generated_at": start_time.isoformat()
        }
        
        # 保存报告到文件
        report_saved = save_daily_report(daily_report, yesterday)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"每日统计报告生成完成 - 耗时: {execution_time:.2f}秒")
        
        # 检查是否需要发送告警
        alerts = check_daily_alerts(daily_report)
        if alerts:
            logger.warning(f"发现 {len(alerts)} 个告警项目")
        
        return {
            "success": True,
            "message": "每日统计报告生成完成",
            "report": daily_report,
            "report_saved": report_saved,
            "alerts": alerts,
            "execution_time": execution_time
        }
        
    except Exception as e:
        logger.error(f"生成每日统计报告失败: {str(e)}", exc_info=True)
        raise self.retry(exc=e)
        
    finally:
        db.close()


def generate_task_statistics(db: Session, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    生成任务执行统计
    """
    try:
        # 基础统计查询
        total_tasks = db.query(func.count(Task.id)).filter(
            Task.created_at.between(start_time, end_time)
        ).scalar()
        
        # 按状态统计
        status_stats = db.query(
            Task.status,
            func.count(Task.id).label('count')
        ).filter(
            Task.created_at.between(start_time, end_time)
        ).group_by(Task.status).all()
        
        status_dict = {status.value: 0 for status in TaskStatusEnum}
        for status, count in status_stats:
            status_dict[status.value] = count
        
        # 完成率计算
        completed_count = status_dict.get(TaskStatusEnum.COMPLETED.value, 0)
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # 失败率计算
        failed_count = status_dict.get(TaskStatusEnum.FAILED.value, 0)
        failure_rate = (failed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # 平均处理时间
        avg_processing_time = db.query(
            func.avg(Task.processing_time)
        ).filter(
            and_(
                Task.created_at.between(start_time, end_time),
                Task.processing_time.isnot(None)
            )
        ).scalar()
        
        return {
            "total_tasks": total_tasks,
            "status_breakdown": status_dict,
            "completion_rate": round(completion_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "average_processing_time": round(float(avg_processing_time or 0), 2)
        }
        
    except Exception as e:
        logger.error(f"生成任务统计失败: {e}")
        return {}


def generate_performance_statistics(db: Session, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    生成性能统计
    """
    try:
        # 最慢的任务
        slowest_tasks = db.query(Task).filter(
            and_(
                Task.created_at.between(start_time, end_time),
                Task.processing_time.isnot(None)
            )
        ).order_by(desc(Task.processing_time)).limit(5).all()
        
        slowest_list = [
            {
                "task_id": task.task_id,
                "processing_time": task.processing_time,
                "status": task.status.value
            }
            for task in slowest_tasks
        ]
        
        # 按小时分布
        hourly_distribution = db.query(
            func.extract('hour', Task.created_at).label('hour'),
            func.count(Task.id).label('count')
        ).filter(
            Task.created_at.between(start_time, end_time)
        ).group_by(func.extract('hour', Task.created_at)).all()
        
        hourly_dict = {hour: 0 for hour in range(24)}
        for hour, count in hourly_distribution:
            hourly_dict[int(hour)] = count
        
        return {
            "slowest_tasks": slowest_list,
            "hourly_distribution": hourly_dict,
            "peak_hour": max(hourly_dict, key=hourly_dict.get) if hourly_dict else 0
        }
        
    except Exception as e:
        logger.error(f"生成性能统计失败: {e}")
        return {}


def generate_error_statistics(db: Session, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    生成错误统计
    """
    try:
        # 失败任务的错误信息统计
        failed_tasks = db.query(Task).filter(
            and_(
                Task.created_at.between(start_time, end_time),
                Task.status == TaskStatusEnum.FAILED,
                Task.error_message.isnot(None)
            )
        ).all()
        
        error_categories = {}
        for task in failed_tasks:
            error_msg = task.error_message or "未知错误"
            # 简单的错误分类
            if "二维码" in error_msg:
                category = "二维码识别错误"
            elif "物流" in error_msg:
                category = "物流查询错误"
            elif "文档" in error_msg:
                category = "文档生成错误"
            elif "超时" in error_msg:
                category = "任务超时"
            elif "数据库" in error_msg:
                category = "数据库错误"
            else:
                category = "其他错误"
            
            error_categories[category] = error_categories.get(category, 0) + 1
        
        # 重试次数统计
        retry_stats = db.query(
            Task.retry_count,
            func.count(Task.id).label('count')
        ).filter(
            and_(
                Task.created_at.between(start_time, end_time),
                Task.retry_count > 0
            )
        ).group_by(Task.retry_count).all()
        
        retry_dict = {retry_count: count for retry_count, count in retry_stats}
        
        return {
            "error_categories": error_categories,
            "retry_statistics": retry_dict,
            "total_failed_tasks": len(failed_tasks)
        }
        
    except Exception as e:
        logger.error(f"生成错误统计失败: {e}")
        return {}


def generate_system_statistics() -> Dict[str, Any]:
    """
    生成系统资源统计
    """
    try:
        # 磁盘使用情况
        total, used, free = shutil.disk_usage("/")
        disk_usage = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round((used / total) * 100, 2)
        }
        
        # Celery队列状态
        queue_stats = get_celery_queue_stats()
        
        return {
            "disk_usage": disk_usage,
            "queue_statistics": queue_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"生成系统统计失败: {e}")
        return {}


def get_celery_queue_stats() -> Dict[str, Any]:
    """
    获取Celery队列统计信息
    """
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        
        # 获取活跃任务
        active_tasks = inspect.active()
        
        # 获取预定任务
        scheduled_tasks = inspect.scheduled()
        
        # 获取保留任务
        reserved_tasks = inspect.reserved()
        
        total_active = sum(len(tasks) for tasks in (active_tasks or {}).values())
        total_scheduled = sum(len(tasks) for tasks in (scheduled_tasks or {}).values())
        total_reserved = sum(len(tasks) for tasks in (reserved_tasks or {}).values())
        
        return {
            "active_tasks": total_active,
            "scheduled_tasks": total_scheduled,
            "reserved_tasks": total_reserved,
            "total_pending": total_active + total_scheduled + total_reserved
        }
        
    except Exception as e:
        logger.warning(f"获取Celery队列统计失败: {e}")
        return {}


def generate_trend_analysis(db: Session, target_date: datetime.date) -> Dict[str, Any]:
    """
    生成趋势分析（与前几天对比）
    """
    try:
        # 获取过去7天的数据
        days_data = []
        for i in range(7):
            date = target_date - timedelta(days=i)
            day_start = datetime.combine(date, datetime.min.time())
            day_end = datetime.combine(date, datetime.max.time())
            
            day_stats = db.query(
                func.count(Task.id).label('total'),
                func.sum(func.case([(Task.status == TaskStatusEnum.COMPLETED, 1)], else_=0)).label('completed'),
                func.sum(func.case([(Task.status == TaskStatusEnum.FAILED, 1)], else_=0)).label('failed')
            ).filter(
                Task.created_at.between(day_start, day_end)
            ).first()
            
            days_data.append({
                "date": date.isoformat(),
                "total": int(day_stats.total or 0),
                "completed": int(day_stats.completed or 0),
                "failed": int(day_stats.failed or 0)
            })
        
        # 计算趋势
        if len(days_data) >= 2:
            today_total = days_data[0]["total"]
            yesterday_total = days_data[1]["total"]
            
            trend_percent = 0
            if yesterday_total > 0:
                trend_percent = ((today_total - yesterday_total) / yesterday_total) * 100
        else:
            trend_percent = 0
        
        return {
            "past_7_days": days_data,
            "trend_percent": round(trend_percent, 2),
            "trend_direction": "增长" if trend_percent > 0 else "下降" if trend_percent < 0 else "持平"
        }
        
    except Exception as e:
        logger.error(f"生成趋势分析失败: {e}")
        return {}


def save_daily_report(report: Dict[str, Any], report_date: datetime.date) -> bool:
    """
    保存每日报告到文件
    """
    try:
        # 确保报告目录存在
        reports_dir = "reports/daily"
        os.makedirs(reports_dir, exist_ok=True)
        
        # 生成报告文件名
        report_filename = f"daily_report_{report_date.strftime('%Y%m%d')}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        # 保存报告
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"每日报告已保存: {report_path}")
        return True
        
    except Exception as e:
        logger.error(f"保存每日报告失败: {e}")
        return False


def check_daily_alerts(report: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    检查是否需要发送告警
    """
    alerts = []
    
    try:
        task_stats = report.get("task_statistics", {})
        system_stats = report.get("system_statistics", {})
        error_stats = report.get("error_statistics", {})
        
        # 检查失败率告警
        failure_rate = task_stats.get("failure_rate", 0)
        if failure_rate > 20:  # 失败率超过20%
            alerts.append({
                "type": "high_failure_rate",
                "message": f"任务失败率过高: {failure_rate}%",
                "severity": "warning"
            })
        
        if failure_rate > 50:  # 失败率超过50%
            alerts.append({
                "type": "critical_failure_rate",
                "message": f"任务失败率严重过高: {failure_rate}%",
                "severity": "critical"
            })
        
        # 检查磁盘空间告警
        disk_usage = system_stats.get("disk_usage", {})
        usage_percent = disk_usage.get("usage_percent", 0)
        if usage_percent > 80:
            alerts.append({
                "type": "disk_space_warning",
                "message": f"磁盘使用率过高: {usage_percent}%",
                "severity": "warning"
            })
        
        if usage_percent > 90:
            alerts.append({
                "type": "disk_space_critical",
                "message": f"磁盘使用率严重过高: {usage_percent}%",
                "severity": "critical"
            })
        
        # 检查任务量异常
        total_tasks = task_stats.get("total_tasks", 0)
        if total_tasks == 0:
            alerts.append({
                "type": "no_tasks",
                "message": "今日没有处理任何任务",
                "severity": "warning"
            })
        
        # 检查错误类型集中度
        error_categories = error_stats.get("error_categories", {})
        total_errors = sum(error_categories.values())
        if total_errors > 0:
            for category, count in error_categories.items():
                if count / total_errors > 0.5:  # 某类错误占比超过50%
                    alerts.append({
                        "type": "concentrated_errors",
                        "message": f"错误类型集中: {category} 占 {count}/{total_errors}",
                        "severity": "warning"
                    })
        
    except Exception as e:
        logger.error(f"检查告警失败: {e}")
        alerts.append({
            "type": "alert_check_error",
            "message": f"告警检查失败: {str(e)}",
            "severity": "error"
        })
    
    return alerts


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 120})
def send_alert_notification(self, alerts: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    发送告警通知
    """
    start_time = datetime.now()
    logger.info(f"开始发送告警通知 - {start_time}, 告警数量: {len(alerts)}")
    
    try:
        if not alerts:
            return {
                "success": True,
                "message": "无需发送告警通知",
                "alerts_sent": 0
            }
        
        # 按严重级别分组
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
        error_alerts = [a for a in alerts if a.get("severity") == "error"]
        
        notifications_sent = 0
        
        # 发送严重告警
        if critical_alerts:
            result = send_critical_alerts(critical_alerts)
            if result:
                notifications_sent += len(critical_alerts)
        
        # 发送警告告警
        if warning_alerts:
            result = send_warning_alerts(warning_alerts)
            if result:
                notifications_sent += len(warning_alerts)
        
        # 发送错误告警
        if error_alerts:
            result = send_error_alerts(error_alerts)
            if result:
                notifications_sent += len(error_alerts)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"告警通知发送完成 - 耗时: {execution_time:.2f}秒, 发送数量: {notifications_sent}")
        
        return {
            "success": True,
            "message": f"发送了 {notifications_sent} 个告警通知",
            "alerts_sent": notifications_sent,
            "execution_time": execution_time
        }
        
    except Exception as e:
        logger.error(f"发送告警通知失败: {str(e)}", exc_info=True)
        raise self.retry(exc=e)


def send_critical_alerts(alerts: List[Dict[str, str]]) -> bool:
    """
    发送严重告警通知
    """
    try:
        # 这里可以实现真实的告警发送逻辑
        # 例如：发送邮件、发送短信、调用webhook等
        
        logger.critical(f"发送严重告警: {len(alerts)} 个")
        for alert in alerts:
            logger.critical(f"严重告警: {alert['message']}")
        
        # 示例：发送到日志文件
        alert_log_path = "logs/critical_alerts.log"
        os.makedirs(os.path.dirname(alert_log_path), exist_ok=True)
        
        with open(alert_log_path, 'a', encoding='utf-8') as f:
            for alert in alerts:
                f.write(f"{datetime.now().isoformat()} - CRITICAL - {alert['message']}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"发送严重告警失败: {e}")
        return False


def send_warning_alerts(alerts: List[Dict[str, str]]) -> bool:
    """
    发送警告告警通知
    """
    try:
        logger.warning(f"发送警告告警: {len(alerts)} 个")
        for alert in alerts:
            logger.warning(f"警告告警: {alert['message']}")
        
        # 示例：发送到日志文件
        alert_log_path = "logs/warning_alerts.log"
        os.makedirs(os.path.dirname(alert_log_path), exist_ok=True)
        
        with open(alert_log_path, 'a', encoding='utf-8') as f:
            for alert in alerts:
                f.write(f"{datetime.now().isoformat()} - WARNING - {alert['message']}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"发送警告告警失败: {e}")
        return False


def send_error_alerts(alerts: List[Dict[str, str]]) -> bool:
    """
    发送错误告警通知
    """
    try:
        logger.error(f"发送错误告警: {len(alerts)} 个")
        for alert in alerts:
            logger.error(f"错误告警: {alert['message']}")
        
        # 示例：发送到日志文件
        alert_log_path = "logs/error_alerts.log"
        os.makedirs(os.path.dirname(alert_log_path), exist_ok=True)
        
        with open(alert_log_path, 'a', encoding='utf-8') as f:
            for alert in alerts:
                f.write(f"{datetime.now().isoformat()} - ERROR - {alert['message']}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"发送错误告警失败: {e}")
        return False


@celery_app.task
def check_disk_space() -> Dict[str, Any]:
    """
    检查磁盘空间使用情况
    每小时15分执行
    """
    start_time = datetime.now()
    logger.info(f"开始检查磁盘空间 - {start_time}")
    
    try:
        total, used, free = shutil.disk_usage("/")
        
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)
        free_gb = free / (1024**3)
        usage_percent = (used / total) * 100
        
        disk_info = {
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "usage_percent": round(usage_percent, 2),
            "status": "normal"
        }
        
        # 判断磁盘使用状态
        if usage_percent > 90:
            disk_info["status"] = "critical"
            logger.critical(f"磁盘空间严重不足: {usage_percent:.1f}%")
        elif usage_percent > 80:
            disk_info["status"] = "warning"
            logger.warning(f"磁盘空间不足: {usage_percent:.1f}%")
        else:
            disk_info["status"] = "normal"
            logger.info(f"磁盘空间正常: {usage_percent:.1f}%")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "disk_info": disk_info,
            "execution_time": execution_time
        }
        
    except Exception as e:
        logger.error(f"检查磁盘空间失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }