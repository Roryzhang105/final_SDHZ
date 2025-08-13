from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.tasks.beat_schedules import BEAT_SCHEDULE, TASK_ROUTES

celery_app = Celery(
    "delivery_receipt_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.receipt_tasks",
        "app.tasks.tracking_tasks", 
        "app.tasks.screenshot_tasks",
        "app.tasks.file_tasks",
        "app.tasks.monitoring_tasks",
        "app.tasks.health_check_tasks"
    ]
)

# 从配置文件导入定时任务配置
beat_schedule = BEAT_SCHEDULE

# 配置Celery (优化性能和稳定性)
celery_app.conf.update(
    # 基本配置
    task_serializer="json",
    accept_content=["json"],  
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    beat_schedule=beat_schedule,
    task_routes=TASK_ROUTES,
    
    # 任务执行配置 (优化性能)
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    result_expires=1800,  # 结果过期时间30分钟 (减少内存占用)
    
    # 超时配置 (防止僵尸任务)
    task_soft_time_limit=180,  # 软时间限制3分钟
    task_time_limit=300,      # 硬时间限制5分钟
    
    # Worker配置 (减少资源争抢)
    worker_prefetch_multiplier=1,  # 每次预取1个任务
    task_acks_late=True,          # 延迟确认
    worker_disable_rate_limits=False,
    
    # 性能优化配置
    task_compression='gzip',      # 启用任务压缩
    result_compression='gzip',    # 启用结果压缩
    task_track_started=True,      # 跟踪任务开始状态
    
    # 事件监控配置
    worker_send_task_events=True,     # Worker发送任务事件
    task_send_sent_event=True,        # 发送任务提交事件
    worker_hijack_root_logger=False,  # 防止日志冲突
    
    # 内存管理
    worker_max_tasks_per_child=100,  # 每个worker子进程最多处理100个任务后重启
    worker_max_memory_per_child=200000,  # 内存限制200MB
    
    # 连接池配置
    broker_pool_limit=10,         # 连接池大小
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=5,
    
    # Beat调度器配置 (使用持久化调度器)
    beat_scheduler='celery.beat:PersistentScheduler',
    beat_schedule_filename='celerybeat-schedule',
)

