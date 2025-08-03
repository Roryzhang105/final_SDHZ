#!/usr/bin/env python3
"""
验证数据库索引创建效果
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_all_indexes():
    """获取数据库中所有索引信息"""
    query = """
    SELECT 
        schemaname,
        tablename,
        indexname,
        indexdef
    FROM pg_indexes 
    WHERE schemaname = 'public'
    ORDER BY tablename, indexname;
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return result.fetchall()


def get_table_indexes(table_name):
    """获取指定表的索引信息"""
    query = """
    SELECT 
        indexname,
        indexdef
    FROM pg_indexes 
    WHERE schemaname = 'public' AND tablename = :table_name
    ORDER BY indexname;
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query), {"table_name": table_name})
        return result.fetchall()


def check_index_usage():
    """检查索引使用统计"""
    query = """
    SELECT 
        schemaname,
        relname as tablename,
        indexrelname as indexname,
        idx_scan as index_scans,
        idx_tup_read as tuples_read,
        idx_tup_fetch as tuples_fetched
    FROM pg_stat_user_indexes 
    WHERE schemaname = 'public'
    ORDER BY relname, indexrelname;
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return result.fetchall()


def verify_specific_indexes():
    """验证特定的索引是否存在"""
    expected_indexes = {
        'tasks': [
            'ix_tasks_status',
            'idx_tasks_created_at',
            'idx_tasks_status_created',
            'idx_tasks_user_status', 
            'idx_tasks_tracking_number'
        ],
        'delivery_receipts': [
            'ix_delivery_receipts_tracking_number',  # tracking_number索引
            'ix_delivery_receipts_status',
            'idx_delivery_receipts_created_at',
            'idx_delivery_receipts_status_created',
            'idx_delivery_receipts_user_status'
        ],
        'tracking_info': [
            'ix_tracking_info_current_status',
            'ix_tracking_info_last_update',
            'idx_tracking_info_created_at',
            'idx_tracking_info_updated_at',
            'idx_tracking_info_status_update',
            'idx_tracking_info_signed_update'
        ]
    }
    
    print("🔍 验证特定索引是否存在...")
    all_passed = True
    
    for table_name, expected in expected_indexes.items():
        print(f"\n📋 表: {table_name}")
        indexes = get_table_indexes(table_name)
        existing_indexes = [idx[0] for idx in indexes]
        
        for expected_index in expected:
            if expected_index in existing_indexes:
                print(f"  ✅ {expected_index}")
            else:
                print(f"  ❌ {expected_index} - 缺失")
                all_passed = False
        
        # 显示所有索引
        print(f"  📊 该表总共有 {len(existing_indexes)} 个索引")
    
    return all_passed


def analyze_index_performance():
    """分析索引性能"""
    print("\n📈 索引使用统计分析:")
    
    usage_stats = check_index_usage()
    
    for stat in usage_stats:
        schema, table, index, scans, reads, fetches = stat
        print(f"  {table}.{index}:")
        print(f"    扫描次数: {scans}")
        print(f"    读取行数: {reads}")
        print(f"    获取行数: {fetches}")
        print()


def test_query_performance():
    """测试查询性能（使用EXPLAIN ANALYZE）"""
    print("🚀 测试查询性能...")
    
    test_queries = [
        {
            "name": "按状态查询任务",
            "query": "SELECT COUNT(*) FROM tasks WHERE status = 'PENDING'"
        },
        {
            "name": "按状态和创建时间查询任务",
            "query": "SELECT * FROM tasks WHERE status = 'COMPLETED' AND created_at > NOW() - INTERVAL '7 days'"
        },
        {
            "name": "按快递单号查询送达回证",
            "query": "SELECT * FROM delivery_receipts WHERE tracking_number = '1151238971060'"
        },
        {
            "name": "按状态查询物流信息",
            "query": "SELECT COUNT(*) FROM tracking_info WHERE current_status = 'delivered'"
        }
    ]
    
    for test in test_queries:
        print(f"\n📊 {test['name']}:")
        explain_query = f"EXPLAIN ANALYZE {test['query']}"
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text(explain_query))
                for row in result:
                    print(f"  {row[0]}")
        except Exception as e:
            print(f"  ❌ 查询失败: {e}")


def main():
    """主函数"""
    print("🔍 数据库索引验证工具")
    print("=" * 50)
    
    try:
        # 1. 验证特定索引
        if verify_specific_indexes():
            print("\n✅ 所有期望的索引都已创建")
        else:
            print("\n⚠️  部分索引缺失")
        
        # 2. 显示所有索引
        print("\n📋 所有索引列表:")
        all_indexes = get_all_indexes()
        current_table = None
        
        for idx in all_indexes:
            schema, table, index_name, index_def = idx
            if table != current_table:
                print(f"\n📊 表: {table}")
                current_table = table
            print(f"  - {index_name}")
            if "btree" in index_def.lower():
                columns = index_def.split("(")[1].split(")")[0] if "(" in index_def else "N/A"
                print(f"    列: {columns}")
        
        print(f"\n📈 总索引数: {len(all_indexes)}")
        
        # 3. 分析索引使用情况
        analyze_index_performance()
        
        # 4. 测试查询性能
        test_query_performance()
        
        print("\n🎉 索引验证完成！")
        
    except Exception as e:
        print(f"❌ 验证过程中出错: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)