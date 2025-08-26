import re
import os
from fastapi import FastAPI, Depends, HTTPException, Body, APIRouter
from sqlalchemy.orm import Session
from uuid import uuid4
from log import configure_logging, logger
import time

from dbmodel import AlipayUser, get_db, Device, TgUser
from webmodel import EncryptedRequest, EncryptedResponse, VerifyRequest, VerifyResponse, TokenRequest
from RSAKeyManager import RSAKeyManager, decrypt_request
from dotenv import load_dotenv

# 优先加载环境变量，确保后续代码能正确读取
load_dotenv(override=True, dotenv_path="./.env")

# 在所有日志记录之前初始化日志配置
configure_logging()

# 全局变量
rsa_manager: RSAKeyManager

# 调试路由
debug_router = APIRouter()


async def lifespan(app: FastAPI):
    # 应用启动时执行
    global rsa_manager
    rsa_manager = RSAKeyManager()

    # 根据环境变量决定是否加载调试接口
    if os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t"):
        logger.warning("调试模式已开启 ⚠️")
        app.include_router(debug_router, prefix="/api/debug", tags=["Debug"])
    else:
        logger.success("调试模式已关闭 ✅")

    yield
    # 可选：应用关闭时执行


app = FastAPI(
    lifespan=lifespan,
    # docs_url=None,
    # redoc_url=None,
)
app.description = "芝麻粒-TK授权码获取接口"


# =======================
# 核心业务逻辑
# =======================
def _verify_logic(verify_request: VerifyRequest, db: Session, authorization: str = None) -> VerifyResponse:
    """核心验证逻辑"""
    # ========== 1. 高级验证（带Token） ==========
    if authorization:
        if not authorization.startswith("Bearer "):
            logger.warning(f"非法请求：[Token格式错误] | Authorization: {authorization}")
            return VerifyResponse(status=202, message="Token格式不正确，必须以Bearer开头")

        token = authorization.replace("Bearer ", "").strip()
        if not token:
            logger.warning(f"非法请求：[Token为空]")
            return VerifyResponse(status=203, message="Token不能为空")

        user = db.query(AlipayUser).filter(AlipayUser.token == token).first()
        if not user:
            logger.warning(f"非法请求：[无效Token] | Token: {token}")
            return VerifyResponse(status=204, message="无效Token")

        if user.device_id != verify_request.device_id:
            logger.warning(f"非法请求：[设备ID不匹配] | 数据库设备ID: {user.device_id}")
            return VerifyResponse(status=205, message="设备ID不匹配")

        if getattr(user, "device_ban", 0) == 1:
            logger.warning(f"设备被禁用请求：[设备已被禁用] | 设备ID: {verify_request.device_id}")
            return VerifyResponse(status=300, message="设备已被禁用")

        if getattr(user, "account_ban", 0) == 1:
            logger.warning(f"账号被禁用请求：[账号已被禁用] | 支付宝ID: {user.alipay_id}")
            return VerifyResponse(status=400, message="账号已被禁用")

        if verify_request.alipay_id and verify_request.alipay_id != user.alipay_id:
            logger.warning(f"非法请求：[账号不匹配] | 数据库账号: {user.alipay_id}")
            return VerifyResponse(status=207, message="账号不匹配")

        logger.info(f"高级验证成功：[设备ID: {verify_request.device_id} | 支付宝ID: {user.alipay_id}]")
        return VerifyResponse(status=100, message="验证成功", token=token, data={"alipay_id": user.alipay_id})

    # ========== 2. 基础验证（无Token） ==========
    else:
        device = db.query(Device).filter(Device.device_id == verify_request.device_id).first()
        if not device:
            return VerifyResponse(status=208, message="请在tg机器人处绑定Verify ID")

        tg_user = db.query(TgUser).filter(TgUser.tg_id == device.tg_id).first()
        if not tg_user:
            return VerifyResponse(status=210, message="设备绑定的TG用户不存在 在机器人处执行/sync 绑定")

        uname = f"@{tg_user.username}" if tg_user.username else f"@{tg_user.first_name or ''} {tg_user.last_name or ''}".strip()
        return VerifyResponse(status=101, message=f"{uname} 欢迎使用!", data={"user": uname})


