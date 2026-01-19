"""Encryption utilities for NCM API.

This module implements the encryption algorithms used by Netease Cloud Music API,
including AES, RSA encryption compatible with the original Node.js implementation.
"""

import json
import hashlib
import random
import string
from typing import Dict, Any, Union
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Util.Padding import pad, unpad
from Crypto.Util.number import bytes_to_long, long_to_bytes
import base64

from .options import CryptoType
from ncm.client.exceptions import EncryptionError

# Constants from original implementation
IV = b'0102030405060708'
PRESET_KEY = b'0CoJUm6Qyw8W8jud'
LINUXAPI_KEY = b'rFgB&h#%2?^eDg:Q'
EAPI_KEY = b'e82ckenh8dichen8'
BASE62_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

# RSA Public Key
RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDgtQn2JZ34ZC28NWYpAUd98iZ37BUrX/aKzmFbt7clFSs6sXqHauqKWqdtLkF2KexO40H1YTX8z2lSgBBOAxLsvaklV8k4cBFK9snQXE9/DDaFt6Rr7iVZMldczhC0JNgTz+SHXT6CBHuX3e9SdB1Ua44oncaTWz7OBGLbCiK45wIDAQAB
-----END PUBLIC KEY-----"""


def _generate_random_string(length: int = 16) -> str:
    """Generate random string for encryption key."""
    return ''.join(random.choice(BASE62_CHARS) for _ in range(length))


def _aes_encrypt(text: str, key: bytes, iv: bytes, mode: int = AES.MODE_CBC) -> str:
    """AES encryption with PKCS7 padding."""
    try:
        cipher = AES.new(key, mode, iv if mode == AES.MODE_CBC else None)
        padded_text = pad(text.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_text)
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        raise EncryptionError(f"AES encryption failed: {str(e)}")


# 调整后的低级 AES 加密函数
def _aes_encrypt_weapi(data_bytes: bytes, key: bytes, iv: bytes, mode: int = AES.MODE_CBC) -> str:
    """
    AES 加密函数，直接接收 bytes 类型数据进行加密。
    使用 PKCS7 填充，并 Base64 编码输出。
    """
    try:
        cipher = AES.new(key, mode, iv)
        # 1. PKCS7 填充
        padded_data = pad(data_bytes, AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        raise EncryptionError(f"AES encryption failed: {str(e)}")


def _aes_encrypt_ecb_hex(text: str, key: bytes) -> str:
    """AES ECB encryption returning hex string."""
    try:
        cipher = AES.new(key, AES.MODE_ECB)
        padded_text = pad(text.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_text)
        return encrypted.hex().upper()
    except Exception as e:
        raise EncryptionError(f"AES ECB encryption failed: {str(e)}")


def _aes_decrypt_ecb_hex(ciphertext: str, key: bytes) -> str:
    """AES ECB decryption from hex string."""
    try:
        cipher = AES.new(key, AES.MODE_ECB)
        encrypted_data = bytes.fromhex(ciphertext)
        decrypted = cipher.decrypt(encrypted_data)
        unpadded = unpad(decrypted, AES.block_size)
        return unpadded.decode('utf-8')
    except Exception as e:
        raise EncryptionError(f"AES ECB decryption failed: {str(e)}")


def _aes_decrypt_ecb(encrypted_data: bytes, key: bytes) -> str:
    """AES ECB decryption from hex string."""
    try:
        cipher = AES.new(key, AES.MODE_ECB)
        decrypted = cipher.decrypt(encrypted_data)
        unpadded = unpad(decrypted, AES.block_size)
        return unpadded.decode('utf-8')
    except Exception as e:
        raise EncryptionError(f"AES ECB decryption failed: {str(e)}")


def _rsa_encrypt(text: str, public_key: str) -> str:
    """RSA encryption with public key."""
    try:
        key = RSA.import_key(public_key)
        cipher = PKCS1_v1_5.new(key)
        encrypted = cipher.encrypt(text.encode('utf-8'))
        return encrypted.hex()
    except Exception as e:
        raise EncryptionError(f"RSA encryption failed: {str(e)}")


# 💡 对照 JavaScript forge.util.bytesToHex(encrypted)
# forge 内部通常使用 Latin-1 编码处理输入字符串
def _rsa_encrypt_raw_forge_style(text: str, public_key_pem: str) -> str:
    """
    对照 node-forge 的 rsaEncrypt 函数（使用 'NONE' 无填充模式）。

    警告: 这种模式（原始/无填充 RSA）是极度不安全的。
    """
    try:
        # 1. 导入密钥
        key = RSA.import_key(public_key_pem)

        # 2. 对照 forge: 字符串输入和编码处理
        # forge.encrypt 默认将 string 转换为 Latin-1 字节
        # 我们在这里使用 Latin-1 (iso-8859-1) 确保最大兼容性
        data = text.encode('iso-8859-1')

        # 3. 检查数据长度 (原始 RSA 需要输入小于模长)
        if len(data) >= key.size_in_bytes():
            raise ValueError("Input data size is too large for raw RSA.")

        # 4. 执行原始 RSA 加密 (Raw RSA)
        # 将字节串转换为长整数 M
        M = bytes_to_long(data)

        # 加密: C = M^e mod n
        # 'n' 是模数, 'e' 是公钥指数
        C = pow(M, key.e, key.n)

        # 5. 对照 forge: 输出处理
        # 将结果长整数 C 转换为定长的字节串
        # long_to_bytes 确保输出字节长度等于密钥长度
        encrypted_bytes = long_to_bytes(C, key.size_in_bytes())

        # 6. 对照 forge.util.bytesToHex()
        return encrypted_bytes.hex()

    except Exception as e:
        # 使用自定义错误与原 Python 代码风格保持一致
        raise EncryptionError(f"Raw RSA encryption failed: {str(e)}")


def encrypt_weapi(data: Dict[str, Any]) -> Dict[str, str]:
    """
    WEAPI encryption (Web API).
    
    Uses double AES encryption with random key + RSA encryption for key.
    This is the default encryption method for web requests.
    """
    try:
        text = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

        # print(text)

        # Generate random 16-character secret key
        secret_key = _generate_random_string(16)

        # First AES encryption with preset key
        first_encrypted = _aes_encrypt_weapi(text.encode('utf-8'), PRESET_KEY, IV)

        # Second AES encryption with random secret key
        second_encrypted = _aes_encrypt_weapi(first_encrypted.encode('utf-8'), secret_key.encode('utf-8'), IV)

        # RSA encrypt the reversed secret key
        reversed_key = secret_key[::-1]
        encrypted_key = _rsa_encrypt_raw_forge_style(reversed_key, RSA_PUBLIC_KEY)

        return {
            'params': second_encrypted,
            'encSecKey': encrypted_key
        }
    except Exception as e:
        raise EncryptionError(f"WEAPI encryption failed: {str(e)}")


def encrypt_linuxapi(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Linux API encryption.
    
    Uses AES ECB encryption with fixed key.
    Used for Linux client API requests.
    """
    try:
        text = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        encrypted = _aes_encrypt_ecb_hex(text, LINUXAPI_KEY)

        return {
            'eparams': encrypted
        }
    except Exception as e:
        raise EncryptionError(f"Linux API encryption failed: {str(e)}")


