from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 数据库配置 - 支持PostgreSQL和SQLite
connect_args = {}
engine_kwargs = {
    "echo": False,
    "future": True,  # 使用SQLAlchemy 2.0风格
}

if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    connect_args = {"check_same_thread": False}
    engine_kwargs.update({
        "connect_args": connect_args,
    })
else:
    # PostgreSQL配置 - 连接池优化
    engine_kwargs.update({
        "pool_size": 20,           # 连接池大小
        "max_overflow": 30,        # 连接池溢出
        "pool_pre_ping": True,     # 连接前ping检查
        "pool_recycle": 3600,      # 连接回收时间(1小时)
        "poolclass": QueuePool,    # 使用队列连接池
        "connect_args": {
            "connect_timeout": 10,
            "application_name": "delivery_receipt_app"
        }
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# 会话配置优化
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # 防止在事务提交后对象过期
)

Base = declarative_base()


# 连接池事件监听器
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """为SQLite设置优化参数"""
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """连接检出时的日志记录"""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """连接检入时的日志记录"""
    logger.debug("Connection checked in to pool")


def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖 - 优化版本
    提供更好的错误处理和资源管理
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    获取数据库会话的同步方法
    用于非FastAPI上下文中的数据库操作
    """
    return SessionLocal()


class DatabaseManager:
    """数据库管理器 - 提供高级数据库操作"""
    
    @staticmethod
    def get_session_with_retry(max_retries: int = 3) -> Session:
        """
        获取数据库会话，带重试机制
        """
        for attempt in range(max_retries):
            try:
                return SessionLocal()
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
        return SessionLocal()
    
    @staticmethod
    def execute_with_retry(func, *args, max_retries: int = 3, **kwargs):
        """
        执行数据库操作，带重试机制
        """
        for attempt in range(max_retries):
            db = None
            try:
                db = DatabaseManager.get_session_with_retry()
                result = func(db, *args, **kwargs)
                db.commit()
                return result
            except Exception as e:
                if db:
                    db.rollback()
                logger.warning(f"Database operation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
            finally:
                if db:
                    db.close()


def init_db() -> None:
    """
    初始化数据库
    创建所有表结构
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def get_db_info() -> dict:
    """
    获取数据库连接信息
    """
    pool = engine.pool
    try:
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
            "pool_class": str(type(pool).__name__)
        }
    except AttributeError as e:
        # 某些连接池属性可能不存在
        return {
            "pool_size": getattr(pool, '_pool', {}).qsize() if hasattr(pool, '_pool') else 'N/A',
            "pool_class": str(type(pool).__name__),
            "note": "某些连接池信息不可用"
        }