from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.core.config import settings

# SQLite配置
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite需要这个参数
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """
    数据库会话依赖
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库
    """
    Base.metadata.create_all(bind=engine)