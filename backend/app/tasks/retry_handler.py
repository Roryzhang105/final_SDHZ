"""
智能重试处理器
根据错误类型和情况自动决定重试策略
"""

import logging
import time
import inspect
from typing import Type, Dict, Any, Optional, Callable, Tuple, Union
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum

from celery.exceptions import Retry
from sqlalchemy.exc import SQLAlchemyError
from requests.exceptions import (
    ConnectionError, 
    Timeout, 
    HTTPError, 
    RequestException,
    ConnectTimeout,
    ReadTimeout
)

logger = logging.getLogger(__name__)


class RetryDecision(Enum):
    """重试决策类型"""
    RETRY_IMMEDIATELY = "retry_immediately"      # 立即重试
    RETRY_WITH_DELAY = "retry_with_delay"       # 延迟重试
    RETRY_WITH_BACKOFF = "retry_with_backoff"   # 指数退避重试
    NO_RETRY = "no_retry"                       # 不重试
    ESCALATE = "escalate"                       # 升级处理


class ErrorCategory(Enum):
    """错误分类"""
    NETWORK_ERROR = "network_error"             # 网络错误
    API_RATE_LIMIT = "api_rate_limit"          # API限流
    DATA_ERROR = "data_error"                  # 数据错误
    SYSTEM_ERROR = "system_error"              # 系统错误
    TEMPORARY_ERROR = "temporary_error"        # 临时错误
    PERMANENT_ERROR = "permanent_error"        # 永久错误


class RetryStrategy:
    """重试策略配置"""
    
    def __init__(self, 
                 decision: RetryDecision,
                 max_retries: int = 3,
                 base_delay: int = 60,
                 max_delay: int = 300,
                 backoff_factor: float = 2.0,
                 jitter: bool = True,
                 escalation_threshold: int = None):
        self.decision = decision
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.escalation_threshold = escalation_threshold or max_retries


# 错误分类映射
ERROR_CLASSIFICATION = {
    # 网络相关错误 - 立即重试
    ConnectionError: ErrorCategory.NETWORK_ERROR,
    ConnectTimeout: ErrorCategory.NETWORK_ERROR,
    ReadTimeout: ErrorCategory.NETWORK_ERROR,
    Timeout: ErrorCategory.NETWORK_ERROR,
    TimeoutError: ErrorCategory.NETWORK_ERROR,
    OSError: ErrorCategory.NETWORK_ERROR,
    
    # HTTP错误需要根据状态码判断
    HTTPError: ErrorCategory.TEMPORARY_ERROR,
    RequestException: ErrorCategory.TEMPORARY_ERROR,
    
    # 数据库错误
    SQLAlchemyError: ErrorCategory.TEMPORARY_ERROR,
    
    # 文件系统错误
    FileNotFoundError: ErrorCategory.DATA_ERROR,
    PermissionError: ErrorCategory.SYSTEM_ERROR,
    IOError: ErrorCategory.TEMPORARY_ERROR,
    
    # 数据验证错误
    ValueError: ErrorCategory.DATA_ERROR,
    TypeError: ErrorCategory.DATA_ERROR,
    KeyError: ErrorCategory.DATA_ERROR,
    
    # 系统错误
    MemoryError: ErrorCategory.SYSTEM_ERROR,
    SystemError: ErrorCategory.SYSTEM_ERROR,
}


# 重试策略配置
RETRY_STRATEGIES = {
    ErrorCategory.NETWORK_ERROR: RetryStrategy(
        decision=RetryDecision.RETRY_IMMEDIATELY,
        max_retries=5,
        base_delay=5,  # 网络错误快速重试
        max_delay=30,
        backoff_factor=1.5
    ),
    
    ErrorCategory.API_RATE_LIMIT: RetryStrategy(
        decision=RetryDecision.RETRY_WITH_DELAY,
        max_retries=3,
        base_delay=300,  # API限流需要等待更长时间
        max_delay=1800,  # 最长等待30分钟
        backoff_factor=2.0
    ),
    
    ErrorCategory.DATA_ERROR: RetryStrategy(
        decision=RetryDecision.NO_RETRY,
        max_retries=0
    ),
    
    ErrorCategory.SYSTEM_ERROR: RetryStrategy(
        decision=RetryDecision.RETRY_WITH_BACKOFF,
        max_retries=2,
        base_delay=120,
        max_delay=600,
        backoff_factor=2.0
    ),
    
    ErrorCategory.TEMPORARY_ERROR: RetryStrategy(
        decision=RetryDecision.RETRY_WITH_BACKOFF,
        max_retries=3,
        base_delay=60,
        max_delay=300,
        backoff_factor=2.0
    ),
    
    ErrorCategory.PERMANENT_ERROR: RetryStrategy(
        decision=RetryDecision.NO_RETRY,
        max_retries=0
    )
}


