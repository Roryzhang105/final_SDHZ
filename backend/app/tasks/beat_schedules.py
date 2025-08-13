"""
Celery Beat 定时任务配置文件
包含所有定时任务的调度配置
"""

from celery.schedules import crontab

# 定时任务配置
BEAT_SCHEDULE = {
    # ============ 任务监控和状态更新 ============
    
    # 每15分钟检查待处理的任务 (降低频率减少CPU占用)
    'check-pending-tasks': {
        'task': 'app.tasks.tracking_tasks.check_pending_tasks',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'high_priority'}
    },
    
    # 每小时更新所有未完成的物流状态
    'update-all-pending-tracking': {
        'task': 'app.tasks.tracking_tasks.update_all_pending_tracking',
        'schedule': crontab(minute=0),  # 每小时整点执行
        'options': {'queue': 'tracking'}
    },
    
    # 每45分钟检查超时任务 (错开执行时间)
    'check-timeout-tasks': {
        'task': 'app.tasks.tracking_tasks.check_timeout_tasks',
        'schedule': crontab(minute='30,45'),  # 在30分和45分执行
        'options': {'queue': 'tracking'}
    },
    
    
    # ============ 文件和数据清理 ============
    
    # 每小时清理旧文件
    'cleanup-old-files': {
        'task': 'app.tasks.file_tasks.cleanup_old_files',
        'schedule': crontab(minute=0),  # 每小时整点执行
        'options': {'queue': 'file'}
    },
    
    # ============ 每日任务 ============
    
    # 每天凌晨2点生成统计报告
    'generate-daily-statistics': {
        'task': 'app.tasks.monitoring_tasks.generate_daily_statistics',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'receipt'}
    },
    
    # 每天凌晨2:30优化数据库
    'optimize-database': {
        'task': 'app.tasks.file_tasks.optimize_database',
        'schedule': crontab(hour=2, minute=30),
        'options': {'queue': 'file'}
    },
    
    # 每天凌晨3点备份数据库
    'backup-database': {
        'task': 'app.tasks.file_tasks.backup_database',
        'schedule': crontab(hour=3, minute=0),
        'options': {'queue': 'file'}
    },
    
    # 每天凌晨4点清理过期任务
    'cleanup-expired-tasks': {
        'task': 'app.tasks.monitoring_tasks.cleanup_expired_tasks',
        'schedule': crontab(hour=4, minute=0),
        'options': {'queue': 'file'}
    },
    
    # ============ 每周任务 ============
    
    
    # 每周一早上8点发送周报
    'generate-weekly-report': {
        'task': 'app.tasks.receipt_tasks.generate_weekly_report',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # 1 = 周一
        'options': {'queue': 'receipt'}
    },
    
    # ============ 每月任务 ============
    
    # 每月1号凌晨5点归档旧数据
    'archive-old-data': {
        'task': 'app.tasks.file_tasks.archive_old_data',
        'schedule': crontab(hour=5, minute=0, day_of_month=1),
        'options': {'queue': 'file'}
    },
    
    # 每月1号上午9点生成月报
    'generate-monthly-report': {
        'task': 'app.tasks.receipt_tasks.generate_monthly_report',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),
        'options': {'queue': 'receipt'}
    },
    
    # ============ 健康检查 ============
    
    # 每20分钟系统健康检查 (降低频率)
    'system-health-check': {
        'task': 'app.tasks.tracking_tasks.system_health_check',
        'schedule': crontab(minute='5,25,45'),  # 错开时间：5分、25分、45分
        'options': {'queue': 'high_priority'}
    },
    
    # 每15分钟监控系统健康状态 (包含Celery状态)
    'monitor-system-health': {
        'task': 'app.tasks.health_check_tasks.monitor_system_health',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'monitoring'}
    },
    
    # 每小时收集Worker统计数据
    'collect-worker-statistics': {
        'task': 'app.tasks.health_check_tasks.collect_worker_statistics',
        'schedule': crontab(minute=10),  # 每小时10分执行
        'options': {'queue': 'monitoring'}
    },
    
    # 每小时检查磁盘空间
    'disk-space-check': {
        'task': 'app.tasks.monitoring_tasks.check_disk_space',
        'schedule': crontab(minute=15),  # 每小时15分执行
        'options': {'queue': 'file'}
    },
    
    # 每天凌晨清理监控数据
    'cleanup-monitoring-data': {
        'task': 'app.tasks.health_check_tasks.cleanup_monitoring_data',
        'schedule': crontab(hour=1, minute=30),
        'options': {'queue': 'low_priority'}
    },
    
    # ============ 失败任务处理 ============
    
}

# 任务优先级配置
TASK_PRIORITIES = {
    'check-pending-tasks': 9,
    'update-all-pending-tracking': 8,
    'system-health-check': 7,
    'check-timeout-tasks': 6,
    'disk-space-check': 5,
    'cleanup-old-files': 4,
    'generate-daily-statistics': 3,
    'cleanup-expired-tasks': 2,
    'backup-database': 2
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
    'app.tasks.file_tasks.cleanup_old_files': {'queue': 'low_priority'},
    'app.tasks.file_tasks.backup_database': {'queue': 'low_priority'},
    'app.tasks.file_tasks.archive_old_data': {'queue': 'low_priority'},
    'app.tasks.monitoring_tasks.cleanup_expired_tasks': {'queue': 'low_priority'},
    
    # 监控任务
    'app.tasks.monitoring_tasks.generate_daily_statistics': {'queue': 'receipt'},
    'app.tasks.monitoring_tasks.check_disk_space': {'queue': 'file'},
    'app.tasks.monitoring_tasks.send_alert_notification': {'queue': 'high_priority'},
    
    # 健康检查任务
    'app.tasks.health_check_tasks.monitor_system_health': {'queue': 'monitoring'},
    'app.tasks.health_check_tasks.collect_worker_statistics': {'queue': 'monitoring'},
    'app.tasks.health_check_tasks.cleanup_monitoring_data': {'queue': 'low_priority'},
    'app.tasks.health_check_tasks.generate_health_report': {'queue': 'monitoring'},
}