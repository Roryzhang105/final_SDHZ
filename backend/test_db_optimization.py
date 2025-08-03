#!/usr/bin/env python3
"""
测试数据库连接优化效果
"""
import sys
import time
import threading
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine, get_db_session, get_db_info, DatabaseManager
from app.core.config import settings
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_connection():
    """测试基本连接"""
    print("🔍 测试基本数据库连接...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ 数据库版本: {version}")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_connection_pool_info():
    """测试连接池信息"""
    print("\n📊 连接池状态信息:")
    try:
        info = get_db_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        return True
    except Exception as e:
        print(f"❌ 获取连接池信息失败: {e}")
        return False


def test_concurrent_connections(num_threads=10, queries_per_thread=5):
    """测试并发连接"""
    print(f"\n🚀 测试并发连接 ({num_threads} 线程, 每线程 {queries_per_thread} 查询)...")
    
    results = []
    errors = []
    
    def worker():
        """工作线程函数"""
        for i in range(queries_per_thread):
            try:
                db = get_db_session()
                result = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
                results.append(result)
                db.close()
                time.sleep(0.1)  # 模拟处理时间
            except Exception as e:
                errors.append(str(e))
    
    # 创建并启动线程
    threads = []
    start_time = time.time()
    
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"  总查询数: {len(results)}")
    print(f"  成功查询: {len(results)}")
    print(f"  失败查询: {len(errors)}")
    print(f"  执行时间: {duration:.2f}秒")
    print(f"  QPS: {len(results)/duration:.2f}")
    
    if errors:
        print("❌ 并发测试有错误:")
        for error in errors[:5]:  # 只显示前5个错误
            print(f"    {error}")
        return False
    else:
        print("✅ 并发测试成功")
        return True


def test_retry_mechanism():
    """测试重试机制"""
    print("\n🔄 测试数据库重试机制...")
    
    def test_query(db):
        """测试查询函数"""
        return db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    
    try:
        result = DatabaseManager.execute_with_retry(test_query)
        print(f"✅ 重试机制测试成功，用户数: {result}")
        return True
    except Exception as e:
        print(f"❌ 重试机制测试失败: {e}")
        return False


def test_connection_lifecycle():
    """测试连接生命周期"""
    print("\n🔄 测试连接生命周期...")
    
    print("  初始连接池状态:")
    initial_info = get_db_info()
    for key, value in initial_info.items():
        print(f"    {key}: {value}")
    
    # 创建多个连接
    sessions = []
    for i in range(5):
        db = get_db_session()
        sessions.append(db)
        print(f"  创建连接 {i+1}")
    
    print("  创建连接后的状态:")
    mid_info = get_db_info()
    for key, value in mid_info.items():
        print(f"    {key}: {value}")
    
    # 关闭连接
    for i, db in enumerate(sessions):
        db.close()
        print(f"  关闭连接 {i+1}")
    
    print("  关闭连接后的状态:")
    final_info = get_db_info()
    for key, value in final_info.items():
        print(f"    {key}: {value}")
    
    return True


def main():
    """主测试函数"""
    print("🧪 数据库连接优化测试")
    print("=" * 50)
    print(f"数据库URL: {settings.DATABASE_URL}")
    print(f"连接池大小: 20")
    print(f"最大溢出: 30")
    print("=" * 50)
    
    tests = [
        ("基本连接测试", test_basic_connection),
        ("连接池信息测试", test_connection_pool_info),
        ("连接生命周期测试", test_connection_lifecycle),
        ("重试机制测试", test_retry_mechanism),
        ("并发连接测试", test_concurrent_connections),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！数据库连接优化成功！")
    else:
        print("⚠️  部分测试失败，请检查配置")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)