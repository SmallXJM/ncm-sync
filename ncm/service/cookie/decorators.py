"""
Cookie session decorators.

Provides a single `with_cookie` decorator for injecting the current NetEase
Cloud Music session and handling retry/failure bookkeeping.
"""

import functools
import logging
from typing import Callable, Optional

from . import get_cookie_manager
from ncm.client.exceptions import AuthenticationError, MusicSessionUnavailableError

logger = logging.getLogger(__name__)


async def _execute_with_cookie(
    func: Callable,
    *args,
    retries: int = 0,
    manual: bool = False,
    **kwargs,
):
    cookie_service = get_cookie_manager()
    last_exception: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            # 尝试获取当前会话
            current_session = await cookie_service.get_current_session()

            # 自动注入 Cookie（若调用方未显式传入）
            if not kwargs.get("cookie"):
                if not current_session:
                    raise MusicSessionUnavailableError(
                        "没有可用的网易云音乐登录会话，请先登录",
                        code=401,
                        details={"reason": "no_current_session"},
                    )
                kwargs["cookie"] = current_session.cookie
                kwargs["_session"] = current_session.to_dict()
            # 即使调用方显式传入了 cookie，也尽量补充当前会话信息，
            # 避免依赖 _session 的下游 controller 出现 KeyError。
            elif current_session and "_session" not in kwargs:
                kwargs["_session"] = current_session.to_dict()

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

                # 认证类错误重试用尽：统一转换为领域异常，
                # 由上层 HTTP 框架决定如何映射为接口响应。
                if isinstance(e, MusicSessionUnavailableError):
                    raise

                raise MusicSessionUnavailableError(
                    str(e) or "网易云音乐登录会话已过期，请重新登录",
                    code=401,
                    details={"reason": "auth_failed"},
                ) from e

            # 非认证错误
            raise

    # 理论上不会走到这里
    raise last_exception


def with_cookie(
    _func: Optional[Callable] = None,
    *,
    max_retries: int = 0,
    manual: bool = False,
):
    """Inject current cookie session and handle auth failure bookkeeping."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await _execute_with_cookie(
                func,
                *args,
                retries=max_retries,
                manual=manual,
                **kwargs,
            )

        return wrapper

    if _func is not None:
        return decorator(_func)

    return decorator


def _is_auth_error(exception: Exception) -> bool:
    """Return True when the exception indicates music-session auth failure."""

    if isinstance(exception, AuthenticationError):
        return True

    error_msg = str(exception).lower()
    auth_keywords = [
        "unauthorized",
        "401",
        "authentication",
        "login",
        "cookie",
        "需要登录",
        "登录失效",
        "会话过期",
        "未登录",
    ]

    return any(keyword in error_msg for keyword in auth_keywords)
