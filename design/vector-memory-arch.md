# 向量记忆系统架构设计

## 概述

基于 LanceDB + Sentence-Transformers 的本地向量记忆系统，专为中文场景优化，支持语义搜索、自动分块、去重和过期管理。

---

## 1. 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        向量记忆系统                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  查询接口层  │  │  记忆管理层  │  │       嵌入生成层         │  │
│  │  (Query API)│  │(Memory Mgmt)│  │   (Embedding Generator)  │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         ▼                ▼                      ▼                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    向量存储层 (LanceDB)                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ 记忆表      │  │ 元数据表    │  │  索引 (IVF_PQ)      │  │  │
│  │  │ (memories) │  │(metadata)  │  │                     │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心模块设计

### 2.1 向量存储层 (Vector Store)

**文件**: `core/vector_store.py`

```python
class LanceDBStore:
    """LanceDB 向量存储封装"""
    
    def __init__(self, db_path: str, dimension: int = 512):
        self.db_path = db_path
        self.dimension = dimension
        self.db = None
        self.table = None
    
    def connect(self) -> None:
        """连接/创建数据库"""
    
    def create_table(self, table_name: str, schema: dict) -> None:
        """创建记忆表"""
    
    def add_vectors(self, vectors: list[dict]) -> list[str]:
        """
        批量添加向量
        Returns: 记录ID列表
        """
    
    def search(
        self, 
        query_vector: np.ndarray, 
        top_k: int = 5,
        filter_expr: str = None
    ) -> list[dict]:
        """
        向量相似度搜索
        """
    
    def update(self, record_id: str, data: dict) -> None:
        """更新记录"""
    
    def delete(self, record_ids: list[str]) -> None:
        """批量删除"""
    
    def create_index(self, metric: str = "cosine") -> None:
        """创建向量索引 (IVF_PQ)"""
```

**数据表 Schema**:

```python
# memories 表结构
{
    "id": "string",           # 唯一ID
    "content": "string",      # 原始文本内容
    "vector": "vector(512)",  # 嵌入向量
    "source": "string",       # 来源标识
    "created_at": "datetime", # 创建时间
    "updated_at": "datetime", # 更新时间
    "expires_at": "datetime", # 过期时间 (nullable)
    "chunk_id": "string",     # 分块ID (用于关联)
    "metadata": "dict",       # 扩展元数据
    "hash": "string",         # 内容哈希 (用于去重)
}
```

---

### 2.2 嵌入生成层 (Embedding Generator)

**文件**: `core/embedder.py`

```python
class SentenceEmbedder:
    """句子嵌入生成器"""
    
    DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"
    DIMENSION = 512
    
    def __init__(self, model_name: str = None, cache_dir: str = None):
        self.model_name = model_name or self.DEFAULT_MODEL
        self.cache_dir = cache_dir or "models/sentence-transformers"
        self.model = None
        self._embedding_cache = {}  # LRU缓存
    
    def load_model(self) -> None:
        """
        加载模型（自动下载首次使用）
        支持本地缓存避免重复下载
        """
    
    def encode(
        self, 
        texts: str | list[str],
        normalize: bool = True,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        文本编码为向量
        
        Args:
            texts: 单条或多条文本
            normalize: 是否归一化（用于余弦相似度）
            batch_size: 批处理大小
        
        Returns:
            向量数组 (N, 512)
        """
    
    def encode_queries(self, queries: str | list[str]) -> np.ndarray:
        """
        查询语句编码（使用query前缀）
        BGE模型推荐: 查询前加 "represent this sentence for searching relevant passages: "
        """
```

**模型管理**:

```python
class ModelManager:
    """模型下载与管理"""
    
    MODELS = {
        "bge-small-zh": {
            "repo": "BAAI/bge-small-zh-v1.5",
            "dimension": 512,
            "description": "中文轻量模型，推荐",
        },
        "bge-base-zh": {
            "repo": "BAAI/bge-base-zh-v1.5", 
            "dimension": 768,
            "description": "中文基础模型",
        },
    }
    
    @classmethod
    def download_model(cls, model_key: str, cache_dir: str) -> str:
        """下载模型到本地缓存"""
    
    @classmethod
    def get_model_path(cls, model_key: str, cache_dir: str) -> str:
        """获取模型本地路径（不存在则下载）"""
```

---

### 2.3 查询接口层 (Query API)

**文件**: `core/query_engine.py`

