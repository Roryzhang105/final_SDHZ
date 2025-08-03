#!/usr/bin/env python3
"""
监控任务测试脚本
用于测试和验证监控任务功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_monitoring_tasks():
    """测试监控任务"""
    print("开始测试监控任务...")
    
    try:
        from app.tasks.monitoring_tasks import (
            cleanup_expired_tasks,
            generate_daily_statistics,
            check_disk_space,
            send_alert_notification
        )
        
        print("✓ 监控任务模块导入成功")
        
        # 测试磁盘空间检查
        print("\n1. 测试磁盘空间检查...")
        disk_result = check_disk_space.apply()
        print(f"磁盘检查结果: {disk_result.result}")
        
        # 测试告警功能
        print("\n2. 测试告警功能...")
        test_alerts = [
            {
                "type": "test_alert",
                "message": "这是一个测试告警",
                "severity": "warning"
            }
        ]
        alert_result = send_alert_notification.apply(args=[test_alerts])
        print(f"告警发送结果: {alert_result.result}")
        
        print("\n✓ 监控任务测试完成")
        
    except Exception as e:
        print(f"✗ 监控任务测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_beat_schedule():
    """测试Beat调度配置"""
    print("\n开始测试Beat调度配置...")
    
    try:
        from app.tasks.beat_schedules import BEAT_SCHEDULE, TASK_ROUTES
        
        print(f"✓ 找到 {len(BEAT_SCHEDULE)} 个定时任务")
        
        # 检查监控任务是否在调度中
        monitoring_tasks = [
            'generate-daily-statistics',
            'cleanup-expired-tasks',
            'disk-space-check'
        ]
        
        for task_name in monitoring_tasks:
            if task_name in BEAT_SCHEDULE:
                task_config = BEAT_SCHEDULE[task_name]
                print(f"✓ 找到监控任务: {task_name}")
                print(f"  - 任务路径: {task_config['task']}")
                print(f"  - 调度规则: {task_config['schedule']}")
                print(f"  - 描述: {task_config['description']}")
            else:
                print(f"✗ 未找到监控任务: {task_name}")
        
        print("\n✓ Beat调度配置测试完成")
        
    except Exception as e:
        print(f"✗ Beat调度配置测试失败: {e}")


def show_monitoring_schedule():
    """显示监控任务调度信息"""
    print("\n监控任务调度信息:")
    print("=" * 60)
    
    try:
        from app.tasks.beat_schedules import BEAT_SCHEDULE
        
        monitoring_tasks = {
            'generate-daily-statistics': '每日统计报告',
            'cleanup-expired-tasks': '清理过期任务',
            'disk-space-check': '磁盘空间检查'
        }
        
        for task_name, description in monitoring_tasks.items():
            if task_name in BEAT_SCHEDULE:
                config = BEAT_SCHEDULE[task_name]
                print(f"\n任务名称: {description} ({task_name})")
                print(f"执行时间: {config['schedule']}")
                print(f"任务队列: {config['options'].get('queue', 'default')}")
                print(f"任务描述: {config['description']}")
                print("-" * 40)
        
    except Exception as e:
        print(f"显示调度信息失败: {e}")


def main():
    """主函数"""
    print("监控任务测试工具")
    print("=" * 50)
    
    # 测试监控任务
    test_monitoring_tasks()
    
    # 测试Beat调度配置
    test_beat_schedule()
    
    # 显示调度信息
    show_monitoring_schedule()
    
    print("\n测试完成!")


if __name__ == "__main__":
    main()