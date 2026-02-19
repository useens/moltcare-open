# Lucas - Python Web API 核心代码实现

## 项目结构

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 主应用入口
│   ├── config.py            # 配置文件
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py      # 认证路由
│   │       └── users.py     # 用户路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py      # JWT 认证
│   │   ├── cache.py         # Redis 缓存封装
│   │   └── logging.py       # 日志模块
│   └── schemas/
│       ├── __init__.py
│       └── user.py          # 数据模型
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest 配置
│   └── test_api.py          # API 测试
├── requirements.txt
└── .env
```

---

## 1. FastAPI 基础框架代码

### app/config.py
```python
"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    # 应用配置
    APP_NAME: str = "FastAPI Web API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（缓存）"""
    return Settings()
```

### app/main.py
```python
"""
FastAPI 主应用入口
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.v1 import auth, users
from app.core.logging import setup_logging, get_logger
from app.core.cache import CacheManager

# 设置日志
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"🚀 Starting {get_settings().APP_NAME} v{get_settings().APP_VERSION}")
    
    # 初始化 Redis 连接
    await CacheManager.connect()
    logger.info("✅ Redis connection established")
    
    yield
    
    # 关闭时执行
    await CacheManager.disconnect()
    logger.info("👋 Application shutdown complete")


def create_application() -> FastAPI:
    """创建 FastAPI 应用实例"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="基于 FastAPI 的高性能 Web API",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # 中间件配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 请求日志和计时中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
        return response
    
    # 注册路由
    app.include_router(auth.router, prefix="/api/v1", tags=["认证"])
    app.include_router(users.router, prefix="/api/v1", tags=["用户"])
    
    return app


app = create_application()


