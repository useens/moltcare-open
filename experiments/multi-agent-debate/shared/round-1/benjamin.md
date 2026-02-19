## [09:21] Benjamin - Round 1

### 我的架构设计

#### 1. 整体架构: 分层架构 (Layered Architecture)

**选择: 清晰的分层架构而非MVC**

```
┌─────────────────────────────────────────────────────────┐
│                      API Layer                          │  ← FastAPI Routers
│              (单一职责: HTTP协议处理)                      │
├─────────────────────────────────────────────────────────┤
│                   Service Layer                         │  ← 业务逻辑
│              (开闭原则: 扩展业务不改动底层)                 │
├─────────────────────────────────────────────────────────┤
│               Repository Layer                          │  ← 数据访问
│        (依赖倒置: 业务层不依赖具体存储实现)                  │
├─────────────────────────────────────────────────────────┤
│                   Model Layer                           │  ← 领域模型/Pydantic
│              (封装业务规则与数据结构)                       │
└─────────────────────────────────────────────────────────┘
```

**选择理由 (SOLID原则):**
- **S-单一职责**: 每层只做一件事，API层不碰数据库，Repository层不碰HTTP
- **D-依赖倒置**: Service依赖Repository抽象，而非具体ORM实现，可无痛切换SQLAlchemy/Tortoise
- **O-开闭原则**: 新增业务功能只需扩展Service，不改动现有代码

**对比MVC的劣势?** MVC的Controller容易膨胀成"上帝类"，分层强制分离关注点。

---

#### 2. RESTful设计规范

**URL命名规范 (Google API Design Guide + 行业最佳实践):**

```
# 资源导向，名词复数
GET    /api/v1/users              # 列表 (支持分页: ?page=1&size=20)
GET    /api/v1/users/{id}         # 详情
POST   /api/v1/users              # 创建
PATCH  /api/v1/users/{id}         # 部分更新 (首选，语义精确)
PUT    /api/v1/users/{id}         # 全量替换
DELETE /api/v1/users/{id}         # 删除

# 子资源
GET    /api/v1/users/{id}/orders  # 用户的订单列表
POST   /api/v1/users/{id}/orders  # 为用户创建订单

# 动作语义用动词 (例外情况)
POST   /api/v1/users/{id}/activate    # 激活用户
POST   /api/v1/auth/login            # 认证相关
```

**状态码规范:**
| 场景 | 状态码 | 说明 |
|------|--------|------|
| 创建成功 | 201 Created | 返回Location头和新资源 |
| 删除成功 | 204 No Content | 无返回体 |
| 部分更新 | 200 OK | PATCH返回更新后资源 |
| 业务错误 | 422 Unprocessable Entity | 参数校验失败 |
| 认证失败 | 401 Unauthorized | 未登录 |
| 权限不足 | 403 Forbidden | 无权限 |
| 资源不存在 | 404 Not Found | URL错误或已删除 |
| 重复请求 | 409 Conflict | 幂等键重复 |
| 限流触发 | 429 Too Many Requests | 配合Retry-After头 |

**版本策略**: URL版本 `/api/v1/`，header备用 `Accept: application/vnd.api.v1+json`

---

#### 3. 安全模型: JWT + RBAC + 纵深防御

**身份认证 (Authentication):**
```python
# JWT策略: Access Token (短效) + Refresh Token (长效)
- Access Token: 15分钟, 内存存储
- Refresh Token: 7天, httpOnly cookie / secure storage
- 算法: RS256 (非对称加密，服务端私钥签名)
- 声明: sub(用户ID), roles(角色), jti(令牌ID用于吊销), exp(过期)
```

**权限控制 (RBAC):**
```
角色层级: admin → manager → user → guest
权限粒度: resource:action (如 user:read, user:write, order:delete)

实现: Service层装饰器
@require_permissions("order:write")
async def create_order(...)

或更细粒度的数据权限:
@require_owner_or_admin(resource="order")
async def update_order(order_id, user_id, ...)
```