class IntelligentRetryHandler:
    """智能重试处理器"""
    
    def __init__(self):
        self.retry_count_cache = {}  # 重试次数缓存
        self.error_history = {}      # 错误历史记录
    
    def classify_error(self, exc: Exception) -> ErrorCategory:
        """
        分类错误类型
        
        Args:
            exc: 异常对象
            
        Returns:
            错误分类
        """
        # 特殊处理HTTP错误（优先级最高）
        if isinstance(exc, HTTPError):
            category = self._classify_http_error(exc)
        else:
            # 首先检查精确匹配
            exc_type = type(exc)
            if exc_type in ERROR_CLASSIFICATION:
                category = ERROR_CLASSIFICATION[exc_type]
            else:
                # 检查继承关系
                category = ErrorCategory.TEMPORARY_ERROR
                for error_type, error_category in ERROR_CLASSIFICATION.items():
                    if isinstance(exc, error_type):
                        category = error_category
                        break
        
        # 检查错误消息中的关键词（优先级最高）
        error_msg = str(exc).lower()
        if any(keyword in error_msg for keyword in ['rate limit', 'too many requests', 'quota exceeded']):
            category = ErrorCategory.API_RATE_LIMIT
        elif any(keyword in error_msg for keyword in ['connection', 'network', 'timeout']):
            category = ErrorCategory.NETWORK_ERROR
        elif any(keyword in error_msg for keyword in ['invalid', 'malformed', 'corrupt']):
            category = ErrorCategory.DATA_ERROR
        
        logger.debug(f"错误分类: {type(exc).__name__} -> {category.value}")
        return category
    
    def _classify_http_error(self, exc: HTTPError) -> ErrorCategory:
        """
        分类HTTP错误
        
        Args:
            exc: HTTP异常
            
        Returns:
            错误分类
        """
        if hasattr(exc, 'response') and exc.response is not None:
            status_code = exc.response.status_code
            
            # 4xx客户端错误
            if 400 <= status_code < 500:
                if status_code == 429:  # Too Many Requests
                    return ErrorCategory.API_RATE_LIMIT
                elif status_code in [400, 401, 403, 404]:  # 客户端错误，不应重试
                    return ErrorCategory.DATA_ERROR
                else:
                    return ErrorCategory.TEMPORARY_ERROR
            
            # 5xx服务器错误
            elif 500 <= status_code < 600:
                if status_code in [500, 502, 503, 504]:  # 临时服务器问题
                    return ErrorCategory.TEMPORARY_ERROR
                else:
                    return ErrorCategory.SYSTEM_ERROR
        
        # 如果没有response或status_code，默认为临时错误
        return ErrorCategory.TEMPORARY_ERROR
    
    def should_retry(self, exc: Exception, retry_count: int, task_name: str = None) -> Tuple[bool, RetryStrategy]:
        """
        判断是否应该重试
        
        Args:
            exc: 异常对象
            retry_count: 当前重试次数
            task_name: 任务名称
            
        Returns:
            (是否重试, 重试策略)
        """
        category = self.classify_error(exc)
        strategy = RETRY_STRATEGIES.get(category, RETRY_STRATEGIES[ErrorCategory.TEMPORARY_ERROR])
        
        # 记录错误历史
        self._record_error(exc, category, task_name)
        
        # 检查是否超过最大重试次数
        if retry_count >= strategy.max_retries:
            logger.warning(f"任务 {task_name} 重试次数已达上限: {retry_count}/{strategy.max_retries}")
            return False, strategy
        
        # 根据决策类型判断
        should_retry = strategy.decision != RetryDecision.NO_RETRY
        
        # 检查是否需要升级处理
        if (strategy.escalation_threshold and 
            retry_count >= strategy.escalation_threshold and 
            should_retry):
            logger.warning(f"任务 {task_name} 达到升级阈值，考虑人工介入")
            # 这里可以发送告警或者其他升级操作
        
        logger.info(f"重试决策: {task_name}, 错误类型: {category.value}, "
                   f"决策: {strategy.decision.value}, 重试: {should_retry}")
        
        return should_retry, strategy
    
    def calculate_delay(self, strategy: RetryStrategy, retry_count: int) -> int:
        """
        计算重试延迟时间
        
        Args:
            strategy: 重试策略
            retry_count: 重试次数
            
        Returns:
            延迟时间（秒）
        """
        if strategy.decision == RetryDecision.RETRY_IMMEDIATELY:
            delay = 0
        elif strategy.decision == RetryDecision.RETRY_WITH_DELAY:
            delay = strategy.base_delay
        elif strategy.decision == RetryDecision.RETRY_WITH_BACKOFF:
            # 指数退避
            delay = min(
                strategy.base_delay * (strategy.backoff_factor ** retry_count),
                strategy.max_delay
            )
        else:
            delay = strategy.base_delay
        
        # 添加随机抖动
        if strategy.jitter and delay > 0:
            import random
            jitter_range = delay * 0.1  # 10%的抖动
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(1, int(delay))  # 确保至少1秒
        
        return int(delay)
    
    def _record_error(self, exc: Exception, category: ErrorCategory, task_name: str = None):
        """
        记录错误历史
        
        Args:
            exc: 异常对象
            category: 错误分类
            task_name: 任务名称
        """
        if task_name:
            if task_name not in self.error_history:
                self.error_history[task_name] = []
            
            self.error_history[task_name].append({
                "timestamp": datetime.now().isoformat(),
                "error_type": type(exc).__name__,
                "error_category": category.value,
                "error_message": str(exc)[:200],  # 限制长度
            })
            
            # 只保留最近50个错误记录
            if len(self.error_history[task_name]) > 50:
                self.error_history[task_name] = self.error_history[task_name][-50:]
    
    def get_error_statistics(self, task_name: str = None) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        Args:
            task_name: 任务名称，如果为None则返回所有任务的统计
            
        Returns:
            错误统计信息
        """
        if task_name and task_name in self.error_history:
            errors = self.error_history[task_name]
        else:
            errors = []
            for task_errors in self.error_history.values():
                errors.extend(task_errors)
        
        if not errors:
            return {"total_errors": 0}
        
        # 统计错误类型
        error_type_counts = {}
        category_counts = {}
        
        for error in errors:
            error_type = error["error_type"]
            category = error["error_category"]
            
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_errors": len(errors),
            "error_type_distribution": error_type_counts,
            "category_distribution": category_counts,
            "recent_errors": errors[-10:] if len(errors) > 10 else errors
        }


# 全局重试处理器实例
retry_handler = IntelligentRetryHandler()


def intelligent_retry(task_func: Callable = None, 
                     custom_strategies: Dict[ErrorCategory, RetryStrategy] = None,
                     failure_callback: Callable = None,
                     retry_callback: Callable = None):
    """
    智能重试装饰器
    
    Args:
        task_func: 任务函数
        custom_strategies: 自定义重试策略
        failure_callback: 失败回调函数
        retry_callback: 重试回调函数
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            task_name = func.__name__
            retry_count = getattr(self.request, 'retries', 0)
            
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                # 使用自定义策略或默认策略
                if custom_strategies:
                    # 临时替换策略
                    original_strategies = RETRY_STRATEGIES.copy()
                    RETRY_STRATEGIES.update(custom_strategies)
                
                try:
                    should_retry, strategy = retry_handler.should_retry(exc, retry_count, task_name)
                    
                    if not should_retry:
                        logger.error(f"任务 {task_name} 不重试: {type(exc).__name__}: {str(exc)}")
                        if failure_callback:
                            failure_callback(self, exc, *args, **kwargs)
                        raise exc
                    
                    # 计算延迟时间
                    delay = retry_handler.calculate_delay(strategy, retry_count)
                    
                    logger.warning(
                        f"任务 {task_name} 第 {retry_count + 1} 次重试，延迟 {delay} 秒. "
                        f"异常: {type(exc).__name__}: {str(exc)}"
                    )
                    
                    # 调用重试回调
                    if retry_callback:
                        retry_callback(self, exc, retry_count, delay, *args, **kwargs)
                    
                    # 执行重试
                    raise self.retry(
                        exc=exc,
                        countdown=delay,
                        max_retries=strategy.max_retries
                    )
                
                finally:
                    # 恢复原始策略
                    if custom_strategies:
                        RETRY_STRATEGIES.clear()
                        RETRY_STRATEGIES.update(original_strategies)
        
        return wrapper
    
    if task_func is None:
        return decorator
    else:
        return decorator(task_func)


