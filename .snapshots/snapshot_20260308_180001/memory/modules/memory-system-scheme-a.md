# 记忆系统方案A设计文档

> **方案名称**: 向量检索 + 语义搜索 + 时间衰减 (Vector Retrieval + Semantic Search + Time Decay)  
> **版本**: v1.0  
> **日期**: 2026-02-09  
> **状态**: 设计阶段  
> **设计依据**: 基于Whisper v2.0队列架构 + 本地记忆系统实践 + 现有MEMORY.md体系

---

## 1. 设计概述

### 1.1 核心思想

方案A采用**三层记忆模型**：

```
┌─────────────────────────────────────────────────────────────┐
│                      三层记忆架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 3: 长期记忆 (Long-term)                               │
│  ├─ 向量存储 (语义理解)                                       │
│  ├─ 关系图谱 (记忆关联)                                       │
│  └─ 核心档案 (身份/偏好/技能)                                 │
│                                                             │
│  Layer 2: 工作记忆 (Working)                                 │
│  ├─ 会话上下文 (当前对话)                                     │
│  ├─ 近期记忆 (1-7天)                                         │
│  └─ 缓存层 (高频访问)                                         │
│                                                             │
│  Layer 1: 原始记忆 (Raw)                                     │
│  ├─ memory/daily/ (每日记录)                                │
│  ├─ 对话日志 (原始输入)                                       │
│  └─ 待处理队列 ( ingestion )                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 设计原则

| 原则 | 说明 | 来源 |
|------|------|------|
| **异步处理** | 记忆写入不阻塞主流程 | Whisper v2.0队列架构 |
| **增量索引** | 只处理变更数据，避免全量重建 | 本地记忆系统实践 |
| **语义优先** | 向量相似度为主，关键词为辅 | 现代RAG最佳实践 |
| **时间感知** | 近期记忆权重更高 | 人类记忆特性 |
| **零外部依赖** | 本地SQLite + MiniLM，无需外部服务 | 自主可控原则 |

---

## 2. 数据流设计

### 2.1 整体数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│                         记忆摄入流程                                 │
└─────────────────────────────────────────────────────────────────────┘

  用户对话/动作
        │
        ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   预处理层    │────▶│   队列层      │────▶│   嵌入层      │
│ Preprocessor  │     │ Ingestion     │     │ Embedding     │
│               │     │ Queue         │     │ Engine        │
└───────────────┘     └───────────────┘     └───────────────┘
        │                                        │
        │    ┌───────────────────────────────┐   │
        └───▶│  原始存储 (memory/daily/)     │◀──┘
             │  - 完整对话记录               │
             │  - 元数据 (时间/标签/来源)    │
             └───────────────────────────────┘
                              │
                              ▼
             ┌───────────────────────────────┐
             │  向量存储 (SQLite + BLOB)     │
             │  - 文档ID                     │
             │  - 384维向量 (MiniLM)         │
             │  - 时间戳/权重/访问记录       │
             └───────────────────────────────┘
                              │
                              ▼
             ┌───────────────────────────────┐
             │  关系图谱 (记忆关联)          │
             │  - 语义关联                   │
             │  - 时间关联                   │
             │  - 显式链接 (用户标注)        │
             └───────────────────────────────┘
```

### 2.2 预处理层 (Preprocessor)

**职责**: 将原始对话转换为结构化记忆单元

```python
class MemoryPreprocessor:
    """记忆预处理器"""
    
    def process(self, raw_input: Conversation) -> MemoryUnit:
        """
        处理流程:
        1. 提取关键信息 (去噪)
        2. 生成摘要 (≤200字)
        3. 提取标签 (关键词)
        4. 识别实体 (人/地点/项目)
        5. 判断重要性 (1-10)
        """
        return MemoryUnit(
            id=generate_uuid(),
            content=raw_input.text,
            summary=generate_summary(raw_input),
            tags=extract_tags(raw_input),
            entities=extract_entities(raw_input),
            importance=score_importance(raw_input),
            timestamp=now(),
            source=raw_input.source  # chat/file/action
        )
```

**处理规则**:
- **去噪**: 移除系统提示词、重复确认语
- **摘要**: 保留"谁做了什么决定"
- **标签**: 自动提取 #指令 #发现 #决策 #错误
- **重要性评分**:
  - 用户明确指令: 8-10
  - 系统配置变更: 7-9
  - 常规对话: 3-5
  - 临时信息: 1-2

### 2.3 队列层 (Ingestion Queue)

**设计参考**: Whisper v2.0的`TranscriptionQueue`