```python
class MemoryQueryEngine:
    """记忆查询引擎"""
    
    def __init__(
        self, 
        vector_store: LanceDBStore,
        embedder: SentenceEmbedder
    ):
        self.store = vector_store
        self.embedder = embedder
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7,
        source_filter: str = None,
        time_range: tuple = None
    ) -> SearchResult:
        """
        语义搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            threshold: 相似度阈值 (0-1)
            source_filter: 来源过滤
            time_range: 时间范围过滤 (start, end)
        
        Returns:
            SearchResult 包含匹配的记忆列表
        """
    
    def search_with_rerank(
        self,
        query: str,
        top_k: int = 5,
        initial_k: int = 20
    ) -> SearchResult:
        """
        带重排序的搜索（先召回再精排）
        """
    
    def get_recent(
        self,
        limit: int = 10,
        source: str = None
    ) -> list[MemoryRecord]:
        """获取最近的记忆"""
    
    def get_by_time_range(
        self,
        start: datetime,
        end: datetime
    ) -> list[MemoryRecord]:
        """按时间范围查询"""
```

**返回数据结构**:

```python
@dataclass
class MemoryRecord:
    id: str
    content: str
    source: str
    created_at: datetime
    similarity: float = 0.0  # 仅搜索时填充
    metadata: dict = None

@dataclass  
class SearchResult:
    query: str
    results: list[MemoryRecord]
    total_found: int
    search_time_ms: float
```

---

### 2.4 记忆管理层 (Memory Manager)

**文件**: `core/memory_manager.py`

```python
class MemoryManager:
    """
    记忆管理器
    职责：分块、去重、过期管理、增量更新
    """
    
    def __init__(
        self,
        vector_store: LanceDBStore,
        embedder: SentenceEmbedder,
        chunker: TextChunker,
        config: MemoryConfig
    ):
        self.store = vector_store
        self.embedder = embedder
        self.chunker = chunker
        self.config = config
    
    # ─────────────────────────────────────────
    # 写入接口
    # ─────────────────────────────────────────
    
    def add(
        self,
        content: str,
        source: str = "default",
        metadata: dict = None,
        expires_in: timedelta = None
    ) -> list[str]:
        """
        添加记忆（自动分块、去重）
        
        Returns: 记录ID列表
        """
    
    def add_batch(
        self,
        items: list[MemoryItem]
    ) -> list[str]:
        """批量添加记忆"""
    
    def update(
        self,
        record_id: str,
        content: str = None,
        metadata: dict = None
    ) -> None:
        """更新记忆内容"""
    
    def delete(self, record_ids: list[str]) -> None:
        """删除记忆"""
    
    # ─────────────────────────────────────────
    # 自动维护
    # ─────────────────────────────────────────
    
    def cleanup_expired(self) -> int:
        """
        清理过期记忆
        Returns: 删除数量
        """
    
    def deduplicate(
        self,
        threshold: float = 0.95
    ) -> list[tuple[str, str]]:
        """
        检测并返回重复记忆
        Returns: [(keep_id, remove_id), ...]
        """
    
    def merge_similar(
        self,
        threshold: float = 0.9
    ) -> list[str]:
        """
        合并非相似记忆
        Returns: 合并后的新记录ID列表
        """
    
    def optimize(self) -> None:
        """优化存储（压缩、重建索引）"""
```

---

## 3. 分块策略 (Text Chunker)

**文件**: `core/chunker.py`

### 3.1 固定长度分块

```python
class FixedChunker:
    """固定长度分块器"""
    
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        split_by: str = "token"  # "token" | "char"
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.split_by = split_by
    
    def split(self, text: str) -> list[Chunk]:
        """将文本分割为块"""
```

### 3.2 语义分块

```python
class SemanticChunker:
    """
    基于语义的智能分块
    策略：
    1. 优先在段落边界分割
    2. 段落过长时按句子分割
    3. 保持上下文连贯性
    """
    
    def __init__(
        self,
        max_chunk_size: int = 512,
        min_chunk_size: int = 100,
        embedder: SentenceEmbedder = None  # 用于语义判断
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.embedder = embedder
    
    def split(self, text: str) -> list[Chunk]:
        """
        语义分块流程：
        1. 按段落初步分割
        2. 小段落合并（语义相似度>阈值）
        3. 大段落按句子分割
        """
```

**数据结构**:

