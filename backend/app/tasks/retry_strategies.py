"""
重试策略配置文件
定义不同业务场景的重试策略
"""

from typing import Dict, Any
from app.tasks.retry_handler import (
    RetryStrategy,
    RetryDecision,
    ErrorCategory,
    create_custom_strategy
)


class RetryStrategies:
    """重试策略配置类"""
    
    # ================== 网络相关策略 ==================
    
    @staticmethod
    def immediate_network_retry() -> RetryStrategy:
        """
        网络错误立即重试策略
        适用于: 网络请求、API调用
        """
        return create_custom_strategy(
            decision=RetryDecision.RETRY_IMMEDIATELY,
            max_retries=5,
            base_delay=0,  # 立即重试
            max_delay=10,
            backoff_factor=1.2,
            jitter=False
        )
    
    @staticmethod
    def progressive_network_retry() -> RetryStrategy:
        """
        网络错误渐进重试策略
        适用于: 复杂网络操作、文件下载
        """
        return create_custom_strategy(
            decision=RetryDecision.RETRY_WITH_BACKOFF,
            max_retries=4,
            base_delay=5,
            max_delay=60,
            backoff_factor=2.0,
            jitter=True
        )
    
    # ================== API限流策略 ==================
    
    @staticmethod
    def api_rate_limit_retry() -> RetryStrategy:
        """
        API限流重试策略
        适用于: 第三方API调用、物流查询
        """
        return create_custom_strategy(
            decision=RetryDecision.RETRY_WITH_DELAY,
            max_retries=3,
            base_delay=300,  # 5分钟
            max_delay=1800,  # 30分钟
            backoff_factor=2.0,
            jitter=True
        )
    
    @staticmethod
    def gentle_api_retry() -> RetryStrategy:
        """
        温和API重试策略
        适用于: 敏感API、付费服务
        """
        return create_custom_strategy(
            decision=RetryDecision.RETRY_WITH_BACKOFF,
            max_retries=2,
            base_delay=600,  # 10分钟
            max_delay=3600,  # 1小时
            backoff_factor=1.5,
            jitter=True
        )
    
    # ================== 数据处理策略 ==================
    
    @staticmethod
    def data_validation_retry() -> RetryStrategy:
        """
        数据验证重试策略
        适用于: 数据解析、格式转换
        """
        return create_custom_strategy(
            decision=RetryDecision.NO_RETRY,
            max_retries=0  # 数据错误不重试
        )
    
    @staticmethod
    def transient_data_retry() -> RetryStrategy:
        """
        临时数据错误重试策略
        适用于: 数据库连接、缓存操作
        """
        return create_custom_strategy(
            decision=RetryDecision.RETRY_WITH_BACKOFF,
            max_retries=3,
            base_delay=30,
            max_delay=180,
            backoff_factor=2.0,
            jitter=True
        )
    
    # ================== 文件操作策略 ==================
    
    @staticmethod
    def file_operation_retry() -> RetryStrategy:
        """
        文件操作重试策略
        适用于: 文件读写、图片处理
        """
        return create_custom_strategy(
            decision=RetryDecision.RETRY_WITH_BACKOFF,
            max_retries=3,
            base_delay=10,
            max_delay=120,
            backoff_factor=2.0,
            jitter=True
        )
    
    @staticmethod
    def critical_file_retry() -> RetryStrategy:
        """
        关键文件操作重试策略
        适用于: 重要文档生成、备份操作
        """
        return create_custom_strategy(
            decision=RetryDecision.RETRY_WITH_BACKOFF,
            max_retries=5,
            base_delay=20,
            max_delay=300,
            backoff_factor=1.8,
            jitter=True
        )
    
    # ================== 系统资源策略 ==================
    
    @staticmethod
    def resource_constraint_retry() -> RetryStrategy:
        """
        资源约束重试策略
        适用于: 内存不足、CPU过载
        """
        return create_custom_strategy(
            decision=RetryDecision.RETRY_WITH_DELAY,
            max_retries=2,
            base_delay=180,  # 3分钟
            max_delay=600,   # 10分钟
            backoff_factor=2.0,
            jitter=True
        )
    
    @staticmethod
    def quick_recovery_retry() -> RetryStrategy:
        """
        快速恢复重试策略
        适用于: 监控任务、健康检查
        """
        return create_custom_strategy(
            decision=RetryDecision.RETRY_IMMEDIATELY,
            max_retries=2,
            base_delay=1,
            max_delay=10,
            backoff_factor=2.0,
            jitter=False
        )


# ================== 业务场景策略映射 ==================

