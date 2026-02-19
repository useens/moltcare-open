# Python Web API 架构设计文档

> **设计人**: Benjamin (架构与逻辑专家)  
> **日期**: 2026-02-19  
> **版本**: v1.0

---

## 1. 整体架构设计

### 1.1 架构选型: 分层架构 (Layered Architecture)

经过对比分析，**分层架构**比MVC更适合现代Python Web API：

| 维度 | MVC | 分层架构 |
|------|-----|----------|
| API友好度 | View层冗余 | 直接面向API |
| 可测试性 | Controller难测 | 每层独立可测 |
| 扩展性 | 垂直扩展 | 支持微服务拆分 |
| 复杂度 | 适合简单应用 | 适合复杂业务 |

### 1.2 技术栈

```
FastAPI 0.100+      # 异步Web框架
SQLAlchemy 2.0      # ORM (支持异步)
Pydantic v2         # 数据验证与序列化
PostgreSQL          # 主数据库
Redis               # 缓存 + 会话存储
Celery              # 异步任务队列
Alembic             # 数据库迁移
Pytest              # 测试框架
```

### 1.3 分层结构

```
┌─────────────────────────────────────────────┐
│  API Layer (Routers)                        │
│  - HTTP协议处理 / 参数校验 / 路由分发        │
│  - Dependencies: Auth, RateLimit, Logging   │
├─────────────────────────────────────────────┤
│  Service Layer                              │
│  - 业务逻辑编排 / 事务控制 / 领域事件       │
│  - 跨实体操作 / 复杂计算                    │
├─────────────────────────────────────────────┤
│  Repository Layer                           │
│  - 数据访问抽象 / ORM封装 / 查询构建        │
│  - 隐藏数据库细节                           │
├─────────────────────────────────────────────┤
│  Domain Layer (Models)                      │
│  - 核心业务实体 / 领域规则 / 值对象         │
│  - 不依赖外部框架                           │
├─────────────────────────────────────────────┤
│  Infrastructure Layer                       │
│  - 外部服务 / 缓存 / 消息队列 / 文件存储    │
└─────────────────────────────────────────────┘
```

### 1.4 目录结构

```
project/
├── app/
│   ├── api/                # API层
│   │   ├── deps.py         # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── users.py    # 用户路由
│   │       └── items.py    # 物品路由
│   ├── core/               # 核心配置
│   │   ├── config.py       # 环境配置
│   │   ├── security.py     # 安全工具
│   │   └── exceptions.py   # 自定义异常
│   ├── services/           # Service层
│   │   ├── user_service.py
│   │   └── item_service.py
│   ├── repositories/       # Repository层
│   │   ├── user_repo.py
│   │   └── base_repo.py    # 通用CRUD
│   ├── models/             # Domain层
│   │   ├── user.py
│   │   └── item.py
│   ├── schemas/            # Pydantic模型
│   │   ├── user.py         # Request/Response
│   │   └── common.py       # 通用结构
│   └── infrastructure/     # 基础设施
│       ├── cache.py        # Redis封装
│       ├── db.py           # 数据库连接
│       └── storage.py      # 文件存储
├── alembic/                # 数据库迁移
├── tests/                  # 测试
└── Dockerfile
```

---

## 2. RESTful API设计规范

### 2.1 URL设计

```http
# 用户资源
GET    /api/v1/users              # 列表 (分页)
GET    /api/v1/users/{id}         # 详情
POST   /api/v1/users              # 创建
PUT    /api/v1/users/{id}         # 全量更新
PATCH  /api/v1/users/{id}         # 部分更新
DELETE /api/v1/users/{id}         # 删除

# 嵌套资源
GET    /api/v1/users/{id}/orders  # 用户订单列表
POST   /api/v1/users/{id}/orders  # 为用户创建订单
```

### 2.2 统一响应格式

**成功响应 (200)**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 123,
    "name": "张三",
    "email": "zhangsan@example.com"
  }
}
```

**分页响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": [...],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 156,
    "pages": 8
  }
}
```

**错误响应**:
```json
{
  "code": 1001,
  "message": "用户不存在",
  "details": "id=999 的用户未找到"
}
```

### 2.3 HTTP状态码使用

| 状态码 | 使用场景 |
|--------|----------|
| 200 | 成功获取/更新 |
| 201 | 创建成功 |
| 204 | 删除成功，无返回体 |
| 400 | 请求参数错误 |
| 401 | 未登录/Token过期 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 409 | 资源冲突 (如重复创建) |
| 422 | 验证失败 (FastAPI默认) |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 2.4 版本控制