```python
@dataclass
class Chunk:
    id: str
    content: str
    index: int           # 在原文中的顺序
    start_pos: int       # 原文起始位置
    end_pos: int         # 原文结束位置
    parent_id: str       # 父文档ID（用于追踪）
```

---

## 4. 数据流定义

### 4.1 写入流程

```
                    写入数据流
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    │   ┌─────────┐    ┌─────────┐    ┌──────────┐   │
    │   │  输入   │───▶│  分块   │───▶│ 去重检查  │   │
    │   │  Text   │    │ Chunker │    │ Deduplic │   │
    │   └─────────┘    └────┬────┘    └────┬─────┘   │
    │                       │               │         │
    │                       ▼               │         │
    │                  ┌─────────┐          │         │
    │                  │  Chunk  │          │         │
    │                  │  List   │          │         │
    │                  └────┬────┘          │         │
    │                       │               │         │
    │                       ▼               ▼         │
    │                  ┌─────────────────────────┐    │
    │                  │      嵌入生成层          │    │
    │                  │  SentenceEmbedder.encode │   │
    │                  └─────────────────────────┘    │
    │                              │                  │
    │                              ▼                  │
    │                  ┌─────────────────────────┐    │
    │                  │      向量存储层          │    │
    │                  │   LanceDBStore.add()    │    │
    │                  └─────────────────────────┘    │
    │                              │                  │
    │                              ▼                  │
    │                       ┌──────────┐              │
    │                       │ 返回 IDs │              │
    │                       └──────────┘              │
    │                                                 │
    └─────────────────────────────────────────────────┘
```

**代码示例**:

```python
async def add_memory_flow(content: str, source: str) -> list[str]:
    # 1. 分块
    chunks = chunker.split(content)
    
    # 2. 去重检查
    unique_chunks = []
    for chunk in chunks:
        chunk_hash = compute_hash(chunk.content)
        if not store.exists_by_hash(chunk_hash):
            unique_chunks.append(chunk)
    
    # 3. 嵌入生成
    texts = [c.content for c in unique_chunks]
    vectors = embedder.encode(texts)
    
    # 4. 构建记录
    records = []
    for chunk, vector in zip(unique_chunks, vectors):
        records.append({
            "id": generate_id(),
            "content": chunk.content,
            "vector": vector,
            "hash": compute_hash(chunk.content),
            "chunk_id": chunk.id,
            "source": source,
            "created_at": now(),
        })
    
    # 5. 存储
    return store.add_vectors(records)
```

### 4.2 查询流程

```
                    查询数据流
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    │   ┌─────────┐    ┌─────────────────────────┐    │
    │   │  查询   │───▶│      嵌入生成层          │    │
    │   │  Query  │    │  embedder.encode_query()│    │
    │   └─────────┘    └─────────────────────────┘    │
    │                              │                  │
    │                              ▼                  │
    │                  ┌─────────────────────────┐    │
    │                  │   查询向量 (512维)       │    │
    │                  └─────────────────────────┘    │
    │                              │                  │
    │                              ▼                  │
    │                  ┌─────────────────────────┐    │
    │                  │      向量存储层          │    │
    │                  │  store.search(vector)   │    │
    │                  │  - IVF索引检索           │    │
    │                  │  - 余弦相似度计算         │    │
    │                  └─────────────────────────┘    │
    │                              │                  │
    │                              ▼                  │
    │                  ┌─────────────────────────┐    │
    │                  │    候选结果 (top_k*2)    │    │
    │                  └─────────────────────────┘    │
    │                              │                  │
    │                              ▼                  │
    │                  ┌─────────────────────────┐    │
    │                  │      后处理层            │    │
    │                  │  - 阈值过滤              │    │
    │                  │  - 重排序 (可选)          │    │
    │                  │  - 元数据过滤            │    │
    │                  └─────────────────────────┘    │
    │                              │                  │
    │                              ▼                  │
    │                       ┌──────────┐              │
    │                       │ 最终结果  │              │
    │                       └──────────┘              │
    │                                                 │
    └─────────────────────────────────────────────────┘
```

---

## 5. 配置方案

### 5.1 配置文件模板

**文件**: `config/vector_memory.yaml`