```python
class MemoryIngestionQueue:
    """记忆摄入队列 - 异步批量处理"""
    
    def __init__(self, batch_size: int = 10, max_workers: int = 2):
        self.batch_size = batch_size
        self.queue = asyncio.PriorityQueue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.pending_memories: List[MemoryUnit] = []
        
    async def submit(self, memory: MemoryUnit, priority: int = 5) -> str:
        """提交记忆到队列"""
        # 高优先级: 用户指令、错误记录
        # 低优先级: 常规对话、系统日志
        await self.queue.put((priority, time.time(), memory))
        
        # 触发批量处理
        if self.queue.qsize() >= self.batch_size:
            await self._flush_batch()
    
    async def _flush_batch(self):
        """批量处理队列中的记忆"""
        batch = []
        while len(batch) < self.batch_size and not self.queue.empty():
            _, _, memory = await self.queue.get()
            batch.append(memory)
        
        # 在线程池中执行嵌入（CPU密集型）
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._embed_and_store_batch,
            batch
        )
```

**队列特性**:
- **优先级**: 用户指令(1) > 错误记录(2) > 决策(3) > 常规对话(5)
- **批量处理**: 每10条或每30秒触发一次
- **错误重试**: 失败任务自动重试3次，指数退避
- **持久化**: 队列状态保存到SQLite，防止数据丢失

### 2.4 嵌入层 (Embedding Engine)

**模型选择**: `all-MiniLM-L6-v2`
- **维度**: 384维
- **大小**: ~80MB
- **速度**: CPU上 ~100 docs/sec
- **质量**: 适合语义相似度任务

```python
class EmbeddingEngine:
    """嵌入引擎 - 文本向量化"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.cache = {}  # 简单LRU缓存
        
    def embed(self, text: str) -> np.ndarray:
        """生成文本嵌入向量"""
        # 缓存检查
        cache_key = hash(text)[:16]
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 生成嵌入
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # 缓存结果
        self.cache[cache_key] = embedding
        return embedding
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """批量嵌入（更高效）"""
        return self.model.encode(texts, convert_to_numpy=True, batch_size=32)
```

---

## 3. 检索逻辑设计

### 3.1 检索流程

```
┌────────────────────────────────────────────────────────────────┐
│                      记忆检索流程                               │
└────────────────────────────────────────────────────────────────┘

  用户Query
       │
       ▼
┌──────────────┐
│  Query理解   │──▶ 意图识别 / 时间范围 / 实体提取
└──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  向量检索    │────▶│  时间衰减    │────▶│  混合排序    │
│  (Top 50)    │     │  权重调整    │     │  最终排序    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                                        │
       ▼                                        ▼
┌──────────────┐                       ┌──────────────┐
│  关键词补充  │                       │  返回Top-K   │
│  (FTS5)      │                       │  (默认5条)   │
└──────────────┘                       └──────────────┘
```

### 3.2 向量检索

```python
class VectorRetriever:
    """向量检索器"""
    
    def __init__(self, db_path: str, embedding_engine: EmbeddingEngine):
        self.conn = sqlite3.connect(db_path)
        self.embedder = embedding_engine
        
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        time_decay: bool = True,
        min_similarity: float = 0.5
    ) -> List[MemoryResult]:
        """
        向量搜索流程:
        1. 生成query嵌入
        2. 获取候选记忆（前50条）
        3. 计算余弦相似度
        4. 应用时间衰减
        5. 混合排序返回
        """
        # 1. 生成query嵌入
        query_embedding = self.embedder.embed(query)
        
        # 2. 获取候选记忆
        candidates = self._get_candidates(query_embedding, limit=50)
        
        # 3. 计算相似度并排序
        results = []
        for memory in candidates:
            similarity = self._cosine_similarity(
                query_embedding, 
                memory.embedding
            )
            
            if similarity < min_similarity:
                continue
                
            # 4. 应用时间衰减
            if time_decay:
                decayed_score = self._apply_time_decay(
                    similarity, 
                    memory.timestamp
                )
            else:
                decayed_score = similarity
                
            results.append(MemoryResult(
                memory=memory,
                similarity=similarity,
                final_score=decayed_score
            ))
        
        # 5. 按最终分数排序
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results[:top_k]
```

### 3.3 时间衰减算法

**目标**: 近期记忆权重更高，但重要记忆衰减更慢

