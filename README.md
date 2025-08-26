# Sesame-TK-Service


芝麻粒-TK授权码获取 - NoneBot

验证服务器 - FastAPI


## 🏗️ 项目结构

```
Sesame-TK-Service/
├── src/
│   ├── shared/                    # 🆕 共享数据库模块
│   │   ├── __init__.py           # 包导出
│   │   ├── database.py           # 核心数据库代码
│   │   └── README.md            # 使用文档
│   ├── bot/                      # 🤖 NoneBot机器人
│   │   ├── __init__.py
│   │   └── plugins/
│   │       └── sesame/           # 芝麻粒插件
│   └── server/                   # 🚀 FastAPI服务器
│       ├── __init__.py
│       ├── main.py              # 服务器主逻辑
│       ├── dbmodel.py           # 数据库模型
│       ├── webmodel.py          # API数据模型
│       ├── log.py               # 日志配置
│       ├── RSAKeyManager.py     # RSA加密管理
│       ├── test_api.py          # API测试脚本
│       ├── private_key.pem      # RSA私钥
│       └── public_key.pem       # RSA公钥
├── .env                         # 环境变量配置
├── .env.dev                     # 开发环境配置
├── .env.prod                    # 生产环境配置
├── pyproject.toml               # 项目配置
├── start_bot_fixed.py           # 🤖 机器人启动脚本
└── README.md                    # 项目文档
```

## 🚀 启动指南

> 在这之前你需要安装`uv`

>> 环境配置
```.env
DRIVER=~fastapi+~httpx
DEBUG_MODE=True
LOG_LEVEL=DEBUG
DRIVER=~fastapi+~httpx
HOST=0.0.0.0  # 配置 NoneBot 监听的 IP / 主机名
PORT=8080  # 配置 NoneBot 监听的端口
COMMAND_START=["/"]  # 配置命令起始字符
COMMAND_SEP=["."]  # 配置命令分割字符
telegram_bots = [{"token": "telegram_bot_token"}]
telegram_proxy = "http://host:prot" #nonebot-tg-proxy
DATABASE_URI = "mysql+pymysql://user:passwd@host:prot/sqlname?charset=utf8mb4"
# DATABASE_URI = "sqlite:///data.db"
```

### 1. 安装依赖
```bash
uv sync
```

### 2. 配置环境变量
复制并修改环境变量文件：
```bash
cp .env.dev .env
# 编辑 .env 文件，配置数据库连接等
```

### 3. 启动NoneBot机器人
```bash
nb run --reload
```

### 4. 启动FastAPI服务器
```bash
uv run .\server\main.py
```

## 💾 数据库配置

项目使用共享数据库模块，支持统一配置：

```bash
# 设置数据库URI
export DATABASE_URI="mysql+pymysql://user:password@host:port/database"
```

## 🔧 核心特性

### 共享数据库模块
- ✅ **统一模型**: `AlipayUser`, `Device`, `TgUser`
- ✅ **类型安全**: 两个服务使用相同的数据库定义
- ✅ **易维护**: 数据库变更只需修改一处
- ✅ **配置统一**: 通过环境变量管理数据库连接

### NoneBot插件
- 🤖 Telegram Bot支持
- 🔑 授权码生成和管理
- 📱 设备绑定功能
- 👤 用户信息同步

### FastAPI服务器
- 🔐 安全API（RSA加密通信）
- 📊 数据验证和Token管理
- 🛡️ 防重放攻击
- 📝 详细日志记录

## 📚 开发指南

### 添加新数据库字段
1. 在 `src/shared/database.py` 中修改ORM模型
2. 两个服务自动使用新的字段定义
3. 运行数据库迁移（如果需要）

### 添加新API端点
1. 在 `src/server/main.py` 中添加路由
2. 在 `src/server/webmodel.py` 中定义数据模型
3. 使用共享数据库进行数据操作

### 添加新机器人命令
1. 在 `src/bot/plugins/sesame/__init__.py` 中添加命令处理
2. 使用共享数据库进行数据操作

## 🔒 安全特性

- RSA加密通信
- 请求签名验证
- 时间戳防重放
- HMAC-SHA256签名

## 📄 许可证

[MIT Non-Commercial License](./LICENSE)