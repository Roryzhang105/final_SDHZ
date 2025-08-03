"""
Celery任务重试配置工具
提供标准化的重试策略和装饰器
"""

import logging
from functools import wraps
from typing import Tuple, Type, Union, Any
from celery import Task
from celery.exceptions import Retry

logger = logging.getLogger(__name__)

# 重试策略配置
RETRY_CONFIGS = {
    # 标准重试策略
    'default': {
        'max_retries': 3,
        'default_retry_delay': 60,  # 1分钟
        'retry_backoff': True,
        'retry_backoff_max': 600,   # 最大10分钟
        'retry_jitter': True,
        'autoretry_for': (Exception,)
    },
    
    # 关键任务重试策略
    'critical': {
        'max_retries': 5,
        'default_retry_delay': 30,  # 30秒
        'retry_backoff': True,
        'retry_backoff_max': 300,   # 最大5分钟
        'retry_jitter': True,
        'autoretry_for': (Exception,)
    },
    
    # 网络相关任务重试策略
    'network': {
        'max_retries': 4,
        'default_retry_delay': 45,  # 45秒
        'retry_backoff': True,
        'retry_backoff_max': 900,   # 最大15分钟
        'retry_jitter': True,
        'autoretry_for': (
            ConnectionError,
            TimeoutError,
            OSError,
            Exception
        )
    },
    
    # 文件操作重试策略
    'file_operation': {
        'max_retries': 3,
        'default_retry_delay': 20,  # 20秒
        'retry_backoff': True,
        'retry_backoff_max': 180,   # 最大3分钟
        'retry_jitter': True,
        'autoretry_for': (
            FileNotFoundError,
            PermissionError,
            OSError,
            IOError,
            Exception
        )
    },
    
    # 数据库操作重试策略
    'database': {
        'max_retries': 3,
        'default_retry_delay': 10,  # 10秒
        'retry_backoff': True,
        'retry_backoff_max': 120,   # 最大2分钟
        'retry_jitter': True,
        'autoretry_for': (Exception,)
    },
    
    # 快速重试策略
    'fast': {
        'max_retries': 2,
        'default_retry_delay': 5,   # 5秒
        'retry_backoff': True,
        'retry_backoff_max': 30,    # 最大30秒
        'retry_jitter': False,
        'autoretry_for': (Exception,)
    }
}


def get_retry_config(strategy: str = 'default') -> dict:
    """
    获取重试配置
    
    Args:
        strategy: 重试策略名称
        
    Returns:
        重试配置字典
    """
    config = RETRY_CONFIGS.get(strategy, RETRY_CONFIGS['default']).copy()
    
    # 添加bind=True以支持self.retry()
    config['bind'] = True
    
    return config


def calculate_retry_delay(retry_count: int, base_delay: int = 60, max_delay: int = 600, 
                         use_exponential: bool = True, jitter: bool = True) -> int:
    """
    计算重试延迟时间（指数退避策略）
    
    Args:
        retry_count: 当前重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        use_exponential: 是否使用指数退避
        jitter: 是否添加随机抖动
        
    Returns:
        计算后的延迟时间（秒）
    """
    if use_exponential:
        # 指数退避: delay = base_delay * (2 ^ retry_count)
        delay = base_delay * (2 ** retry_count)
    else:
        # 线性退避: delay = base_delay * retry_count
        delay = base_delay * (retry_count + 1)
    
    # 限制最大延迟
    delay = min(delay, max_delay)
    
    # 添加随机抖动以避免雷群效应
    if jitter:
        import random
        jitter_range = delay * 0.1  # 10%的抖动
        delay += random.uniform(-jitter_range, jitter_range)
        delay = max(1, int(delay))  # 确保至少1秒
    
    return int(delay)


class RetryTaskMixin:
    """
    重试任务混入类
    提供标准化的重试逻辑
    """
    
    def retry_with_backoff(self, exc: Exception = None, retry_count: int = None, 
                          strategy: str = 'default', **kwargs) -> None:
        """
        使用退避策略重试任务
        
        Args:
            exc: 触发重试的异常
            retry_count: 当前重试次数
            strategy: 重试策略
            **kwargs: 额外的重试参数
        """
        config = RETRY_CONFIGS.get(strategy, RETRY_CONFIGS['default'])
        
        if retry_count is None:
            retry_count = self.request.retries
        
        # 检查是否超过最大重试次数
        if retry_count >= config['max_retries']:
            logger.error(f"任务 {self.name} 重试次数已达上限 ({config['max_retries']}), 最终失败")
            raise exc or Exception("任务重试次数超限")
        
        # 计算延迟时间
        delay = calculate_retry_delay(
            retry_count=retry_count,
            base_delay=config['default_retry_delay'],
            max_delay=config.get('retry_backoff_max', 600),
            use_exponential=config.get('retry_backoff', True),
            jitter=config.get('retry_jitter', True)
        )
        
        logger.warning(
            f"任务 {self.name} 第 {retry_count + 1} 次重试，延迟 {delay} 秒. "
            f"异常: {str(exc) if exc else 'Unknown'}"
        )
        
        # 执行重试
        raise self.retry(
            exc=exc,
            countdown=delay,
            max_retries=config['max_retries'],
            **kwargs
        )


