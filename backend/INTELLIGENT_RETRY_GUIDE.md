# 智能重试系统使用指南

## 概述

智能重试系统根据错误类型自动决定重试策略，提供比传统重试机制更智能和高效的错误处理方案。

## 核心特性

### 1. 智能错误分类

系统自动将错误分为以下类别：

- **网络错误** (`NETWORK_ERROR`): 连接超时、网络中断等
- **API限流** (`API_RATE_LIMIT`): 429错误、调用频率限制
- **数据错误** (`DATA_ERROR`): 数据格式错误、验证失败
- **系统错误** (`SYSTEM_ERROR`): 内存不足、系统资源问题
- **临时错误** (`TEMPORARY_ERROR`): 数据库连接失败等可恢复错误
- **永久错误** (`PERMANENT_ERROR`): 不应重试的严重错误

### 2. 智能重试决策

根据错误类型采用不同策略：

- **立即重试** (`RETRY_IMMEDIATELY`): 网络抖动等瞬时错误
- **延迟重试** (`RETRY_WITH_DELAY`): API限流需要等待冷却
- **指数退避** (`RETRY_WITH_BACKOFF`): 系统负载等需要渐进等待
- **不重试** (`NO_RETRY`): 数据格式错误等无法通过重试解决

## 使用方法

### 1. 基础使用

```python
from app.tasks.retry_handler import intelligent_retry
from app.tasks.retry_strategies import RetryConfigFactory

# 为任务配置智能重试
@celery_app.task(**RetryConfigFactory.create_celery_config('tracking'))
@intelligent_retry
def my_tracking_task(self, tracking_number: str):
    # 任务实现
    result = call_tracking_api(tracking_number)
    return result
```

### 2. 使用预定义业务策略

```python
from app.tasks.retry_strategies import tracking_intelligent_retry

@celery_app.task(**RetryConfigFactory.create_celery_config('tracking'))
@tracking_intelligent_retry
def update_tracking_info(self, tracking_number: str):
    # 物流跟踪专用的智能重试策略
    pass
```

### 3. 自定义重试策略

```python
from app.tasks.retry_handler import intelligent_retry
from app.tasks.retry_strategies import BusinessRetryStrategies

@celery_app.task(**RetryConfigFactory.create_celery_config('custom'))
@intelligent_retry(
    custom_strategies=BusinessRetryStrategies.TRACKING_QUERY,
    failure_callback=my_failure_callback,
    retry_callback=my_retry_callback
)
def custom_task(self):
    pass
```

## 重试策略配置

### 网络错误策略

```python
# 立即重试，适用于网络抖动
{
    "decision": "RETRY_IMMEDIATELY",
    "max_retries": 5,
    "base_delay": 0,
    "max_delay": 10,
    "backoff_factor": 1.2
}
```

### API限流策略

```python
# 延迟重试，适用于API限流
{
    "decision": "RETRY_WITH_DELAY", 
    "max_retries": 3,
    "base_delay": 300,  # 5分钟
    "max_delay": 1800,  # 30分钟
    "backoff_factor": 2.0
}
```

### 数据错误策略

```python
# 不重试，适用于数据格式错误
{
    "decision": "NO_RETRY",
    "max_retries": 0
}
```

## 业务场景配置

### 1. 物流跟踪 (`tracking`)

```python
TRACKING_QUERY = {
    ErrorCategory.NETWORK_ERROR: 渐进重试(5s->10s->20s->40s),
    ErrorCategory.API_RATE_LIMIT: 延迟重试(5min->10min->20min),
    ErrorCategory.DATA_ERROR: 不重试,
    ErrorCategory.TEMPORARY_ERROR: 指数退避重试
}
```

### 2. 截图生成 (`screenshot`)

```python
SCREENSHOT_CAPTURE = {
    ErrorCategory.NETWORK_ERROR: 立即重试,
    ErrorCategory.SYSTEM_ERROR: 资源约束重试,
    ErrorCategory.TEMPORARY_ERROR: 文件操作重试
}
```

### 3. 文档生成 (`document`)

```python
DOCUMENT_GENERATION = {
    ErrorCategory.DATA_ERROR: 不重试,
    ErrorCategory.SYSTEM_ERROR: 资源约束重试,
    ErrorCategory.TEMPORARY_ERROR: 关键文件重试
}
```

## 错误处理示例

### 1. 网络错误处理

```python
@tracking_intelligent_retry
def query_express_api(self, tracking_number: str):
    try:
        response = requests.get(api_url, timeout=30)
        return response.json()
    except requests.exceptions.ConnectTimeout:
        # 网络连接超时 -> 立即重试
        raise ConnectionError(f"连接超时: {tracking_number}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            # API限流 -> 延迟重试
            raise HTTPError("API限流", response=e.response)
        else:
            # 其他HTTP错误 -> 根据状态码决定
            raise e
```

### 2. 数据验证错误

```python
@document_intelligent_retry  
def generate_receipt(self, data: dict):
    try:
        # 验证输入数据
        if not data.get('tracking_number'):
            # 数据错误 -> 不重试
            raise ValueError("缺少必需的tracking_number字段")
        
        # 生成文档
        return create_document(data)
    except ValueError as e:
        # 数据验证错误不应重试
        logger.error(f"数据验证失败: {str(e)}")
        raise e
```

### 3. 系统资源错误

