# 失败任务自动处理系统使用指南

## 🎯 系统概述

失败任务自动处理系统能够智能分析失败原因，自动恢复可恢复的任务，并及时通知相关人员处理不可恢复的问题。

## 🔧 核心功能

### 1. 智能失败分析
系统自动将失败任务分为6个类别：

| 分类 | 描述 | 处理策略 | 示例错误 |
|------|------|---------|---------|
| **可恢复网络错误** | 网络连接问题 | 立即重试 | connection timeout, network unreachable |
| **可恢复系统错误** | 系统资源问题 | 延迟重试 | memory error, disk space, permission denied |
| **可恢复临时错误** | 服务临时不可用 | 渐进重试 | database connection failed, rate limit exceeded |
| **不可恢复数据错误** | 数据格式问题 | 通知管理员 | invalid data format, malformed json |
| **不可恢复配置错误** | 配置问题 | 通知管理员 | api key invalid, authentication failed |
| **不可恢复业务错误** | 业务逻辑问题 | 通知用户 | resource not found, courier not supported |

### 2. 自动恢复策略

#### 网络错误恢复
```
第1次重试: 30秒后
第2次重试: 60秒后  
第3次重试: 120秒后
第4次重试: 240秒后
最大重试: 5次
```

#### 系统错误恢复
```
第1次重试: 5分钟后
第2次重试: 10分钟后
第3次重试: 20分钟后
最大重试: 3次
```

#### 临时错误恢复
```
第1次重试: 3分钟后
第2次重试: 6分钟后
第3次重试: 12分钟后
最大重试: 3次
```

### 3. 通知机制

#### 管理员通知（数据/配置错误）
- 记录到 `logs/admin_alerts.log`
- 发送系统告警（可扩展邮件/短信）
- 标记为高优先级处理

#### 用户通知（业务错误）
- 记录到 `logs/user_notifications.log`
- 创建系统消息（可扩展站内信）
- 提供错误解决建议

## 📅 定时任务配置

### 失败任务扫描 (每30分钟)
```python
'scan-and-process-failed-tasks': {
    'task': 'app.tasks.failure_tasks.scan_and_process_failed_tasks',
    'schedule': crontab(minute='*/30'),  # 每30分钟执行
    'options': {'queue': 'recovery'},
    'description': '扫描失败任务，自动分析和恢复可恢复的任务'
}
```

### 失败模式分析 (每6小时)
```python
'analyze-failure-patterns': {
    'task': 'app.tasks.failure_tasks.analyze_failure_patterns',
    'schedule': crontab(minute=0, hour='*/6'),  # 每6小时执行
    'options': {'queue': 'monitoring'},
    'description': '分析失败任务模式，生成趋势报告和改进建议'
}
```

## 🚀 使用方法

### 1. 自动运行
系统会自动执行，无需人工干预：
- 每30分钟扫描最近24小时的失败任务
- 自动分析失败原因并分类
- 对可恢复任务进行自动重试
- 对不可恢复任务发送通知

### 2. 手动恢复特定任务
```python
from app.tasks.failure_tasks import manual_recovery_task

# 恢复指定失败任务
result = manual_recovery_task.delay(task_id=123)

# 强制重试（忽略重试次数限制）
result = manual_recovery_task.delay(task_id=123, force_retry=True)
```

### 3. 查看处理报告
```bash
# 查看失败任务处理报告
ls reports/failure_processing/
cat reports/failure_processing/failure_processing_20231201_140000.json

# 查看失败模式分析报告
ls reports/failure_analysis/
cat reports/failure_analysis/failure_analysis_20231201_140000.json
```

### 4. 监控告警日志
```bash
# 查看管理员告警
tail -f logs/admin_alerts.log

# 查看用户通知
tail -f logs/user_notifications.log
```

## 📊 处理报告格式

### 失败任务处理报告
```json
{
  "success": true,
  "message": "失败任务处理完成",
  "total_processed": 15,
  "stats": {
    "scanned": 15,
    "analyzed": 15,
    "recovered": 8,
    "notified": 5,
    "errors": []
  },
  "results": [
    {
      "task_id": 123,
      "category": "recoverable_network",
      "action_taken": "auto_recovery",
      "success": true,
      "message": "任务将在30秒后重试",
      "retry_delay": 30
    }
  ],
  "processed_at": "2023-12-01T14:00:00"
}
```

### 失败模式分析报告
```json
{
  "success": true,
  "analysis_period": "7天",
  "total_failures": 45,
  "category_distribution": {
    "recoverable_network": 20,
    "recoverable_temporary": 12,
    "unrecoverable_data": 8,
    "unrecoverable_config": 3,
    "unrecoverable_business": 2
  },
  "task_type_failures": {
    "tracking_update": 25,
    "receipt_generation": 15,
    "screenshot_capture": 5
  },
  "insights": [
    "主要失败原因是recoverable_network，占比44.4%",
    "有71.1%的失败是可自动恢复的",
    "建议检查网络连接稳定性和API服务可用性"
  ]
}
```

## 🔍 错误模式匹配规则

### 网络错误模式
```python
patterns = [
    r'connection.*timeout',
    r'network.*unreachable', 
    r'connection.*refused',
    r'dns.*resolution.*failed',
    r'socket.*timeout',
    r'read.*timeout'
]
```

### 系统错误模式
```python
patterns = [
    r'memory.*error',
    r'disk.*space',
    r'no.*space.*left',
    r'resource.*temporarily.*unavailable',
    r'too.*many.*open.*files',
    r'permission.*denied'
]
```

