import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi import HTTPException
from log import logger
from webmodel import EncryptedRequest

# 签名密钥（应从环境变量获取）
SIGNATURE_KEY = os.getenv("SECURITY_SIGNATURE_KEY", "sesame-fansirsqi-byseven-2025")


class RSAKeyManager:
    def __init__(self, private_key_path: str = "./server/private_key.pem", public_key_path: str = "./server/public_key.pem"):
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self.private_key = None
        self.public_key = None
        self.load_or_generate_keys()

    def load_or_generate_keys(self):
        # 如果密钥文件存在，加载它们
        if os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path):
            with open(self.private_key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
            with open(self.public_key_path, "rb") as f:
                self.public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
        else:
            # 生成新的RSA密钥对
            self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
            self.public_key = self.private_key.public_key()

            # 保存私钥
            pem = self.private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
            with open(self.private_key_path, "wb") as f:
                f.write(pem)

            # 保存公钥
            pem = self.public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
            with open(self.public_key_path, "wb") as f:
                f.write(pem)

    def get_public_key_pem(self) -> str:
        """获取PEM格式的公钥，用于Xposed模块"""
        pem = self.public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
        return pem.decode("utf-8")

    def decrypt_aes_key(self, encrypted_key: bytes) -> bytes:
        """使用私钥解密AES密钥"""
        return self.private_key.decrypt(encrypted_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))

    def encrypt_response(self, data: Dict[str, Any], aes_key: bytes) -> Dict[str, str]:
        """使用AES密钥加密响应数据"""
        iv = os.urandom(12)  # GCM标准IV长度
        encryptor = Cipher(algorithms.AES(aes_key), modes.GCM(iv), backend=default_backend()).encryptor()

        # 添加时间戳防止重放攻击
        data["ts"] = int(time.time())
        data_bytes = json.dumps(data).encode("utf-8")
        ciphertext = encryptor.update(data_bytes) + encryptor.finalize()

        return {"iv": base64.b64encode(iv).decode("utf-8"), "data": base64.b64encode(ciphertext).decode("utf-8"), "tag": base64.b64encode(encryptor.tag).decode("utf-8")}


def verify_request_signature(request_data: Dict[str, Any], signature_key: str) -> bool:
    """验证请求签名"""
    # 构建签名数据（按字段名排序以确保一致性）
    sig_data = request_data.get("key", "") + request_data.get("data", "") + request_data.get("iv", "") + request_data.get("tag", "") + str(request_data.get("ts", 0))

    expected_sig = hmac.new(key=signature_key.encode(), msg=sig_data.encode(), digestmod=hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_sig, request_data.get("sig", ""))


def decrypt_request(encrypted_request: EncryptedRequest, rsa_manager: RSAKeyManager) -> tuple[Dict[str, Any], bytes]:
    """解密客户端请求，并返回解密后的数据和AES密钥"""
    try:
        # 1. 验证时间戳（防止重放攻击，允许5分钟内的时间差）
        current_time = int(time.time())
        if abs(current_time - encrypted_request.ts) > 300:
            logger.warning(f"重放攻击检测: 时间差 {abs(current_time - encrypted_request.ts)} 秒")
            raise HTTPException(status_code=401, detail="请求已过期")

        # 2. 验证签名
        request_dict = encrypted_request.dict()
        if not verify_request_signature(request_dict, SIGNATURE_KEY):
            logger.warning("请求签名验证失败")
            raise HTTPException(status_code=401, detail="请求签名无效")

        # 3. 解密AES密钥
        encrypted_key = base64.b64decode(encrypted_request.key)
        aes_key = rsa_manager.decrypt_aes_key(encrypted_key)

        # 4. 解密数据
        iv = base64.b64decode(encrypted_request.iv)
        ciphertext = base64.b64decode(encrypted_request.data)
        tag = base64.b64decode(encrypted_request.tag)

        decryptor = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag), backend=default_backend()).decryptor()

        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
        return json.loads(decrypted_data.decode("utf-8")), aes_key

    except Exception as e:
        logger.error(f"请求解密失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"请求解密失败:{e}")
