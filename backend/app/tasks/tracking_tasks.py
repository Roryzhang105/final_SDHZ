import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import current_app as celery_app
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import SessionLocal
from app.core.config import settings
from app.services.tracking import TrackingService
from app.models.task import Task, TaskStatusEnum
from app.models.delivery_receipt import DeliveryReceipt
from app.services.express_tracking import ExpressTrackingService

# 设置日志
logger = logging.getLogger(__name__)


@celery_app.task
def update_tracking_info(tracking_number: str):
    """
    更新物流跟踪信息的异步任务
    """
    db: Session = SessionLocal()
    try:
        service = TrackingService(db)
        receipt = service.get_receipt_by_tracking_number(tracking_number)
        
        if not receipt:
            return {"error": "未找到对应的送达回证"}
        
        # 调用快递查询API
        tracking_data = fetch_tracking_data(tracking_number, receipt.courier_code or receipt.courier_company)
        
        if tracking_data:
            # 更新物流信息
            service.create_or_update_tracking(
                receipt_id=receipt.id,
                current_status=tracking_data.get("status", ""),
                tracking_data=tracking_data,
                notes=f"自动更新于 {tracking_data.get('update_time', '')}"
            )
            
            return {"message": "物流信息更新成功", "tracking_number": tracking_number}
        else:
            return {"error": "获取物流信息失败"}
            
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


def fetch_tracking_data(tracking_number: str, courier_code: str) -> dict:
    """
    调用快递查询API获取物流数据
    """
    try:
        # 使用ExpressTrackingService调用快递100 API
        from app.services.express_tracking import ExpressTrackingService
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            express_service = ExpressTrackingService(db)
            
            # 调用快递100 API查询
            result = express_service.query_express(tracking_number, courier_code or "ems")
            
            if result["success"]:
                # 转换为tracking_tasks期望的格式
                return {
                    "tracking_number": tracking_number,
                    "courier_code": result.get("company_code", courier_code),
                    "status": result.get("current_status", ""),
                    "is_signed": result.get("is_signed", False),
                    "sign_time": result.get("sign_time", ""),
                    "update_time": result.get("last_update", ""),
                    "traces": result.get("traces", []),
                    "raw_data": result.get("raw_data", {}),
                    "from_cache": result.get("from_cache", False)
                }
            else:
                print(f"快递100 API查询失败: {result.get('error', '未知错误')}")
                return None
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"获取物流数据失败: {e}")
        return None


@celery_app.task
def batch_update_tracking(tracking_numbers: list):
    """
    批量更新物流信息
    """
    results = []
    for tracking_number in tracking_numbers:
        result = update_tracking_info.delay(tracking_number)
        results.append({"tracking_number": tracking_number, "task_id": result.id})
    
    return {"message": f"批量更新 {len(tracking_numbers)} 个物流信息", "tasks": results}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def update_all_pending_tracking(self) -> Dict[str, Any]:
    """
    定时任务：更新所有未完成的物流跟踪信息
    每小时执行一次，批量查询并更新物流状态
    """
    start_time = datetime.now()
    logger.info(f"开始执行定时物流更新任务 - {start_time}")
    
    db: Session = SessionLocal()
    
    try:
        # 统计信息
        stats = {
            "total_checked": 0,
            "updated": 0,
            "completed": 0,
            "failed": 0,
            "errors": []
        }
        
        # 查询所有需要更新的任务
        pending_tasks = get_pending_tracking_tasks(db)
        stats["total_checked"] = len(pending_tasks)
        
        logger.info(f"找到 {len(pending_tasks)} 个待更新的物流任务")
        
        if not pending_tasks:
            logger.info("没有需要更新的物流任务")
            return {
                "success": True,
                "message": "没有需要更新的物流任务",
                "stats": stats,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
        
        # 分批处理任务，每批最多50个
        batch_size = 50
        for i in range(0, len(pending_tasks), batch_size):
            batch = pending_tasks[i:i + batch_size]
            batch_stats = process_tracking_batch(db, batch)
            
            # 累加统计信息
            stats["updated"] += batch_stats["updated"]
            stats["completed"] += batch_stats["completed"]
            stats["failed"] += batch_stats["failed"]
            stats["errors"].extend(batch_stats["errors"])
            
            logger.info(f"批次 {i//batch_size + 1} 处理完成: 更新 {batch_stats['updated']}, 完成 {batch_stats['completed']}, 失败 {batch_stats['failed']}")
        
        # 提交所有更改
        db.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"定时物流更新任务完成 - 耗时: {execution_time:.2f}秒, 统计: {stats}")
        
        return {
            "success": True,
            "message": "物流跟踪更新完成",
            "stats": stats,
            "execution_time": execution_time
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"定时物流更新任务失败: {str(e)}", exc_info=True)
        
        # Celery 自动重试
        raise self.retry(exc=e)
        
    finally:
        db.close()