```yaml
# ═══════════════════════════════════════════════════
# 向量记忆系统配置文件
# ═══════════════════════════════════════════════════

# ───────────────────────────────────────────────────
# 嵌入模型配置
# ───────────────────────────────────────────────────
embedding:
  # 模型选择
  # 推荐中文模型:
  #   - BAAI/bge-small-zh-v1.5 (默认, 512维, 轻量)
  #   - BAAI/bge-base-zh-v1.5 (768维, 效果更好)
  #   - BAAI/bge-large-zh-v1.5 (1024维, 最佳效果)
  model: "BAAI/bge-small-zh-v1.5"
  
  # 向量维度 (根据模型自动检测)
  dimension: 512
  
  # 模型缓存目录
  cache_dir: "models/sentence-transformers"
  
  # 是否使用GPU (CUDA)
  use_gpu: false
  
  # 批处理大小
  batch_size: 32
  
  # 查询前缀 (BGE模型推荐)
  query_prefix: "represent this sentence for searching relevant passages: "

# ───────────────────────────────────────────────────
# 分块配置
# ───────────────────────────────────────────────────
chunking:
  # 分块策略: "fixed" | "semantic"
  strategy: "semantic"
  
  # 固定长度分块配置
  fixed:
    chunk_size: 512        # 每块token数
    overlap: 50            # 重叠token数
    split_by: "token"      # "token" | "char"
  
  # 语义分块配置
  semantic:
    max_chunk_size: 512    # 最大块大小
    min_chunk_size: 100    # 最小块大小
    merge_threshold: 0.85  # 语义相似度阈值(合并段落)

# ───────────────────────────────────────────────────
# 向量存储配置 (LanceDB)
# ───────────────────────────────────────────────────
storage:
  # 存储路径
  db_path: "memory/vector"
  
  # 表名
  table_name: "memories"
  
  # 向量索引配置
  index:
    # 索引类型: "IVF_PQ" | "FLAT"
    type: "IVF_PQ"
    
    # 距离度量: "cosine" | "l2" | "dot"
    metric: "cosine"
    
    # IVF参数
    num_partitions: 256     # 分区数 (数据量大时增加)
    
    # PQ参数
    num_sub_vectors: 64     # 子向量数 (维度512时)
  
  # 自动优化
  auto_optimize:
    enabled: true
    threshold_mb: 100       # 超过此大小时自动优化

# ───────────────────────────────────────────────────
# 查询配置
# ───────────────────────────────────────────────────
query:
  # 默认返回结果数
  default_top_k: 5
  
  # 默认相似度阈值
  default_threshold: 0.7
  
  # 重排序配置
  reranking:
    enabled: false
    initial_k: 20          # 首次召回数量
    
  # 缓存配置
  cache:
    enabled: true
    max_size: 1000         # 最大缓存条目数
    ttl: 3600              # 缓存TTL(秒)

# ───────────────────────────────────────────────────
# 记忆管理配置
# ───────────────────────────────────────────────────
memory_management:
  # 去重配置
  deduplication:
    enabled: true
    threshold: 0.95        # 相似度超过此值视为重复
  
  # 过期管理
  expiration:
    enabled: true
    default_ttl_days: 365  # 默认过期时间
    
  # 自动清理
  cleanup:
    enabled: true
    interval_hours: 24     # 清理间隔
    
  # 增量更新
  incremental:
    enabled: true          # 支持增量更新
    max_batch_size: 100    # 批量更新大小

# ───────────────────────────────────────────────────
# 日志配置
# ───────────────────────────────────────────────────
logging:
  level: "INFO"            # DEBUG | INFO | WARNING | ERROR
  file: "logs/vector_memory.log"
  max_size_mb: 10
  backup_count: 5
```

### 5.2 环境变量配置

```bash
# .env 文件模板

# 模型配置
VECTOR_MEMORY_MODEL=BAAI/bge-small-zh-v1.5
VECTOR_MEMORY_CACHE_DIR=./models

# 存储配置
VECTOR_MEMORY_DB_PATH=./memory/vector

# 性能配置
VECTOR_MEMORY_BATCH_SIZE=32
VECTOR_MEMORY_USE_GPU=false

# 日志
VECTOR_MEMORY_LOG_LEVEL=INFO
```

---

## 6. 模块接口汇总

### 6.1 核心类接口

