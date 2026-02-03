import asyncio
import random
from typing import Callable, Any, TypeVar
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable,
    *args,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    **kwargs
) -> Any:
    """
    带指数退避的重试机制

    Args:
        func: 异步函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动

    Returns:
        函数执行结果

    Raises:
        最后一次尝试的异常
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(f"重试失败 (已尝试 {max_retries + 1} 次): {e}")
                raise

            # 计算延迟时间
            delay = min(
                initial_delay * (exponential_base ** attempt),
                max_delay
            )

            if jitter:
                delay *= (0.5 + random.random())

            logger.warning(
                f"重试 {attempt + 1}/{max_retries} "
                f"(延迟 {delay:.1f}s): {type(e).__name__}: {e}"
            )

            await asyncio.sleep(delay)

    raise last_exception
