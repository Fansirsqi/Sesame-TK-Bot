# dbmodel.py - FastAPI服务器数据库模块（使用共享数据库）

import sys
import os
# 添加项目根目录到Python路径，以便导入shared模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入共享数据库模块
from shared.database import (
    Base,
    AlipayUser,
    Device,
    TgUser,
    get_db_session,
    init_db as shared_init_db,
    get_database_uri,
    get_global_engine,
    get_global_session
)

# 为了向后兼容，保持原有的接口
DATABASE_URI = get_database_uri()

# ===== FastAPI依赖 =====
def get_db():
    """FastAPI dependency to get a DB session."""
    yield from get_db_session()

# ===== 初始化数据库（创建表）=====
def init_db(database_uri=None):
    """
    初始化数据库，创建表
    如果没有提供database_uri，使用环境变量或默认值
    """
    if database_uri is None:
        database_uri = DATABASE_URI
    return shared_init_db(database_uri)

# ===== 全局引擎和会话管理器（可选）=====
# 如果需要全局访问，可以使用这些函数
def get_engine():
    """获取全局数据库引擎"""
    return get_global_engine()

def get_session_local():
    """获取全局会话管理器"""
    return get_global_session()