```python
def apply_time_decay(
    base_score: float,
    timestamp: datetime,
    importance: int,
    decay_half_life: timedelta = timedelta(days=7)
) -> float:
    """
    时间衰减公式:
    
    decayed_score = base_score * exp(-λ * days_ago) * importance_boost
    
    其中:
    - λ = ln(2) / half_life  (衰减系数)
    - importance_boost = 1 + (importance - 5) / 10  (重要性加成)
    
    示例:
    - 7天前的一般记忆: score * 0.5
    - 7天前的重要记忆(=9): score * 0.5 * 1.4 = score * 0.7
    - 30天前的一般记忆: score * 0.06
    - 30天前的重要记忆: score * 0.06 * 1.4 = score * 0.08
    """
    days_ago = (datetime.now() - timestamp).days
    
    # 基础衰减
    lambda_val = math.log(2) / decay_half_life.days
    time_factor = math.exp(-lambda_val * days_ago)
    
    # 重要性加成 (重要记忆衰减更慢)
    importance_boost = 1 + (importance - 5) / 10
    
    return base_score * time_factor * importance_boost
```

**时间衰减曲线**:

```
分数
 1.0 ┤●
     │ ●
 0.8 ┤  ●
     │   ●
 0.6 ┤    ●  ← 重要记忆 (importance=9)
     │     ╲
 0.4 ┤      ●
     │       ╲  ← 一般记忆 (importance=5)
 0.2 ┤        ●
     │         ╲
   0 ┤          ●───────
     └────┬────┬────┬────┬────▶ 时间
          7天  14天  30天  60天
```

### 3.4 混合排序

**多维度排序公式**:

```
final_score = (
    w1 * semantic_score +      # 语义相似度 (0-1)
    w2 * temporal_score +      # 时间新鲜度 (0-1)
    w3 * importance_score +    # 重要性 (0-1)
    w4 * access_score          # 访问频率 (0-1)
)

默认权重:
- w1 (语义): 0.4
- w2 (时间): 0.3
- w3 (重要性): 0.2
- w4 (访问): 0.1

权重可根据查询类型动态调整:
- "最近做了什么" → temporal权重提高
- "关于XX的所有信息" → semantic权重提高
- "重要的决定" → importance权重提高
```

---

## 4. 集成点设计

### 4.1 与现有MEMORY.md的集成