def get_intelligent_retry_config(error_category: ErrorCategory = None) -> dict:
    """
    获取智能重试配置
    
    Args:
        error_category: 错误分类，如果为None则使用默认策略
        
    Returns:
        Celery任务配置
    """
    if error_category and error_category in RETRY_STRATEGIES:
        strategy = RETRY_STRATEGIES[error_category]
    else:
        strategy = RETRY_STRATEGIES[ErrorCategory.TEMPORARY_ERROR]
    
    return {
        'bind': True,
        'max_retries': strategy.max_retries,
        'default_retry_delay': strategy.base_delay,
        'retry_backoff': True,
        'retry_backoff_max': strategy.max_delay,
        'retry_jitter': strategy.jitter,
        'autoretry_for': ()  # 不使用自动重试，由智能处理器控制
    }


def create_custom_strategy(decision: RetryDecision,
                          max_retries: int = 3,
                          base_delay: int = 60,
                          max_delay: int = 300,
                          backoff_factor: float = 2.0,
                          jitter: bool = True) -> RetryStrategy:
    """
    创建自定义重试策略
    
    Args:
        decision: 重试决策
        max_retries: 最大重试次数
        base_delay: 基础延迟时间
        max_delay: 最大延迟时间
        backoff_factor: 退避因子
        jitter: 是否添加抖动
        
    Returns:
        重试策略对象
    """
    return RetryStrategy(
        decision=decision,
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter
    )


