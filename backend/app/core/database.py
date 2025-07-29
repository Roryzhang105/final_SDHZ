from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.core.config import settings

engine = create_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    pool_recycle=300,
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