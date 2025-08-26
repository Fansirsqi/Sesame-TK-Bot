# database.py - NoneBot插件数据库模块（使用共享数据库）

import sys
import os

# 添加项目根目录到Python路径，以便导入shared模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入共享数据库模块
from shared.database import Base, AlipayUser, Device, TgUser, get_db as shared_get_db, init_db as shared_init_db, get_database_uri

# 为了向后兼容，保持原有的接口
DATABASE_URI = get_database_uri()


# ===== 上下文管理器：用于安全获取 session =====
def get_db(engine):
    """
    获取数据库连接（session），使用方式：
    with get_db(engine) as db:
        db.query(...)
    """
    return shared_get_db(engine)


# ===== 初始化数据库（创建表）=====
def init_db(database_uri=None):
    """
    初始化数据库，创建表
    如果没有提供database_uri，使用环境变量或默认值
    """
    if database_uri is None:
        database_uri = DATABASE_URI
    return shared_init_db(database_uri)
