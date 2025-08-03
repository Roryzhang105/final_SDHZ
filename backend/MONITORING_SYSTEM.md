# 定时任务监控系统文档

## 概述

监控系统提供全面的任务监控、数据清理、统计报告和告警功能，确保系统稳定运行和数据完整性。

## 主要功能

### 1. 任务清理 (`cleanup_expired_tasks`)

**执行时间**: 每天凌晨4点
**功能**: 清理过期任务和相关数据

#### 清理策略
- **已完成任务**: 保留30天
- **失败任务**: 保留7天  
- **临时文件**: 保留24小时
- **日志文件**: 保留30天

#### 清理内容
```python
# 任务相关文件
- 原始图片文件 (image_path)
- 生成的文档 (document_path)
- 截图文件 (screenshot_path)

# 回证相关文件
- 二维码文件 (qr_code_path)
- 条形码文件 (barcode_path)
- 回证文档 (delivery_receipt_doc_path)
- 物流截图 (tracking_screenshot_path)

# 系统文件
- 临时文件目录
- 过期日志文件
```

#### 返回统计信息
```json
{
  "tasks_cleaned": 150,
  "files_cleaned": 45,
  "receipts_cleaned": 12,
  "logs_cleaned": 8,
  "disk_space_freed_mb": 2048.5,
  "errors": []
}
```

### 2. 统计报告 (`generate_daily_statistics`)

**执行时间**: 每天凌晨2点
**功能**: 生成详细的每日运行统计报告

#### 统计内容

##### 任务统计
- 总任务数量
- 各状态任务分布
- 完成率和失败率
- 平均处理时间

##### 性能统计  
- 最慢的5个任务
- 24小时任务分布
- 高峰时段分析

##### 错误统计
- 错误类型分类
- 重试次数统计
- 失败任务详情

##### 系统统计
- 磁盘使用情况
- Celery队列状态
- 资源使用情况

##### 趋势分析
- 过去7天数据对比
- 增长趋势分析
- 异常变化检测

#### 报告格式
```json
{
  "date": "2023-12-01",
  "task_statistics": {
    "total_tasks": 1250,
    "status_breakdown": {
      "completed": 1100,
      "failed": 45,
      "pending": 15,
      "processing": 90
    },
    "completion_rate": 88.0,
    "failure_rate": 3.6,
    "average_processing_time": 45.2
  },
  "performance_statistics": {
    "slowest_tasks": [...],
    "hourly_distribution": {...},
    "peak_hour": 14
  },
  "error_statistics": {
    "error_categories": {
      "二维码识别错误": 12,
      "物流查询错误": 8,
      "文档生成错误": 3
    },
    "retry_statistics": {...}
  },
  "system_statistics": {
    "disk_usage": {
      "total_gb": 500.0,
      "used_gb": 350.2,
      "free_gb": 149.8,
      "usage_percent": 70.04
    },
    "queue_statistics": {...}
  },
  "trend_analysis": {...}
}
```

### 3. 磁盘空间监控 (`check_disk_space`)

**执行时间**: 每小时15分
**功能**: 监控磁盘空间使用情况

#### 告警阈值
- **警告**: 使用率 > 80%
- **严重**: 使用率 > 90%

#### 返回信息
```json
{
  "success": true,
  "disk_info": {
    "total_gb": 500.0,
    "used_gb": 350.2,
    "free_gb": 149.8,
    "usage_percent": 70.04,
    "status": "normal"  // normal, warning, critical
  }
}
```

### 4. 告警系统 (`send_alert_notification`)

**触发条件**: 检测到异常情况时自动执行
**功能**: 发送多级别告警通知

#### 告警级别
- **Critical**: 严重告警，需要立即处理
- **Warning**: 警告告警，需要关注
- **Error**: 错误告警，系统异常

#### 告警条件

##### 任务相关告警
```python
# 失败率告警
if failure_rate > 20%:  # 警告
if failure_rate > 50%:  # 严重

# 任务量异常
if total_tasks == 0:    # 警告：无任务处理

# 错误集中度
if single_error_type > 50% of total_errors:  # 警告
```

##### 系统资源告警
```python
# 磁盘空间
if disk_usage > 80%:  # 警告
if disk_usage > 90%:  # 严重
```

#### 告警输出
- 日志文件记录
- 控制台输出
- 可扩展: 邮件、短信、Webhook

## 配置信息

### Beat调度配置

```python
# 每日统计报告 - 凌晨2点
'generate-daily-statistics': {
    'task': 'app.tasks.monitoring_tasks.generate_daily_statistics',
    'schedule': crontab(hour=2, minute=0),
    'options': {'queue': 'receipt'}
},

# 清理过期任务 - 凌晨4点  
'cleanup-expired-tasks': {
    'task': 'app.tasks.monitoring_tasks.cleanup_expired_tasks',
    'schedule': crontab(hour=4, minute=0),
    'options': {'queue': 'file'}
},

# 磁盘空间检查 - 每小时15分
'disk-space-check': {
    'task': 'app.tasks.monitoring_tasks.check_disk_space',
    'schedule': crontab(minute=15),
    'options': {'queue': 'file'}
}
```