**威胁分析与防御:**
| 威胁 | 防御措施 | 实现位置 |
|------|----------|----------|
| SQL注入 | 参数化查询 + ORM | Repository层 |
| XSS | 输出转义 + CSP头 | API层中间件 |
| CSRF | SameSite Cookie + Token验证 | 认证中间件 |
| 重放攻击 | 请求时间戳窗口 + 幂等键 | 网关/中间件 |
| 暴力破解 | 登录限流 (5次/分钟/IP) | Redis + 中间件 |
| 敏感数据泄露 | 字段级加密 (AES-256-GCM) | Model层 |
| 越权访问 | 资源所有权校验 | Service层装饰器 |

---

#### 4. 可扩展性: 支持平滑演进到微服务

**单体阶段的预留设计:**

```
当前单体                 未来拆分
┌─────────────┐          ┌─────────────┐  ┌─────────────┐
│  API Layer  │    →     │  API Gateway │  │  API Gateway │
├─────────────┤          ├─────────────┤  ├─────────────┤
│ UserService │    →     │  User Svc   │  │  Order Svc  │
│ OrderService│          └─────────────┘  └─────────────┘
└─────────────┘                │                │
                        ┌─────┴────┐      ┌────┴────┐
                        │User DB   │      │Order DB │
                        └──────────┘      └─────────┘
```

**拆分就绪的设计决策:**
1. **Repository抽象**: 今天用SQLAlchemy查本地DB，明天可改为HTTP客户端调其他服务，Service层无感知
2. **事件驱动预留**: 引入Celery/RabbitMQ处理异步任务，为服务间通信打基础
3. **无共享状态**: 会话不存内存，全走Redis，水平扩展无状态
4. **配置外置**: 数据库连接、缓存地址全环境变量，容器化友好
5. **健康检查**: `/health`, `/ready`, `/metrics` 端点，K8s就绪

**扩展性指标预留:**
- 数据库: 读写分离配置位、分库分表策略接口
- 缓存: Redis多级缓存，热点数据本地Caffeine + 分布式Redis
- 异步: 耗时操作全异步化，API响应<200ms P99

---

### 我预计到会被质疑的点

**来自Harper的质疑:**
- *"FastAPI太新，社区生态不如Django成熟，出了问题怎么办?"*
- 我的回应准备: FastAPI基于Starlette+Pydantic，底层稳定；类型提示降低维护成本；性能碾压Django，适合API-first项目

- *"分层太啰嗦，直接Controller调ORM更快上线"*
- 我的回应准备: 短期快，长期债。业务复杂后Controller会变成泥球，重构成本指数级上升。分层是"慢思考快行动"

**来自Lucas的质疑:**
- *"为什么不用GraphQL? REST对复杂查询不够灵活"*
- 我的回应准备: GraphQL有N+1查询、缓存困难、学习曲线陡峭问题。REST + 良好的资源设计能满足80%场景，复杂查询可用专用端点

- *"JWT吊销困难，为什么不直接用Session?"*
- 我的回应准备: 无状态利于水平扩展；吊销可用黑名单+短有效期妥协；Session在分布式下需Sticky Session或共享存储，复杂度不低

---

### 我的架构底线

**绝不妥协的原则:**

1. **必须分层，Controller不许直接调ORM**  
   这是架构腐化的起点，一旦开了口子，技术债会以指数速度累积

2. **必须接口抽象，Repository必须是抽象类/Protocol**  
   依赖倒置是解耦的核心，没有抽象就无法测试，无法切换实现

3. **认证与业务逻辑必须分离**  
   安全不能靠"记得检查"，必须靠框架/装饰器强制执行

4. **状态必须外置**  
   服务必须无状态，这是水平扩展的前提，也是云原生12要素之一

**可讨论的:**
- 用FastAPI还是Flask? 可以讨论，但类型提示是必须的
- JWT有效期具体多长? 可以数据驱动调整
- 用PostgreSQL还是MySQL? 业务适配为主

---

**结论**: 这个架构以**分层+抽象+无状态**为核心，短期略有 overhead，长期可在不重构核心代码的前提下，平滑支撑从单体到微服务的演进。

