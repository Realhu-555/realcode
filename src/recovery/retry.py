"""错误恢复：指数退避重试

原则:
- 只对"可重试错误"重试（网络抖动、超时、5xx、限流）
- 4xx 业务错误不重试（重试无意义，还烧钱）
- 指数退避 + 抖动，避免重试风暴
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def is_retryable_openai_error(exc: Exception) -> bool:
    """判断 OpenAI/DeepSeek SDK 异常是否值得重试

    可重试:
    - 网络层错误（连接失败、超时）
    - 5xx（服务端临时故障）
    - 429（限流）
    不可重试:
    - 4xx（参数错误、鉴权失败等——重试无意义）
    """
    status = getattr(exc, "status_code", None)
    if status is not None:
        try:
            code = int(status)
            return 500 <= code < 600 or code == 429
        except (TypeError, ValueError):
            pass
    name = type(exc).__name__.lower()
    if "connection" in name or "timeout" in name:
        return True
    msg = str(exc).lower()
    return any(k in msg for k in ("connection", "timeout", "rate limit", "temporarily", "overloaded"))


def retry_call(
    fn: Callable[..., T],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
    jitter: float = 0.5,
    retryable: Callable[[Exception], bool] | None = None,
    on_retry: Callable[[int, float, Exception], None] | None = None,
    **kwargs: Any,
) -> T:
    """同步指数退避重试包装

    Args:
        fn: 要调用的函数
        max_retries: 最大重试次数（默认 3）
        base_delay: 首次重试延迟（秒）
        max_delay: 最大延迟上限
        jitter: 随机抖动上限（秒）
        retryable: 自定义"是否可重试"判断；None 时全部异常都可重试
        on_retry: 每次重试前的回调 (attempt, delay, exc)

    Returns:
        函数成功返回的结果

    Raises:
        最后一次尝试的异常（重试耗尽）
    """
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt >= max_retries:
                raise
            if retryable is not None and not retryable(e):
                raise
            delay = min(max_delay, base_delay * (2 ** attempt)) + random.uniform(0, jitter)
            if on_retry is not None:
                on_retry(attempt, delay, e)
            time.sleep(delay)
            attempt += 1
