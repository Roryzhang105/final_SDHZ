"""
使用智能重试的物流跟踪任务示例
展示如何在实际任务中使用智能重试系统
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from celery import current_app as celery_app
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from requests.exceptions import ConnectionError, Timeout, HTTPError
import requests

from app.core.database import SessionLocal
from app.core.config import settings
from app.services.tracking import TrackingService
from app.services.delivery_receipt import DeliveryReceiptService
from app.models.task import Task, TaskStatusEnum
from app.models.delivery_receipt import DeliveryReceipt, DeliveryStatusEnum

# 导入智能重试系统
from app.tasks.retry_handler import (
    intelligent_retry,
    get_intelligent_retry_config,
    log_intelligent_retry_failure,
    log_intelligent_retry_attempt
)
from app.tasks.retry_strategies import (
    tracking_intelligent_retry,
    RetryConfigFactory,
    BusinessRetryStrategies
)

logger = logging.getLogger(__name__)


@celery_app.task(**RetryConfigFactory.create_celery_config('tracking'))
@tracking_intelligent_retry
def intelligent_update_tracking_info(self, tracking_number: str):
    """
    智能重试的物流信息更新任务
    
    - 网络错误：渐进重试 (5秒 -> 10秒 -> 20秒 -> 40秒)
    - API限流：延迟重试 (5分钟 -> 10分钟 -> 20分钟)
    - 数据错误：不重试，直接失败
    - 服务器错误：延迟重试
    """
    logger.info(f"开始智能更新物流信息: {tracking_number}")
    
    db: Session = SessionLocal()
    
    try:
        tracking_service = TrackingService(db)
        receipt_service = DeliveryReceiptService(db)
        
        # 查找对应的送达回证
        receipt = tracking_service.get_receipt_by_tracking_number(tracking_number)
        if not receipt:
            # 数据错误 - 不重试
            error_msg = f"未找到物流单号对应的送达回证: {tracking_number}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"找到送达回证: {receipt.id}, 快递公司: {receipt.courier_company}")
        
        # 调用第三方API查询物流信息
        tracking_data = query_express_api(tracking_number, receipt.courier_company)
        
        if not tracking_data:
            # 可能的API错误 - 允许重试
            raise ConnectionError(f"无法获取物流信息: {tracking_number}")
        
        # 更新物流信息到数据库
        try:
            tracking_info = tracking_service.create_or_update_tracking(
                receipt_id=receipt.id,
                current_status=tracking_data.get("status", ""),
                tracking_data=tracking_data,
                notes=f"智能重试系统更新于 {datetime.now().isoformat()}"
            )
            
            # 根据物流状态更新送达回证状态
            if tracking_data.get("status") == "已签收":
                receipt_service.update_receipt_status(
                    receipt.id, 
                    DeliveryStatusEnum.DELIVERED.value
                )
            elif tracking_data.get("status") in ["运输中", "派件中"]:
                receipt_service.update_receipt_status(
                    receipt.id, 
                    DeliveryStatusEnum.SENT.value
                )
            
            db.commit()
            
            logger.info(f"物流信息更新成功: {tracking_number}, 状态: {tracking_data.get('status')}")
            
            return {
                "success": True,
                "tracking_number": tracking_number,
                "status": tracking_data.get("status"),
                "tracking_info": tracking_info.id if tracking_info else None,
                "updated_at": datetime.now().isoformat()
            }
            
        except SQLAlchemyError as e:
            # 数据库错误 - 允许重试
            logger.error(f"数据库操作失败: {tracking_number}, 错误: {str(e)}")
            db.rollback()
            raise e
            
    except ValueError as e:
        # 数据验证错误 - 不重试
        logger.error(f"数据验证错误: {tracking_number}, 错误: {str(e)}")
        raise e
        
    except (ConnectionError, Timeout, HTTPError) as e:
        # 网络相关错误 - 智能重试
        logger.warning(f"网络错误，将重试: {tracking_number}, 错误: {str(e)}")
        raise e
        
    except Exception as e:
        # 其他未知错误 - 允许重试
        logger.error(f"未知错误: {tracking_number}, 错误: {str(e)}")
        raise e
        
    finally:
        db.close()


def query_express_api(tracking_number: str, courier_company: str) -> Optional[Dict[str, Any]]:
    """
    查询快递API获取物流信息
    
    Args:
        tracking_number: 物流单号
        courier_company: 快递公司
        
    Returns:
        物流信息字典或None
        
    Raises:
        ConnectionError: 网络连接错误
        HTTPError: HTTP请求错误
        Timeout: 请求超时
    """
    try:
        # 快递公司代码映射
        courier_codes = {
            "顺丰": "SF",
            "中通": "ZTO",
            "圆通": "YTO",
            "申通": "STO",
            "韵达": "YD",
            "EMS": "EMS"
        }
        
        courier_code = courier_codes.get(courier_company, "AUTO")
        
        # 调用快递鸟API（示例）
        api_url = "https://api.kdniao.com/Ebusiness/EbusinessOrderHandle.aspx"
        
        # 构造请求参数
        params = {
            "RequestType": "1002",  # 即时查询
            "ShipperCode": courier_code,
            "LogisticCode": tracking_number,
            "CustomerName": "",
        }
        
        # 发送请求
        response = requests.post(
            api_url,
            json=params,
            timeout=30,  # 30秒超时
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'DeliveryReceipt/1.0'
            }
        )
        
        # 检查HTTP状态码
        if response.status_code == 429:
            # API限流错误
            raise HTTPError(f"API限流: {response.status_code}", response=response)
        elif response.status_code >= 500:
            # 服务器错误
            raise HTTPError(f"服务器错误: {response.status_code}", response=response)
        elif response.status_code >= 400:
            # 客户端错误
            raise HTTPError(f"客户端错误: {response.status_code}", response=response)
        
        response.raise_for_status()
        
        # 解析响应数据
        data = response.json()
        
        if not data.get("Success"):
            # API返回失败
            error_msg = data.get("Reason", "API查询失败")
            if "超过调用频率" in error_msg or "限流" in error_msg:
                raise HTTPError("API调用频率限制", response=type('MockResponse', (), {'status_code': 429})())
            else:
                raise ConnectionError(f"API查询失败: {error_msg}")
        
        # 提取物流信息
        traces = data.get("Traces", [])
        if not traces:
            return None
        
        # 获取最新状态
        latest_trace = traces[0] if traces else {}
        
        return {
            "status": latest_trace.get("AcceptStation", ""),
            "update_time": latest_trace.get("AcceptTime", ""),
            "location": latest_trace.get("Location", ""),
            "traces": traces,
            "courier_company": courier_company,
            "courier_code": courier_code,
            "query_time": datetime.now().isoformat()
        }
        
    except requests.exceptions.ConnectTimeout:
        raise ConnectionError(f"连接超时: {tracking_number}")
    except requests.exceptions.ReadTimeout:
        raise Timeout(f"读取超时: {tracking_number}")
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"连接错误: {tracking_number}, {str(e)}")
    except requests.exceptions.HTTPError as e:
        raise HTTPError(f"HTTP错误: {tracking_number}, {str(e)}")


@celery_app.task(**RetryConfigFactory.create_celery_config('tracking'))
@tracking_intelligent_retry
def intelligent_batch_update_tracking(self, tracking_numbers: List[str]):
    """
    智能批量更新物流信息
    
    对每个物流单号应用智能重试策略
    """
    if not tracking_numbers:
        logger.warning("批量更新: 收到空的物流单号列表")
        return {
            "success": True,
            "message": "无需处理的物流单号",
            "total": 0,
            "results": []
        }
    
    logger.info(f"开始智能批量更新 {len(tracking_numbers)} 个物流信息")
    
    results = []
    successful = 0
    failed = 0
    
    try:
        for tracking_number in tracking_numbers:
            try:
                # 验证物流单号格式
                if not isinstance(tracking_number, str) or not tracking_number.strip():
                    logger.error(f"无效的物流单号: {tracking_number}")
                    failed += 1
                    results.append({
                        "tracking_number": tracking_number,
                        "status": "failed",
                        "error": "无效的物流单号格式"
                    })
                    continue
                
                # 启动智能重试任务
                result = intelligent_update_tracking_info.delay(tracking_number.strip())
                successful += 1
                results.append({
                    "tracking_number": tracking_number,
                    "task_id": result.id,
                    "status": "submitted"
                })
                logger.debug(f"物流更新任务已提交: {tracking_number} -> {result.id}")
                
            except Exception as e:
                failed += 1
                error_msg = f"启动物流更新任务失败: {tracking_number}, 错误: {str(e)}"
                logger.error(error_msg)
                results.append({
                    "tracking_number": tracking_number,
                    "status": "failed",
                    "error": error_msg
                })
        
        logger.info(f"智能批量更新完成: 成功提交 {successful} 个, 失败 {failed} 个")
        
        return {
            "success": True,
            "message": f"智能批量处理 {len(tracking_numbers)} 个物流单号",
            "total": len(tracking_numbers),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"智能批量更新时发生意外错误: {str(e)}")
        raise e


@celery_app.task(**RetryConfigFactory.create_celery_config('tracking'))
@intelligent_retry(
    custom_strategies=BusinessRetryStrategies.TRACKING_QUERY,
    failure_callback=log_intelligent_retry_failure,
    retry_callback=log_intelligent_retry_attempt
)
def intelligent_update_all_pending_tracking(self):
    """
    智能更新所有待处理的物流信息
    
    使用智能重试处理数据库连接和查询错误
    """
    logger.info("开始智能更新所有待处理的物流信息")
    
    db: Session = SessionLocal()
    
    try:
        # 查询所有需要更新的物流信息
        cutoff_time = datetime.now() - timedelta(hours=2)  # 2小时内未更新的
        
        pending_receipts = db.query(DeliveryReceipt).filter(
            DeliveryReceipt.status.in_([
                DeliveryStatusEnum.PROCESSING,
                DeliveryStatusEnum.SENT
            ]),
            DeliveryReceipt.tracking_number.isnot(None),
            or_(
                DeliveryReceipt.updated_at < cutoff_time,
                DeliveryReceipt.updated_at.is_(None)
            )
        ).limit(50).all()  # 限制批次大小
        
        if not pending_receipts:
            logger.info("没有需要更新的物流信息")
            return {
                "success": True,
                "message": "没有需要更新的物流信息",
                "total": 0,
                "tasks": []
            }
        
        logger.info(f"找到 {len(pending_receipts)} 个需要更新的物流信息")
        
        # 提取物流单号
        tracking_numbers = [receipt.tracking_number for receipt in pending_receipts]
        
        # 批量提交智能重试任务
        batch_result = intelligent_batch_update_tracking.delay(tracking_numbers)
        
        logger.info(f"智能批量更新任务已提交: {batch_result.id}")
        
        return {
            "success": True,
            "message": f"智能更新 {len(pending_receipts)} 个待处理物流信息",
            "total": len(pending_receipts),
            "batch_task_id": batch_result.id,
            "tracking_numbers": tracking_numbers
        }
        
    except SQLAlchemyError as e:
        logger.error(f"数据库查询错误: {str(e)}")
        db.rollback()
        raise e
        
    except Exception as e:
        logger.error(f"智能更新所有待处理物流信息失败: {str(e)}")
        raise e
        
    finally:
        db.close()


# 错误分析和监控任务
@celery_app.task(**RetryConfigFactory.create_celery_config('monitoring'))
@intelligent_retry(
    custom_strategies=BusinessRetryStrategies.MONITORING_TASKS,
    failure_callback=log_intelligent_retry_failure,
    retry_callback=log_intelligent_retry_attempt
)
def analyze_tracking_errors(self, hours: int = 24):
    """
    分析物流跟踪任务的错误模式
    """
    from app.tasks.retry_handler import analyze_task_errors
    
    logger.info(f"开始分析最近 {hours} 小时的物流跟踪错误")
    
    try:
        # 分析不同任务的错误情况
        task_names = [
            "intelligent_update_tracking_info",
            "intelligent_batch_update_tracking", 
            "intelligent_update_all_pending_tracking"
        ]
        
        analysis_report = {
            "analysis_time": datetime.now().isoformat(),
            "analysis_period_hours": hours,
            "task_analyses": {}
        }
        
        for task_name in task_names:
            analysis = analyze_task_errors(task_name)
            analysis_report["task_analyses"][task_name] = analysis
            
            logger.info(f"任务 {task_name} 错误分析:")
            logger.info(f"  - 总错误数: {analysis.get('total_errors', 0)}")
            logger.info(f"  - 建议: {analysis.get('suggestions', [])}")
        
        return {
            "success": True,
            "analysis_report": analysis_report
        }
        
    except Exception as e:
        logger.error(f"分析物流跟踪错误失败: {str(e)}")
        raise e