#!/usr/bin/env python3
"""
测试Celery监控系统的完整功能
包括任务调度、监控数据收集、健康检查等
"""

import os
import sys
import time
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有必需的模块导入"""
    print("=== 测试模块导入 ===")
    try:
        from app.tasks.celery_app import celery_app
        print("✓ Celery应用导入成功")
        
        from app.tasks.health_check_tasks import monitor_system_health, collect_worker_statistics, cleanup_monitoring_data
        print("✓ 健康检查任务导入成功")
        
        from app.services.celery_monitor import CeleryMonitorService
        print("✓ 监控服务导入成功")
        
        from app.models.celery_monitor import CeleryTaskMonitor, CeleryBeatHealth, WorkerStatistics, RetryStatistics
        print("✓ 监控数据模型导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_beat_schedule():
    """测试Beat调度配置"""
    print("\n=== 测试Beat调度配置 ===")
    try:
        from app.tasks.celery_app import celery_app
        
        beat_schedule = celery_app.conf.beat_schedule or {}
        if not beat_schedule:
            print("✗ Beat调度配置为空")
            return False
            
        print(f"✓ 已配置 {len(beat_schedule)} 个定时任务")
        
        # 检查健康检查任务
        health_tasks = [name for name in beat_schedule if 'health' in name or 'monitor' in name]
        print(f"✓ 找到 {len(health_tasks)} 个健康检查任务:")
        for task_name in health_tasks:
            task_config = beat_schedule[task_name]
            print(f"  - {task_name}: {task_config['task']}")
            
        return True
    except Exception as e:
        print(f"✗ Beat配置测试失败: {e}")
        return False

def test_database_models():
    """测试数据库模型"""
    print("\n=== 测试数据库模型 ===")
    try:
        from app.core.database import SessionLocal
        from app.models.celery_monitor import CeleryTaskMonitor, CeleryBeatHealth
        
        db = SessionLocal()
        
        # 测试表是否存在
        try:
            count = db.query(CeleryTaskMonitor).count()
            print(f"✓ CeleryTaskMonitor表正常，当前记录数: {count}")
        except Exception as e:
            print(f"✗ CeleryTaskMonitor表访问失败: {e}")
            
        try:
            count = db.query(CeleryBeatHealth).count()
            print(f"✓ CeleryBeatHealth表正常，当前记录数: {count}")
        except Exception as e:
            print(f"✗ CeleryBeatHealth表访问失败: {e}")
            
        db.close()
        return True
    except Exception as e:
        print(f"✗ 数据库模型测试失败: {e}")
        return False

def test_health_check():
    """测试健康检查功能"""
    print("\n=== 测试健康检查功能 ===")
    try:
        from app.tasks.health_check_tasks import monitor_system_health
        
        result = monitor_system_health()
        
        if result.get('success'):
            print("✓ 健康检查任务执行成功")
            
            # 显示系统状态
            data = result.get('data', {})
            system = data.get('system', {})
            celery_info = data.get('celery', {})
            tasks = data.get('tasks', {})
            
            print(f"  系统状态:")
            print(f"    - CPU使用率: {system.get('cpu_percent', 0):.1f}%")
            print(f"    - 内存使用率: {system.get('memory_percent', 0):.1f}%")
            print(f"    - 磁盘使用率: {system.get('disk_percent', 0):.1f}%")
            
            print(f"  Celery状态:")
            print(f"    - 消息代理连接: {'正常' if celery_info.get('broker_connected') else '异常'}")
            print(f"    - Worker数量: {celery_info.get('worker_count', 0)}")
            print(f"    - 活跃任务: {celery_info.get('active_tasks', 0)}")
            
            print(f"  任务统计:")
            print(f"    - 今日总任务: {tasks.get('total_today', 0)}")
            print(f"    - 今日失败: {tasks.get('failed_today', 0)}")
            print(f"    - 失败率: {tasks.get('failure_rate', 0):.1f}%")
            
            # 显示告警
            alerts = result.get('alerts', [])
            if alerts:
                print(f"  ⚠️  检测到 {len(alerts)} 个告警:")
                for alert in alerts[:3]:  # 只显示前3个
                    print(f"    - {alert.get('type')}: {alert.get('message')}")
            else:
                print("  ✅ 系统状态正常，无告警")
                
        else:
            print(f"✗ 健康检查失败: {result.get('message')}")
            return False
            
        return True
    except Exception as e:
        print(f"✗ 健康检查测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_service():
    """测试监控服务"""
    print("\n=== 测试监控服务 ===")
    try:
        from app.core.database import SessionLocal
        from app.services.celery_monitor import CeleryMonitorService
        
        db = SessionLocal()
        service = CeleryMonitorService(db)
        
        # 测试仪表板统计
        stats = service.get_dashboard_stats()
        print("✓ 仪表板统计获取成功")
        print(f"  - 总任务数: {stats.get('total_tasks', 0)}")
        print(f"  - 今日任务: {stats.get('today_tasks', 0)}")
        print(f"  - 成功率: {stats.get('success_rate', 0):.1f}%")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ 监控服务测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("Celery监控系统完整测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("模块导入", test_imports),
        ("Beat调度配置", test_beat_schedule), 
        ("数据库模型", test_database_models),
        ("健康检查", test_health_check),
        ("监控服务", test_monitoring_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print()
        if test_func():
            passed += 1
        else:
            print(f"⚠️  {test_name} 测试未通过")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Celery监控系统配置正确")
        print("\n建议:")
        print("1. 启动Celery Worker: ./start.sh dev")
        print("2. 访问前端监控页面: http://localhost:3000/app/admin/celery-monitor")
        print("3. 观察健康检查任务的定期执行")
    else:
        print("⚠️  部分测试失败，请检查配置")
    
    return passed == total

if __name__ == "__main__":
    main()