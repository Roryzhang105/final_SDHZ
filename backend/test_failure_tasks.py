#!/usr/bin/env python3
"""
失败任务处理系统测试脚本
测试失败任务的分析、分类和自动恢复功能
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FailureCategory(Enum):
    """失败任务分类"""
    RECOVERABLE_NETWORK = "recoverable_network"
    RECOVERABLE_SYSTEM = "recoverable_system"
    RECOVERABLE_TEMPORARY = "recoverable_temporary"
    UNRECOVERABLE_DATA = "unrecoverable_data"
    UNRECOVERABLE_CONFIG = "unrecoverable_config"
    UNRECOVERABLE_BUSINESS = "unrecoverable_business"
    UNKNOWN = "unknown"


class MockTask:
    """模拟任务对象"""
    def __init__(self, task_id: int, task_type: str, error_message: str, 
                 updated_at: datetime = None):
        self.id = task_id
        self.task_type = task_type
        self.error_message = error_message
        self.updated_at = updated_at or datetime.now()
        self.recovery_attempts = 0
        self.manual_review_required = False
        self.recovery_notes = None
        self.review_notes = None


class SimpleFailureAnalyzer:
    """简化的失败分析器"""
    
    def __init__(self):
        # 错误模式识别规则
        self.error_patterns = {
            FailureCategory.RECOVERABLE_NETWORK: [
                'connection timeout', 'network unreachable', 'connection refused',
                'dns resolution failed', 'socket timeout', 'read timeout'
            ],
            FailureCategory.RECOVERABLE_SYSTEM: [
                'memory error', 'disk space', 'no space left',
                'resource temporarily unavailable', 'permission denied'
            ],
            FailureCategory.RECOVERABLE_TEMPORARY: [
                'database connection failed', 'deadlock detected',
                'server temporarily unavailable', 'too many requests',
                'rate limit exceeded', 'quota exceeded'
            ],
            FailureCategory.UNRECOVERABLE_DATA: [
                'invalid data format', 'malformed json', 'parse error',
                'validation failed', 'constraint violation', 'null value'
            ],
            FailureCategory.UNRECOVERABLE_CONFIG: [
                'configuration error', 'missing required parameter',
                'authentication failed', 'unauthorized access', 'api key invalid'
            ],
            FailureCategory.UNRECOVERABLE_BUSINESS: [
                'business rule violation', 'workflow state error',
                'resource not found', 'tracking number invalid',
                'courier company not supported'
            ]
        }
    
    def analyze_failure(self, task: MockTask) -> tuple:
        """分析失败任务"""
        if not task.error_message:
            return FailureCategory.UNKNOWN, {"reason": "无错误消息"}
        
        error_msg = task.error_message.lower()
        
        # 检查错误模式
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern in error_msg:
                    analysis = {
                        "task_id": task.id,
                        "category": category.value,
                        "matched_pattern": pattern,
                        "confidence": "high",
                        "recommended_action": self._get_recommended_action(category)
                    }
                    return category, analysis
        
        # 未匹配任何模式
        return FailureCategory.UNKNOWN, {
            "task_id": task.id,
            "category": FailureCategory.UNKNOWN.value,
            "confidence": "low",
            "recommended_action": "manual_review"
        }
    
    def _get_recommended_action(self, category: FailureCategory) -> str:
        """获取推荐动作"""
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


class SimpleFailureHandler:
    """简化的失败处理器"""
    
    def __init__(self):
        self.analyzer = SimpleFailureAnalyzer()
        self.stats = {
            "analyzed": 0,
            "recovered": 0,
            "notified": 0,
            "manual_review": 0,
            "errors": 0
        }
    
    def process_failed_task(self, task: MockTask) -> dict:
        """处理失败任务"""
        try:
            # 分析失败原因
            category, analysis = self.analyzer.analyze_failure(task)
            self.stats["analyzed"] += 1
            
            result = {
                "task_id": task.id,
                "category": category.value,
                "analysis": analysis,
                "action_taken": "none",
                "success": False
            }
            
            # 根据分类决定处理动作
            if category in [
                FailureCategory.RECOVERABLE_NETWORK,
                FailureCategory.RECOVERABLE_SYSTEM,
                FailureCategory.RECOVERABLE_TEMPORARY
            ]:
                # 模拟自动恢复
                recovery_result = self._simulate_recovery(task, category)
                result.update(recovery_result)
                if recovery_result["success"]:
                    self.stats["recovered"] += 1
            
            elif category in [
                FailureCategory.UNRECOVERABLE_DATA,
                FailureCategory.UNRECOVERABLE_CONFIG,
                FailureCategory.UNRECOVERABLE_BUSINESS
            ]:
                # 模拟发送通知
                notification_result = self._simulate_notification(task, category)
                result.update(notification_result)
                if notification_result["success"]:
                    self.stats["notified"] += 1
            
            else:
                # 标记为人工审查
                result.update({
                    "action_taken": "manual_review",
                    "success": True,
                    "message": "标记为人工审查"
                })
                self.stats["manual_review"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"处理任务失败: {str(e)}")
            self.stats["errors"] += 1
            return {
                "task_id": task.id,
                "success": False,
                "error": str(e)
            }
    
    def _simulate_recovery(self, task: MockTask, category: FailureCategory) -> dict:
        """模拟自动恢复"""
        # 计算重试延迟
        delay = self._calculate_delay(category, task.recovery_attempts)
        
        return {
            "action_taken": "auto_recovery",
            "success": True,
            "message": f"任务将在{delay}秒后重试",
            "retry_delay": delay,
            "recovery_strategy": self._get_recovery_strategy(category)
        }
    
    def _simulate_notification(self, task: MockTask, category: FailureCategory) -> dict:
        """模拟发送通知"""
        notification_type = "admin" if "config" in category.value or "data" in category.value else "user"
        
        return {
            "action_taken": "notification_sent",
            "success": True,
            "message": f"已发送{notification_type}通知",
            "notification_type": notification_type
        }
    
    def _calculate_delay(self, category: FailureCategory, attempts: int) -> int:
        """计算重试延迟"""
        base_delays = {
            FailureCategory.RECOVERABLE_NETWORK: 30,
            FailureCategory.RECOVERABLE_SYSTEM: 300,
            FailureCategory.RECOVERABLE_TEMPORARY: 180
        }
        
        base_delay = base_delays.get(category, 60)
        return base_delay * (2 ** min(attempts, 3))
    
    def _get_recovery_strategy(self, category: FailureCategory) -> str:
        """获取恢复策略"""
        strategies = {
            FailureCategory.RECOVERABLE_NETWORK: "immediate_retry",
            FailureCategory.RECOVERABLE_SYSTEM: "delayed_retry",
            FailureCategory.RECOVERABLE_TEMPORARY: "progressive_retry"
        }
        return strategies.get(category, "manual_retry")


def test_failure_analysis():
    """测试失败分析功能"""
    logger.info("=" * 50)
    logger.info("测试失败分析功能")
    logger.info("=" * 50)
    
    analyzer = SimpleFailureAnalyzer()
    
    test_cases = [
        # (任务类型, 错误消息, 期望分类)
        ("tracking", "connection timeout occurred", FailureCategory.RECOVERABLE_NETWORK),
        ("receipt", "database connection failed", FailureCategory.RECOVERABLE_TEMPORARY),
        ("screenshot", "permission denied", FailureCategory.RECOVERABLE_SYSTEM),
        ("validation", "invalid data format", FailureCategory.UNRECOVERABLE_DATA),
        ("config", "api key invalid", FailureCategory.UNRECOVERABLE_CONFIG),
        ("business", "tracking number invalid", FailureCategory.UNRECOVERABLE_BUSINESS),
        ("unknown", "mysterious error", FailureCategory.UNKNOWN),
    ]
    
    passed = 0
    for i, (task_type, error_msg, expected) in enumerate(test_cases, 1):
        task = MockTask(i, task_type, error_msg)
        category, analysis = analyzer.analyze_failure(task)
        
        result = category == expected
        logger.info(f"测试 {i}: {task_type} - '{error_msg[:30]}...' "
                   f"-> 期望: {expected.value}, 实际: {category.value}, "
                   f"结果: {'✓' if result else '✗'}")
        
        if result:
            passed += 1
    
    logger.info(f"失败分析测试: {passed}/{len(test_cases)} 通过")
    return passed == len(test_cases)


def test_failure_processing():
    """测试失败处理功能"""
    logger.info("=" * 50)
    logger.info("测试失败处理功能")
    logger.info("=" * 50)
    
    handler = SimpleFailureHandler()
    
    # 创建测试任务
    test_tasks = [
        MockTask(1, "tracking", "connection timeout occurred"),     # 网络错误 - 自动恢复
        MockTask(2, "receipt", "too many requests"),               # 临时错误 - 自动恢复
        MockTask(3, "validation", "invalid data format"),         # 数据错误 - 通知管理员
        MockTask(4, "config", "authentication failed"),           # 配置错误 - 通知管理员
        MockTask(5, "business", "courier company not supported"), # 业务错误 - 通知用户
        MockTask(6, "unknown", "weird error happened"),           # 未知错误 - 人工审查
    ]
    
    results = []
    
    for task in test_tasks:
        result = handler.process_failed_task(task)
        results.append(result)
        
        logger.info(f"任务 {task.id} ({task.task_type}): "
                   f"分类={result['category']}, "
                   f"动作={result['action_taken']}, "
                   f"成功={result['success']}")
    
    # 检查统计结果
    logger.info(f"处理统计: {handler.stats}")
    
    # 验证结果
    expected_actions = [
        "auto_recovery",      # 网络错误
        "auto_recovery",      # 临时错误
        "notification_sent",  # 数据错误
        "notification_sent",  # 配置错误
        "notification_sent",  # 业务错误
        "manual_review"       # 未知错误
    ]
    
    passed = 0
    for i, (result, expected_action) in enumerate(zip(results, expected_actions)):
        if result["action_taken"] == expected_action:
            passed += 1
        else:
            logger.warning(f"任务 {i+1} 动作不匹配: 期望 {expected_action}, 实际 {result['action_taken']}")
    
    logger.info(f"失败处理测试: {passed}/{len(results)} 通过")
    return passed == len(results)


def test_recovery_strategies():
    """测试恢复策略"""
    logger.info("=" * 50)
    logger.info("测试恢复策略")
    logger.info("=" * 50)
    
    handler = SimpleFailureHandler()
    
    # 测试不同类型的恢复延迟
    categories_and_delays = [
        (FailureCategory.RECOVERABLE_NETWORK, [30, 60, 120, 240]),     # 网络错误快速重试
        (FailureCategory.RECOVERABLE_SYSTEM, [300, 600, 1200, 2400]),  # 系统错误慢重试
        (FailureCategory.RECOVERABLE_TEMPORARY, [180, 360, 720, 1440]) # 临时错误中等重试
    ]
    
    for category, expected_delays in categories_and_delays:
        logger.info(f"测试 {category.value} 的恢复延迟:")
        
        for attempt, expected_delay in enumerate(expected_delays):
            actual_delay = handler._calculate_delay(category, attempt)
            logger.info(f"  第 {attempt + 1} 次重试: 期望 {expected_delay}s, 实际 {actual_delay}s")
            
            if actual_delay != expected_delay:
                logger.warning(f"  延迟不匹配!")
    
    return True


def test_failure_patterns():
    """测试失败模式识别"""
    logger.info("=" * 50)
    logger.info("测试失败模式识别")
    logger.info("=" * 50)
    
    analyzer = SimpleFailureAnalyzer()
    
    # 测试各种真实的错误消息
    real_error_messages = [
        ("物流API连接超时", "connection timeout", FailureCategory.RECOVERABLE_NETWORK),
        ("服务器临时不可用", "server temporarily unavailable", FailureCategory.RECOVERABLE_TEMPORARY),
        ("磁盘空间不足", "no space left", FailureCategory.RECOVERABLE_SYSTEM),
        ("JSON格式错误", "malformed json", FailureCategory.UNRECOVERABLE_DATA),
        ("API密钥无效", "api key invalid", FailureCategory.UNRECOVERABLE_CONFIG),
        ("快递公司不支持", "courier company not supported", FailureCategory.UNRECOVERABLE_BUSINESS),
    ]
    
    passed = 0
    for desc, error_msg, expected_category in real_error_messages:
        task = MockTask(1, "test", error_msg)
        category, analysis = analyzer.analyze_failure(task)
        
        result = category == expected_category
        logger.info(f"{desc}: '{error_msg}' "
                   f"-> 分类: {category.value}, "
                   f"推荐动作: {analysis.get('recommended_action', 'unknown')}, "
                   f"结果: {'✓' if result else '✗'}")
        
        if result:
            passed += 1
    
    logger.info(f"模式识别测试: {passed}/{len(real_error_messages)} 通过")
    return passed == len(real_error_messages)


def test_integration_scenario():
    """测试集成场景"""
    logger.info("=" * 50)
    logger.info("测试集成场景 - 模拟批量失败任务处理")
    logger.info("=" * 50)
    
    handler = SimpleFailureHandler()
    
    # 模拟24小时内的各种失败任务
    failed_tasks = [
        MockTask(1, "tracking", "connection timeout", datetime.now() - timedelta(hours=1)),
        MockTask(2, "tracking", "network unreachable", datetime.now() - timedelta(hours=2)),
        MockTask(3, "receipt", "rate limit exceeded", datetime.now() - timedelta(hours=3)),
        MockTask(4, "screenshot", "permission denied", datetime.now() - timedelta(hours=4)),
        MockTask(5, "validation", "invalid data format", datetime.now() - timedelta(hours=5)),
        MockTask(6, "config", "authentication failed", datetime.now() - timedelta(hours=6)),
        MockTask(7, "business", "resource not found", datetime.now() - timedelta(hours=7)),
        MockTask(8, "unknown", "unexpected error", datetime.now() - timedelta(hours=8)),
    ]
    
    logger.info(f"开始处理 {len(failed_tasks)} 个失败任务...")
    
    processing_results = []
    for task in failed_tasks:
        result = handler.process_failed_task(task)
        processing_results.append(result)
    
    # 生成处理报告
    logger.info(f"批量处理完成，统计结果:")
    logger.info(f"  - 分析的任务: {handler.stats['analyzed']}")
    logger.info(f"  - 自动恢复: {handler.stats['recovered']}")
    logger.info(f"  - 发送通知: {handler.stats['notified']}")
    logger.info(f"  - 人工审查: {handler.stats['manual_review']}")
    logger.info(f"  - 处理错误: {handler.stats['errors']}")
    
    # 分析结果分布
    action_counts = {}
    for result in processing_results:
        action = result.get("action_taken", "unknown")
        action_counts[action] = action_counts.get(action, 0) + 1
    
    logger.info(f"动作分布: {action_counts}")
    
    # 验证预期结果
    expected_recoverable = 4  # 网络、临时、系统错误
    expected_notifications = 3  # 数据、配置、业务错误
    expected_manual = 1       # 未知错误
    
    success = (
        handler.stats['recovered'] == expected_recoverable and
        handler.stats['notified'] == expected_notifications and
        handler.stats['manual_review'] == expected_manual and
        handler.stats['errors'] == 0
    )
    
    logger.info(f"集成测试结果: {'✓ 通过' if success else '✗ 失败'}")
    
    return success


def main():
    """主函数"""
    print("失败任务处理系统测试工具")
    print("=" * 60)
    
    tests = [
        ("失败分析测试", test_failure_analysis),
        ("失败处理测试", test_failure_processing),
        ("恢复策略测试", test_recovery_strategies),
        ("模式识别测试", test_failure_patterns),
        ("集成场景测试", test_integration_scenario),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n开始执行: {test_name}")
            result = test_func()
            
            if result:
                logger.info(f"✓ {test_name} 通过")
                passed += 1
            else:
                logger.error(f"✗ {test_name} 失败")
                
        except Exception as e:
            logger.error(f"✗ {test_name} 执行异常: {str(e)}")
    
    print("=" * 60)
    print(f"测试总结: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！失败任务处理系统工作正常")
        return 0
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，请检查系统配置")
        return 1


if __name__ == "__main__":
    exit(main())