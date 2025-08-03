import logging
from celery import current_app as celery_app
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.services.delivery_receipt import DeliveryReceiptService
from app.models.delivery_receipt import DeliveryStatusEnum
from app.tasks.retry_config import (
    get_retry_config, 
    retry_task,
    log_task_failure,
    log_task_retry,
    RetryTaskMixin
)

logger = logging.getLogger(__name__)


@celery_app.task(**get_retry_config('critical'))
@retry_task('critical', on_failure=log_task_failure, on_retry=log_task_retry)
def process_delivery_receipt(self, receipt_id: int):
    """
    处理送达回证的异步任务
    包括生成二维码、条形码、填充模板文档等
    
    重试策略: critical (最多5次重试，30秒起始延迟，指数退避)
    """
    logger.info(f"开始处理送达回证: {receipt_id}")
    
    db: Session = SessionLocal()
    service = None
    
    try:
        service = DeliveryReceiptService(db)
        receipt = service.get_delivery_receipt(receipt_id)
        
        if not receipt:
            error_msg = f"送达回证不存在: {receipt_id}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        logger.info(f"找到回证记录: {receipt.tracking_number}")
        
        # 更新状态为处理中
        try:
            service.update_receipt_status(receipt_id, DeliveryStatusEnum.PROCESSING.value)
            logger.info(f"回证状态更新为处理中: {receipt_id}")
        except SQLAlchemyError as e:
            logger.error(f"更新回证状态失败: {receipt_id}, 错误: {str(e)}")
            raise e
        
        # 1. 生成二维码和条形码
        try:
            from app.tasks.file_tasks import generate_qr_and_barcode
            qr_task_result = generate_qr_and_barcode.delay(receipt_id)
            logger.info(f"二维码生成任务已启动: {qr_task_result.id}")
        except Exception as e:
            logger.error(f"启动二维码生成任务失败: {receipt_id}, 错误: {str(e)}")
            raise e
        
        # 2. 填充文档模板
        try:
            from app.tasks.file_tasks import fill_receipt_template
            template_task_result = fill_receipt_template.delay(receipt_id)
            logger.info(f"文档模板填充任务已启动: {template_task_result.id}")
        except Exception as e:
            logger.error(f"启动文档模板填充任务失败: {receipt_id}, 错误: {str(e)}")
            raise e
        
        # 3. 查询物流信息
        try:
            from app.tasks.tracking_tasks import update_tracking_info
            tracking_task_result = update_tracking_info.delay(receipt.tracking_number)
            logger.info(f"物流信息更新任务已启动: {tracking_task_result.id}")
        except Exception as e:
            logger.error(f"启动物流信息更新任务失败: {receipt.tracking_number}, 错误: {str(e)}")
            raise e
        
        # 提交数据库事务
        db.commit()
        
        logger.info(f"送达回证处理完成: {receipt_id}")
        return {
            "success": True,
            "message": "送达回证处理完成",
            "receipt_id": receipt_id,
            "tracking_number": receipt.tracking_number,
            "subtasks": {
                "qr_generation": qr_task_result.id,
                "template_filling": template_task_result.id,
                "tracking_update": tracking_task_result.id
            }
        }
        
    except SQLAlchemyError as e:
        logger.error(f"数据库操作失败: {receipt_id}, 错误: {str(e)}")
        db.rollback()
        
        # 尝试更新状态为失败
        try:
            if service:
                service.update_receipt_status(receipt_id, DeliveryStatusEnum.FAILED.value)
                db.commit()
        except Exception as status_error:
            logger.error(f"更新失败状态也失败了: {receipt_id}, 错误: {str(status_error)}")
        
        raise e
        
    except Exception as e:
        logger.error(f"处理送达回证失败: {receipt_id}, 错误: {str(e)}")
        db.rollback()
        
        # 尝试更新状态为失败
        try:
            if service:
                service.update_receipt_status(receipt_id, DeliveryStatusEnum.FAILED.value)
                db.commit()
        except Exception as status_error:
            logger.error(f"更新失败状态失败: {receipt_id}, 错误: {str(status_error)}")
        
        raise e
        
    finally:
        db.close()