def get_pending_tracking_tasks(db: Session) -> List[Task]:
    """
    获取所有需要更新物流的任务
    """
    try:
        # 查询条件：
        # 1. 状态为 TRACKING（正在跟踪）
        # 2. 或状态为 DELIVERED 但最近24小时内更新过的（确保签收状态稳定）
        # 3. 有快递单号的任务
        # 4. 最近7天内的任务（避免更新过老的任务）
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        
        pending_tasks = db.query(Task).filter(
            and_(
                Task.tracking_number.isnot(None),
                Task.tracking_number != "",
                Task.created_at >= seven_days_ago,
                or_(
                    Task.status == TaskStatusEnum.TRACKING,
                    and_(
                        Task.status == TaskStatusEnum.DELIVERED,
                        Task.updated_at >= twenty_four_hours_ago
                    )
                )
            )
        ).all()
        
        logger.info(f"查询到 {len(pending_tasks)} 个待更新的物流任务")
        return pending_tasks
        
    except Exception as e:
        logger.error(f"查询待更新任务失败: {str(e)}")
        return []


def process_tracking_batch(db: Session, tasks: List[Task]) -> Dict[str, Any]:
    """
    批量处理一组物流任务
    """
    batch_stats = {
        "updated": 0,
        "completed": 0,
        "failed": 0,
        "errors": []
    }
    
    express_service = ExpressTrackingService(db)
    
    for task in tasks:
        try:
            # 更新单个任务的物流信息
            result = update_single_task_tracking(db, express_service, task)
            
            if result["success"]:
                batch_stats["updated"] += 1
                
                # 检查是否已完成
                if result.get("completed"):
                    batch_stats["completed"] += 1
                    
            else:
                batch_stats["failed"] += 1
                batch_stats["errors"].append({
                    "task_id": task.task_id,
                    "tracking_number": task.tracking_number,
                    "error": result.get("error", "未知错误")
                })
                
        except Exception as e:
            batch_stats["failed"] += 1
            error_msg = f"处理任务 {task.task_id} 失败: {str(e)}"
            batch_stats["errors"].append({
                "task_id": task.task_id,
                "tracking_number": task.tracking_number,
                "error": error_msg
            })
            logger.error(error_msg)
    
    return batch_stats