class BusinessRetryStrategies:
    """业务场景重试策略配置"""
    
    # 物流跟踪相关
    TRACKING_QUERY = {
        ErrorCategory.NETWORK_ERROR: RetryStrategies.progressive_network_retry(),
        ErrorCategory.API_RATE_LIMIT: RetryStrategies.api_rate_limit_retry(),
        ErrorCategory.DATA_ERROR: RetryStrategies.data_validation_retry(),
        ErrorCategory.TEMPORARY_ERROR: RetryStrategies.transient_data_retry()
    }
    
    # 截图生成相关
    SCREENSHOT_CAPTURE = {
        ErrorCategory.NETWORK_ERROR: RetryStrategies.immediate_network_retry(),
        ErrorCategory.SYSTEM_ERROR: RetryStrategies.resource_constraint_retry(),
        ErrorCategory.TEMPORARY_ERROR: RetryStrategies.file_operation_retry()
    }
    
    # 文档生成相关
    DOCUMENT_GENERATION = {
        ErrorCategory.DATA_ERROR: RetryStrategies.data_validation_retry(),
        ErrorCategory.SYSTEM_ERROR: RetryStrategies.resource_constraint_retry(),
        ErrorCategory.TEMPORARY_ERROR: RetryStrategies.critical_file_retry()
    }
    
    # 二维码/条形码生成
    CODE_GENERATION = {
        ErrorCategory.DATA_ERROR: RetryStrategies.data_validation_retry(),
        ErrorCategory.TEMPORARY_ERROR: RetryStrategies.file_operation_retry(),
        ErrorCategory.SYSTEM_ERROR: RetryStrategies.resource_constraint_retry()
    }
    
    # 邮件发送相关
    EMAIL_DELIVERY = {
        ErrorCategory.NETWORK_ERROR: RetryStrategies.progressive_network_retry(),
        ErrorCategory.API_RATE_LIMIT: RetryStrategies.gentle_api_retry(),
        ErrorCategory.DATA_ERROR: RetryStrategies.data_validation_retry(),
        ErrorCategory.TEMPORARY_ERROR: RetryStrategies.transient_data_retry()
    }
    
    # 监控任务相关
    MONITORING_TASKS = {
        ErrorCategory.NETWORK_ERROR: RetryStrategies.quick_recovery_retry(),
        ErrorCategory.SYSTEM_ERROR: RetryStrategies.quick_recovery_retry(),
        ErrorCategory.TEMPORARY_ERROR: RetryStrategies.quick_recovery_retry()
    }
    
    # 数据库操作相关
    DATABASE_OPERATIONS = {
        ErrorCategory.NETWORK_ERROR: RetryStrategies.immediate_network_retry(),
        ErrorCategory.TEMPORARY_ERROR: RetryStrategies.transient_data_retry(),
        ErrorCategory.SYSTEM_ERROR: RetryStrategies.resource_constraint_retry()
    }


# ================== 自定义重试条件 ==================

class CustomRetryConditions:
    """自定义重试条件"""
    
    @staticmethod
    def should_retry_http_error(exc, status_code: int) -> bool:
        """
        判断HTTP错误是否应该重试
        
        Args:
            exc: HTTP异常
            status_code: HTTP状态码
            
        Returns:
            是否应该重试
        """
        # 5xx服务器错误通常可以重试
        if 500 <= status_code < 600:
            return True
        
        # 429 Too Many Requests 应该重试
        if status_code == 429:
            return True
        
        # 502, 503, 504 网关错误可以重试
        if status_code in [502, 503, 504]:
            return True
        
        # 4xx客户端错误通常不应重试
        if 400 <= status_code < 500:
            # 除了408 Request Timeout 和 409 Conflict 可能可以重试
            if status_code in [408, 409]:
                return True
            return False
        
        return False
    
    @staticmethod
    def should_retry_database_error(exc) -> bool:
        """
        判断数据库错误是否应该重试
        
        Args:
            exc: 数据库异常
            
        Returns:
            是否应该重试
        """
        error_msg = str(exc).lower()
        
        # 连接相关错误可以重试
        if any(keyword in error_msg for keyword in [
            'connection', 'timeout', 'network', 'lost connection'
        ]):
            return True
        
        # 锁定相关错误可以重试
        if any(keyword in error_msg for keyword in [
            'deadlock', 'lock wait timeout', 'locked'
        ]):
            return True
        
        # 语法错误不应重试
        if any(keyword in error_msg for keyword in [
            'syntax error', 'invalid syntax', 'constraint violation'
        ]):
            return False
        
        return True
    
    @staticmethod
    def should_retry_file_error(exc) -> bool:
        """
        判断文件错误是否应该重试
        
        Args:
            exc: 文件异常
            
        Returns:
            是否应该重试
        """
        error_msg = str(exc).lower()
        
        # 权限错误可能是临时的
        if 'permission denied' in error_msg:
            return True
        
        # 文件不存在通常不应重试
        if 'no such file' in error_msg:
            return False
        
        # 磁盘空间不足需要等待清理
        if 'no space left' in error_msg:
            return True
        
        # 设备忙可以重试
        if 'device or resource busy' in error_msg:
            return True
        
        return True


