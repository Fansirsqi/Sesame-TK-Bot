# database.py - NoneBot插件数据库模块 (Async ORM)

import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.database import (
    Base,
    AlipayUser,
    Device,
    TgUser,
    AsyncGenerator,
    AsyncSessionLocal,
    AsyncSession,
    get_db_session as shared_get_db_session,
    init_db as shared_init_db,
    get_database_uri,
    get_global_engine,
    get_global_session,
)

DATABASE_URI = get_database_uri()


# ===== FastAPI/NoneBot 依赖 =====
async def get_db_session():
    return shared_get_db_session()


# ===== 初始化数据库 =====
async def init_db():
    return await shared_init_db()