采用**URL路径版本**策略：
- `/api/v1/users` - 当前版本
- `/api/v2/users` - 新版本

优势：
- 直观可见
- 便于API文档生成
- 支持多版本并行

---

## 3. 安全设计

### 3.1 认证流程 (JWT + Refresh Token)

```
┌─────────┐     1. 登录请求      ┌─────────┐
│  Client │ ─────────────────→ │  Auth   │
│         │   {username, pwd}  │ Service │
│         │ ←───────────────── │         │
│         │   2. 返回双Token    │         │
│         │   {access, refresh} │        │
└─────────┘                    └─────────┘
       │
       │ 3. 后续请求携带Access Token
       ▼
┌─────────┐     4. 验证Token      ┌─────────┐
│  Client │ ─────────────────→ │   API   │
│         │   Authorization:    │ Server  │
│         │   Bearer {token}    │         │
│         │ ←───────────────── │         │
│         │   5. 返回数据        │         │
└─────────┘                    └─────────┘
       │
       │ 6. Access Token过期 (15分钟)
       ▼
┌─────────┐     7. 刷新请求      ┌─────────┐
│  Client │ ─────────────────→ │  Auth   │
│         │   {refresh_token}   │ Service │
│         │ ←───────────────── │         │
│         │   8. 新Access Token │         │
└─────────┘                    └─────────┘
```

**Token配置**:
- Access Token: JWT, 有效期15分钟, 内存存储
- Refresh Token: 随机字符串, 有效期7天, HttpOnly Cookie
- 黑名单: Redis存储注销Token, 过期时间与Token相同

### 3.2 权限控制 (RBAC)

**模型设计**:
```
User -> Role -> Permission -> Resource:Action

示例:
用户A -> 管理员 -> user:read, user:write, order:read...
用户B -> 普通用户 -> user:read:self, order:read:self...
```

**权限粒度**:
1. **菜单权限**: 前端路由控制
2. **按钮权限**: 操作按钮可见性
3. **数据权限**: 行级控制 (只能看自己的数据)
4. **字段权限**: 列级控制 (敏感字段脱敏)

### 3.3 中间件顺序

```python
# 中间件执行顺序 (从上到下)
app.add_middleware(CORSMiddleware)      # 1. 跨域
app.add_middleware(RequestLogging)      # 2. 请求日志
app.add_middleware(RateLimitMiddleware) # 3. 限流
app.add_middleware(AuthMiddleware)      # 4. 认证
app.add_middleware(PermissionMiddleware) # 5. 权限
# 6. 业务处理
```

### 3.4 安全加固清单

**输入安全**:
- ✅ SQL注入: 使用SQLAlchemy ORM, 禁止字符串拼接
- ✅ XSS防护: 响应头 `Content-Type: application/json`
- ✅ CSRF防护: SameSite=Strict Cookie
- ✅ 文件上传: 白名单扩展名 + 文件头检查 + 大小限制

**传输安全**:
- ✅ 强制HTTPS (HSTS头)
- ✅ 敏感数据AES加密
- ✅ API密钥环境变量管理

**审计监控**:
- ✅ 登录日志 (IP, 时间, UA, 结果)
- ✅ 操作日志 (用户, 操作, 时间, 影响)
- ✅ 异常告警 (暴力破解: 5分钟5次失败)

---

## 4. 性能优化方案

### 4.1 瓶颈识别矩阵

| 层级 | 潜在瓶颈 | 影响 |
|------|----------|------|
| 网络 | DNS解析慢, SSL握手, 大Body | 延迟增加 |
| 应用 | 同步阻塞, 大量验证, 序列化 | 吞吐量下降 |
| 业务 | 复杂计算, 循环查询 | CPU飙升 |
| 数据 | 慢查询, 连接池满, 锁竞争 | 响应超时 |
| 外部 | 第三方API超时/限流 | 级联故障 |

### 4.2 数据库优化

**连接池配置**:
```python
# SQLAlchemy 2.0 异步配置
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,              # 基础连接数
    max_overflow=20,           # 最大溢出
    pool_timeout=30,           # 等待超时(秒)
    pool_recycle=1800,         # 连接回收(30分钟)
    echo=False
)
```

**查询优化**:
- 使用 `selectinload` 解决N+1问题
- 分页使用 cursor-based (避免大offset)
- 添加复合索引 (通过EXPLAIN分析)
- 读写分离 (主写从读)