@app.get("/")
async def root():
    """根路径 - API 信息"""
    settings = get_settings()
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    redis_status = await CacheManager.health_check()
    return {
        "status": "healthy",
        "redis": "connected" if redis_status else "disconnected",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
```

---

## 2. JWT 认证中间件

### app/core/security.py
```python
"""
JWT 认证与安全工具
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
    
    Returns:
        JWT 令牌字符串
    """
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌"""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码并验证 JWT 令牌
    
    Args:
        token: JWT 令牌字符串
    
    Returns:
        解码后的数据字典，验证失败返回 None
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    获取当前用户（依赖注入）
    
    Args:
        credentials: HTTP 认证凭证
    
    Returns:
        用户数据字典
    
    Raises:
        HTTPException: 认证失败时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception
    
    return {
        "id": user_id,
        "username": payload.get("username"),
        "email": payload.get("email"),
        "roles": payload.get("roles", [])
    }


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前活跃用户"""
    # 这里可以添加用户状态检查逻辑
    return current_user


class PermissionChecker:
    """权限检查装饰器类"""
    
    def __init__(self, required_roles: list):
        self.required_roles = required_roles
    
    def __call__(self, user: Dict[str, Any] = Depends(get_current_user)):
        user_roles = set(user.get("roles", []))
        required = set(self.required_roles)
        
        if not required.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return user


def require_roles(roles: list):
    """角色要求装饰器工厂函数"""
    return PermissionChecker(roles)
```

### app/api/v1/auth.py
```python
"""
认证相关路由
"""
from datetime import timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    get_current_user
)
from app.config import get_settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# 模拟用户数据库（实际项目中使用真实数据库）
FAKE_USERS_DB = {
    "admin": {
        "id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin123"),
        "roles": ["admin", "user"],
        "disabled": False
    },
    "user": {
        "id": "2",
        "username": "user",
        "email": "user@example.com",
        "hashed_password": get_password_hash("user123"),
        "roles": ["user"],
        "disabled": False
    }
}


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TokenRefresh(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class UserCreate(BaseModel):
    """用户创建模型"""
    username: str
    email: str
    password: str


@router.post("/auth/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    用户登录
    
    - 验证用户名密码
    - 返回访问令牌和刷新令牌
    """
    user = FAKE_USERS_DB.get(login_data.username)
    
    if not user or not verify_password(
        login_data.password,
        user["hashed_password"]
    ):
        logger.warning(f"Login failed for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 创建令牌数据
    token_data = {
        "sub": user["id"],
        "username": user["username"],
        "email": user["email"],
        "roles": user["roles"]
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    logger.info(f"User logged in: {user['username']}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/auth/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """
    刷新访问令牌
    
    - 使用刷新令牌获取新的访问令牌
    """
    payload = decode_token(token_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    user_id = payload.get("sub")
    user = next(
        (u for u in FAKE_USERS_DB.values() if u["id"] == user_id),
        None
    )
    
    if not user or user.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 创建新令牌
    new_token_data = {
        "sub": user["id"],
        "username": user["username"],
        "email": user["email"],
        "roles": user["roles"]
    }
    
    return Token(
        access_token=create_access_token(new_token_data),
        refresh_token=create_refresh_token(new_token_data),
        token_type="bearer",
        expires_in=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/auth/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@router.post("/auth/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    用户登出
    
    实际实现中应该将令牌加入黑名单
    """
    logger.info(f"User logged out: {current_user.get('username')}")
    return {"message": "登出成功"}
```

---

## 3. Redis 缓存封装

### app/core/cache.py
```python
"""
Redis 缓存管理器
"""
import json
import pickle
from typing import Optional, Any, Union, List
from datetime import timedelta

import redis.asyncio as redis

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Redis 缓存管理器"""
    
    _instance: Optional[redis.Redis] = None
    _connected: bool = False
    
    @classmethod
    async def connect(cls) -> redis.Redis:
        """
        建立 Redis 连接
        
        Returns:
            Redis 连接实例
        """
        if cls._instance is None:
            settings = get_settings()
            try:
                cls._instance = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False
                )
                await cls._instance.ping()
                cls._connected = True
                logger.info("Redis connected successfully")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                cls._connected = False
                raise
        return cls._instance
    
    @classmethod
    async def disconnect(cls):
        """断开 Redis 连接"""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            cls._connected = False
            logger.info("Redis disconnected")
    
    @classmethod
    async def health_check(cls) -> bool:
        """健康检查"""
        if not cls._instance:
            return False
        try:
            await cls._instance.ping()
            return True
        except:
            return False
    
    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        """获取 Redis 客户端实例"""
        return cls._instance
    
    # ========== 基础操作 ==========
    
    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值或 None
        """
        if not cls._instance:
            return None
        
        try:
            data = await cls._instance.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @classmethod
    async def set(
        cls,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒或 timedelta）
        
        Returns:
            是否设置成功
        """
        if not cls._instance:
            return False
        
        try:
            serialized = pickle.dumps(value)
            
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            
            await cls._instance.set(key, serialized, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @classmethod
    async def delete(cls, key: str) -> bool:
        """删除缓存"""
        if not cls._instance:
            return False
        
        try:
            result = await cls._instance.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    @classmethod
    async def exists(cls, key: str) -> bool:
        """检查键是否存在"""
        if not cls._instance:
            return False
        
        try:
            return await cls._instance.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    @classmethod
    async def expire(cls, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not cls._instance:
            return False
        
        try:
            return await cls._instance.expire(key, seconds)
        except Exception as e:
            logger.error(f"Cache expire error: {e}")
            return False
    
    @classmethod
    async def ttl(cls, key: str) -> int:
        """获取剩余过期时间"""
        if not cls._instance:
            return -2
        
        try:
            return await cls._instance.ttl(key)
        except Exception as e:
            logger.error(f"Cache ttl error: {e}")
            return -2
    
    # ========== 高级操作 ==========
    
    @classmethod
    async def get_or_set(
        cls,
        key: str,
        factory,
        expire: Optional[Union[int, timedelta]] = None
    ) -> Any:
        """
        获取或设置缓存（缓存穿透保护）
        
        Args:
            key: 缓存键
            factory: 数据生成函数
            expire: 过期时间
        
        Returns:
            缓存值
        """
        # 尝试获取缓存
        cached = await cls.get(key)
        if cached is not None:
            return cached
        
        # 生成新数据
        value = await factory() if callable(factory) else factory
        
        # 设置缓存
        await cls.set(key, value, expire)
        
        return value
    
    @classmethod
    async def increment(cls, key: str, amount: int = 1) -> int:
        """原子递增"""
        if not cls._instance:
            return 0
        
        try:
            return await cls._instance.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0
    
    @classmethod
    async def decrement(cls, key: str, amount: int = 1) -> int:
        """原子递减"""
        if not cls._instance:
            return 0
        
        try:
            return await cls._instance.decrby(key, amount)
        except Exception as e:
            logger.error(f"Cache decrement error: {e}")
            return 0
    
    @classmethod
    async def mget(cls, keys: List[str]) -> List[Optional[Any]]:
        """批量获取"""
        if not cls._instance or not keys:
            return [None] * len(keys)
        
        try:
            data_list = await cls._instance.mget(keys)
            return [
                pickle.loads(data) if data else None
                for data in data_list
            ]
        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            return [None] * len(keys)
    
    @classmethod
    async def mset(
        cls,
        mapping: dict,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """批量设置"""
        if not cls._instance:
            return False
        
        try:
            serialized = {
                k: pickle.dumps(v) for k, v in mapping.items()
            }
            await cls._instance.mset(serialized)
            
            # 设置过期时间
            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                for key in mapping.keys():
                    await cls._instance.expire(key, expire)
            
            return True
        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False
    
    @classmethod
    async def delete_pattern(cls, pattern: str) -> int:
        """
        按模式删除键
        
        Args:
            pattern: Redis 模式（如 "user:*"）
        
        Returns:
            删除的键数量
        """
        if not cls._instance:
            return 0
        
        try:
            keys = []
            async for key in cls._instance.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await cls._instance.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete_pattern error: {e}")
            return 0
    
    @classmethod
    async def flush(cls) -> bool:
        """清空所有缓存（谨慎使用）"""
        if not cls._instance:
            return False
        
        try:
            await cls._instance.flushdb()
            logger.warning("Cache flushed")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


# ========== 装饰器 ==========

def cached(
    key_prefix: str,
    expire: Optional[Union[int, timedelta]] = None,
    key_builder = None
):
    """
    缓存装饰器
    
    Args:
        key_prefix: 缓存键前缀
        expire: 过期时间
        key_builder: 自定义键构建函数
    
    Example:
        @cached("user", expire=300)
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            
            # 尝试获取缓存
            cached_value = await CacheManager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 设置缓存
            await CacheManager.set(cache_key, result, expire)
            
            return result
        
        return wrapper
    return decorator


def cache_evict(key_prefix: str, key_builder=None):
    """
    缓存清除装饰器
    
    在函数执行后清除匹配的缓存
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
                await CacheManager.delete(cache_key)
            else:
                await CacheManager.delete_pattern(f"{key_prefix}:*")
            
            return result
        
        return wrapper
    return decorator
```

---

## 4. 日志记录模块

### app/core/logging.py
```python
"""
日志配置与管理
"""
import sys
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from app.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""
    
    # ANSI 颜色码
    COLORS = {
        "DEBUG": "\033[36m",      # 青色
        "INFO": "\033[32m",       # 绿色
        "WARNING": "\033[33m",    # 黄色
        "ERROR": "\033[31m",      # 红色
        "CRITICAL": "\033[35m",   # 紫色
        "RESET": "\033[0m"        # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # 保存原始级别名
        levelname = record.levelname
        
        # 添加颜色
        color = self.COLORS.get(levelname, self.COLORS["RESET"])
        record.levelname = f"{color}{levelname}{self.COLORS['RESET']}"
        
        result = super().format(record)
        
        # 恢复原始级别名
        record.levelname = levelname
        
        return result


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None
) -> None:
    """
    配置日志系统
    
    Args:
        log_level: 日志级别
        log_dir: 日志文件目录
    """
    settings = get_settings()
    level = log_level or settings.LOG_LEVEL
    
    # 创建日志目录
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    console_format = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（JSON 格式）
    if log_dir:
        # 错误日志
        error_file = Path(log_dir) / "error.log"
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_handler)
        
        # 完整日志
        app_file = Path(log_dir) / "app.log"
        app_handler = logging.FileHandler(app_file)
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(app_handler)
    
    # 第三方库日志级别调整
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("redis").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器实例
    
    Args:
        name: 日志器名称
    
    Returns:
        Logger 实例
    """
    return logging.getLogger(name)


class LoggerMixin:
    """日志混入类，为类提供日志功能"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取类日志器"""
        return logging.getLogger(self.__class__.__module__)


class RequestContext:
    """请求上下文日志管理"""
    
    _context: Dict[str, Any] = {}
    
    @classmethod
    def set(cls, key: str, value: Any):
        """设置上下文值"""
        cls._context[key] = value
    
    @classmethod
    def get(cls, key: str, default=None):
        """获取上下文值"""
        return cls._context.get(key, default)
    
    @classmethod
    def clear(cls):
        """清除上下文"""
        cls._context.clear()
    
    @classmethod
    def get_filter_dict(cls) -> Dict[str, Any]:
        """获取过滤器字典"""
        return cls._context.copy()


class ContextFilter(logging.Filter):
    """添加上下文信息的日志过滤器"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加请求上下文到日志记录"""
        context = RequestContext.get_filter_dict()
        
        for key, value in context.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        
        return True


def add_context_filter(logger: logging.Logger):
    """为日志器添加上下文过滤器"""
    context_filter = ContextFilter()
    logger.addFilter(context_filter)
    return logger


# 便捷函数
def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context
):
    """
    带上下文的日志记录
    
    Args:
        logger: 日志器
        level: 日志级别
        message: 日志消息
        **context: 额外的上下文信息
    """
    extra = {}
    for key, value in context.items():
        extra[key] = value
    
    getattr(logger, level.lower())(message, extra=extra)
```

---

## 5. Pytest 测试示例

### tests/conftest.py
```python
"""
Pytest 配置和共享 fixtures
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import create_application
from app.core.security import create_access_token
from app.core.cache import CacheManager


# ========== Fixtures ==========

@pytest.fixture(scope="session")
def app():
    """创建应用实例"""
    return create_application()


@pytest.fixture
def client(app):
    """同步测试客户端"""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(app):
    """异步测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_token():
    """普通用户测试令牌"""
    token_data = {
        "sub": "2",
        "username": "user",
        "email": "user@example.com",
        "roles": ["user"]
    }
    return create_access_token(token_data)


@pytest.fixture
def admin_token():
    """管理员测试令牌"""
    token_data = {
        "sub": "1",
        "username": "admin",
        "email": "admin@example.com",
        "roles": ["admin", "user"]
    }
    return create_access_token(token_data)


@pytest_asyncio.fixture(autouse=True)
async def clean_cache():
    """每个测试前清理缓存"""
    # 清理缓存
    await CacheManager.delete_pattern("test:*")
    yield
    # 测试后清理
    await CacheManager.delete_pattern("test:*")


# ========== 自定义标记 ==========

def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "auth: marks tests as authentication tests")
    config.addinivalue_line("markers", "cache: marks tests as cache tests")


# ========== 共享测试数据 ==========

@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123!"
    }