### 数据错误模式
```python
patterns = [
    r'invalid.*data.*format',
    r'malformed.*json',
    r'parse.*error',
    r'validation.*failed',
    r'constraint.*violation',
    r'null.*value.*in.*column'
]
```

## ⚙️ 配置选项

### 环境变量
```bash
# .env
FAILURE_RECOVERY_ENABLED=true
FAILURE_SCAN_INTERVAL_MINUTES=30
FAILURE_MAX_RECOVERY_ATTEMPTS=3
FAILURE_NOTIFICATION_ENABLED=true
```

### 自定义错误模式
```python
# 在 FailureAnalyzer 中添加自定义模式
custom_patterns = {
    FailureCategory.CUSTOM_ERROR: [
        r'custom.*error.*pattern',
        r'specific.*business.*rule'
    ]
}
```

### 自定义通知渠道
```python
def send_custom_notification(notification):
    # 集成邮件服务
    send_email(notification)
    
    # 集成短信服务  
    send_sms(notification)
    
    # 集成钉钉/企微
    send_dingtalk(notification)
```

## 📈 监控指标

### 关键指标
- **自动恢复成功率**: >80%
- **失败任务处理时延**: <30分钟
- **错误分类准确率**: >95%
- **通知及时性**: <5分钟

### 告警阈值
```python
ALERT_THRESHOLDS = {
    'failure_rate_threshold': 20,      # 失败率>20%告警
    'recovery_failure_threshold': 5,   # 连续5次恢复失败告警
    'notification_delay_threshold': 10, # 通知延迟>10分钟告警
    'unknown_error_threshold': 10      # 未知错误>10个告警
}
```

## 🛠️ 故障排除

### 1. 自动恢复不工作
```bash
# 检查定时任务状态
python celery_beat_manager.py status

# 查看任务队列
celery -A app.tasks.celery_app inspect active

# 检查任务日志
tail -f logs/celery.log | grep failure_tasks
```

### 2. 错误分类不准确
```python
# 测试错误分析器
from app.tasks.failure_tasks import FailureAnalyzer

analyzer = FailureAnalyzer()
category, analysis = analyzer.analyze_failure(failed_task)
print(f"分类: {category}, 分析: {analysis}")
```

### 3. 通知不发送
```bash
# 检查日志文件权限
ls -la logs/
chmod 755 logs/
mkdir -p logs

# 检查告警日志
tail -f logs/admin_alerts.log
tail -f logs/user_notifications.log
```

### 4. 恢复次数过多
```python
# 查看任务恢复历史
task = db.query(Task).filter(Task.id == task_id).first()
print(f"恢复次数: {task.recovery_attempts}")
print(f"恢复记录: {task.recovery_notes}")
```

## 🎯 最佳实践

### 1. 错误消息规范化
```python
# 使用结构化错误消息
error_message = f"[{error_category}] {specific_error}: {context_info}"

# 示例
"[NETWORK] Connection timeout: API服务器连接超时，请检查网络连接"
"[DATA] Validation failed: 快递单号格式不正确，应为10-20位数字或字母"
```

### 2. 任务重试设计
```python
# 在任务中记录重试信息
@celery_app.task(bind=True)
def my_task(self):
    try:
        # 任务逻辑
        pass
    except Exception as e:
        # 记录详细错误信息
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "context": get_task_context(),
            "timestamp": datetime.now().isoformat()
        }
        raise Exception(json.dumps(error_details))
```

### 3. 监控和告警
```python
# 定期检查系统健康状态
@celery_app.task
def check_failure_recovery_health():
    recent_failures = count_recent_failures()
    recovery_rate = calculate_recovery_rate()
    
    if recovery_rate < 0.8:
        send_alert(f"自动恢复成功率过低: {recovery_rate:.2%}")
    
    if recent_failures > 50:
        send_alert(f"最近失败任务过多: {recent_failures}")
```

### 4. 业务集成
```python
# 集成业务逻辑
class BusinessFailureHandler:
    def handle_business_failure(self, task, error):
        if task.task_type == "order_processing":
            # 订单处理失败 -> 通知客服
            notify_customer_service(task, error)
        elif task.task_type == "payment_processing": 
            # 支付处理失败 -> 通知财务
            notify_finance_team(task, error)
```

## 📝 扩展开发

### 1. 添加新的错误类型
```python
# 在 FailureCategory 中添加新类型
class FailureCategory(Enum):
    CUSTOM_BUSINESS_ERROR = "custom_business_error"

# 在 FailureAnalyzer 中添加匹配规则
self.error_patterns[FailureCategory.CUSTOM_BUSINESS_ERROR] = [
    r'custom.*business.*error',
    r'specific.*validation.*failed'
]
```

### 2. 自定义恢复策略
```python
def custom_recovery_strategy(task, category, analysis):
    if task.task_type == "special_task":
        # 特殊任务使用特殊恢复策略
        return {
            "delay": calculate_special_delay(task),
            "strategy": "custom_progressive_retry",
            "max_attempts": 5
        }
```

### 3. 集成外部监控系统
```python
def send_to_monitoring_system(failure_event):
    # 发送到 Prometheus
    failure_counter.inc(labels={'category': failure_event['category']})
    
    # 发送到 ELK Stack
    elasticsearch_client.index(
        index='failure-events',
        body=failure_event
    )
    
    # 发送到 APM 系统
    apm_client.capture_message(
        'Task Failure',
        extra=failure_event
    )
```

失败任务自动处理系统现已完全配置完成，可以大幅提升系统的自愈能力和运维效率！🚀