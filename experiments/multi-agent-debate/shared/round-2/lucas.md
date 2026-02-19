## [09:23] Lucas - Round 2

### 我同意的点

- @Harper: FastAPI确实开发效率高，我之前用过2个项目，类型提示+自动文档确实香，新手3天能上手
- @Harper: JWT无状态确实是水平扩展的前提，这点在实际生产验证过
- @Benjamin: 接口返回状态码规范化是好的，团队沟通成本会降低
- @Benjamin: 认证与业务分离这个原则我认同，用装饰器比手动检查靠谱

---

### 我的质疑

#### 质疑 @Benjamin: 四层架构是典型的过度设计

**问题：Repository Layer增加了不必要的工作量**

实际经验：
- 我做过5个FastAPI项目，3个用了Repository模式，2个直接ORM
- 用了Repository的那3个，**代码量增加了40%**，但业务复杂度并没有降低
- 很多场景就是简单的CRUD，Repository层里全是`get_by_id`, `list_all`这种毫无业务逻辑的透传方法

具体坑点：
```python
# Benjamin推荐的方式：
user_repo = UserRepository()
user = await user_repo.get_by_id(db, user_id)

# 实际项目中99%的情况：
user = await db.get(User, user_id)
```

Repository的价值在哪里？如果你要切换ORM（SQLAlchemy→Tortoise），确实有好处，但**概率<1%**。为了这个1%的概率，每天多写50%的代码？

**建议：** 
- 前期直接用SQLAlchemy ORM，Service层直接操作
- 只有当某个表有复杂查询逻辑时，才提取Repository
- 别上来就抽象，需要抽象的时候代码会告诉你的

**工期影响：** 严格四层架构会让开发时间增加 **2-3周**

---

#### 质疑 @Benjamin: 微服务预留是YAGNI（You Ain't Gonna Need It）

**问题：为未来微服务做设计是浪费时间**

实际经验：
- 我经历过2个"预留微服务扩展"的项目，最后**都没有拆分**
- 单体跑了3年，日活10万了还是单体，因为"能跑就别动"
- 预留的那些"抽象接口"反而成了维护负担，每次改需求要跨好几层

Benjamin说的"平滑演进"，实际上演进成本主要在：
1. 数据一致性（分布式事务）
2. 服务间通信（网络延迟、超时、重试）
3. 运维复杂度（监控、日志聚合）

这些**不是加个Repository层就能解决的**。等你真的拆分时，业务逻辑早就变了，预留的接口也对不上。

**建议：**
- 先写单体，但代码要模块化（User模块、Order模块分开文件）
- 真的需要拆分时，用领域驱动设计（DDD）重新梳理，别指望3年前写的Repository

---

#### 质疑 @Harper: Redis缓存不是所有场景都需要

**问题：三层缓存（L1+L2+L3）增加了系统复杂度**

实际经验：
- 我接手过一个项目，上来就Redis Cluster + 本地缓存
- 结果日活5000，数据库压力根本不大，缓存命中率统计：Redis只有30%
- 最坑的是**缓存一致性**，一个更新操作要同步3个地方，出了好几次bug

Harper给的"10万QPS"数据是理论值，实际业务：
- 90%的API日PV < 1000
- PostgreSQL单表百万数据，简单查询<50ms完全够用
- 加缓存后：代码复杂度↑，运维成本↑，故障点↑

**建议：**
- 先实现基础功能，**性能瓶颈时再优化**
- 初期用PostgreSQL连接池（pgbouncer），大多数小项目够用
- 真的需要缓存时，先上最简单的Redis单节点，别一上来就Cluster

---

#### 质疑 @Harper: structlog是小众选择，维护成本高

**问题：团队学习成本 + 排障困难**

实际经验：
- 我用过structlog，确实性能好30%，但**出问题的时候只有你自己会调**
- 团队成员更熟悉标准logging，招人的时候structslog算"特殊技能"
- 标准logging + `python-json-logger` 完全可以输出JSON，够用

```python
# 标准方案，人人都会
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
```

**建议：** 用标准库+成熟插件，别为了30%性能增加团队认知负担

---

#### 质疑 @Harper: JWT+Redis黑名单不如直接用Session

**问题：既然要Redis，那JWT的无状态优势就没了**

实际经验：
- JWT的优势是"无状态"，但Harper自己说要Redis存黑名单+token版本号
- 既然要查Redis，那和查Session表有什么区别？
- JWT还多了：Token体积大（1KB vs 32B）、Token续期复杂、客户端存储麻烦

**建议：**
- 小规模用Redis-backed Session（如`redis-session`中间件）
- 大规模/跨域场景再用JWT
- 别为了技术酷而选JWT

---

### 我的回应

#### 关于过度设计

实际项目中，**简单可维护比完美架构更重要**。

我看过太多项目死在"架构洁癖"上：
- 分层分得太多，新人2周才能上手
- 抽象得太早，后来业务变了，抽象层成了阻碍
- 预留了微服务能力，结果3年后还是单体

好的架构是**演化出来**的，不是**设计出来**的。

#### 关于工期

Benjamin的设计估算：4周开发 + 2周联调

我的估算：
- Benjamin方案：6周（分层+测试+联调）
- 简化方案：3周（快速MVP）

差出来的3周做什么不好？早一个月上线，早一个月收用户反馈。

---

### 我的实现原则

1. **先跑起来，再优化（MVP思路）**
   - 第一版能用就行，别追求"最佳实践"
   - 用户量上来了，瓶颈自然会出现，那时优化方向也很明确

2. **不要为不存在的问题做设计**
   - "未来可能要微服务" → 不，你可能不需要
   - "未来可能换ORM" → 不，SQLAlchemy够用5年
   - "未来可能上缓存" → 不，先监控一下再说

3. **代码是负债，不是资产**
   - 每行代码都要维护
   - 能少一层抽象就少一层
   - 能写简单就不写复杂

4. **团队效率 > 个人技术追求**
   - 选大家熟悉的工具
   - 代码是给同事看的，不是炫技的
   - 招人的时候，"会FastAPI+SQLAlchemy"比"会structlog+Repository模式"容易找

---

### 总结

我质疑的不是技术本身，而是**时机**：
- Benjamin的分层架构是好的，但**现在不需要**
- Harper的Redis缓存是快的，但**现在用不上**

先做减法，把核心功能做出来。等用户量上来了，架构自然会告诉你哪里需要改。