@celery_app.task(**get_retry_config('default'))
@retry_task('default', on_failure=log_task_failure, on_retry=log_task_retry)
def batch_process_receipts(self, receipt_ids: list):
    """
    批量处理送达回证
    
    重试策略: default (最多3次重试，60秒起始延迟，指数退避)
    """
    if not receipt_ids:
        logger.warning("批量处理回证: 收到空的回证ID列表")
        return {
            "success": True,
            "message": "无需处理的回证",
            "total": 0,
            "tasks": []
        }
    
    logger.info(f"开始批量处理 {len(receipt_ids)} 个送达回证")
    
    results = []
    successful = 0
    failed = 0
    
    try:
        for receipt_id in receipt_ids:
            try:
                # 验证receipt_id类型
                if not isinstance(receipt_id, int):
                    logger.error(f"无效的回证ID类型: {receipt_id} (类型: {type(receipt_id)})")
                    failed += 1
                    results.append({
                        "receipt_id": receipt_id,
                        "status": "failed",
                        "error": "无效的回证ID类型"
                    })
                    continue
                
                # 启动处理任务
                result = process_delivery_receipt.delay(receipt_id)
                successful += 1
                results.append({
                    "receipt_id": receipt_id,
                    "task_id": result.id,
                    "status": "submitted"
                })
                logger.debug(f"回证处理任务已提交: {receipt_id} -> {result.id}")
                
            except Exception as e:
                failed += 1
                error_msg = f"启动回证处理任务失败: {receipt_id}, 错误: {str(e)}"
                logger.error(error_msg)
                results.append({
                    "receipt_id": receipt_id,
                    "status": "failed",
                    "error": error_msg
                })
        
        logger.info(f"批量处理回证完成: 成功提交 {successful} 个, 失败 {failed} 个")
        
        return {
            "success": True,
            "message": f"批量处理 {len(receipt_ids)} 个送达回证",
            "total": len(receipt_ids),
            "successful": successful,
            "failed": failed,
            "tasks": results
        }
        
    except Exception as e:
        logger.error(f"批量处理回证时发生意外错误: {str(e)}")
        raise e


