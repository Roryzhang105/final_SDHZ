"""
Celery Beat 定时任务配置文件
包含所有定时任务的调度配置
"""

from celery.schedules import crontab

# 定时任务配置
BEAT_SCHEDULE = {
    # ============ 任务监控和状态更新 ============
    
    # 每5分钟检查待处理的任务
    'check-pending-tasks': {
        'task': 'app.tasks.tracking_tasks.check_pending_tasks',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'tracking'},
        'description': '检查并处理待处理的任务，重试失败的任务'
    },
    
    # 每小时更新所有未完成的物流状态
    'update-all-pending-tracking': {
        'task': 'app.tasks.tracking_tasks.update_all_pending_tracking',
        'schedule': crontab(minute=0),  # 每小时整点执行
        'options': {'queue': 'tracking'},
        'description': '批量更新所有未完成的物流跟踪信息'
    },
    
    # 每30分钟检查超时任务
    'check-timeout-tasks': {
        'task': 'app.tasks.tracking_tasks.check_timeout_tasks',
        'schedule': crontab(minute='*/30'),
        'options': {'queue': 'tracking'},
        'description': '检查并处理超时的任务'
    },
    
    # 每30分钟扫描和处理失败任务
    'scan-and-process-failed-tasks': {
        'task': 'app.tasks.failure_tasks.scan_and_process_failed_tasks',
        'schedule': crontab(minute='*/30'),
        'options': {'queue': 'recovery'},
        'description': '扫描失败任务，自动分析和恢复可恢复的任务'
    },
    
    # ============ 文件和数据清理 ============
    
    # 每小时清理临时文件
    'cleanup-temp-files': {
        'task': 'app.tasks.file_tasks.cleanup_temp_files',
        'schedule': crontab(minute=0),  # 每小时整点执行
        'options': {'queue': 'file'},
        'description': '清理临时文件和过期的上传文件'
    },
    
    # 每2小时清理过期的任务结果
    'cleanup-expired-results': {
        'task': 'app.tasks.file_tasks.cleanup_expired_results',
        'schedule': crontab(minute=0, hour='*/2'),
        'options': {'queue': 'file'},
        'description': '清理过期的Celery任务结果'
    },
    
    # ============ 每日任务 ============
    
    # 每天凌晨2点生成统计报告
    'generate-daily-statistics': {
        'task': 'app.tasks.monitoring_tasks.generate_daily_statistics',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'receipt'},
        'description': '生成每日任务处理统计报告'
    },
    
    # 每天凌晨2:30优化数据库
    'optimize-database': {
        'task': 'app.tasks.file_tasks.optimize_database',
        'schedule': crontab(hour=2, minute=30),
        'options': {'queue': 'file'},
        'description': '优化数据库性能，重建索引'
    },
    
    # 每天凌晨3点备份数据库
    'backup-database': {
        'task': 'app.tasks.file_tasks.backup_database',
        'schedule': crontab(hour=3, minute=0),
        'options': {'queue': 'file'},
        'description': '备份数据库到本地和云存储'
    },
    
    # 每天凌晨4点清理过期任务
    'cleanup-expired-tasks': {
        'task': 'app.tasks.monitoring_tasks.cleanup_expired_tasks',
        'schedule': crontab(hour=4, minute=0),
        'options': {'queue': 'file'},
        'description': '清理超过保留期限的已完成任务'
    },
    
    # ============ 每周任务 ============
    
    # 每周日凌晨4点清理日志文件
    'cleanup-logs': {
        'task': 'app.tasks.file_tasks.cleanup_old_logs',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # 0 = 周日
        'options': {'queue': 'file'},
        'description': '清理过期的日志文件'
    },
    
    # 每周一早上8点发送周报
    'generate-weekly-report': {
        'task': 'app.tasks.receipt_tasks.generate_weekly_report',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # 1 = 周一
        'options': {'queue': 'receipt'},
        'description': '生成和发送周统计报告'
    },
    
    # ============ 每月任务 ============
    
    # 每月1号凌晨5点归档旧数据
    'archive-old-data': {
        'task': 'app.tasks.file_tasks.archive_old_data',
        'schedule': crontab(hour=5, minute=0, day_of_month=1),
        'options': {'queue': 'file'},
        'description': '归档超过3个月的历史数据'
    },
    
    # 每月1号上午9点生成月报
    'generate-monthly-report': {
        'task': 'app.tasks.receipt_tasks.generate_monthly_report',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),
        'options': {'queue': 'receipt'},
        'description': '生成月度统计报告'
    },
    
    # ============ 健康检查 ============
    
    # 每10分钟系统健康检查
    'system-health-check': {
        'task': 'app.tasks.tracking_tasks.system_health_check',
        'schedule': crontab(minute='*/10'),
        'options': {'queue': 'tracking'},
        'description': '检查系统服务状态和资源使用情况'
    },
    
    # 每小时检查磁盘空间
    'disk-space-check': {
        'task': 'app.tasks.monitoring_tasks.check_disk_space',
        'schedule': crontab(minute=15),  # 每小时15分执行
        'options': {'queue': 'file'},
        'description': '检查磁盘空间使用情况，发送告警'
    },
    
    # ============ 失败任务处理 ============
    
    # 每6小时分析失败任务模式
    'analyze-failure-patterns': {
        'task': 'app.tasks.failure_tasks.analyze_failure_patterns',
        'schedule': crontab(minute=0, hour='*/6'),
        'options': {'queue': 'monitoring'},
        'description': '分析失败任务模式，生成趋势报告和改进建议'
    }
}

