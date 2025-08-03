#!/usr/bin/env python3
"""
数据库主键序列修复脚本
修复PostgreSQL表主键序列与数据不同步的问题
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import text
from app.core.database import engine, get_db_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_sequence_for_table(session, table_name, id_column='id'):
    """修复单个表的主键序列"""
    try:
        # 获取表的当前最大ID
        max_id_query = text(f"SELECT COALESCE(MAX({id_column}), 0) FROM {table_name}")
        result = session.execute(max_id_query)
        max_id = result.scalar()
        
        # 设置序列的下一个值为最大ID + 1
        next_val = max_id + 1
        sequence_name = f"{table_name}_{id_column}_seq"
        
        # 重置序列
        reset_query = text(f"SELECT setval('{sequence_name}', {next_val}, false)")
        session.execute(reset_query)
        
        logger.info(f"✅ 修复表 {table_name}: 最大ID={max_id}, 下一个序列值={next_val}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 修复表 {table_name} 失败: {e}")
        return False

def fix_all_sequences():
    """修复所有表的主键序列"""
    session = get_db_session()
    
    try:
        logger.info("🔧 开始修复数据库主键序列...")
        
        # 需要修复的表列表
        tables_to_fix = [
            'users',
            'tasks', 
            'delivery_receipts',
            'tracking_info',
            'recognition_results',
            'recognition_tasks',
            'courier_patterns',
            'couriers'
        ]
        
        success_count = 0
        total_count = len(tables_to_fix)
        
        for table_name in tables_to_fix:
            if fix_sequence_for_table(session, table_name):
                success_count += 1
        
        session.commit()
        
        logger.info(f"🎉 序列修复完成: {success_count}/{total_count} 个表修复成功")
        
        if success_count == total_count:
            logger.info("✅ 所有表的主键序列已成功修复")
            return True
        else:
            logger.warning(f"⚠️  有 {total_count - success_count} 个表修复失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 修复过程中发生错误: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def verify_sequences():
    """验证序列修复结果"""
    session = get_db_session()
    
    try:
        logger.info("🔍 验证序列修复结果...")
        
        tables_to_check = [
            'users',
            'tasks', 
            'delivery_receipts',
            'tracking_info'
        ]
        
        for table_name in tables_to_check:
            # 获取当前最大ID
            max_id_query = text(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            result = session.execute(max_id_query)
            max_id = result.scalar()
            
            # 获取序列的当前值
            sequence_name = f"{table_name}_id_seq"
            seq_query = text(f"SELECT currval('{sequence_name}')")
            try:
                seq_result = session.execute(seq_query)
                current_seq = seq_result.scalar()
                
                # 验证序列值是否正确
                if current_seq > max_id:
                    logger.info(f"✅ {table_name}: 最大ID={max_id}, 序列值={current_seq} (正确)")
                else:
                    logger.warning(f"⚠️  {table_name}: 最大ID={max_id}, 序列值={current_seq} (可能仍有问题)")
                    
            except Exception as e:
                # 如果序列还没有被使用过，currval会失败
                logger.info(f"📋 {table_name}: 最大ID={max_id}, 序列未初始化 (正常)")
        
        logger.info("🔍 序列验证完成")
        
    except Exception as e:
        logger.error(f"❌ 验证过程中发生错误: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("=== 数据库主键序列修复工具 ===")
    
    # 执行修复
    if fix_all_sequences():
        # 验证修复结果
        verify_sequences()
        logger.info("🎉 数据库主键序列修复完成！")
        sys.exit(0)
    else:
        logger.error("❌ 数据库主键序列修复失败！")
        sys.exit(1)