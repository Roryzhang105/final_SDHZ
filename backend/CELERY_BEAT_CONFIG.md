# Celery Beat 定时任务配置文档

## 概述

本项目使用 Celery Beat 实现定时任务调度，支持任务监控、数据清理、报告生成等自动化操作。

## 文件结构

```
backend/
├── app/tasks/
│   ├── celery_app.py           # Celery 应用配置
│   ├── beat_schedules.py       # 定时任务配置
│   ├── tracking_tasks.py       # 物流跟踪任务
│   ├── receipt_tasks.py        # 回证生成任务
│   ├── file_tasks.py          # 文件处理任务
│   └── screenshot_tasks.py     # 截图任务
├── celery_beat_manager.py      # Beat 管理脚本
├── docker-compose.celery.yml   # Docker 配置
└── CELERY_BEAT_CONFIG.md      # 配置文档
```

## 配置详情

### 1. 时区设置

```python
timezone="Asia/Shanghai"
enable_utc=False
```

### 2. 调度器配置

使用数据库调度器，支持动态添加和修改任务：

```python
beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler'
```

### 3. 定时任务列表

#### 任务监控类 (每5-30分钟)
- `check-pending-tasks`: 检查待处理任务
- `update-tracking-status`: 更新物流状态  
- `check-timeout-tasks`: 检查超时任务
- `system-health-check`: 系统健康检查

#### 文件清理类 (每小时-每2小时)
- `cleanup-temp-files`: 清理临时文件
- `cleanup-expired-results`: 清理过期结果
- `check-disk-space`: 检查磁盘空间

#### 每日任务 (凌晨2-4点)
- `generate-daily-report`: 生成日报
- `optimize-database`: 优化数据库
- `backup-database`: 备份数据库
- `cleanup-expired-tasks`: 清理过期任务

#### 每周任务 (周日/周一)
- `cleanup-logs`: 清理日志文件
- `generate-weekly-report`: 生成周报

#### 每月任务 (每月1号)
- `archive-old-data`: 归档历史数据
- `generate-monthly-report`: 生成月报

## 队列配置

### 队列优先级
- `high_priority`: 关键任务 (健康检查、待处理任务)
- `tracking`: 物流相关任务
- `receipt`: 回证生成任务
- `screenshot`: 截图任务
- `low_priority`: 清理和备份任务

### 任务路由
```python
TASK_ROUTES = {
    'app.tasks.tracking_tasks.check_pending_tasks': {'queue': 'high_priority'},
    'app.tasks.tracking_tasks.system_health_check': {'queue': 'high_priority'},
    'app.tasks.file_tasks.cleanup_*': {'queue': 'low_priority'},
    # ...
}
```

## 使用方法

### 1. 本地运行

#### 启动 Celery Beat
```bash
# 后台运行
python celery_beat_manager.py start

# 前台运行 (便于调试)
python celery_beat_manager.py foreground

# 指定日志级别
python celery_beat_manager.py start --loglevel debug
```

#### 管理命令
```bash
# 查看状态
python celery_beat_manager.py status

# 查看日志
python celery_beat_manager.py logs
python celery_beat_manager.py logs --lines 100 --follow

# 重启服务
python celery_beat_manager.py restart

# 停止服务
python celery_beat_manager.py stop

# 列出所有定时任务
python celery_beat_manager.py list

# 清除调度文件
python celery_beat_manager.py clear
```

### 2. Docker 运行

```bash
# 启动所有 Celery 服务
docker-compose -f docker-compose.celery.yml up -d

# 查看日志
docker-compose -f docker-compose.celery.yml logs -f celery_beat

# 停止服务
docker-compose -f docker-compose.celery.yml down
```

### 3. 监控界面

访问 Celery Flower: http://localhost:5555

## 任务重试配置

### 默认重试策略
```python
'default': {
    'autoretry_for': (Exception,),
    'retry_kwargs': {'max_retries': 3, 'countdown': 60},
    'retry_backoff': True,
    'retry_jitter': True
}
```

### 关键任务重试策略
```python
'critical': {
    'autoretry_for': (Exception,),
    'retry_kwargs': {'max_retries': 5, 'countdown': 30},
    'retry_backoff': True,
    'retry_jitter': True
}
```

## 性能配置

```python
# 任务执行配置
task_soft_time_limit=300      # 软时间限制5分钟
task_time_limit=600           # 硬时间限制10分钟
worker_prefetch_multiplier=1  # 每次预取1个任务
task_acks_late=True          # 延迟确认
result_expires=3600          # 结果过期时间1小时
```

## 环境变量

```bash
# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost/db
```

## 日志配置

### 日志文件位置
- Beat 调度器: `logs/celerybeat.log`
- Worker 日志: `logs/celery_worker.log`
- 任务结果: `logs/task_results.log`

### 日志级别
- `debug`: 详细调试信息
- `info`: 一般信息 (推荐)
- `warning`: 警告信息
- `error`: 错误信息

## 故障排除

### 1. Beat 无法启动
```bash
# 检查 PID 文件
rm -f celerybeat.pid

# 清除调度文件
python celery_beat_manager.py clear

# 重新启动
python celery_beat_manager.py start
```

### 2. 任务不执行
```bash
# 检查 Redis 连接
redis-cli ping

# 检查数据库连接
python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"

# 查看 Beat 日志
python celery_beat_manager.py logs --follow
```

### 3. 时区问题
确保系统时区和 Celery 时区配置一致：
```python
timezone="Asia/Shanghai"
enable_utc=False
```

## 扩展配置

### 添加新的定时任务

1. 在 `beat_schedules.py` 中添加任务配置
2. 在对应的任务模块中实现任务函数
3. 重启 Celery Beat

### 修改调度时间

可以通过管理界面或直接修改配置文件来调整任务执行时间。

### 任务依赖

对于有依赖关系的任务，可以使用 Celery 的 chain 和 group 功能来组织任务执行顺序。

## 最佳实践

1. **资源监控**: 定期检查系统资源使用情况
2. **日志轮转**: 配置日志轮转避免磁盘空间不足
3. **任务幂等**: 确保任务可以安全重复执行
4. **异常处理**: 为所有任务添加适当的异常处理
5. **性能优化**: 根据任务特性调整队列和并发配置