"""
企业微信签名验证与消息解密

- verify_signature: 校验回调请求签名（SHA1）
- decrypt_message: AES-256-CBC 解密企业微信加密消息
"""
import base64
import hashlib
import struct
import xml.etree.ElementTree as ET
from typing import Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def verify_signature(token: str, timestamp: str, nonce: str, signature: str) -> bool:
    """校验企业微信回调签名（SHA1）"""
    parts = sorted([token, timestamp, nonce])
    digest = hashlib.sha1("".join(parts).encode()).hexdigest()
    return digest == signature


def decrypt_message(encrypt_msg: str, encoding_aes_key: str, corp_id: str) -> Optional[str]:
    """
    解密企业微信加密消息

    企业微信 AES 加密格式（解密后明文）：
      [16B random] + [4B msg_len(BE)] + [msg] + [corp_id] + [PKCS7 padding]
    """
    aes_key = base64.b64decode(encoding_aes_key + "=")
    ciphertext = base64.b64decode(encrypt_msg)

    cipher = Cipher(
        algorithms.AES(aes_key),
        modes.CBC(aes_key[:16]),
        backend=default_backend(),
    )
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    # 去掉 PKCS7 padding
    pad_len = plaintext[-1]
    plaintext = plaintext[:-pad_len]

    # 跳过前 16 字节随机串，读取消息长度
    msg_len = struct.unpack(">I", plaintext[16:20])[0]
    msg_content = plaintext[20: 20 + msg_len].decode("utf-8")

    # 校验 corp_id
    from_corp_id = plaintext[20 + msg_len:].decode("utf-8")
    if from_corp_id != corp_id:
        raise ValueError(f"corp_id 不匹配: expected={corp_id}, got={from_corp_id}")

    return msg_content


def parse_xml_message(xml_str: str) -> dict:
    """解析企业微信消息 XML，返回字段字典"""
    root = ET.fromstring(xml_str)
    result = {}
    for child in root:
        text = child.text or ""
        # 去掉 CDATA 包裹
        result[child.tag] = text.strip()
    return result