def retry_task(strategy: str = 'default', 
               custom_exceptions: Tuple[Type[Exception], ...] = None,
               on_failure=None,
               on_retry=None):
    """
    任务重试装饰器
    
    Args:
        strategy: 重试策略名称
        custom_exceptions: 自定义需要重试的异常类型
        on_failure: 失败回调函数
        on_retry: 重试回调函数
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                config = RETRY_CONFIGS.get(strategy, RETRY_CONFIGS['default'])
                
                # 检查是否需要重试此异常
                autoretry_for = custom_exceptions or config.get('autoretry_for', (Exception,))
                
                if not isinstance(exc, autoretry_for):
                    logger.error(f"任务 {func.__name__} 遇到不重试的异常: {type(exc).__name__}: {str(exc)}")
                    if on_failure:
                        on_failure(self, exc, *args, **kwargs)
                    raise exc
                
                # 检查重试次数
                retry_count = self.request.retries
                max_retries = config['max_retries']
                
                if retry_count >= max_retries:
                    logger.error(f"任务 {func.__name__} 重试次数已达上限 ({max_retries}), 最终失败: {str(exc)}")
                    if on_failure:
                        on_failure(self, exc, *args, **kwargs)
                    raise exc
                
                # 计算延迟时间
                delay = calculate_retry_delay(
                    retry_count=retry_count,
                    base_delay=config['default_retry_delay'],
                    max_delay=config.get('retry_backoff_max', 600),
                    use_exponential=config.get('retry_backoff', True),
                    jitter=config.get('retry_jitter', True)
                )
                
                logger.warning(
                    f"任务 {func.__name__} 第 {retry_count + 1} 次重试，延迟 {delay} 秒. "
                    f"异常: {type(exc).__name__}: {str(exc)}"
                )
                
                # 调用重试回调
                if on_retry:
                    on_retry(self, exc, retry_count, delay, *args, **kwargs)
                
                # 执行重试
                raise self.retry(
                    exc=exc,
                    countdown=delay,
                    max_retries=max_retries
                )
        
        return wrapper
    
    return decorator


def log_task_failure(task_self, exc, *args, **kwargs):
    """
    记录任务失败信息的回调函数
    """
    logger.error(
        f"任务最终失败: {task_self.name}, "
        f"任务ID: {task_self.request.id}, "
        f"异常: {type(exc).__name__}: {str(exc)}, "
        f"参数: args={args}, kwargs={kwargs}"
    )


def log_task_retry(task_self, exc, retry_count, delay, *args, **kwargs):
    """
    记录任务重试信息的回调函数
    """
    logger.info(
        f"任务重试: {task_self.name}, "
        f"任务ID: {task_self.request.id}, "
        f"重试次数: {retry_count + 1}, "
        f"延迟: {delay}秒, "
        f"异常: {type(exc).__name__}: {str(exc)}"
    )


# 预定义的装饰器
retry_default = lambda func: retry_task('default', on_failure=log_task_failure, on_retry=log_task_retry)(func)
retry_critical = lambda func: retry_task('critical', on_failure=log_task_failure, on_retry=log_task_retry)(func)
retry_network = lambda func: retry_task('network', on_failure=log_task_failure, on_retry=log_task_retry)(func)
retry_file_operation = lambda func: retry_task('file_operation', on_failure=log_task_failure, on_retry=log_task_retry)(func)
retry_database = lambda func: retry_task('database', on_failure=log_task_failure, on_retry=log_task_retry)(func)
retry_fast = lambda func: retry_task('fast', on_failure=log_task_failure, on_retry=log_task_retry)(func)


def create_task_with_retry(celery_app, strategy: str = 'default', **task_kwargs):
    """
    创建带重试功能的任务装饰器
    
    Args:
        celery_app: Celery应用实例
        strategy: 重试策略
        **task_kwargs: 额外的任务参数
        
    Returns:
        任务装饰器
    """
    config = get_retry_config(strategy)
    
    # 合并配置
    final_config = {**config, **task_kwargs}
    
    def decorator(func):
        # 应用重试装饰器
        func = retry_task(strategy, on_failure=log_task_failure, on_retry=log_task_retry)(func)
        
        # 创建Celery任务
        return celery_app.task(**final_config)(func)
    
    return decorator


# 常用的任务创建装饰器
def default_task(celery_app, **kwargs):
    return create_task_with_retry(celery_app, 'default', **kwargs)

def critical_task(celery_app, **kwargs):
    return create_task_with_retry(celery_app, 'critical', **kwargs)

def network_task(celery_app, **kwargs):
    return create_task_with_retry(celery_app, 'network', **kwargs)

def file_task(celery_app, **kwargs):
    return create_task_with_retry(celery_app, 'file_operation', **kwargs)

def database_task(celery_app, **kwargs):
    return create_task_with_retry(celery_app, 'database', **kwargs)