def encrypt_eapi(url: str, data: Dict[str, Any]) -> Dict[str, str]:
    """
    EAPI encryption (Enhanced API).
    
    Uses AES ECB encryption with MD5 digest for integrity.
    Used for mobile client API requests.
    """
    try:
        text = json.dumps(data, separators=(',', ':'), ensure_ascii=False) if isinstance(data, dict) else str(data)

        # Create message for MD5 hash
        message = f"nobody{url}use{text}md5forencrypt"
        digest = hashlib.md5(message.encode('utf-8')).hexdigest()

        # Create data string with digest
        data_string = f"{url}-36cd479b6b5-{text}-36cd479b6b5-{digest}"

        # AES ECB encryption
        encrypted = _aes_encrypt_ecb_hex(data_string, EAPI_KEY)

        return {
            'params': encrypted
        }
    except Exception as e:
        raise EncryptionError(f"EAPI encryption failed: {str(e)}")


def decrypt_eapi_response(encrypted_data: Union[str, bytes]) -> Dict[str, Any]:
    """
    Decrypt EAPI response.
    
    Decrypts encrypted response data from EAPI endpoints.
    """
    try:
        if isinstance(encrypted_data, str):
            en_data = bytes.fromhex(encrypted_data)
        else:
            en_data = encrypted_data
        decrypted = _aes_decrypt_ecb(en_data, EAPI_KEY)
        return json.loads(decrypted)
    except Exception as e:
        raise EncryptionError(f"EAPI response decryption failed: {str(e)}")


def get_crypto_function(crypto_type: CryptoType):
    """Get encryption function by type."""
    crypto_map = {
        CryptoType.WEAPI: encrypt_weapi,
        CryptoType.LINUXAPI: encrypt_linuxapi,
        CryptoType.EAPI: encrypt_eapi,
        CryptoType.API: lambda data: data  # No encryption for API
    }

    return crypto_map.get(crypto_type)


# Utility functions for compatibility
def md5_hash(text: str) -> str:
    """Generate MD5 hash."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def generate_device_id() -> str:
    """Generate random device ID."""
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(32))