def update_single_task_tracking(db: Session, express_service: ExpressTrackingService, task: Task) -> Dict[str, Any]:
    """
    更新单个任务的物流跟踪信息
    """
    try:
        logger.debug(f"更新任务 {task.task_id} 的物流信息，快递单号: {task.tracking_number}")
        
        # 确定快递公司代码
        company_code = task.courier_company or "ems"
        if company_code and len(company_code) > 10:
            # 如果是中文公司名，尝试转换为代码
            company_mapping = {
                "中国邮政": "ems",
                "顺丰": "sf",
                "圆通": "yt",
                "申通": "sto",
                "韵达": "yd",
                "中通": "zt"
            }
            company_code = company_mapping.get(company_code, "ems")
        
        # 查询物流信息
        tracking_result = express_service.query_express(task.tracking_number, company_code)
        
        if not tracking_result.get("success"):
            return {
                "success": False,
                "error": tracking_result.get("error", "物流查询失败")
            }
        
        # 检查数据是否有更新
        old_status = task.delivery_status
        new_status = tracking_result.get("current_status", "")
        is_signed = tracking_result.get("is_signed", False)
        
        # 更新任务数据
        task.tracking_data = tracking_result
        task.delivery_status = new_status
        
        # 检查是否已签收
        completed = False
        if is_signed and task.status != TaskStatusEnum.DELIVERED:
            task.status = TaskStatusEnum.DELIVERED
            
            # 解析签收时间
            sign_time_str = tracking_result.get("sign_time", "")
            if sign_time_str:
                try:
                    if "T" in sign_time_str:
                        task.delivery_time = datetime.fromisoformat(sign_time_str.replace('Z', '+00:00'))
                    else:
                        task.delivery_time = datetime.strptime(sign_time_str, "%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.warning(f"解析签收时间失败: {e}")
                    task.delivery_time = datetime.now()
            else:
                task.delivery_time = datetime.now()
            
            completed = True
            logger.info(f"任务 {task.task_id} 已签收，签收时间: {task.delivery_time}")
        
        # 更新时间戳
        task.updated_at = datetime.now()
        
        # 记录状态变化
        if old_status != new_status:
            logger.info(f"任务 {task.task_id} 物流状态更新: {old_status} -> {new_status}")
        
        return {
            "success": True,
            "completed": completed,
            "status_changed": old_status != new_status,
            "old_status": old_status,
            "new_status": new_status
        }
        
    except Exception as e:
        logger.error(f"更新任务 {task.task_id} 物流信息失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 120})
def check_pending_tasks(self) -> Dict[str, Any]:
    """
    检查并处理待处理的任务
    每5分钟执行一次，检查是否有卡住的任务需要重新处理
    """
    start_time = datetime.now()
    logger.info(f"开始执行任务检查 - {start_time}")
    
    db: Session = SessionLocal()
    
    try:
        stats = {
            "checked": 0,
            "restarted": 0,
            "failed_marked": 0,
            "errors": []
        }
        
        # 查询超时的任务（超过30分钟还在处理中的）
        timeout_threshold = datetime.now() - timedelta(minutes=30)
        
        stuck_tasks = db.query(Task).filter(
            and_(
                Task.status.in_([
                    TaskStatusEnum.PENDING,
                    TaskStatusEnum.RECOGNIZING,
                    TaskStatusEnum.TRACKING,
                    TaskStatusEnum.GENERATING
                ]),
                Task.updated_at < timeout_threshold
            )
        ).all()
        
        stats["checked"] = len(stuck_tasks)
        logger.info(f"发现 {len(stuck_tasks)} 个可能卡住的任务")
        
        for task in stuck_tasks:
            try:
                # 检查任务具体情况并决定处理方式
                action = determine_task_action(task)
                
                if action == "restart":
                    # 重启任务
                    restart_stuck_task(db, task)
                    stats["restarted"] += 1
                    logger.info(f"重启任务: {task.task_id}")
                    
                elif action == "fail":
                    # 标记为失败
                    task.status = TaskStatusEnum.FAILED
                    task.error_message = f"任务超时自动标记为失败 - {datetime.now()}"
                    stats["failed_marked"] += 1
                    logger.warning(f"标记任务失败: {task.task_id}")
                
            except Exception as e:
                error_msg = f"处理卡住任务 {task.task_id} 失败: {str(e)}"
                stats["errors"].append(error_msg)
                logger.error(error_msg)
        
        db.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"任务检查完成 - 耗时: {execution_time:.2f}秒, 统计: {stats}")
        
        return {
            "success": True,
            "message": "任务检查完成",
            "stats": stats,
            "execution_time": execution_time
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"任务检查失败: {str(e)}", exc_info=True)
        raise self.retry(exc=e)
        
    finally:
        db.close()


def determine_task_action(task: Task) -> str:
    """
    判断卡住的任务应该采取什么行动
    """
    # 如果重试次数过多，标记为失败
    if task.retry_count >= 3:
        return "fail"
    
    # 如果是很久以前的任务，标记为失败
    if task.created_at < datetime.now() - timedelta(days=1):
        return "fail"
    
    # 其他情况尝试重启
    return "restart"


def restart_stuck_task(db: Session, task: Task):
    """
    重启卡住的任务
    """
    # 增加重试计数
    task.retry_count += 1
    task.updated_at = datetime.now()
    task.error_message = None
    
    # 根据任务当前状态决定重启策略
    if task.status == TaskStatusEnum.PENDING:
        # 如果还是待处理，触发二维码识别
        from app.services.task import TaskService
        task_service = TaskService(db)
        # 异步触发处理
        import asyncio
        asyncio.create_task(task_service._trigger_qr_recognition(task.task_id))
        
    elif task.status == TaskStatusEnum.RECOGNIZING:
        # 如果在识别中，重置为待处理
        task.status = TaskStatusEnum.PENDING
        
    elif task.status == TaskStatusEnum.TRACKING:
        # 如果在跟踪中但卡住了，可能需要重新触发跟踪
        if task.tracking_number:
            # 有快递单号，在下次定时更新中会被处理
            pass
        else:
            # 没有快递单号，重置为识别状态
            task.status = TaskStatusEnum.RECOGNIZING
    
    elif task.status == TaskStatusEnum.GENERATING:
        # 如果在生成中，重置为已投递状态
        task.status = TaskStatusEnum.DELIVERED


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 300})
def check_timeout_tasks(self) -> Dict[str, Any]:
    """
    检查超时的任务
    每30分钟执行一次，处理长时间无响应的任务
    """
    start_time = datetime.now()
    logger.info(f"开始检查超时任务 - {start_time}")
    
    db: Session = SessionLocal()
    
    try:
        # 查询超过2小时没有更新的处理中任务
        timeout_threshold = datetime.now() - timedelta(hours=2)
        
        timeout_tasks = db.query(Task).filter(
            and_(
                Task.status.in_([
                    TaskStatusEnum.RECOGNIZING,
                    TaskStatusEnum.TRACKING,
                    TaskStatusEnum.GENERATING
                ]),
                Task.updated_at < timeout_threshold
            )
        ).all()
        
        processed = 0
        for task in timeout_tasks:
            try:
                task.status = TaskStatusEnum.FAILED
                task.error_message = f"任务超时自动标记为失败 - 超过2小时无响应 - {datetime.now()}"
                task.updated_at = datetime.now()
                processed += 1
                logger.warning(f"超时任务已标记为失败: {task.task_id}")
                
            except Exception as e:
                logger.error(f"处理超时任务 {task.task_id} 失败: {str(e)}")
        
        db.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"超时任务检查完成 - 处理 {processed} 个任务, 耗时: {execution_time:.2f}秒")
        
        return {
            "success": True,
            "message": f"处理了 {processed} 个超时任务",
            "processed": processed,
            "execution_time": execution_time
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"超时任务检查失败: {str(e)}", exc_info=True)
        raise self.retry(exc=e)
        
    finally:
        db.close()