**缓存策略**:
```python
# Redis 缓存模式
async def get_user(user_id: int):
    # 1. 查缓存
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # 2. 查数据库
    user = await db.get(User, user_id)
    
    # 3. 写入缓存 (TTL 5分钟)
    await redis.setex(f"user:{user_id}", 300, json.dumps(user))
    return user
```

缓存问题防护:
- **穿透**: 布隆过滤器
- **击穿**: 互斥锁 (set nx)
- **雪崩**: 随机TTL (5-10分钟)

### 4.3 应用层优化

**异步改造**:
```python
# ✅ 正确: 全部异步
@app.get("/users/{id}")
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    return await user_service.get(db, id)

# ❌ 错误: 同步调用
@app.get("/users/{id}")
def get_user(id: int):  # 缺少async
    return requests.get(...)  # 阻塞!
```

**响应优化**:
- 启用Gzip压缩 (响应 > 1KB)
- 分页默认限制 (max 100条)
- 字段过滤 `?fields=id,name,email`

### 4.4 部署优化

**多进程配置**:
```bash
# 生产环境启动命令
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools

# Workers = 2 * CPU核心数 (假设2核CPU = 4 workers)
```

**水平扩展**:
```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (负载均衡)  │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
     ┌─────────┐     ┌─────────┐     ┌─────────┐
     │ FastAPI │     │ FastAPI │     │ FastAPI │
     │  Pod 1  │     │  Pod 2  │     │  Pod 3  │
     └────┬────┘     └────┬────┘     └────┬────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
                    ┌─────────────┐
                    │   Redis     │
                    │ (共享会话)   │
                    └─────────────┘
```

### 4.5 性能指标基线

| 指标 | 目标值 | 预警值 | 严重值 |
|------|--------|--------|--------|
| P99延迟 | < 200ms | > 500ms | > 1s |
| 吞吐量 | > 1000 RPS | < 500 RPS | < 200 RPS |
| 错误率 | < 0.1% | > 1% | > 5% |
| CPU使用率 | < 70% | > 85% | > 95% |
| 内存使用率 | < 80% | > 90% | > 95% |

### 4.6 监控方案

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────→│ Prometheus  │────→│   Grafana   │
│  (metrics)  │     │  (时序数据)  │     │  (可视化)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       │ 链路追踪
       ▼
┌─────────────┐     ┌─────────────┐
│ OpenTelemetry│────→│   Jaeger    │
│   (SDK)     │     │  (链路分析)  │
└─────────────┘     └─────────────┘
```

---

## 5. 代码示例

### 5.1 完整请求流程示例

```python
# api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_permission
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("user:create"))
):
    """创建用户 (需要user:create权限)"""
    service = UserService(db)
    
    # 检查邮箱是否已存在
    if await service.get_by_email(user_in.email):
        raise HTTPException(409, "邮箱已被注册")
    
    # 创建用户
    user = await service.create(user_in)
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详情"""
    service = UserService(db)
    user = await service.get(user_id)
    
    if not user:
        raise HTTPException(404, "用户不存在")
    
    # 数据权限: 普通用户只能看自己
    if not current_user.is_admin and user.id != current_user.id:
        raise HTTPException(403, "无权限查看")
    
    return user
```

```python
# services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)
    
    async def get(self, user_id: int) -> User | None:
        return await self.repo.get(user_id)
    
    async def get_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(email)
    
    async def create(self, user_in: UserCreate) -> User:
        # 密码加密
        hashed_password = get_password_hash(user_in.password)
        
        user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            name=user_in.name
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
```

---

## 6. 总结

### 6.1 架构亮点

1. **分层清晰**: 各层职责单一，便于测试和维护
2. **异步优先**: FastAPI原生异步，高并发性能好
3. **安全第一**: JWT双Token + RBAC权限 + 多层防护
4. **性能优化**: 缓存 + 连接池 + 限流 + 监控全覆盖

### 6.2 实施建议

**阶段1 (MVP)**: 基础API + JWT认证
**阶段2 (增强)**: 权限系统 + 缓存优化
**阶段3 (扩展)**: 微服务拆分 + 监控完善

### 6.3 风险提示

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 数据库性能瓶颈 | 中 | 高 | 早期做好索引和缓存设计 |
| 安全漏洞 | 低 | 高 | 代码审计 + 依赖扫描 |
| 第三方依赖过时 | 高 | 中 | 定期更新 + 锁定版本 |

---

**文档结束**
