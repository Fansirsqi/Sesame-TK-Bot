# src/shared/database.py - 共享数据库模块 (Async ORM)

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, BigInteger, Integer, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator, Optional
import os
from dotenv import load_dotenv


# ===== ORM 基类 =====
class Base(DeclarativeBase):
    pass


# ===== ORM 模型 =====
class AlipayUser(Base):
    __tablename__ = "alipay_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alipay_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Device(Base):
    __tablename__ = "device"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


# ===== 配置 =====
def get_database_uri() -> str:
    """从环境变量获取数据库URI"""
    # 必须使用 async driver
    load_dotenv(".env", override=True)
    return os.getenv("DATABASE_URI", "sqlite+aiosqlite:///src/sesame.db")


# ===== 初始化引擎和 session 工厂 =====
_engine = create_async_engine(get_database_uri(), echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    _engine, expire_on_commit=False, class_=AsyncSession
)


# ===== 获取异步 session (FastAPI/NoneBot 依赖注入) =====
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# ===== 初始化数据库（建表）=====
async def init_db():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ===== 提供全局引擎和 session 工厂 =====
def get_global_engine():
    return _engine


def get_global_session():
    return AsyncSessionLocal
