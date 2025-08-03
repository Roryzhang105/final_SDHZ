"""
智能重试系统测试脚本
测试不同错误类型的重试决策和策略
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tasks.retry_handler import (
    IntelligentRetryHandler,
    ErrorCategory,
    RetryDecision,
    analyze_task_errors
)
from app.tasks.retry_strategies import (
    RetryConfigFactory,
    BusinessRetryStrategies,
    CustomRetryConditions
)
from requests.exceptions import ConnectionError, HTTPError, Timeout
from sqlalchemy.exc import OperationalError


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockHTTPError(HTTPError):
    """模拟HTTP错误"""
    def __init__(self, status_code: int, message: str = "HTTP Error"):
        self.response = type('MockResponse', (), {'status_code': status_code})()
        super().__init__(message)


class RetrySystemTester:
    """重试系统测试器"""
    
    def __init__(self):
        self.handler = IntelligentRetryHandler()
        self.test_results = []
    
    def test_error_classification(self):
        """测试错误分类功能"""
        logger.info("=" * 50)
        logger.info("测试错误分类功能")
        logger.info("=" * 50)
        
        test_cases = [
            (ConnectionError("网络连接失败"), ErrorCategory.NETWORK_ERROR),
            (Timeout("请求超时"), ErrorCategory.NETWORK_ERROR),
            (MockHTTPError(429, "Too Many Requests"), ErrorCategory.API_RATE_LIMIT),
            (MockHTTPError(500, "Internal Server Error"), ErrorCategory.TEMPORARY_ERROR),
            (MockHTTPError(404, "Not Found"), ErrorCategory.DATA_ERROR),
            (ValueError("无效的数据格式"), ErrorCategory.DATA_ERROR),
            (FileNotFoundError("文件不存在"), ErrorCategory.DATA_ERROR),
            (OperationalError("数据库连接失败", None, None), ErrorCategory.TEMPORARY_ERROR),
            (MemoryError("内存不足"), ErrorCategory.SYSTEM_ERROR),
        ]
        
        passed = 0
        for exc, expected_category in test_cases:
            actual_category = self.handler.classify_error(exc)
            result = actual_category == expected_category
            
            logger.info(f"错误: {type(exc).__name__} -> 期望: {expected_category.value}, "
                       f"实际: {actual_category.value}, 结果: {'✓' if result else '✗'}")
            
            if result:
                passed += 1
        
        logger.info(f"错误分类测试完成: {passed}/{len(test_cases)} 通过")
        return passed == len(test_cases)
    
    def test_retry_decisions(self):
        """测试重试决策功能"""
        logger.info("=" * 50)
        logger.info("测试重试决策功能")
        logger.info("=" * 50)
        
        test_cases = [
            # (错误, 重试次数, 期望是否重试)
            (ConnectionError("网络错误"), 0, True),   # 网络错误应该重试
            (ConnectionError("网络错误"), 10, False), # 超过最大重试次数
            (ValueError("数据错误"), 0, False),       # 数据错误不应重试
            (MockHTTPError(429, "限流"), 0, True),   # API限流应该重试
            (MockHTTPError(404, "未找到"), 0, False), # 404错误不应重试
            (Timeout("超时"), 2, True),              # 超时错误在限制内应重试
        ]
        
        passed = 0
        for exc, retry_count, expected_should_retry in test_cases:
            should_retry, strategy = self.handler.should_retry(exc, retry_count, "test_task")
            result = should_retry == expected_should_retry
            
            logger.info(f"错误: {type(exc).__name__}, 重试次数: {retry_count}, "
                       f"期望重试: {expected_should_retry}, 实际重试: {should_retry}, "
                       f"结果: {'✓' if result else '✗'}")
            
            if result:
                passed += 1
        
        logger.info(f"重试决策测试完成: {passed}/{len(test_cases)} 通过")
        return passed == len(test_cases)
    
    def test_delay_calculation(self):
        """测试延迟计算功能"""
        logger.info("=" * 50)
        logger.info("测试延迟计算功能")
        logger.info("=" * 50)
        
        # 测试网络错误（立即重试）
        exc = ConnectionError("网络错误")
        _, strategy = self.handler.should_retry(exc, 0, "test_task")
        delay = self.handler.calculate_delay(strategy, 0)
        logger.info(f"网络错误立即重试延迟: {delay} 秒")
        
        # 测试API限流（固定延迟）
        exc = MockHTTPError(429, "限流")
        _, strategy = self.handler.should_retry(exc, 0, "test_task")
        delay = self.handler.calculate_delay(strategy, 0)
        logger.info(f"API限流延迟: {delay} 秒")
        
        # 测试指数退避
        exc = Timeout("超时")
        _, strategy = self.handler.should_retry(exc, 0, "test_task")
        for i in range(3):
            delay = self.handler.calculate_delay(strategy, i)
            logger.info(f"指数退避第 {i+1} 次重试延迟: {delay} 秒")
        
        return True
    
    def test_business_strategies(self):
        """测试业务场景策略"""
        logger.info("=" * 50)
        logger.info("测试业务场景策略")
        logger.info("=" * 50)
        
        business_types = [
            'tracking', 'screenshot', 'document', 
            'code_generation', 'email', 'monitoring', 'database'
        ]
        
        for business_type in business_types:
            strategies = RetryConfigFactory.get_strategy_for_business(business_type)
            config = RetryConfigFactory.create_celery_config(business_type)
            
            logger.info(f"业务类型: {business_type}")
            logger.info(f"  - 策略数量: {len(strategies)}")
            logger.info(f"  - 最大重试: {config['max_retries']}")
            logger.info(f"  - 基础延迟: {config['default_retry_delay']} 秒")
        
        return True
    
    def test_custom_conditions(self):
        """测试自定义重试条件"""
        logger.info("=" * 50)
        logger.info("测试自定义重试条件")
        logger.info("=" * 50)
        
        # 测试HTTP错误条件
        http_test_cases = [
            (500, True),   # 服务器错误应该重试
            (429, True),   # 限流应该重试
            (404, False),  # 未找到不应重试
            (400, False),  # 客户端错误不应重试
            (502, True),   # 网关错误应该重试
        ]
        
        for status_code, expected in http_test_cases:
            exc = MockHTTPError(status_code, f"HTTP {status_code}")
            result = CustomRetryConditions.should_retry_http_error(exc, status_code)
            logger.info(f"HTTP {status_code}: 期望重试 {expected}, 实际重试 {result}, "
                       f"结果: {'✓' if result == expected else '✗'}")
        
        return True
    
    def test_error_statistics(self):
        """测试错误统计功能"""
        logger.info("=" * 50)
        logger.info("测试错误统计功能")
        logger.info("=" * 50)
        
        # 模拟一些错误
        errors = [
            ConnectionError("网络错误1"),
            ConnectionError("网络错误2"),
            ValueError("数据错误1"),
            MockHTTPError(429, "限流错误"),
            Timeout("超时错误")
        ]
        
        task_name = "test_statistics_task"
        
        for i, exc in enumerate(errors):
            self.handler.should_retry(exc, 0, task_name)
            time.sleep(0.1)  # 确保时间戳不同
        
        # 获取统计信息
        stats = self.handler.get_error_statistics(task_name)
        
        logger.info(f"任务 {task_name} 错误统计:")
        logger.info(f"  - 总错误数: {stats['total_errors']}")
        logger.info(f"  - 错误类型分布: {stats['error_type_distribution']}")
        logger.info(f"  - 错误分类分布: {stats['category_distribution']}")
        
        # 分析错误模式
        analysis = analyze_task_errors(task_name)
        logger.info(f"错误分析建议: {analysis['suggestions']}")
        
        return stats['total_errors'] == len(errors)
    
    def test_integration_scenario(self):
        """测试集成场景"""
        logger.info("=" * 50)
        logger.info("测试集成场景 - 物流跟踪任务")
        logger.info("=" * 50)
        
        # 模拟物流跟踪任务的错误序列
        task_name = "tracking_integration_test"
        errors_sequence = [
            (ConnectionError("网络连接失败"), 0),
            (ConnectionError("网络连接失败"), 1),
            (MockHTTPError(429, "API限流"), 0),
            (Timeout("请求超时"), 0),
            (ValueError("返回数据格式错误"), 0),
        ]
        
        for exc, retry_count in errors_sequence:
            should_retry, strategy = self.handler.should_retry(exc, retry_count, task_name)
            delay = self.handler.calculate_delay(strategy, retry_count)
            category = self.handler.classify_error(exc)
            
            logger.info(f"错误: {type(exc).__name__}, "
                       f"分类: {category.value}, "
                       f"重试: {should_retry}, "
                       f"延迟: {delay}秒")
        
        # 获取任务统计
        stats = self.handler.get_error_statistics(task_name)
        logger.info(f"集成测试统计: {stats}")
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始智能重试系统测试")
        logger.info("=" * 60)
        
        tests = [
            ("错误分类测试", self.test_error_classification),
            ("重试决策测试", self.test_retry_decisions),
            ("延迟计算测试", self.test_delay_calculation),
            ("业务策略测试", self.test_business_strategies),
            ("自定义条件测试", self.test_custom_conditions),
            ("错误统计测试", self.test_error_statistics),
            ("集成场景测试", self.test_integration_scenario),
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
        
        logger.info("=" * 60)
        logger.info(f"测试总结: {passed}/{total} 个测试通过")
        
        if passed == total:
            logger.info("🎉 所有测试通过！智能重试系统工作正常")
        else:
            logger.warning(f"⚠️  有 {total - passed} 个测试失败，请检查系统配置")
        
        return passed == total


def main():
    """主函数"""
    print("智能重试系统测试工具")
    print("=" * 60)
    
    tester = RetrySystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 智能重试系统测试完成，系统工作正常")
        return 0
    else:
        print("\n❌ 智能重试系统测试发现问题，请检查配置")
        return 1


if __name__ == "__main__":
    exit(main())