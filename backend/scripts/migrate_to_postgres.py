#!/usr/bin/env python3
"""
SQLite 到 PostgreSQL 数据迁移脚本
"""
import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import create_engine, MetaData, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# 导入应用配置和模型
from app.core.config import settings
from app.models.base import Base
from app.models import (
    User, DeliveryReceipt, Courier, TrackingInfo, 
    RecognitionTask, RecognitionResult, CourierPattern, Task
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """数据库迁移器"""
    
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        
        # SQLite 连接
        self.sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
        self.sqlite_session = sessionmaker(bind=self.sqlite_engine)
        
        # PostgreSQL 连接
        self.postgres_engine = create_engine(settings.DATABASE_URL)
        self.postgres_session = sessionmaker(bind=self.postgres_engine)
        
        # 模型列表（按依赖顺序）
        self.models = [
            User,
            Courier,
            DeliveryReceipt,
            TrackingInfo,
            CourierPattern,
            RecognitionTask,
            RecognitionResult,
            Task
        ]
    
    def check_sqlite_exists(self) -> bool:
        """检查 SQLite 数据库文件是否存在"""
        if not os.path.exists(self.sqlite_path):
            logger.error(f"SQLite 数据库文件不存在: {self.sqlite_path}")
            return False
        
        logger.info(f"找到 SQLite 数据库: {self.sqlite_path}")
        return True
    
    def check_connections(self) -> bool:
        """检查数据库连接"""
        try:
            # 检查 SQLite 连接
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("SQLite 连接成功")
            
            # 检查 PostgreSQL 连接
            with self.postgres_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("PostgreSQL 连接成功")
            
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def create_postgres_tables(self) -> bool:
        """在 PostgreSQL 中创建表结构"""
        try:
            Base.metadata.create_all(bind=self.postgres_engine)
            logger.info("PostgreSQL 表结构创建成功")
            return True
        except Exception as e:
            logger.error(f"创建 PostgreSQL 表结构失败: {e}")
            return False
    
    def get_table_row_count(self, engine, table_name: str) -> int:
        """获取表的行数"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.scalar()
        except Exception:
            return 0
    
    def backup_postgres_data(self) -> bool:
        """备份现有的 PostgreSQL 数据（如果有）"""
        try:
            postgres_session = self.postgres_session()
            
            # 检查是否有数据需要备份
            total_rows = 0
            for model in self.models:
                count = postgres_session.query(model).count()
                total_rows += count
                if count > 0:
                    logger.info(f"表 {model.__tablename__} 有 {count} 行数据")
            
            if total_rows > 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"postgres_backup_{timestamp}.sql"
                logger.warning(f"PostgreSQL 中已有 {total_rows} 行数据")
                logger.warning(f"建议先手动备份数据: pg_dump > {backup_file}")
                
                response = input("是否继续迁移？这将清除现有数据 (y/N): ")
                if response.lower() != 'y':
                    return False
            
            postgres_session.close()
            return True
        except Exception as e:
            logger.error(f"检查 PostgreSQL 数据失败: {e}")
            return False
    
    def clear_postgres_tables(self) -> bool:
        """清空 PostgreSQL 表数据"""
        try:
            postgres_session = self.postgres_session()
            
            # 按反向依赖顺序删除数据
            for model in reversed(self.models):
                deleted_count = postgres_session.query(model).delete()
                if deleted_count > 0:
                    logger.info(f"清空表 {model.__tablename__}: {deleted_count} 行")
            
            postgres_session.commit()
            postgres_session.close()
            logger.info("PostgreSQL 表数据清空完成")
            return True
        except Exception as e:
            logger.error(f"清空 PostgreSQL 表失败: {e}")
            return False
    
    def migrate_table_data(self, model_class) -> bool:
        """迁移单个表的数据"""
        table_name = model_class.__tablename__
        logger.info(f"开始迁移表: {table_name}")
        
        sqlite_session = self.sqlite_session()
        postgres_session = self.postgres_session()
        
        try:
            # 从 SQLite 读取数据
            sqlite_data = sqlite_session.query(model_class).all()
            total_rows = len(sqlite_data)
            
            if total_rows == 0:
                logger.info(f"表 {table_name} 无数据，跳过")
                return True
            
            logger.info(f"从 SQLite 读取到 {total_rows} 行数据")
            
            # 批量插入到 PostgreSQL
            batch_size = 1000
            migrated_count = 0
            
            for i in range(0, total_rows, batch_size):
                batch = sqlite_data[i:i + batch_size]
                
                for row in batch:
                    # 创建新的实例（避免 session 冲突）
                    row_dict = {}
                    for column in model_class.__table__.columns:
                        value = getattr(row, column.name, None)
                        row_dict[column.name] = value
                    
                    new_row = model_class(**row_dict)
                    postgres_session.add(new_row)
                
                postgres_session.commit()
                migrated_count += len(batch)
                logger.info(f"已迁移 {migrated_count}/{total_rows} 行")
            
            logger.info(f"表 {table_name} 迁移完成: {migrated_count} 行")
            return True
            
        except Exception as e:
            logger.error(f"迁移表 {table_name} 失败: {e}")
            postgres_session.rollback()
            return False
        finally:
            sqlite_session.close()
            postgres_session.close()
    
    def verify_migration(self) -> bool:
        """验证迁移结果"""
        logger.info("开始验证迁移结果...")
        
        sqlite_session = self.sqlite_session()
        postgres_session = self.postgres_session()
        
        try:
            verification_passed = True
            
            for model in self.models:
                table_name = model.__tablename__
                
                # 统计行数
                sqlite_count = sqlite_session.query(model).count()
                postgres_count = postgres_session.query(model).count()
                
                logger.info(f"表 {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
                
                if sqlite_count != postgres_count:
                    logger.error(f"表 {table_name} 数据行数不一致！")
                    verification_passed = False
                
                # 简单的数据完整性检查
                if sqlite_count > 0:
                    # 检查第一行和最后一行的ID
                    sqlite_first = sqlite_session.query(model).first()
                    postgres_first = postgres_session.query(model).first()
                    
                    if hasattr(sqlite_first, 'id') and hasattr(postgres_first, 'id'):
                        if sqlite_first.id != postgres_first.id:
                            logger.warning(f"表 {table_name} 第一行ID不一致")
            
            if verification_passed:
                logger.info("✅ 数据迁移验证通过")
            else:
                logger.error("❌ 数据迁移验证失败")
            
            return verification_passed
            
        except Exception as e:
            logger.error(f"验证迁移结果失败: {e}")
            return False
        finally:
            sqlite_session.close()
            postgres_session.close()
    
    def run_migration(self) -> bool:
        """执行完整的迁移流程"""
        logger.info("开始数据库迁移...")
        start_time = datetime.now()
        
        # 1. 检查 SQLite 文件存在
        if not self.check_sqlite_exists():
            return False
        
        # 2. 检查数据库连接
        if not self.check_connections():
            return False
        
        # 3. 创建 PostgreSQL 表结构
        if not self.create_postgres_tables():
            return False
        
        # 4. 备份检查
        if not self.backup_postgres_data():
            return False
        
        # 5. 清空 PostgreSQL 数据
        if not self.clear_postgres_tables():
            return False
        
        # 6. 迁移数据
        for model in self.models:
            if not self.migrate_table_data(model):
                logger.error(f"迁移失败，停止在表: {model.__tablename__}")
                return False
        
        # 7. 验证迁移结果
        if not self.verify_migration():
            logger.error("迁移验证失败")
            return False
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"🎉 数据迁移完成！耗时: {duration}")
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SQLite 到 PostgreSQL 数据迁移')
    parser.add_argument(
        '--sqlite-path',
        default='./delivery_receipt.db',
        help='SQLite 数据库文件路径 (默认: ./delivery_receipt.db)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制迁移，不询问确认'
    )
    
    args = parser.parse_args()
    
    # 创建迁移器
    migrator = DatabaseMigrator(args.sqlite_path)
    
    if not args.force:
        print("⚠️  数据迁移警告:")
        print("1. 这将清空目标 PostgreSQL 数据库中的所有数据")
        print("2. 请确保已备份重要数据")
        print("3. 请确保 PostgreSQL 服务正在运行")
        print(f"4. SQLite 源文件: {args.sqlite_path}")
        print(f"5. PostgreSQL 目标: {settings.DATABASE_URL}")
        print()
        
        response = input("确认继续？(y/N): ")
        if response.lower() != 'y':
            print("迁移已取消")
            return False
    
    # 执行迁移
    success = migrator.run_migration()
    
    if success:
        print("\n✅ 迁移成功完成！")
        print("下一步:")
        print("1. 更新应用配置使用 PostgreSQL")
        print("2. 重启应用服务")
        print("3. 验证应用功能正常")
    else:
        print("\n❌ 迁移失败！")
        print("请检查日志文件 migration.log 获取详细错误信息")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)