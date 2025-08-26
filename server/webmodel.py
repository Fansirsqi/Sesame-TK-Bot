from pydantic import BaseModel
from typing import Optional


# =======================
# FastAPI Models
# =======================
class VerifyRequest(BaseModel):
    device_id: Optional[str] = None
    alipay_id: Optional[str] = None


class VerifyResponse(BaseModel):
    """验证响应模型"""

    status: int  # 100 成功,200 失败,300 设备被禁用,400 用户被禁用
    "响应状态码"
    message: str
    "响应消息"
    token: Optional[str] = None
    "用户Token"
    data: Optional[dict] = None
    "响应数据"


class TokenRequest(BaseModel):
    """Token模型"""

    device_id: str
    "设备ID"
    alipay_id: Optional[str] = None
    """用户ID"""


class EncryptedRequest(BaseModel):
    """加密请求数据结构"""

    key: str
    "RSA加密后的AES密钥(base64)"
    data: str
    "AES加密后的数据(base64)"
    iv: str
    "AES初始化向量(base64)"
    tag: str
    "GCM认证标签(base64)"
    ts: int
    "时间戳(用于防重放)"
    sig: str
    "请求签名"


class EncryptedResponse(BaseModel):
    """加密响应数据结构"""

    iv: str
    "AES初始化向量(base64)"
    data: str
    "AES加密后的数据(base64)"
    tag: str
    "GCM认证标签(base64)"
