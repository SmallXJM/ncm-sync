"""
简化的 Service 装饰器系统（统一版）

专为单实例 NAS 服务设计的 Cookie 管理装饰器
"""

import functools
import logging
from typing import Callable, Optional
from . import get_cookie_manager
from ncm.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


# =========================
# 核心执行逻辑（唯一入口）
# =========================
async def _execute_with_cookie(
    func: Callable,
    *args,
    retries: int = 0,
    manual: bool = False,
    **kwargs
):
    cookie_service = get_cookie_manager()
    last_exception: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            # 自动注入 Cookie（若调用方未显式传入）
            # if not kwargs.get("cookie"):
            session = cookie_service.get_current_session()
            if not session:
                raise AuthenticationError("没有可用的登录会话，请先登录")
            kwargs["cookie"] = session.cookie
            kwargs["_session"] = session.to_dict()

            result = await func(*args, **kwargs)

            # 手动模式：期望返回 (result, success)
            if manual:
                if isinstance(result, tuple) and len(result) == 2:
                    actual_result, success = result
                    if success:
                        await cookie_service.mark_cookie_success()
                    else:
                        await cookie_service.mark_cookie_failure()
                    return actual_result
                return result

            # 自动模式：成功即标记成功
            await cookie_service.mark_cookie_success()
            return result

        except Exception as e:
            last_exception = e

            if _is_auth_error(e):
                logger.warning(
                    f"认证失败 (尝试 {attempt + 1}/{retries + 1}): {str(e)}"
                )
                await cookie_service.mark_cookie_failure()

                # 还有重试机会则继续
                if attempt < retries:
                    logger.info("准备重试，尝试使用新的 Cookie")
                    continue

            # 非认证错误或重试次数用尽
            raise

    # 理论上不会走到这里
    raise last_exception


# =========================
# 统一装饰器：with_cookie
# =========================
def with_cookie(
    _func: Optional[Callable] = None,
    *,
    max_retries: int = 0,
    manual: bool = False,
):
    """
    统一的 Cookie 装饰器

    使用方式：
        @with_cookie
        @with_cookie()
        @with_cookie(max_retries=2)
        @with_cookie(manual=True)

    Args:
        max_retries: 认证失败时最大重试次数，0 表示不重试
        manual: 是否启用手动 Cookie 成功/失败管理
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await _execute_with_cookie(
                func,
                *args,
                retries=max_retries,
                manual=manual,
                **kwargs
            )
        return wrapper

    # 支持 @with_cookie 直接使用
    if _func is not None:
        return decorator(_func)

    return decorator


# =========================
# 认证错误判断
# =========================
def _is_auth_error(exception: Exception) -> bool:
    """
    判断是否是认证相关错误
    """
    if isinstance(exception, AuthenticationError):
        return True

    error_msg = str(exception).lower()
    auth_keywords = [
        "unauthorized", "401", "authentication", "login", "cookie",
        "需要登录", "登录失效", "会话过期", "未登录"
    ]

    return any(keyword in error_msg for keyword in auth_keywords)