```
┌─────────────────────────────────────────────────────────────┐
│               MEMORY.md 集成策略                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MEMORY.md (人工维护)                                        │
│  ├─ 核心身份定义                                            │
│  ├─ 重要决策记录                                            │
│  ├─ 系统架构概览                                            │
│  └─ 快速导航链接                                            │
│         │                                                   │
│         │  双向同步                                          │
│         ▼                                                   │
│  向量存储 (自动维护)                                         │
│  ├─ 所有记忆的语义表示                                       │
│  ├─ 自动提取的关系图谱                                       │
│  └─ 访问统计和衰减计算                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**集成规则**:
1. **MEMORY.md作为入口**: 保留人工编辑的核心记忆
2. **自动同步机制**: 
   - MEMORY.md中的内容自动索引到向量存储
   - 向量存储中的高频访问记忆建议更新到MEMORY.md
3. **检索优先级**: 
   - 优先检索MEMORY.md（快速匹配）
   - 再检索向量存储（语义匹配）

### 4.2 与memory/daily/的集成

```python
class DailyMemorySync:
    """每日记忆同步器"""
    
    def sync_daily_to_vector(self, date: str = None):
        """
        将daily文件同步到向量存储
        流程:
        1. 读取当天的memory/daily/YYYY-MM-DD.md
        2. 按段落分割
        3. 为每个段落生成嵌入
        4. 存储到向量数据库
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        daily_file = f"memory/daily/{date}.md"
        
        # 读取并解析
        sections = self._parse_daily_file(daily_file)
        
        for section in sections:
            memory_unit = MemoryUnit(
                content=section.content,
                source_file=daily_file,
                timestamp=section.timestamp,
                tags=section.tags,
                importance=section.importance
            )
            
            # 提交到摄入队列
            await self.ingestion_queue.submit(memory_unit)
    
    def sync_vector_to_daily(self, memory_id: str):
        """
        将向量存储中的记忆导出到daily文件
        用于: 整理重要发现、补充遗漏记录
        """
        memory = self.vector_store.get(memory_id)
        
        # 追加到当天daily文件
        daily_file = f"memory/daily/{datetime.now().strftime('%Y-%m-%d')}.md"
        append_to_file(daily_file, format_memory_entry(memory))
```

### 4.3 与memory/modules/的集成

**模块分类存储**:

```
memory/modules/
├── user-profile.md          → 标签: #user #profile (importance=10)
├── safety-protocol.md       → 标签: #safety #protocol (importance=10)
├── restore-guide.md         → 标签: #restore #emergency (importance=10)
├── auto-healing.md          → 标签: #healing #system (importance=8)
├── error-lessons.md         → 标签: #error #lesson (importance=8)
├── memory-system-arch.md    → 标签: #memory #architecture (importance=9)
└── [其他模块]               → 相应标签和重要性
```

**自动分类逻辑**:
```python
def auto_classify_memory(memory: MemoryUnit) -> str:
    """自动分类记忆到对应模块"""
    
    # 基于标签匹配
    tag_to_module = {
        '#安全': 'safety-protocol',
        '#备份': 'restore-guide',
        '#恢复': 'restore-guide',
        '#错误': 'error-lessons',
        '#故障': 'auto-healing',
        '#记忆': 'memory-system-arch',
        '#用户': 'user-profile',
        '#偏好': 'user-profile',
    }
    
    for tag, module in tag_to_module.items():
        if tag in memory.tags:
            return module
    
    # 基于语义匹配
    module_embeddings = load_module_embeddings()
    memory_embedding = embed(memory.content)
    
    best_match = None
    best_score = 0
    for module, embedding in module_embeddings.items():
        score = cosine_similarity(memory_embedding, embedding)
        if score > best_score and score > 0.7:
            best_match = module
            best_score = score
    
    return best_match or 'general'
```

### 4.4 与memory/tags/的集成

**标签系统作为过滤器**:

```python
class TaggedMemorySearch:
    """带标签过滤的记忆搜索"""
    
    def search_with_tags(
        self,
        query: str,
        include_tags: List[str] = None,
        exclude_tags: List[str] = None,
        **kwargs
    ) -> List[MemoryResult]:
        """
        先按标签过滤，再执行向量搜索
        """
        # 1. 标签预过滤
        if include_tags:
            candidate_ids = self._get_memories_by_tags(include_tags)
        else:
            candidate_ids = None
            
        # 2. 执行向量搜索（带过滤）
        results = self.vector_search.search(
            query,
            candidate_ids=candidate_ids,
            **kwargs
        )
        
        # 3. 排除标签过滤
        if exclude_tags:
            results = [
                r for r in results
                if not any(tag in r.memory.tags for tag in exclude_tags)
            ]
        
        return results
```

---

## 5. 实现路径

### 5.1 阶段划分

```
┌────────────────────────────────────────────────────────────────┐
│                      分阶段实施计划                             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Phase 1: 基础架构 (Week 1)                                    │
│  ├─ [ ] 搭建SQLite + MiniLM基础框架                           │
│  ├─ [ ] 实现基本CRUD操作                                      │
│  ├─ [ ] 实现向量相似度计算                                    │
│  └─ [ ] 单元测试覆盖                                          │
│                                                                │
│  Phase 2: 队列与异步 (Week 2)                                  │
│  ├─ [ ] 实现摄入队列 (参考Whisper架构)                        │
│  ├─ [ ] 实现批量嵌入处理                                      │
│  ├─ [ ] 实现错误重试机制                                      │
│  └─ [ ] 集成到daily文件写入流程                               │
│                                                                │
│  Phase 3: 检索优化 (Week 3)                                    │
│  ├─ [ ] 实现时间衰减算法                                      │
│  ├─ [ ] 实现混合排序                                          │
│  ├─ [ ] 集成FTS5关键词搜索                                    │
│  └─ [ ] 性能基准测试                                          │
│                                                                │
│  Phase 4: 集成与优化 (Week 4)                                  │
│  ├─ [ ] 与MEMORY.md双向同步                                   │
│  ├─ [ ] 与modules/自动分类集成                                │
│  ├─ [ ] 缓存层优化 (LRU + 预热)                               │
│  └─ [ ] 完整集成测试                                          │
│                                                                │
│  Phase 5: 生产就绪 (Week 5)                                    │
│  ├─ [ ] 压力测试 (10万+记忆)                                  │
│  ├─ [ ] 监控与告警                                            │
│  ├─ [ ] 文档完善                                              │
│  └─ [ ] 正式发布                                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| **向量数据库** | SQLite + BLOB | 零外部依赖，已在本地记忆系统验证 |
| **嵌入模型** | all-MiniLM-L6-v2 | 384维，80MB，CPU友好，质量足够 |
| **全文搜索** | SQLite FTS5 | 内置功能，无需额外依赖 |
| **异步框架** | asyncio | Python标准库，Whisper架构已验证 |
| **线程池** | concurrent.futures | 嵌入计算CPU密集型，需要多线程 |

### 5.3 文件结构

```
memory/
├── daily/                           # 原始每日记录
├── summary/                         # 定期总结
├── tags/                            # 标签索引
├── modules/                         # 模块化知识
├── archive/                         # 归档
│
└── vector-store/                    # 【新增】向量存储
    ├── memory.db                    # SQLite主数据库
    │   ├── documents               # 记忆元数据表
    │   ├── document_vectors        # 向量存储表 (BLOB)
    │   ├── memory_relations        # 记忆关联表
    │   └── search_history          # 搜索历史表
    │
    ├── models/                      # 嵌入模型缓存
    │   └── all-MiniLM-L6-v2/       # MiniLM模型文件
    │
    └── scripts/                     # 管理脚本
        ├── memory-cli.py           # 命令行工具
        ├── ingestion-daemon.py     # 摄入守护进程
        └── maintenance.py          # 维护脚本
```

### 5.4 API设计

```python
# 核心API接口

class MemorySystem:
    """记忆系统主类"""
    
    # 写入接口
    async def ingest(self, content: str, **metadata) -> str:
        """摄入新记忆，返回记忆ID"""
        
    async def ingest_batch(self, memories: List[MemoryUnit]) -> List[str]:
        """批量摄入记忆"""
        
    # 检索接口
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        time_decay: bool = True,
        tags: List[str] = None
    ) -> List[MemoryResult]:
        """语义搜索记忆"""
        
    async def recall_recent(
        self, 
        days: int = 7, 
        tags: List[str] = None
    ) -> List[MemoryResult]:
        """回忆近期记忆"""
        
    async def find_related(self, memory_id: str, top_k: int = 5) -> List[MemoryResult]:
        """查找相关记忆"""
        
    # 管理接口
    async def sync_from_daily(self, date: str = None):
        """从daily文件同步到向量存储"""
        
    async def sync_to_memory_md(self):
        """将高频记忆同步到MEMORY.md"""
        
    async def get_stats(self) -> MemoryStats:
        """获取系统统计信息"""
```

### 5.5 性能目标

| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| 单次搜索延迟 | < 200ms | 1万记忆基准 |
| 批量嵌入速度 | > 50 docs/sec | CPU基准测试 |
| 存储占用 | < 500 bytes/doc | 向量+元数据 |
| 并发处理 | 4-8 并发 | 多线程测试 |
| 数据库大小 | < 1GB / 10万记忆 | 存储测试 |

---

## 6. 风险评估与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| MiniLM模型加载慢 | 中 | 中 | 懒加载 + 预加载策略 |
| 向量搜索性能下降 | 中 | 高 | 分层检索 + 近似搜索 |
| 数据库文件过大 | 低 | 中 | 定期归档 + 压缩 |
| 嵌入质量不佳 | 低 | 中 | 可调参数 + 备选模型 |
| 并发写入冲突 | 中 | 中 | 队列串行化 + WAL模式 |

---

## 7. 与现有技能的关系

### 7.1 继承的设计经验

| 来源 | 继承的设计 | 应用场景 |
|------|-----------|----------|
| **Whisper v2.0** | 队列+异步架构 | 记忆摄入不阻塞主流程 |
| **Whisper v2.0** | LRU模型缓存 | 嵌入模型缓存管理 |
| **Whisper v2.0** | 错误重试机制 | 摄入失败自动重试 |
| **本地记忆系统** | SQLite+BLOB存储 | 向量存储方案 |
| **本地记忆系统** | 余弦相似度计算 | 语义相似度排序 |
| **memory-index-arch** | FTS5全文搜索 | 关键词补充检索 |
| **memory-index-arch** | 触发器自动同步 | 索引自动维护 |

### 7.2 方案A的独特贡献

1. **时间衰减算法**: 模拟人类记忆的自然遗忘曲线
2. **三层记忆模型**: 长期/工作/原始记忆的明确分层
3. **混合排序**: 语义+时间+重要性+访问频率的多维排序
4. **双向同步**: 向量存储与传统文件的自动同步

---

## 8. 总结

### 8.1 方案A核心优势

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ✅ 零外部依赖 - 纯本地SQLite + MiniLM                      │
│   ✅ 语义理解 - 向量检索捕捉深层语义关联                       │
│   ✅ 时间感知 - 自动遗忘不重要的旧记忆                         │
│   ✅ 异步架构 - 摄入不阻塞主流程                              │
│   ✅ 渐进集成 - 与现有MEMORY.md/daily/体系无缝融合            │
│   ✅ 经验复用 - 基于Whisper v2.0验证的队列架构                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 下一步行动

1. **立即**: 评审本设计文档
2. **本周**: 启动Phase 1基础架构开发
3. **下周**: 实现队列与异步处理
4. **持续**: 每阶段完成后性能基准测试

---

*文档版本: 1.0*  
*设计完成时间: 2026-02-09*  
*待评审: 是*
