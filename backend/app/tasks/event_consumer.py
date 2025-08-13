"""
Celery事件消费者
监听Celery任务事件并将其记录到数据库中
"""

import logging
import threading
from datetime import datetime
from celery import Celery
from celery.events import EventReceiver
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.celery_monitor import CeleryMonitorService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


class CeleryEventConsumer:
    """Celery事件消费者"""
    
    def __init__(self):
        self.celery_app = celery_app
        self.running = False
        self.thread = None
    
    def start(self):
        """启动事件消费者"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._consume_events, daemon=True)
        self.thread.start()
        logger.info("Celery事件消费者已启动")
    
    def stop(self):
        """停止事件消费者"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Celery事件消费者已停止")
    
    def _consume_events(self):
        """消费事件循环"""
        connection = self.celery_app.connection()
        
        def task_sent_handler(event):
            """处理任务发送事件"""
            self._handle_task_event(event['uuid'], 'task-sent', event)
        
        def task_received_handler(event):
            """处理任务接收事件"""
            self._handle_task_event(event['uuid'], 'task-received', event)
        
        def task_started_handler(event):
            """处理任务开始事件"""
            self._handle_task_event(event['uuid'], 'task-started', event)
        
        def task_succeeded_handler(event):
            """处理任务成功事件"""
            self._handle_task_event(event['uuid'], 'task-succeeded', event)
        
        def task_failed_handler(event):
            """处理任务失败事件"""
            self._handle_task_event(event['uuid'], 'task-failed', event)
        
        def task_retry_handler(event):
            """处理任务重试事件"""
            self._handle_task_event(event['uuid'], 'task-retry', event)
        
        def task_revoked_handler(event):
            """处理任务撤销事件"""
            self._handle_task_event(event['uuid'], 'task-revoked', event)
        
        # 注册事件处理器
        handlers = {
            'task-sent': task_sent_handler,
            'task-received': task_received_handler,
            'task-started': task_started_handler,
            'task-succeeded': task_succeeded_handler,
            'task-failed': task_failed_handler,
            'task-retry': task_retry_handler,
            'task-revoked': task_revoked_handler,
        }
        
        try:
            with connection.channel() as channel:
                recv = EventReceiver(
                    channel,
                    handlers=handlers,
                    app=self.celery_app
                )
                
                logger.info("开始监听Celery事件...")
                
                while self.running:
                    try:
                        recv.capture(limit=None, timeout=1.0, wakeup=True)
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        logger.error(f"事件消费出错: {e}")
                        if not self.running:
                            break
                        continue
                        
        except Exception as e:
            logger.error(f"事件消费者启动失败: {e}")
        finally:
            connection.release()
    
    def _handle_task_event(self, task_id: str, event_type: str, event_data: dict):
        """处理单个任务事件"""
        try:
            db: Session = SessionLocal()
            try:
                monitor_service = CeleryMonitorService(db)
                monitor_service.record_task_event(task_id, event_type, event_data)
                logger.debug(f"记录任务事件: {task_id} - {event_type}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"处理任务事件失败 {task_id}: {e}")


# 全局事件消费者实例
event_consumer = CeleryEventConsumer()


def start_event_consumer():
    """启动事件消费者"""
    event_consumer.start()


def stop_event_consumer():
    """停止事件消费者"""
    event_consumer.stop()


if __name__ == "__main__":
    import time
    
    # 启动事件消费者
    start_event_consumer()
    
    try:
        # 保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event_consumer()