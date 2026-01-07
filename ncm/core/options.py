"""Data models for NCM API."""

from enum import Enum
from typing import Optional, Dict, Any, Union, List
from dataclasses import dataclass, field
import json


class CryptoType(Enum):
    """Encryption types supported by NCM API."""
    WEAPI = "weapi"
    EAPI = "eapi"
    LINUXAPI = "linuxapi"
    API = "api"


class OSType(Enum):
    """Operating system types."""
    PC = "pc"
    LINUX = "linux"
    ANDROID = "android"
    IPHONE = "iphone"


@dataclass
class RequestOptions:
    """Options for API requests."""

    # Encryption settings
    crypto: Optional[CryptoType] = CryptoType.EAPI  # Should be set by API module, not default
    encrypt_response: bool = True

    # Authentication
    cookie: Optional[Union[str, Dict[str, str]]] = None

    # Network settings
    proxy: Optional[str] = None
    real_ip: Optional[str] = None
    random_cn_ip: bool = False
    user_agent: Optional[str] = None

    # Device settings
    os_type: OSType = OSType.PC
    device_id: Optional[str] = None

    # Headers
    headers: Dict[str, str] = field(default_factory=dict)

    # Other options
    check_token: bool = False
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "crypto": self.crypto.value,
            "encrypt_response": self.encrypt_response,
            "cookie": self.cookie,
            "proxy": self.proxy,
            "real_ip": self.real_ip,
            "random_cn_ip": self.random_cn_ip,
            "user_agent": self.user_agent,
            "os_type": self.os_type.value,
            "device_id": self.device_id,
            "headers": self.headers,
            "check_token": self.check_token,
            "timeout": self.timeout
        }


@dataclass
class APIResponse:
    """Response from NCM API."""

    status: int
    body: Dict[str, Any]
    cookies: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)

    @property
    def code(self) -> int:
        """Get response code from body or status."""
        return self.body.get("code", self.status)

    @property
    def message(self) -> str:
        """Get response message."""
        return self.body.get("message", self.body.get("msg", ""))

    @property
    def data(self) -> Any:
        """Get response data."""
        return self.body.get("data", self.body)

    @property
    def success(self) -> bool:
        """Check if request was successful."""
        return self.code == 200

    @property
    def body_json(self) -> str:
        """Check if request was successful."""
        return self.get_body_json()

    def get_body_json(self, indent=None) -> str:
        return json.dumps(self.body, ensure_ascii=False, indent=indent)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "body": self.body,
            "cookies": self.cookies,
            "headers": self.headers
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

def _create_options(
        crypto: Optional[CryptoType] = None,
        **kwargs
) -> RequestOptions:
    """Create RequestOptions with defaults."""
    # 1. 从 **kwargs (即 query) 中提取所需的值
    # 2. 使用 .get() 方法安全地访问字典，如果键不存在则返回 None
    # 3. 使用 or 逻辑实现和 JavaScript 类似的“如果左侧为空则使用右侧”的逻辑

    # 获取 crypto 的值：
    # 优先级：传入的 crypto 参数 > kwargs['crypto'] > 默认空字符串 ''
    option_crypto = crypto
    if not option_crypto:
        option_crypto = kwargs.get('crypto', CryptoType.EAPI)

    # 获取 e_r 的值：
    # 优先级：kwargs['e_r'] > 默认值 None (相当于 JavaScript 的 undefined)
    e_r_value = kwargs.get('encrypt_response', None)

    return RequestOptions(
        crypto=option_crypto,
        encrypt_response=e_r_value if e_r_value is not None else True,
        cookie=kwargs.get('cookie'),
        proxy=kwargs.get('proxy'),
        real_ip=kwargs.get('real_ip'),
        random_cn_ip=kwargs.get('random_cn_ip', False),
        user_agent=kwargs.get('user_agent'),
        os_type=kwargs.get('os_type', OSType.PC),
        device_id=kwargs.get('device_id'),
        headers=kwargs.get('headers', {}),
        check_token=kwargs.get('check_token', False),
        timeout=kwargs.get('timeout', 30)
    )