```python
@intelligent_retry(custom_strategies={
    ErrorCategory.SYSTEM_ERROR: resource_constraint_retry()
})
def memory_intensive_task(self):
    try:
        # 内存密集型操作
        large_data = process_large_dataset()
        return large_data
    except MemoryError:
        # 内存不足 -> 延迟重试，等待系统资源释放
        raise MemoryError("内存不足，等待资源释放")
```

## 监控和分析

### 1. 错误统计

```python
from app.tasks.retry_handler import analyze_task_errors

# 分析特定任务的错误模式
analysis = analyze_task_errors('update_tracking_info')
print(f"总错误数: {analysis['total_errors']}")
print(f"错误分布: {analysis['category_distribution']}")
print(f"建议: {analysis['suggestions']}")
```

### 2. 实时监控

```python
# 获取任务错误统计
@celery_app.task
def monitor_retry_errors():
    from app.tasks.retry_handler import retry_handler
    
    stats = retry_handler.get_error_statistics()
    
    # 检查是否有异常模式
    if stats.get('total_errors', 0) > 100:
        send_alert("重试错误数量异常")
    
    return stats
```

## 最佳实践

### 1. 错误分类准确性

```python
# 确保抛出正确的异常类型
def api_call():
    try:
        response = requests.get(url)
        if response.status_code == 429:
            # 明确标识为限流错误
            raise HTTPError("API限流", response=response)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        # 网络连接错误
        raise ConnectionError("网络连接失败")
```

### 2. 合理设置重试参数

```python
# 根据业务需求调整重试策略
custom_strategy = create_custom_strategy(
    decision=RetryDecision.RETRY_WITH_BACKOFF,
    max_retries=3,      # 不要设置过高
    base_delay=60,      # 根据业务场景调整
    max_delay=300,      # 设置合理上限
    backoff_factor=2.0, # 避免过于激进
    jitter=True         # 防止雷群效应
)
```

### 3. 监控和告警

```python
# 设置错误阈值监控
def check_retry_health():
    analysis = analyze_task_errors()
    
    # 检查失败率
    total_errors = analysis.get('total_errors', 0)
    if total_errors > 50:
        send_alert(f"重试错误数量过高: {total_errors}")
    
    # 检查特定错误类型
    category_dist = analysis.get('category_distribution', {})
    data_errors = category_dist.get('data_error', 0)
    if data_errors > 10:
        send_alert(f"数据错误数量异常: {data_errors}")
```

### 4. 错误恢复

```python
# 实现错误恢复机制
@intelligent_retry
def resilient_task(self, data):
    try:
        return process_data(data)
    except ValueError as e:
        # 尝试数据修复
        if "format" in str(e).lower():
            cleaned_data = clean_data_format(data)
            return process_data(cleaned_data)
        raise e
```

## 配置文件示例

### 1. 环境变量配置

```bash
# .env文件
INTELLIGENT_RETRY_ENABLED=true
RETRY_DEFAULT_MAX_RETRIES=3
RETRY_DEFAULT_BASE_DELAY=60
RETRY_NETWORK_MAX_RETRIES=5
RETRY_API_RATE_LIMIT_DELAY=300
```

### 2. Django/Flask设置

```python
# settings.py
INTELLIGENT_RETRY_CONFIG = {
    'ENABLED': True,
    'DEFAULT_STRATEGY': 'progressive',
    'NETWORK_IMMEDIATE_RETRY': True,
    'API_RATE_LIMIT_DELAY': 300,
    'DATA_ERROR_NO_RETRY': True,
    'MONITORING_ENABLED': True,
    'ERROR_THRESHOLD': 50
}
```

## 故障排除

### 1. 重试不生效

```bash
# 检查装饰器顺序
# 正确：
@celery_app.task(**config)
@intelligent_retry
def task(): pass

# 错误：
@intelligent_retry
@celery_app.task(**config)  
def task(): pass
```

### 2. 错误分类不准确

```python
# 检查异常类型
logger.debug(f"异常类型: {type(exc).__name__}")
logger.debug(f"异常消息: {str(exc)}")

# 自定义错误分类
def custom_classify_error(exc):
    if "custom_error" in str(exc):
        return ErrorCategory.DATA_ERROR
    return original_classify_error(exc)
```

### 3. 重试次数过多

```python
# 检查重试配置
strategy = get_strategy_for_error(exc)
logger.info(f"重试策略: {strategy}")
logger.info(f"当前重试次数: {retry_count}")
logger.info(f"最大重试次数: {strategy.max_retries}")
```

## 性能考虑

### 1. 内存使用

```python
# 定期清理错误历史
@celery_app.task
def cleanup_retry_history():
    from app.tasks.retry_handler import retry_handler
    
    # 清理超过24小时的错误记录
    retry_handler.cleanup_old_errors(hours=24)
```

### 2. 数据库连接

```python
# 在重试期间正确管理数据库连接
@intelligent_retry
def db_task(self):
    db = SessionLocal()
    try:
        # 数据库操作
        result = db.query(Model).all()
        db.commit()
        return result
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()  # 确保连接释放
```

### 3. 任务队列优化

```python
# 使用不同队列处理不同类型的重试
CELERY_ROUTES = {
    'app.tasks.*_immediate_*': {'queue': 'immediate'},
    'app.tasks.*_delayed_*': {'queue': 'delayed'},
    'app.tasks.*_no_retry_*': {'queue': 'critical'},
}
```