| 类名 | 文件 | 主要职责 |
|------|------|----------|
| `LanceDBStore` | `core/vector_store.py` | 向量存储封装 |
| `SentenceEmbedder` | `core/embedder.py` | 嵌入生成 |
| `ModelManager` | `core/embedder.py` | 模型下载管理 |
| `MemoryQueryEngine` | `core/query_engine.py` | 查询接口 |
| `MemoryManager` | `core/memory_manager.py` | 记忆生命周期管理 |
| `FixedChunker` | `core/chunker.py` | 固定长度分块 |
| `SemanticChunker` | `core/chunker.py` | 语义分块 |
| `MemoryConfig` | `config/config.py` | 配置管理 |

### 6.2 快速使用示例

```python
from vector_memory import MemorySystem

# 初始化（首次自动下载模型）
memory = MemorySystem.from_config("config/vector_memory.yaml")

# 添加记忆
ids = memory.add(
    content="用户说：明天下午3点开会",
    source="chat_session_001",
    expires_in=timedelta(days=7)
)

# 搜索记忆
results = memory.search(
    query="会议时间是什么时候？",
    top_k=5,
    threshold=0.7
)

for r in results.results:
    print(f"[{r.similarity:.2f}] {r.content}")

# 批量添加
data = [
    {"content": "...", "source": "doc1"},
    {"content": "...", "source": "doc2"},
]
memory.add_batch(data)

# 清理过期记忆
deleted_count = memory.cleanup_expired()
print(f"清理了 {deleted_count} 条过期记忆")
```

---

## 7. 技术要点说明

### 7.1 模型自动下载机制

```python
def ensure_model_loaded(model_name: str, cache_dir: str):
    """
    确保模型已下载到本地
    使用 HuggingFace snapshot_download 实现断点续传
    """
    from huggingface_hub import snapshot_download
    
    local_path = Path(cache_dir) / model_name.replace("/", "--")
    
    if not local_path.exists():
        print(f"首次使用，正在下载模型: {model_name}")
        snapshot_download(
            repo_id=model_name,
            local_dir=str(local_path),
            local_dir_use_symlinks=False
        )
    
    return str(local_path)
```

### 7.2 增量更新策略

```python
def incremental_update(self, new_items: list[MemoryItem]):
    """
    增量更新策略：
    1. 计算新内容的hash
    2. 查询已存在的hash
    3. 仅添加不存在的记录
    4. 批量写入（提高性能）
    """
    # 1. 计算hash
    new_hashes = [compute_hash(item.content) for item in new_items]
    
    # 2. 查询已有记录
    existing = self.store.find_by_hashes(new_hashes)
    existing_hashes = {r["hash"] for r in existing}
    
    # 3. 过滤已存在
    to_add = [
        item for item, h in zip(new_items, new_hashes)
        if h not in existing_hashes
    ]
    
    # 4. 批量写入
    if to_add:
        return self.add_batch(to_add)
    return []
```

### 7.3 索引策略

```python
def create_index(self):
    """
    IVF_PQ 索引说明：
    - IVF: 倒排文件索引，将向量空间划分为多个区域
    - PQ: 乘积量化，压缩向量减少存储
    
    适用场景：
    - 中等规模数据 (1万 - 100万向量)
    - 内存有限的情况
    - 对搜索速度有要求但可接受少量精度损失
    
    参数调优：
    - num_partitions: 通常设置为 sqrt(n_vectors)
    - num_sub_vectors: 维度/8 到 维度/4
    """
    self.table.create_index(
        metric="cosine",
        num_partitions=256,
        num_sub_vectors=64,
        vector_column_name="vector"
    )
```

---

## 8. 项目结构

```
vector_memory/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── vector_store.py      # LanceDB封装
│   ├── embedder.py          # 嵌入生成
│   ├── query_engine.py      # 查询接口
│   ├── memory_manager.py    # 记忆管理
│   └── chunker.py           # 分块策略
├── config/
│   ├── __init__.py
│   ├── config.py            # 配置加载
│   └── vector_memory.yaml   # 默认配置
├── models/                  # 模型缓存目录
│   └── sentence-transformers/
├── memory/                  # 向量数据存储
│   └── vector/
├── utils/
│   ├── __init__.py
│   └── helpers.py           # 工具函数
└── tests/
    └── test_*.py
```

---

## 9. 依赖清单

```txt
# requirements.txt
lancedb>=0.5.0
sentence-transformers>=2.2.0
numpy>=1.24.0
pyyaml>=6.0
pydantic>=2.0.0
tqdm>=4.65.0        # 下载进度条
```

---

## 10. 性能预期