def _get_token_logic(token_request: TokenRequest, db: Session) -> VerifyResponse:
    """核心获取Token逻辑"""
    if not re.match(r"^[a-zA-Z0-9\-_]{8,64}$", token_request.device_id):
        return VerifyResponse(status=212, message="设备ID格式不正确")
    if not re.match(r"^\d{16}$", token_request.alipay_id):
        return VerifyResponse(status=213, message="支付宝ID必须是16位数字")

    user = db.query(AlipayUser).filter(AlipayUser.device_id == token_request.device_id, AlipayUser.alipay_id == token_request.alipay_id).first()
    if not user:
        return VerifyResponse(status=214, message="设备与支付宝账号不匹配")
    if getattr(user, "device_ban", 0) == 1:
        return VerifyResponse(status=300, message="设备已被禁用")
    if getattr(user, "account_ban", 0) == 1:
        return VerifyResponse(status=400, message="账号已被禁用")

    if not user.token:
        user.token = str(uuid4().hex)
        db.commit()
        logger.info(f"Token生成成功：[设备ID: {token_request.device_id} | 支付宝ID: {token_request.alipay_id}]")

    logger.info(f"Token发放成功：[设备ID: {token_request.device_id} | 支付宝ID: {token_request.alipay_id}]")
    return VerifyResponse(status=100, message="Token获取成功", token=user.token, data={"alipay_id": user.alipay_id})


# =======================
# Public API
# =======================
@app.post("/api/public_key")
async def get_public_key():
    """获取服务端公钥，用于Xposed模块初始化"""
    return {"status": 100, "message": "公钥获取成功", "public_key": rsa_manager.get_public_key_pem(), "timestamp": int(time.time())}


# =======================
# Secure API
# =======================
@app.post("/api/secure/verify", response_model=EncryptedResponse)
async def secure_verify(encrypted_request: EncryptedRequest, db: Session = Depends(get_db)):
    """安全验证API（处理加密请求并返回加密响应）"""
    aes_key = None
    try:
        request_data, aes_key = decrypt_request(encrypted_request, rsa_manager)
        verify_request = VerifyRequest(**request_data)
        authorization = request_data.get("authorization")
        response = _verify_logic(verify_request, db, authorization)
        return rsa_manager.encrypt_response(response.model_dump(exclude_none=True), aes_key)
    except Exception as e:
        logger.error(f"安全验证过程中发生错误: {str(e)} | 请求: {encrypted_request.model_dump_json()}")
        if aes_key:
            response = VerifyResponse(status=500, message="服务器内部错误")
            return rsa_manager.encrypt_response(response.model_dump(exclude_none=True), aes_key)
        raise HTTPException(status_code=400, detail="请求处理失败，无法加密响应")


@app.post("/api/secure/token", response_model=EncryptedResponse)
async def secure_get_token(encrypted_request: EncryptedRequest, db: Session = Depends(get_db)):
    """安全获取Token API（处理加密请求并返回加密响应）"""
    aes_key = None
    try:
        request_data, aes_key = decrypt_request(encrypted_request, rsa_manager)
        token_request = TokenRequest(**request_data)
        response = _get_token_logic(token_request, db)
        return rsa_manager.encrypt_response(response.model_dump(exclude_none=True), aes_key)
    except Exception as e:
        logger.error(f"安全Token获取过程中发生错误: {str(e)} | 请求: {encrypted_request.model_dump_json()}")
        if aes_key:
            response = VerifyResponse(status=500, message="服务器内部错误")
            return rsa_manager.encrypt_response(response.model_dump(exclude_none=True), aes_key)
        raise HTTPException(status_code=400, detail="请求处理失败，无法加密响应")


# =======================
# Debug API
# =======================
@debug_router.post("/verify", response_model=VerifyResponse)
async def debug_verify(verify_request: VerifyRequest, db: Session = Depends(get_db), authorization: str = Body(None, embed=True)):
    """调试验证API（处理明文请求并返回明文响应）"""
    return _verify_logic(verify_request, db, authorization)


@debug_router.post("/token", response_model=VerifyResponse)
async def debug_get_token(token_request: TokenRequest, db: Session = Depends(get_db)):
    """调试获取Token API（处理明文请求并返回明文响应）"""
    return _get_token_logic(token_request, db)


# =======================
# Health Check
# =======================
@app.get("/ping")
async def ping():
    return {"status": "ok"}


if __name__ == "__main__":
    try:
        import uvicorn

        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8008,
            reload=True,
            reload_dirs=[
                "./server",
                "./shared",
                # "./src",
            ],  # 只监控关键源代码目录
        )
    except ImportError:
        logger.info("缺少 uvicorn 依赖，请运行 'pip install uvicorn'")