@celery_app.task(**get_retry_config('default'))
@retry_task('default', on_failure=log_task_failure, on_retry=log_task_retry)  
def generate_daily_report(self):
    """
    生成每日送达回证统计报告
    
    重试策略: default (最多3次重试，60秒起始延迟，指数退避)
    """
    from datetime import datetime, timedelta
    import json
    import os
    
    logger.info("开始生成每日送达回证统计报告")
    
    db: Session = SessionLocal()
    
    try:
        # 统计昨天的数据
        yesterday = (datetime.now() - timedelta(days=1)).date()
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_end = datetime.combine(yesterday, datetime.max.time())
        
        service = DeliveryReceiptService(db)
        
        # 获取昨日回证统计
        from sqlalchemy import func
        from app.models.delivery_receipt import DeliveryReceipt
        
        # 总数统计
        total_receipts = db.query(func.count(DeliveryReceipt.id)).filter(
            DeliveryReceipt.created_at.between(yesterday_start, yesterday_end)
        ).scalar()
        
        # 按状态统计
        status_stats = db.query(
            DeliveryReceipt.status,
            func.count(DeliveryReceipt.id).label('count')
        ).filter(
            DeliveryReceipt.created_at.between(yesterday_start, yesterday_end)
        ).group_by(DeliveryReceipt.status).all()
        
        status_dict = {}
        for status, count in status_stats:
            status_dict[status.value] = count
        
        # 成功率计算
        sent_count = status_dict.get(DeliveryStatusEnum.SENT.value, 0)
        delivered_count = status_dict.get(DeliveryStatusEnum.DELIVERED.value, 0)
        failed_count = status_dict.get(DeliveryStatusEnum.FAILED.value, 0)
        
        success_rate = 0
        if total_receipts > 0:
            success_rate = ((sent_count + delivered_count) / total_receipts) * 100
        
        # 生成报告
        report = {
            "date": yesterday.isoformat(),
            "total_receipts": total_receipts,
            "status_breakdown": status_dict,
            "success_rate": round(success_rate, 2),
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存报告到文件
        reports_dir = "reports/receipts"
        os.makedirs(reports_dir, exist_ok=True)
        
        report_filename = f"receipt_daily_report_{yesterday.strftime('%Y%m%d')}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"每日送达回证统计报告生成完成: {report_path}")
        
        return {
            "success": True,
            "message": "每日送达回证统计报告生成完成",
            "report": report,
            "report_file": report_path
        }
        
    except SQLAlchemyError as e:
        logger.error(f"生成每日报告时数据库错误: {str(e)}")
        db.rollback()
        raise e
        
    except Exception as e:
        logger.error(f"生成每日报告失败: {str(e)}")
        raise e
        
    finally:
        db.close()


@celery_app.task(**get_retry_config('default'))
@retry_task('default', on_failure=log_task_failure, on_retry=log_task_retry)
def generate_weekly_report(self):
    """
    生成每周送达回证统计报告
    
    重试策略: default (最多3次重试，60秒起始延迟，指数退避)
    """
    from datetime import datetime, timedelta
    import json
    import os
    
    logger.info("开始生成每周送达回证统计报告")
    
    db: Session = SessionLocal()
    
    try:
        # 统计上周的数据
        today = datetime.now().date()
        last_monday = today - timedelta(days=today.weekday() + 7)  # 上周一
        last_sunday = last_monday + timedelta(days=6)  # 上周日
        
        week_start = datetime.combine(last_monday, datetime.min.time())
        week_end = datetime.combine(last_sunday, datetime.max.time())
        
        service = DeliveryReceiptService(db)
        
        # 获取上周回证统计
        from sqlalchemy import func
        from app.models.delivery_receipt import DeliveryReceipt
        
        # 总数统计
        total_receipts = db.query(func.count(DeliveryReceipt.id)).filter(
            DeliveryReceipt.created_at.between(week_start, week_end)
        ).scalar()
        
        # 按状态统计
        status_stats = db.query(
            DeliveryReceipt.status,
            func.count(DeliveryReceipt.id).label('count')
        ).filter(
            DeliveryReceipt.created_at.between(week_start, week_end)
        ).group_by(DeliveryReceipt.status).all()
        
        status_dict = {}
        for status, count in status_stats:
            status_dict[status.value] = count
        
        # 按天统计
        daily_stats = db.query(
            func.date(DeliveryReceipt.created_at).label('date'),
            func.count(DeliveryReceipt.id).label('count')
        ).filter(
            DeliveryReceipt.created_at.between(week_start, week_end)
        ).group_by(func.date(DeliveryReceipt.created_at)).all()
        
        daily_dict = {}
        for date, count in daily_stats:
            daily_dict[date.isoformat()] = count
        
        # 成功率计算
        sent_count = status_dict.get(DeliveryStatusEnum.SENT.value, 0)
        delivered_count = status_dict.get(DeliveryStatusEnum.DELIVERED.value, 0)
        
        success_rate = 0
        if total_receipts > 0:
            success_rate = ((sent_count + delivered_count) / total_receipts) * 100
        
        # 生成报告
        report = {
            "week_start": last_monday.isoformat(),
            "week_end": last_sunday.isoformat(),
            "total_receipts": total_receipts,
            "status_breakdown": status_dict,
            "daily_breakdown": daily_dict,
            "success_rate": round(success_rate, 2),
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存报告到文件
        reports_dir = "reports/receipts"
        os.makedirs(reports_dir, exist_ok=True)
        
        report_filename = f"receipt_weekly_report_{last_monday.strftime('%Y%m%d')}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"每周送达回证统计报告生成完成: {report_path}")
        
        return {
            "success": True,
            "message": "每周送达回证统计报告生成完成",
            "report": report,
            "report_file": report_path
        }
        
    except SQLAlchemyError as e:
        logger.error(f"生成每周报告时数据库错误: {str(e)}")
        db.rollback()
        raise e
        
    except Exception as e:
        logger.error(f"生成每周报告失败: {str(e)}")
        raise e
        
    finally:
        db.close()


@celery_app.task(**get_retry_config('default'))
@retry_task('default', on_failure=log_task_failure, on_retry=log_task_retry)
def generate_monthly_report(self):
    """
    生成每月送达回证统计报告
    
    重试策略: default (最多3次重试，60秒起始延迟，指数退避)
    """
    from datetime import datetime, timedelta
    import calendar
    import json
    import os
    
    logger.info("开始生成每月送达回证统计报告")
    
    db: Session = SessionLocal()
    
    try:
        # 统计上月的数据
        today = datetime.now().date()
        
        # 计算上月第一天和最后一天
        if today.month == 1:
            last_month = 12
            last_year = today.year - 1
        else:
            last_month = today.month - 1
            last_year = today.year
        
        month_start = datetime(last_year, last_month, 1)
        last_day = calendar.monthrange(last_year, last_month)[1]
        month_end = datetime(last_year, last_month, last_day, 23, 59, 59)
        
        service = DeliveryReceiptService(db)
        
        # 获取上月回证统计
        from sqlalchemy import func
        from app.models.delivery_receipt import DeliveryReceipt
        
        # 总数统计
        total_receipts = db.query(func.count(DeliveryReceipt.id)).filter(
            DeliveryReceipt.created_at.between(month_start, month_end)
        ).scalar()
        
        # 按状态统计
        status_stats = db.query(
            DeliveryReceipt.status,
            func.count(DeliveryReceipt.id).label('count')
        ).filter(
            DeliveryReceipt.created_at.between(month_start, month_end)
        ).group_by(DeliveryReceipt.status).all()
        
        status_dict = {}
        for status, count in status_stats:
            status_dict[status.value] = count
        
        # 按周统计
        weekly_stats = db.query(
            func.extract('week', DeliveryReceipt.created_at).label('week'),
            func.count(DeliveryReceipt.id).label('count')
        ).filter(
            DeliveryReceipt.created_at.between(month_start, month_end)
        ).group_by(func.extract('week', DeliveryReceipt.created_at)).all()
        
        weekly_dict = {}
        for week, count in weekly_stats:
            weekly_dict[f"week_{int(week)}"] = count
        
        # 成功率计算
        sent_count = status_dict.get(DeliveryStatusEnum.SENT.value, 0)
        delivered_count = status_dict.get(DeliveryStatusEnum.DELIVERED.value, 0)
        
        success_rate = 0
        if total_receipts > 0:
            success_rate = ((sent_count + delivered_count) / total_receipts) * 100
        
        # 生成报告
        report = {
            "month": f"{last_year}-{last_month:02d}",
            "month_start": month_start.isoformat(),
            "month_end": month_end.isoformat(),
            "total_receipts": total_receipts,
            "status_breakdown": status_dict,
            "weekly_breakdown": weekly_dict,
            "success_rate": round(success_rate, 2),
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存报告到文件
        reports_dir = "reports/receipts"
        os.makedirs(reports_dir, exist_ok=True)
        
        report_filename = f"receipt_monthly_report_{last_year}{last_month:02d}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"每月送达回证统计报告生成完成: {report_path}")
        
        return {
            "success": True,
            "message": "每月送达回证统计报告生成完成",
            "report": report,
            "report_file": report_path
        }
        
    except SQLAlchemyError as e:
        logger.error(f"生成每月报告时数据库错误: {str(e)}")
        db.rollback()
        raise e
        
    except Exception as e:
        logger.error(f"生成每月报告失败: {str(e)}")
        raise e
        
    finally:
        db.close()