# ================== 配置工厂 ==================

class RetryConfigFactory:
    """重试配置工厂"""
    
    @staticmethod
    def get_strategy_for_business(business_type: str) -> Dict[ErrorCategory, RetryStrategy]:
        """
        根据业务类型获取重试策略
        
        Args:
            business_type: 业务类型
            
        Returns:
            重试策略映射
        """
        strategy_map = {
            'tracking': BusinessRetryStrategies.TRACKING_QUERY,
            'screenshot': BusinessRetryStrategies.SCREENSHOT_CAPTURE,
            'document': BusinessRetryStrategies.DOCUMENT_GENERATION,
            'code_generation': BusinessRetryStrategies.CODE_GENERATION,
            'email': BusinessRetryStrategies.EMAIL_DELIVERY,
            'monitoring': BusinessRetryStrategies.MONITORING_TASKS,
            'database': BusinessRetryStrategies.DATABASE_OPERATIONS
        }
        
        return strategy_map.get(business_type, {
            ErrorCategory.TEMPORARY_ERROR: RetryStrategies.transient_data_retry(),
            ErrorCategory.NETWORK_ERROR: RetryStrategies.progressive_network_retry()
        })
    
    @staticmethod
    def create_celery_config(business_type: str) -> Dict[str, Any]:
        """
        为特定业务类型创建Celery任务配置
        
        Args:
            business_type: 业务类型
            
        Returns:
            Celery任务配置
        """
        strategies = RetryConfigFactory.get_strategy_for_business(business_type)
        
        # 使用默认策略作为基础配置
        default_strategy = strategies.get(
            ErrorCategory.TEMPORARY_ERROR, 
            RetryStrategies.transient_data_retry()
        )
        
        return {
            'bind': True,
            'max_retries': default_strategy.max_retries,
            'default_retry_delay': default_strategy.base_delay,
            'retry_backoff': True,
            'retry_backoff_max': default_strategy.max_delay,
            'retry_jitter': default_strategy.jitter,
            'autoretry_for': ()  # 由智能处理器控制
        }


# ================== 预定义业务装饰器 ==================

def tracking_intelligent_retry(func):
    """物流跟踪智能重试装饰器"""
    from app.tasks.retry_handler import intelligent_retry
    return intelligent_retry(
        custom_strategies=BusinessRetryStrategies.TRACKING_QUERY
    )(func)


def screenshot_intelligent_retry(func):
    """截图生成智能重试装饰器"""
    from app.tasks.retry_handler import intelligent_retry
    return intelligent_retry(
        custom_strategies=BusinessRetryStrategies.SCREENSHOT_CAPTURE
    )(func)


def document_intelligent_retry(func):
    """文档生成智能重试装饰器"""
    from app.tasks.retry_handler import intelligent_retry
    return intelligent_retry(
        custom_strategies=BusinessRetryStrategies.DOCUMENT_GENERATION
    )(func)


def code_generation_intelligent_retry(func):
    """二维码生成智能重试装饰器"""
    from app.tasks.retry_handler import intelligent_retry
    return intelligent_retry(
        custom_strategies=BusinessRetryStrategies.CODE_GENERATION
    )(func)


def email_intelligent_retry(func):
    """邮件发送智能重试装饰器"""
    from app.tasks.retry_handler import intelligent_retry
    return intelligent_retry(
        custom_strategies=BusinessRetryStrategies.EMAIL_DELIVERY
    )(func)


def monitoring_intelligent_retry(func):
    """监控任务智能重试装饰器"""
    from app.tasks.retry_handler import intelligent_retry
    return intelligent_retry(
        custom_strategies=BusinessRetryStrategies.MONITORING_TASKS
    )(func)


def database_intelligent_retry(func):
    """数据库操作智能重试装饰器"""
    from app.tasks.retry_handler import intelligent_retry
    return intelligent_retry(
        custom_strategies=BusinessRetryStrategies.DATABASE_OPERATIONS
    )(func)