@celery_app.task
def system_health_check() -> Dict[str, Any]:
    """
    系统健康检查
    每10分钟执行一次
    """
    start_time = datetime.now()
    logger.info(f"开始系统健康检查 - {start_time}")
    
    health_status = {
        "database": False,
        "redis": False,
        "disk_space": False,
        "task_queue": False,
        "errors": []
    }
    
    # 检查数据库连接
    try:
        db = SessionLocal()
        db.execute("SELECT 1").scalar()
        db.close()
        health_status["database"] = True
    except Exception as e:
        health_status["errors"].append(f"数据库连接失败: {str(e)}")
    
    # 检查Redis连接
    try:
        from celery import current_app
        result = current_app.control.ping(timeout=10)
        if result:
            health_status["redis"] = True
        else:
            health_status["errors"].append("Redis连接超时")
    except Exception as e:
        health_status["errors"].append(f"Redis连接失败: {str(e)}")
    
    # 检查磁盘空间
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_percent = (free / total) * 100
        
        if free_percent > 10:  # 至少10%空闲空间
            health_status["disk_space"] = True
        else:
            health_status["errors"].append(f"磁盘空间不足: 剩余 {free_percent:.1f}%")
    except Exception as e:
        health_status["errors"].append(f"磁盘空间检查失败: {str(e)}")
    
    # 检查任务队列
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        active = inspect.active()
        
        if active is not None:
            health_status["task_queue"] = True
        else:
            health_status["errors"].append("无法获取任务队列状态")
    except Exception as e:
        health_status["errors"].append(f"任务队列检查失败: {str(e)}")
    
    # 计算整体健康状态
    healthy_checks = sum([
        health_status["database"],
        health_status["redis"],
        health_status["disk_space"],
        health_status["task_queue"]
    ])
    
    overall_health = healthy_checks >= 3  # 至少3个检查通过
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    result = {
        "success": overall_health,
        "health_status": health_status,
        "healthy_checks": healthy_checks,
        "total_checks": 4,
        "execution_time": execution_time
    }
    
    if overall_health:
        logger.info(f"系统健康检查通过 - {healthy_checks}/4 项检查通过")
    else:
        logger.warning(f"系统健康检查失败 - 仅 {healthy_checks}/4 项检查通过, 错误: {health_status['errors']}")
    
    return result