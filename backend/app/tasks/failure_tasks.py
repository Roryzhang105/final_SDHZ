"""
失败任务自动处理系统
定时扫描、分析和处理失败的任务
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from celery import current_app as celery_app
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, or_, desc

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.task import Task, TaskStatusEnum
from app.models.delivery_receipt import DeliveryReceipt, DeliveryStatusEnum
from app.services.task import TaskService
from app.services.delivery_receipt import DeliveryReceiptService

# 导入智能重试系统
from app.tasks.retry_handler import (
    IntelligentRetryHandler,
    ErrorCategory,
    RetryDecision,
    analyze_task_errors
)
from app.tasks.retry_strategies import (
    RetryConfigFactory,
    BusinessRetryStrategies
)

logger = logging.getLogger(__name__)


class FailureCategory(Enum):
    """失败任务分类"""
    RECOVERABLE_NETWORK = "recoverable_network"        # 可恢复的网络错误
    RECOVERABLE_SYSTEM = "recoverable_system"          # 可恢复的系统错误  
    RECOVERABLE_TEMPORARY = "recoverable_temporary"    # 可恢复的临时错误
    UNRECOVERABLE_DATA = "unrecoverable_data"         # 不可恢复的数据错误
    UNRECOVERABLE_CONFIG = "unrecoverable_config"     # 不可恢复的配置错误
    UNRECOVERABLE_BUSINESS = "unrecoverable_business" # 不可恢复的业务错误
    UNKNOWN = "unknown"                               # 未知类型


class FailureAnalyzer:
    """失败任务分析器"""
    
    def __init__(self):
        self.retry_handler = IntelligentRetryHandler()
        # 错误模式识别规则
        self.error_patterns = {
            # 网络相关错误模式
            FailureCategory.RECOVERABLE_NETWORK: [
                r'connection.*timeout',
                r'network.*unreachable',
                r'connection.*refused',
                r'dns.*resolution.*failed',
                r'socket.*timeout',
                r'read.*timeout',
                r'connect.*timeout',
                r'http.*timeout',
                r'request.*timeout',
                r'connection.*reset',
                r'temporary.*failure.*in.*name.*resolution'
            ],
            
            # 系统资源相关错误
            FailureCategory.RECOVERABLE_SYSTEM: [
                r'memory.*error',
                r'disk.*space',
                r'no.*space.*left',
                r'resource.*temporarily.*unavailable',
                r'too.*many.*open.*files',
                r'permission.*denied',
                r'device.*or.*resource.*busy',
                r'cannot.*allocate.*memory',
                r'system.*overloaded'
            ],
            
            # 临时错误
            FailureCategory.RECOVERABLE_TEMPORARY: [
                r'database.*connection.*failed',
                r'deadlock.*detected',
                r'lock.*wait.*timeout',
                r'server.*temporarily.*unavailable',
                r'service.*unavailable',
                r'internal.*server.*error',
                r'bad.*gateway',
                r'gateway.*timeout',
                r'too.*many.*requests',
                r'rate.*limit.*exceeded',
                r'quota.*exceeded',
                r'temporarily.*overloaded'
            ],
            
            # 数据相关错误（不可恢复）
            FailureCategory.UNRECOVERABLE_DATA: [
                r'invalid.*data.*format',
                r'malformed.*json',
                r'parse.*error',
                r'validation.*failed',
                r'constraint.*violation',
                r'foreign.*key.*constraint',
                r'duplicate.*key',
                r'null.*value.*in.*column',
                r'data.*type.*mismatch',
                r'invalid.*input.*syntax',
                r'value.*out.*of.*range',
                r'division.*by.*zero'
            ],
            
            # 配置错误（不可恢复）
            FailureCategory.UNRECOVERABLE_CONFIG: [
                r'configuration.*error',
                r'missing.*required.*parameter',
                r'invalid.*configuration',
                r'authentication.*failed',
                r'unauthorized.*access',
                r'forbidden.*access',
                r'api.*key.*invalid',
                r'certificate.*error',
                r'ssl.*error',
                r'missing.*environment.*variable'
            ],
            
            # 业务逻辑错误（不可恢复）
            FailureCategory.UNRECOVERABLE_BUSINESS: [
                r'business.*rule.*violation',
                r'workflow.*state.*error',
                r'invalid.*operation',
                r'operation.*not.*allowed',
                r'resource.*not.*found',
                r'file.*not.*found',
                r'tracking.*number.*invalid',
                r'courier.*company.*not.*supported',
                r'template.*not.*found'
            ]
        }
    
    def analyze_failure(self, task: Task) -> Tuple[FailureCategory, Dict[str, Any]]:
        """
        分析失败任务，确定失败类别和详情
        
        Args:
            task: 失败的任务对象
            
        Returns:
            (失败类别, 分析详情)
        """
        if not task.error_message:
            return FailureCategory.UNKNOWN, {"reason": "无错误消息"}
        
        error_msg = task.error_message.lower()
        analysis = {
            "task_id": task.id,
            "task_type": task.task_type,
            "error_message": task.error_message,
            "failed_at": task.updated_at.isoformat() if task.updated_at else None,
            "retry_count": getattr(task, 'retry_count', 0),
            "analysis_time": datetime.now().isoformat()
        }
        
        # 按优先级检查错误模式
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_msg, re.IGNORECASE):
                    analysis.update({
                        "category": category.value,
                        "matched_pattern": pattern,
                        "confidence": "high",
                        "recommended_action": self._get_recommended_action(category)
                    })
                    return category, analysis
        
        # 如果没有匹配的模式，使用智能重试处理器分析
        try:
            # 尝试从错误消息重构异常
            mock_exc = Exception(task.error_message)
            error_category = self.retry_handler.classify_error(mock_exc)
            
            # 映射到失败类别
            if error_category == ErrorCategory.NETWORK_ERROR:
                category = FailureCategory.RECOVERABLE_NETWORK
            elif error_category == ErrorCategory.API_RATE_LIMIT:
                category = FailureCategory.RECOVERABLE_TEMPORARY
            elif error_category == ErrorCategory.SYSTEM_ERROR:
                category = FailureCategory.RECOVERABLE_SYSTEM
            elif error_category == ErrorCategory.DATA_ERROR:
                category = FailureCategory.UNRECOVERABLE_DATA
            elif error_category == ErrorCategory.TEMPORARY_ERROR:
                category = FailureCategory.RECOVERABLE_TEMPORARY
            else:
                category = FailureCategory.UNKNOWN
            
            analysis.update({
                "category": category.value,
                "error_category": error_category.value,
                "confidence": "medium",
                "recommended_action": self._get_recommended_action(category)
            })
            
        except Exception as e:
            logger.warning(f"智能分析失败: {str(e)}")
            category = FailureCategory.UNKNOWN
            analysis.update({
                "category": category.value,
                "confidence": "low",
                "recommended_action": "manual_review"
            })
        
        return category, analysis
    
    def _get_recommended_action(self, category: FailureCategory) -> str:
        """获取推荐的处理动作"""
        action_map = {
            FailureCategory.RECOVERABLE_NETWORK: "auto_retry_with_delay",
            FailureCategory.RECOVERABLE_SYSTEM: "auto_retry_with_backoff",
            FailureCategory.RECOVERABLE_TEMPORARY: "auto_retry_progressive",
            FailureCategory.UNRECOVERABLE_DATA: "notify_admin_data_issue",
            FailureCategory.UNRECOVERABLE_CONFIG: "notify_admin_config_issue",
            FailureCategory.UNRECOVERABLE_BUSINESS: "notify_user_business_issue",
            FailureCategory.UNKNOWN: "manual_review"
        }
        return action_map.get(category, "manual_review")


class FailureTaskHandler:
    """失败任务处理器"""
    
    def __init__(self):
        self.analyzer = FailureAnalyzer()
        self.recovery_stats = {
            "scanned": 0,
            "analyzed": 0,
            "recovered": 0,
            "notified": 0,
            "errors": []
        }
    
    def scan_failed_tasks(self, hours: int = 24) -> List[Task]:
        """
        扫描指定时间范围内的失败任务
        
        Args:
            hours: 扫描时间范围（小时）
            
        Returns:
            失败任务列表
        """
        db: Session = SessionLocal()
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            failed_tasks = db.query(Task).filter(
                and_(
                    Task.status == TaskStatusEnum.FAILED,
                    Task.updated_at >= cutoff_time,
                    # 排除已经处理过的任务
                    or_(
                        Task.recovery_attempts.is_(None),
                        Task.recovery_attempts < 3  # 最多尝试3次恢复
                    )
                )
            ).order_by(desc(Task.updated_at)).limit(100).all()
            
            self.recovery_stats["scanned"] = len(failed_tasks)
            logger.info(f"扫描到 {len(failed_tasks)} 个失败任务")
            
            return failed_tasks
            
        except SQLAlchemyError as e:
            logger.error(f"扫描失败任务时数据库错误: {str(e)}")
            self.recovery_stats["errors"].append(f"数据库扫描错误: {str(e)}")
            return []
        finally:
            db.close()
    
    def process_failed_task(self, task: Task) -> Dict[str, Any]:
        """
        处理单个失败任务
        
        Args:
            task: 失败的任务
            
        Returns:
            处理结果
        """
        result = {
            "task_id": task.id,
            "task_type": task.task_type,
            "action_taken": "none",
            "success": False,
            "message": "",
            "analysis": {}
        }
        
        try:
            # 分析失败原因
            category, analysis = self.analyzer.analyze_failure(task)
            result["analysis"] = analysis
            self.recovery_stats["analyzed"] += 1
            
            logger.info(f"任务 {task.id} 失败分析: {category.value}")
            
            # 根据失败类别决定处理动作
            if category in [
                FailureCategory.RECOVERABLE_NETWORK,
                FailureCategory.RECOVERABLE_SYSTEM,
                FailureCategory.RECOVERABLE_TEMPORARY
            ]:
                # 尝试自动恢复
                recovery_result = self._attempt_recovery(task, category, analysis)
                result.update(recovery_result)
                
            elif category in [
                FailureCategory.UNRECOVERABLE_DATA,
                FailureCategory.UNRECOVERABLE_CONFIG,
                FailureCategory.UNRECOVERABLE_BUSINESS
            ]:
                # 发送通知
                notification_result = self._send_failure_notification(task, category, analysis)
                result.update(notification_result)
                
            else:
                # 未知类型，标记为需要人工审查
                result.update({
                    "action_taken": "manual_review_required",
                    "success": True,
                    "message": "任务需要人工审查"
                })
                self._mark_for_manual_review(task, analysis)
            
            return result
            
        except Exception as e:
            logger.error(f"处理失败任务 {task.id} 时发生错误: {str(e)}")
            self.recovery_stats["errors"].append(f"处理任务 {task.id} 错误: {str(e)}")
            result.update({
                "success": False,
                "message": f"处理异常: {str(e)}"
            })
            return result
    
    def _attempt_recovery(self, task: Task, category: FailureCategory, 
                         analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        尝试自动恢复失败任务
        
        Args:
            task: 失败任务
            category: 失败类别
            analysis: 分析结果
            
        Returns:
            恢复结果
        """
        db: Session = SessionLocal()
        
        try:
            # 确定恢复策略
            recovery_strategy = self._get_recovery_strategy(category)
            
            # 计算重试延迟
            retry_delay = self._calculate_recovery_delay(task, category)
            
            # 更新任务状态和恢复尝试次数
            task.recovery_attempts = getattr(task, 'recovery_attempts', 0) + 1
            task.recovery_notes = json.dumps({
                "last_recovery_attempt": datetime.now().isoformat(),
                "recovery_strategy": recovery_strategy,
                "failure_analysis": analysis
            })
            
            db.commit()
            
            # 根据任务类型重新提交任务
            new_task_result = self._resubmit_task(task, retry_delay)
            
            if new_task_result["success"]:
                self.recovery_stats["recovered"] += 1
                logger.info(f"任务 {task.id} 自动恢复成功，新任务ID: {new_task_result.get('new_task_id')}")
                
                return {
                    "action_taken": "auto_recovery",
                    "success": True,
                    "message": f"任务已重新提交，延迟 {retry_delay} 秒",
                    "recovery_strategy": recovery_strategy,
                    "new_task_id": new_task_result.get("new_task_id"),
                    "retry_delay": retry_delay
                }
            else:
                return {
                    "action_taken": "recovery_failed",
                    "success": False,
                    "message": f"自动恢复失败: {new_task_result.get('error')}"
                }
                
        except Exception as e:
            logger.error(f"自动恢复任务 {task.id} 失败: {str(e)}")
            db.rollback()
            return {
                "action_taken": "recovery_error",
                "success": False,
                "message": f"恢复过程异常: {str(e)}"
            }
        finally:
            db.close()
    
    def _get_recovery_strategy(self, category: FailureCategory) -> str:
        """获取恢复策略"""
        strategy_map = {
            FailureCategory.RECOVERABLE_NETWORK: "immediate_retry",
            FailureCategory.RECOVERABLE_SYSTEM: "delayed_retry",
            FailureCategory.RECOVERABLE_TEMPORARY: "progressive_retry"
        }
        return strategy_map.get(category, "manual_retry")
    
    def _calculate_recovery_delay(self, task: Task, category: FailureCategory) -> int:
        """计算恢复延迟时间"""
        recovery_attempts = getattr(task, 'recovery_attempts', 0)
        
        base_delays = {
            FailureCategory.RECOVERABLE_NETWORK: 30,      # 30秒
            FailureCategory.RECOVERABLE_SYSTEM: 300,      # 5分钟
            FailureCategory.RECOVERABLE_TEMPORARY: 180    # 3分钟
        }
        
        base_delay = base_delays.get(category, 60)
        
        # 指数退避，但有上限
        delay = base_delay * (2 ** min(recovery_attempts, 4))
        return min(delay, 3600)  # 最长1小时
    
    def _resubmit_task(self, task: Task, delay: int) -> Dict[str, Any]:
        """
        重新提交任务
        
        Args:
            task: 原任务
            delay: 延迟时间
            
        Returns:
            提交结果
        """
        try:
            # 根据任务类型重新提交
            if task.task_type == "delivery_receipt":
                from app.tasks.receipt_tasks import process_delivery_receipt
                result = process_delivery_receipt.apply_async(
                    args=[task.delivery_receipt_id],
                    countdown=delay
                )
                
            elif task.task_type == "tracking_update":
                from app.tasks.tracking_tasks import update_tracking_info
                # 需要从任务参数中提取tracking_number
                task_params = json.loads(task.parameters) if task.parameters else {}
                tracking_number = task_params.get("tracking_number", "")
                
                if tracking_number:
                    result = update_tracking_info.apply_async(
                        args=[tracking_number],
                        countdown=delay
                    )
                else:
                    return {"success": False, "error": "缺少tracking_number参数"}
                
            elif task.task_type == "screenshot_capture":
                from app.tasks.screenshot_tasks import capture_tracking_screenshot_task
                task_params = json.loads(task.parameters) if task.parameters else {}
                tracking_number = task_params.get("tracking_number", "")
                
                if tracking_number:
                    result = capture_tracking_screenshot_task.apply_async(
                        args=[tracking_number],
                        countdown=delay
                    )
                else:
                    return {"success": False, "error": "缺少tracking_number参数"}
                
            else:
                return {"success": False, "error": f"不支持的任务类型: {task.task_type}"}
            
            return {
                "success": True,
                "new_task_id": result.id,
                "delay": delay
            }
            
        except Exception as e:
            logger.error(f"重新提交任务失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _send_failure_notification(self, task: Task, category: FailureCategory, 
                                  analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送失败通知
        
        Args:
            task: 失败任务
            category: 失败类别
            analysis: 分析结果
            
        Returns:
            通知结果
        """
        try:
            # 生成通知内容
            notification = self._generate_notification(task, category, analysis)
            
            # 根据失败类别选择通知对象
            if category == FailureCategory.UNRECOVERABLE_DATA:
                # 数据问题通知管理员
                notification_result = self._notify_admin(notification)
            elif category == FailureCategory.UNRECOVERABLE_CONFIG:
                # 配置问题通知管理员
                notification_result = self._notify_admin(notification)
            elif category == FailureCategory.UNRECOVERABLE_BUSINESS:
                # 业务问题通知用户
                notification_result = self._notify_user(task, notification)
            else:
                notification_result = {"success": False, "error": "未知通知类型"}
            
            if notification_result["success"]:
                self.recovery_stats["notified"] += 1
            
            return {
                "action_taken": "notification_sent",
                "success": notification_result["success"],
                "message": notification_result.get("message", ""),
                "notification_type": notification["type"]
            }
            
        except Exception as e:
            logger.error(f"发送失败通知时发生错误: {str(e)}")
            return {
                "action_taken": "notification_failed",
                "success": False,
                "message": f"通知发送失败: {str(e)}"
            }
    
    def _generate_notification(self, task: Task, category: FailureCategory, 
                              analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成通知内容"""
        notification = {
            "type": "task_failure",
            "severity": "high" if "unrecoverable" in category.value else "medium",
            "task_id": task.id,
            "task_type": task.task_type,
            "failure_category": category.value,
            "error_message": task.error_message,
            "failed_at": task.updated_at.isoformat() if task.updated_at else None,
            "analysis": analysis,
            "created_at": datetime.now().isoformat()
        }
        
        # 生成用户友好的描述
        if category == FailureCategory.UNRECOVERABLE_DATA:
            notification["title"] = "数据错误导致任务失败"
            notification["description"] = "任务因数据格式或内容错误而无法完成，需要检查输入数据"
        elif category == FailureCategory.UNRECOVERABLE_CONFIG:
            notification["title"] = "配置错误导致任务失败"
            notification["description"] = "任务因系统配置错误而无法完成，需要检查系统设置"
        elif category == FailureCategory.UNRECOVERABLE_BUSINESS:
            notification["title"] = "业务逻辑错误导致任务失败"
            notification["description"] = "任务因业务规则冲突而无法完成，需要检查业务流程"
        else:
            notification["title"] = "任务失败需要处理"
            notification["description"] = "任务失败，需要人工介入处理"
        
        return notification
    
    def _notify_admin(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """通知管理员"""
        try:
            # 记录到管理员告警日志
            admin_log_file = "logs/admin_alerts.log"
            
            import os
            os.makedirs(os.path.dirname(admin_log_file), exist_ok=True)
            
            with open(admin_log_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - {json.dumps(notification, ensure_ascii=False)}\n")
            
            logger.warning(f"管理员告警: {notification['title']} - 任务ID: {notification['task_id']}")
            
            # TODO: 这里可以集成邮件、短信、钉钉等通知方式
            # send_email_to_admin(notification)
            # send_dingtalk_notification(notification)
            
            return {
                "success": True,
                "message": "管理员通知已发送",
                "notification_method": "log_file"
            }
            
        except Exception as e:
            logger.error(f"通知管理员失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _notify_user(self, task: Task, notification: Dict[str, Any]) -> Dict[str, Any]:
        """通知用户"""
        try:
            # 记录到用户通知日志
            user_log_file = "logs/user_notifications.log"
            
            import os
            os.makedirs(os.path.dirname(user_log_file), exist_ok=True)
            
            with open(user_log_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - {json.dumps(notification, ensure_ascii=False)}\n")
            
            logger.info(f"用户通知: {notification['title']} - 任务ID: {notification['task_id']}")
            
            # TODO: 这里可以集成用户通知方式
            # send_user_notification(task.user_id, notification)
            # create_system_message(task.user_id, notification)
            
            return {
                "success": True,
                "message": "用户通知已发送",
                "notification_method": "log_file"
            }
            
        except Exception as e:
            logger.error(f"通知用户失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _mark_for_manual_review(self, task: Task, analysis: Dict[str, Any]):
        """标记任务需要人工审查"""
        db: Session = SessionLocal()
        
        try:
            task.manual_review_required = True
            task.review_notes = json.dumps({
                "marked_at": datetime.now().isoformat(),
                "reason": "failure_analysis_uncertain",
                "analysis": analysis
            })
            
            db.commit()
            logger.info(f"任务 {task.id} 已标记为需要人工审查")
            
        except Exception as e:
            logger.error(f"标记人工审查失败: {str(e)}")
            db.rollback()
        finally:
            db.close()


# Celery任务定义
@celery_app.task(**RetryConfigFactory.create_celery_config('monitoring'))
def scan_and_process_failed_tasks():
    """
    扫描和处理失败任务的定时任务
    """
    logger.info("开始扫描和处理失败任务")
    
    handler = FailureTaskHandler()
    
    try:
        # 扫描最近24小时的失败任务
        failed_tasks = handler.scan_failed_tasks(hours=24)
        
        if not failed_tasks:
            logger.info("没有需要处理的失败任务")
            return {
                "success": True,
                "message": "没有失败任务需要处理",
                "stats": handler.recovery_stats
            }
        
        results = []
        
        # 处理每个失败任务
        for task in failed_tasks:
            try:
                result = handler.process_failed_task(task)
                results.append(result)
                
                logger.info(f"任务 {task.id} 处理完成: {result['action_taken']}")
                
            except Exception as e:
                logger.error(f"处理失败任务 {task.id} 时发生异常: {str(e)}")
                handler.recovery_stats["errors"].append(f"任务 {task.id} 处理异常: {str(e)}")
        
        # 生成处理报告
        report = {
            "success": True,
            "message": f"失败任务处理完成",
            "total_processed": len(results),
            "stats": handler.recovery_stats,
            "results": results,
            "processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"失败任务处理报告: {handler.recovery_stats}")
        
        # 保存处理报告
        save_failure_processing_report(report)
        
        return report
        
    except Exception as e:
        logger.error(f"扫描和处理失败任务时发生错误: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "stats": handler.recovery_stats
        }


@celery_app.task(**RetryConfigFactory.create_celery_config('monitoring'))
def analyze_failure_patterns():
    """
    分析失败模式，生成趋势报告
    """
    logger.info("开始分析失败任务模式")
    
    db: Session = SessionLocal()
    
    try:
        # 分析最近7天的失败任务模式
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        failed_tasks = db.query(Task).filter(
            and_(
                Task.status == TaskStatusEnum.FAILED,
                Task.updated_at >= start_time,
                Task.updated_at <= end_time
            )
        ).all()
        
        if not failed_tasks:
            return {
                "success": True,
                "message": "没有失败任务数据进行分析",
                "analysis_period": "7天",
                "total_failures": 0
            }
        
        analyzer = FailureAnalyzer()
        
        # 统计分析
        category_counts = {}
        error_patterns = {}
        task_type_failures = {}
        daily_failures = {}
        
        for task in failed_tasks:
            # 失败类别统计
            category, analysis = analyzer.analyze_failure(task)
            category_counts[category.value] = category_counts.get(category.value, 0) + 1
            
            # 错误模式统计
            if task.error_message:
                error_key = task.error_message[:100]  # 取前100字符作为键
                error_patterns[error_key] = error_patterns.get(error_key, 0) + 1
            
            # 任务类型失败统计
            task_type_failures[task.task_type] = task_type_failures.get(task.task_type, 0) + 1
            
            # 每日失败统计
            day_key = task.updated_at.date().isoformat() if task.updated_at else "unknown"
            daily_failures[day_key] = daily_failures.get(day_key, 0) + 1
        
        # 生成分析报告
        analysis_report = {
            "success": True,
            "analysis_period": "7天",
            "analysis_time": datetime.now().isoformat(),
            "total_failures": len(failed_tasks),
            "category_distribution": category_counts,
            "top_error_patterns": dict(sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]),
            "task_type_failures": task_type_failures,
            "daily_failure_trend": daily_failures,
            "insights": generate_failure_insights(category_counts, task_type_failures)
        }
        
        # 保存分析报告
        save_failure_analysis_report(analysis_report)
        
        logger.info(f"失败模式分析完成: 总失败数 {len(failed_tasks)}")
        
        return analysis_report
        
    except SQLAlchemyError as e:
        logger.error(f"分析失败模式时数据库错误: {str(e)}")
        return {"success": False, "error": f"数据库错误: {str(e)}"}
    except Exception as e:
        logger.error(f"分析失败模式时发生错误: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def generate_failure_insights(category_counts: Dict[str, int], 
                             task_type_failures: Dict[str, int]) -> List[str]:
    """生成失败分析洞察"""
    insights = []
    total_failures = sum(category_counts.values())
    
    if total_failures == 0:
        return ["没有失败任务数据"]
    
    # 分析主要失败类型
    most_common_category = max(category_counts.items(), key=lambda x: x[1])
    if most_common_category[1] / total_failures > 0.4:
        insights.append(f"主要失败原因是{most_common_category[0]}，占比{most_common_category[1]/total_failures*100:.1f}%")
    
    # 分析可恢复失败比例
    recoverable_count = sum(count for category, count in category_counts.items() 
                           if 'recoverable' in category)
    if recoverable_count / total_failures > 0.6:
        insights.append(f"有{recoverable_count/total_failures*100:.1f}%的失败是可自动恢复的")
    
    # 分析任务类型
    if task_type_failures:
        most_failed_task = max(task_type_failures.items(), key=lambda x: x[1])
        insights.append(f"失败最多的任务类型是{most_failed_task[0]}，共{most_failed_task[1]}次")
    
    # 提供改进建议
    if category_counts.get('recoverable_network', 0) > total_failures * 0.3:
        insights.append("建议检查网络连接稳定性和API服务可用性")
    
    if category_counts.get('unrecoverable_data', 0) > total_failures * 0.2:
        insights.append("建议加强输入数据验证和错误处理")
    
    return insights


def save_failure_processing_report(report: Dict[str, Any]):
    """保存失败任务处理报告"""
    try:
        import os
        
        reports_dir = "reports/failure_processing"
        os.makedirs(reports_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(reports_dir, f"failure_processing_{timestamp}.json")
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"失败任务处理报告已保存: {report_file}")
        
    except Exception as e:
        logger.error(f"保存失败任务处理报告失败: {str(e)}")


def save_failure_analysis_report(report: Dict[str, Any]):
    """保存失败分析报告"""
    try:
        import os
        
        reports_dir = "reports/failure_analysis"
        os.makedirs(reports_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(reports_dir, f"failure_analysis_{timestamp}.json")
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"失败分析报告已保存: {report_file}")
        
    except Exception as e:
        logger.error(f"保存失败分析报告失败: {str(e)}")


# 手动触发的恢复任务
@celery_app.task(**RetryConfigFactory.create_celery_config('critical'))
def manual_recovery_task(task_id: int, force_retry: bool = False):
    """
    手动恢复指定的失败任务
    
    Args:
        task_id: 任务ID
        force_retry: 是否强制重试（忽略恢复次数限制）
    """
    logger.info(f"开始手动恢复任务: {task_id}")
    
    db: Session = SessionLocal()
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            return {"success": False, "error": f"任务 {task_id} 不存在"}
        
        if task.status != TaskStatusEnum.FAILED:
            return {"success": False, "error": f"任务 {task_id} 状态不是失败"}
        
        # 检查恢复次数限制
        recovery_attempts = getattr(task, 'recovery_attempts', 0)
        if not force_retry and recovery_attempts >= 3:
            return {"success": False, "error": "任务恢复次数已达上限，请使用force_retry=True强制重试"}
        
        handler = FailureTaskHandler()
        result = handler.process_failed_task(task)
        
        logger.info(f"手动恢复任务 {task_id} 完成: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"手动恢复任务 {task_id} 失败: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()