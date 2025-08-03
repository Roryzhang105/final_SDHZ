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
        "app.tasks.monitoring_tasks"
    ]
)

# 从配置文件导入定时任务配置
beat_schedule = BEAT_SCHEDULE

# 配置Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    beat_schedule=beat_schedule,
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',  # 使用数据库调度器
    task_routes=TASK_ROUTES,
    # 任务执行相关配置
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    result_expires=3600,  # 结果过期时间1小时
    task_soft_time_limit=300,  # 软时间限制5分钟
    task_time_limit=600,  # 硬时间限制10分钟
    worker_prefetch_multiplier=1,  # 每次预取1个任务
    task_acks_late=True,  # 延迟确认
    worker_disable_rate_limits=False,
)