```

### tests/test_api.py
```python
"""
API 端点测试
"""
import pytest
import pytest_asyncio

from app.core.cache import CacheManager


# ========== 基础测试 ==========

class TestHealthEndpoints:
    """健康检查端点测试"""
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """测试健康检查端点"""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "redis" in data
        assert "timestamp" in data


# ========== 认证测试 ==========

@pytest.mark.auth
class TestAuthEndpoints:
    """认证端点测试"""
    
    def test_login_success(self, client):
        """测试成功登录"""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_failure(self, client):
        """测试登录失败"""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_get_current_user(self, client, test_user_token):
        """测试获取当前用户"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "user"
        assert "id" in data
    
    def test_get_current_user_no_token(self, client):
        """测试无令牌访问"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403
    
    def test_get_current_user_invalid_token(self, client):
        """测试无效令牌"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, async_client, test_user_token):
        """测试刷新令牌"""
        # 先登录获取刷新令牌
        login_response = await async_client.post("/api/v1/auth/login", json={
            "username": "user",
            "password": "user123"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # 使用刷新令牌获取新令牌
        response = await async_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


# ========== 缓存测试 ==========

@pytest.mark.cache
class TestCacheOperations:
    """缓存操作测试"""
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        key = "test:key1"
        value = {"data": "test", "number": 42}
        
        # 设置缓存
        success = await CacheManager.set(key, value, expire=60)
        assert success is True
        
        # 获取缓存
        cached = await CacheManager.get(key)
        assert cached == value
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """测试缓存过期"""
        import asyncio
        
        key = "test:expire"
        value = "temporary"
        
        # 设置 1 秒过期的缓存
        await CacheManager.set(key, value, expire=1)
        
        # 立即获取应该存在
        cached = await CacheManager.get(key)
        assert cached == value
        
        # 等待过期
        await asyncio.sleep(1.5)
        
        # 过期后应该不存在
        cached = await CacheManager.get(key)
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """测试缓存删除"""
        key = "test:delete"
        
        await CacheManager.set(key, "value")
        assert await CacheManager.exists(key) is True
        
        deleted = await CacheManager.delete(key)
        assert deleted is True
        assert await CacheManager.exists(key) is False
    
    @pytest.mark.asyncio
    async def test_cache_increment(self):
        """测试原子递增"""
        key = "test:counter"
        
        # 初始递增
        value = await CacheManager.increment(key, 1)
        assert value == 1
        
        # 再次递增
        value = await CacheManager.increment(key, 5)
        assert value == 6
        
        # 清理
        await CacheManager.delete(key)
    
    @pytest.mark.asyncio
    async def test_cache_get_or_set(self):
        """测试获取或设置"""
        call_count = 0
        
        async def factory():
            nonlocal call_count
            call_count += 1
            return f"computed_{call_count}"
        
        key = "test:get_or_set"
        
        # 第一次调用应该执行工厂函数
        result1 = await CacheManager.get_or_set(key, factory, expire=60)
        assert result1 == "computed_1"
        assert call_count == 1
        
        # 第二次调用应该使用缓存
        result2 = await CacheManager.get_or_set(key, factory, expire=60)
        assert result2 == "computed_1"
        assert call_count == 1  # 工厂函数没有再次被调用
    
    @pytest.mark.asyncio
    async def test_cache_mget_mset(self):
        """测试批量操作"""
        mapping = {
            "test:batch:1": "value1",
            "test:batch:2": "value2",
            "test:batch:3": "value3"
        }
        
        # 批量设置
        success = await CacheManager.mset(mapping, expire=60)
        assert success is True
        
        # 批量获取
        keys = list(mapping.keys())
        values = await CacheManager.mget(keys)
        assert values == list(mapping.values())
    
    @pytest.mark.asyncio
    async def test_cache_delete_pattern(self):
        """测试模式删除"""
        # 设置多个键
        for i in range(5):
            await CacheManager.set(f"test:pattern:{i}", f"value{i}")
        
        # 模式删除
        deleted = await CacheManager.delete_pattern("test:pattern:*")
        assert deleted == 5
        
        # 验证删除
        for i in range(5):
            exists = await CacheManager.exists(f"test:pattern:{i}")
            assert exists is False


# ========== 性能测试 ==========

@pytest.mark.slow
class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, async_client):
        """测试并发缓存访问"""
        import asyncio
        
        async def access_cache(i):
            key = f"test:concurrent:{i}"
            await CacheManager.set(key, f"value_{i}")
            return await CacheManager.get(key)
        
        # 并发执行 100 个操作
        tasks = [access_cache(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 100
        assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_login_performance(self, async_client):
        """测试登录性能"""
        import time
        
        start = time.time()
        
        for _ in range(10):
            response = await async_client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "admin123"
            })
            assert response.status_code == 200
        
        elapsed = time.time() - start
        assert elapsed < 5.0  # 10 次登录应在 5 秒内完成


# ========== 边缘情况测试 ==========

class TestEdgeCases:
    """边缘情况测试"""
    
    def test_malformed_json(self, client):
        """测试畸形 JSON"""
        response = client.post(
            "/api/v1/auth/login",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_fields(self, client):
        """测试缺少字段"""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin"
            # 缺少 password
        })
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_cache_complex_objects(self):
        """测试缓存复杂对象"""
        complex_data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "list": [1, 2, 3, {"nested": "value"}],
            "dict": {"key": "value", "nested": {"deep": "data"}},
            "tuple": (1, 2, 3),
            "set": {4, 5, 6}
        }
        
        await CacheManager.set("test:complex", complex_data)
        cached = await CacheManager.get("test:complex")
        
        # pickle 可以正确序列化和反序列化
        assert cached["string"] == "test"
        assert cached["number"] == 42
        assert cached["list"] == [1, 2, 3, {"nested": "value"}]
```

---

## 依赖配置

### requirements.txt
```
# FastAPI
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# 认证
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# 缓存
redis>=5.0.0

# 配置
pydantic>=2.5.0
pydantic-settings>=2.1.0

# 测试
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
pytest-cov>=4.1.0

# 其他
python-dotenv>=1.0.0
```

### .env.example
```env
# 应用配置
APP_NAME=FastAPI Web API
APP_VERSION=1.0.0
DEBUG=true

# 服务器配置
HOST=0.0.0.0
PORT=8000

# JWT 配置
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_URL=redis://localhost:6379/0

# 日志配置
LOG_LEVEL=INFO
```

---

## 运行测试

```bash
# 安装依赖
pip install -r requirements.txt

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_api.py::TestAuthEndpoints

# 运行带覆盖率报告
pytest --cov=app --cov-report=html

# 运行慢速测试
pytest -m slow

# 排除慢速测试
pytest -m "not slow"

# 详细输出
pytest -v
```

---

## 项目特点

| 模块 | 特性 |
|------|------|
| **FastAPI** | 异步支持、自动文档、类型验证 |
| **JWT** | 访问令牌 + 刷新令牌、角色权限控制 |
| **Redis** | 连接池、批量操作、装饰器支持 |
| **日志** | JSON格式、彩色控制台、上下文支持 |
| **测试** | 异步支持、fixtures、覆盖率 |

---

*代码由 Lucas 编写 | 2026-02-19*