| 指标 | 预期值 | 说明 |
|------|--------|------|
| 嵌入生成 | ~100 texts/sec | bge-small-zh, CPU |
| 向量搜索 | <10ms | 10万向量, IVF_PQ索引 |
| 存储空间 | ~2KB/向量 | 512维 + 元数据 |
| 内存占用 | ~200MB | 模型加载后 |

---

## 11. 演进路线与优化建议 (v2.1更新)

基于Agent记忆系统对比分析 (Signal 8深度学习)，提出以下优化方向：

### 11.1 短期优化 (1-2周)

#### MCP原生支持
封装记忆能力为MCP Server，接入Agent生态：
```python
# mcp_server.py - MCP协议封装
from mcp.server import Server

class MemoryMCPServer(Server):
    @tool
    async def memory_add(self, content: str, importance: int = 5, tags: list = None):
        """添加记忆到长期存储"""
        return await self.memory.add(content, importance=importance, tags=tags)
    
    @tool
    async def memory_search(self, query: str, top_k: int = 5):
        """语义检索相关记忆"""
        return await self.memory.search(query, top_k=top_k)
    
    @tool
    async def memory_get_context(self, topic: str, time_range: str = "1h"):
        """获取当前话题的上下文记忆"""
        return await self.memory.get_context_for_topic(topic, time_range)
```

#### 抗失忆压缩机制
解决上下文压缩导致的关键信息丢失：
```python
class AntiAmnesiaCompressor:
    KEY_PATTERNS = [
        r"(?:记住|别忘了|重要).+",  # 用户强调
        r"(?:决定|选择|同意).+",     # 决策信息
        r"(?:明天|下周|稍后).+",     # 时间约定
    ]
    
    def compress(self, context, max_tokens):
        # 1. 识别关键信息
        key_info = self.extract_key_info(context)
        # 2. 预留关键信息空间
        # 3. 压缩非关键内容
        # 4. 向量备份原始内容
```

### 11.2 中期优化 (1个月)

#### 分层记忆架构完善
实现L1-L5完整分层：
```
L1 瞬时记忆 (Sensory)     → 内存缓存，当前对话窗口
L2 工作记忆 (Working)     → SQLite，当日高频访问
L3 短期记忆 (Short-term)  → LanceDB，本周语义检索
L4 长期记忆 (Long-term)   → 压缩归档，持久化存储
L5 永久记忆 (Permanent)   → 关键事实结构化存储
```

#### LongMemEval基准测试
接入行业标准评估框架：
```python
# 长上下文记忆评估
from benchmarks import LongMemEval

evaluator = LongMemEval()
results = evaluator.evaluate(memory_system)
# 目标: 达到85%+准确率 (当前SOTA 92.8%)
```

### 11.3 长期规划 (3个月)

#### 实体关系图谱
增强记忆关联能力：
```python
class EntityGraph:
    def extract_entities(self, text) -> List[Entity]:
        """使用NER提取实体"""
        
    def link_relations(self, e1: Entity, e2: Entity, relation: str):
        """建立实体关系边"""
        
    def get_related_memories(self, entity: Entity) -> List[Memory]:
        """获取关联记忆"""
```

#### 主动回忆机制
从被动检索转向主动召回：
```python
class ProactiveRecall:
    def __init__(self):
        self.time_decay = TimeDecayModel()
        self.association_graph = AssociationGraph()
    
    def predict_relevant_memories(self, current_topic) -> List[Memory]:
        """基于当前话题预测可能相关的记忆"""
        # 1. 时序关联
        # 2. 主题关联
        # 3. 用户行为模式
```

### 11.4 竞品对标矩阵

| 维度 | Engram | MemoryStack | mem0 | 森森目标 |
|------|--------|-------------|------|----------|
| **存储引擎** | SQLite | 自定义 | Pinecone | LanceDB ✓ |
| **协议支持** | MCP ✓ | MCP | 多协议 | MCP ⏳ |
| **中文优化** | 一般 | 未验证 | 一般 | **优秀** ✓ |
| **LongMemEval** | 未公开 | **92.8%** | 未公开 | 目标85%+ ⏳ |
| **分层架构** | 基础 | **完善** | 完善 | 完善 ⏳ |
| **生态集成** | 新兴 | 学术界 | **47k stars** | 扩展中 ⏳ |

---

*文档版本: 1.1*  
*最后更新: 2026-02-14 (Signal 8深度学习内化)*
