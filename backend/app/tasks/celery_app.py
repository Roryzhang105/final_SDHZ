from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "delivery_receipt_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.receipt_tasks",
        "app.tasks.tracking_tasks", 
        "app.tasks.screenshot_tasks",
        "app.tasks.file_tasks"
    ]
)

# 配置Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.receipt_tasks.*": {"queue": "receipt"},
        "app.tasks.tracking_tasks.*": {"queue": "tracking"},
        "app.tasks.screenshot_tasks.*": {"queue": "screenshot"},
        "app.tasks.file_tasks.*": {"queue": "file"},
    }
)