### 任务优先级

```python
TASK_PRIORITIES = {
    'check-pending-tasks': 9,           # 最高优先级
    'update-all-pending-tracking': 8,
    'system-health-check': 7,
    'check-timeout-tasks': 6,
    'disk-space-check': 5,             # 监控任务
    'cleanup-temp-files': 4,
    'generate-daily-statistics': 3,     # 监控任务
    'cleanup-expired-tasks': 2,        # 监控任务
    'backup-database': 2,
    'cleanup-logs': 1
}
```

### 队列路由

```python
TASK_ROUTES = {
    # 监控任务路由
    'app.tasks.monitoring_tasks.generate_daily_statistics': {'queue': 'receipt'},
    'app.tasks.monitoring_tasks.check_disk_space': {'queue': 'file'},
    'app.tasks.monitoring_tasks.send_alert_notification': {'queue': 'high_priority'},
    'app.tasks.monitoring_tasks.cleanup_expired_tasks': {'queue': 'low_priority'},
}
```

## 使用方法

### 1. 手动执行监控任务

```bash
# 手动执行清理任务
python -c "from app.tasks.monitoring_tasks import cleanup_expired_tasks; print(cleanup_expired_tasks.apply().result)"

# 手动生成统计报告
python -c "from app.tasks.monitoring_tasks import generate_daily_statistics; print(generate_daily_statistics.apply().result)"

# 手动检查磁盘空间
python -c "from app.tasks.monitoring_tasks import check_disk_space; print(check_disk_space.apply().result)"
```

### 2. 测试监控系统

```bash
# 使用测试脚本
python test_monitoring.py
```

### 3. 查看监控报告

```bash
# 查看每日报告文件
ls reports/daily/
cat reports/daily/daily_report_20231201.json

# 查看告警日志
tail -f logs/critical_alerts.log
tail -f logs/warning_alerts.log
tail -f logs/error_alerts.log
```

### 4. 监控Beat调度状态

```bash
# 查看Beat调度器状态
python celery_beat_manager.py status

# 查看Beat日志
python celery_beat_manager.py logs --follow

# 列出所有定时任务
python celery_beat_manager.py list
```

## 文件结构

```
backend/
├── app/tasks/
│   └── monitoring_tasks.py        # 监控任务模块
├── reports/
│   ├── daily/                     # 每日报告
│   │   ├── daily_report_20231201.json
│   │   └── daily_report_20231202.json
│   └── alerts/                    # 告警记录
├── logs/
│   ├── critical_alerts.log        # 严重告警日志
│   ├── warning_alerts.log         # 警告告警日志
│   ├── error_alerts.log          # 错误告警日志
│   └── celerybeat.log             # Beat调度器日志
├── test_monitoring.py             # 监控测试脚本
└── MONITORING_SYSTEM.md          # 本文档
```

## 扩展配置

### 自定义清理策略

```python
# 修改清理配置
cleanup_config = {
    "completed_tasks_days": 30,    # 可调整保留天数
    "failed_tasks_days": 7,        
    "temp_files_hours": 24,        
    "log_files_days": 30           
}
```

### 自定义告警阈值

```python
# 修改告警条件
def check_daily_alerts(report):
    # 自定义告警逻辑
    failure_rate = report.get("task_statistics", {}).get("failure_rate", 0)
    
    if failure_rate > 15:  # 自定义阈值
        alerts.append({
            "type": "custom_failure_rate",
            "message": f"自定义失败率告警: {failure_rate}%",
            "severity": "warning"
        })
```

### 扩展告警渠道

```python
def send_email_alert(alerts):
    """发送邮件告警"""
    # 实现邮件发送逻辑
    pass

def send_webhook_alert(alerts):
    """发送Webhook告警"""
    # 实现Webhook调用逻辑
    pass
```

## 最佳实践

1. **定期检查报告**: 每日查看统计报告，关注异常趋势
2. **设置合理阈值**: 根据业务需求调整告警阈值
3. **及时响应告警**: 建立告警响应流程
4. **定期备份报告**: 重要报告数据应定期备份
5. **监控磁盘空间**: 确保有足够空间存储报告和日志
6. **优化清理策略**: 根据业务需求调整数据保留策略

## 故障排除

### 1. 监控任务不执行
```bash
# 检查Beat调度器状态
python celery_beat_manager.py status

# 查看Beat日志
python celery_beat_manager.py logs

# 重启Beat调度器
python celery_beat_manager.py restart
```

### 2. 报告生成失败
```bash
# 检查数据库连接
python -c "from app.core.database import SessionLocal; db = SessionLocal(); db.execute('SELECT 1').scalar(); print('数据库连接正常')"

# 手动执行报告生成
python test_monitoring.py
```

### 3. 告警不发送
```bash
# 检查告警日志权限
ls -la logs/
chmod 755 logs/
mkdir -p logs

# 测试告警功能
python -c "from app.tasks.monitoring_tasks import send_alert_notification; print(send_alert_notification.apply(args=[[{'type': 'test', 'message': '测试', 'severity': 'warning'}]]).result)"
```