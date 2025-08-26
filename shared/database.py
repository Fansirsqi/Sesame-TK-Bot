# src/shared/database.py - 共享数据库模块

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
from sqlalchemy import DateTime, String, BigInteger, Integer, func, create_engine
from contextlib import contextmanager
from typing import Generator, Optional
import os


# ===== ORM 模型 =====
class Base(DeclarativeBase):
    pass


class AlipayUser(Base):
    __tablename__ = "alipay_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alipay_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Device(Base):
    __tablename__ = "device"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class TgUser(Base):
    __tablename__ = "tg_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


# ===== 配置部分 =====
def get_database_uri() -> str:
    """从环境变量获取数据库URI"""
    return os.getenv("DATABASE_URI")


# ===== 同步上下文管理器（用于NoneBot） =====
@contextmanager
def get_db(engine) -> Generator[Session, None, None]:
    """
    获取数据库连接（session），使用方式：
    with get_db(engine) as db:
        db.query(...)
    """
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== FastAPI依赖生成器（用于FastAPI） =====
def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency to get a DB session."""
    database_uri = get_database_uri()
    engine = create_engine(database_uri, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== 初始化数据库（创建表）=====
def init_db(database_uri: Optional[str] = None) -> object:
    """初始化数据库，创建表"""
    if database_uri is None:
        database_uri = get_database_uri()

    engine = create_engine(database_uri, echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


# ===== 全局引擎和会话管理器（可选，用于特殊需求） =====
# 注意：这些全局变量应谨慎使用，特别是在多线程环境中
_engine = None
_SessionLocal = None


def get_global_engine():
    """获取全局数据库引擎（懒加载）"""
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_uri(), echo=False)
    return _engine


def get_global_session():
    """获取全局会话管理器（懒加载）"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_global_engine())
    return _SessionLocal
