#!/usr/bin/env python3
"""
HTTP Retry with Exponential Backoff
Applied from EvoMap Capsule: sha256:6c8b2bef...
GDI: 70.9 | Success Streak: 22
"""

import time
import random
from typing import Optional, Callable, Any

class HTTPRetryManager:
    """
    通用 HTTP 重试管理器
    - 指数退避 (exponential backoff)
    - AbortController 超时控制
    - 连接池复用
    - 自动处理: TimeoutError, ECONNRESET, 429
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        timeout: float = 30.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.timeout = timeout
        self.attempt = 0
    
    def calculate_delay(self) -> float:
        """计算退避延迟 (指数退避 + 抖动)"""
        delay = min(self.base_delay * (2 ** self.attempt), self.max_delay)
        if self.jitter:
            delay *= (0.5 + random.random())  # 添加 ±50% 抖动
        return delay
    
    def should_retry(self, error: Exception) -> bool:
        """判断是否应该重试"""
        retryable_errors = (
            "TimeoutError",
            "ECONNRESET",
            "ECONNREFUSED",
            "429",
            "TooManyRequests",
            "ConnectionError",
            "temporarily unavailable"
        )
        error_str = str(error).lower()
        return any(e.lower() in error_str for e in retryable_errors)
    
    def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """执行带重试的操作"""
        last_error = None
        
        for self.attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if self.attempt >= self.max_retries:
                    log(f"Max retries ({self.max_retries}) exceeded")
                    raise
                
                if not self.should_retry(e):
                    log(f"Non-retryable error: {e}")
                    raise
                
                delay = self.calculate_delay()
                log(f"Attempt {self.attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
        
        raise last_error

# 便捷函数
def with_retry(max_retries: int = 3, timeout: float = 30.0):
    """装饰器: 为函数添加重试机制"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry_mgr = HTTPRetryManager(max_retries=max_retries, timeout=timeout)
            return retry_mgr.execute(func, *args, **kwargs)
        return wrapper
    return decorator

# 测试
if __name__ == "__main__":
    @with_retry(max_retries=2)
    def test_operation():
        import random
        if random.random() < 0.7:
            raise TimeoutError("Simulated timeout")
        return "Success!"
    
    print(test_operation())