# 预定义的智能重试装饰器
def network_retry(func):
    """网络错误智能重试装饰器"""
    return intelligent_retry(
        custom_strategies={
            ErrorCategory.NETWORK_ERROR: RETRY_STRATEGIES[ErrorCategory.NETWORK_ERROR]
        }
    )(func)


def api_retry(func):
    """API调用智能重试装饰器"""
    return intelligent_retry(
        custom_strategies={
            ErrorCategory.API_RATE_LIMIT: RETRY_STRATEGIES[ErrorCategory.API_RATE_LIMIT],
            ErrorCategory.NETWORK_ERROR: RETRY_STRATEGIES[ErrorCategory.NETWORK_ERROR]
        }
    )(func)


def data_safe_retry(func):
    """数据安全重试装饰器（数据错误不重试）"""
    return intelligent_retry(
        custom_strategies={
            ErrorCategory.DATA_ERROR: RETRY_STRATEGIES[ErrorCategory.DATA_ERROR]
        }
    )(func)


# 错误分析工具
def analyze_task_errors(task_name: str = None) -> Dict[str, Any]:
    """
    分析任务错误模式
    
    Args:
        task_name: 任务名称
        
    Returns:
        错误分析报告
    """
    stats = retry_handler.get_error_statistics(task_name)
    
    # 生成建议
    suggestions = []
    
    if stats.get("total_errors", 0) > 0:
        category_dist = stats.get("category_distribution", {})
        
        # 分析主要错误类型
        if category_dist.get("network_error", 0) > 0:
            suggestions.append("检查网络连接和服务可用性")
        
        if category_dist.get("api_rate_limit", 0) > 0:
            suggestions.append("考虑增加API调用间隔或申请更高限额")
        
        if category_dist.get("data_error", 0) > 0:
            suggestions.append("检查输入数据格式和有效性")
        
        if category_dist.get("system_error", 0) > 0:
            suggestions.append("检查系统资源使用情况")
    
    return {
        **stats,
        "suggestions": suggestions,
        "analysis_timestamp": datetime.now().isoformat()
    }


def log_intelligent_retry_failure(task_self, exc, *args, **kwargs):
    """智能重试失败日志回调"""
    error_stats = retry_handler.get_error_statistics(task_self.name)
    
    logger.error(
        f"智能重试最终失败: {task_self.name}, "
        f"任务ID: {task_self.request.id}, "
        f"异常: {type(exc).__name__}: {str(exc)}, "
        f"历史错误数: {error_stats.get('total_errors', 0)}"
    )


def log_intelligent_retry_attempt(task_self, exc, retry_count, delay, *args, **kwargs):
    """智能重试尝试日志回调"""
    category = retry_handler.classify_error(exc)
    
    logger.info(
        f"智能重试: {task_self.name}, "
        f"任务ID: {task_self.request.id}, "
        f"重试次数: {retry_count + 1}, "
        f"错误分类: {category.value}, "
        f"延迟: {delay}秒, "
        f"异常: {type(exc).__name__}: {str(exc)}"
    )