# 任务优先级配置
TASK_PRIORITIES = {
    'check-pending-tasks': 9,
    'scan-and-process-failed-tasks': 8,           # 失败任务恢复优先级高
    'update-all-pending-tracking': 8,
    'system-health-check': 7,
    'check-timeout-tasks': 6,
    'disk-space-check': 5,
    'cleanup-temp-files': 4,
    'analyze-failure-patterns': 3,               # 失败分析优先级中等
    'generate-daily-statistics': 3,
    'cleanup-expired-tasks': 2,
    'backup-database': 2,
    'cleanup-logs': 1
}

# 任务重试配置
TASK_RETRY_CONFIG = {
    'default': {
        'autoretry_for': (Exception,),
        'retry_kwargs': {'max_retries': 3, 'countdown': 60},
        'retry_backoff': True,
        'retry_jitter': True
    },
    'critical': {
        'autoretry_for': (Exception,),
        'retry_kwargs': {'max_retries': 5, 'countdown': 30},
        'retry_backoff': True,
        'retry_jitter': True
    }
}

# 队列路由配置
TASK_ROUTES = {
    # 高优先级任务
    'app.tasks.tracking_tasks.check_pending_tasks': {'queue': 'high_priority'},
    'app.tasks.tracking_tasks.system_health_check': {'queue': 'high_priority'},
    
    # 普通任务
    'app.tasks.tracking_tasks.update_all_pending_tracking': {'queue': 'tracking'},
    'app.tasks.tracking_tasks.update_tracking_info': {'queue': 'tracking'},
    'app.tasks.tracking_tasks.check_timeout_tasks': {'queue': 'tracking'},
    'app.tasks.receipt_tasks.*': {'queue': 'receipt'},
    'app.tasks.screenshot_tasks.*': {'queue': 'screenshot'},
    
    # 低优先级任务
    'app.tasks.file_tasks.cleanup_*': {'queue': 'low_priority'},
    'app.tasks.file_tasks.backup_*': {'queue': 'low_priority'},
    'app.tasks.file_tasks.archive_*': {'queue': 'low_priority'},
    'app.tasks.monitoring_tasks.cleanup_expired_tasks': {'queue': 'low_priority'},
    
    # 监控任务
    'app.tasks.monitoring_tasks.generate_daily_statistics': {'queue': 'receipt'},
    'app.tasks.monitoring_tasks.check_disk_space': {'queue': 'file'},
    'app.tasks.monitoring_tasks.send_alert_notification': {'queue': 'high_priority'},
}