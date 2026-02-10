# Vector Memory System Architecture 架构说明

> 向量记忆系统的详细架构设计和技术实现

---

## 🏗️ 系统架构 System Architecture

### 整体架构 Overall Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Vector Memory System                                  │
│                         向量记忆系统 v1.0                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         API Layer 接口层                             │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│   │  │    init     │  │    index    │  │   search    │  │   related  │  │   │
│   │  │    初始化    │  │    索引     │  │    搜索     │  │   关联发现  │  │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      Core Layer 核心层                               │   │
│   │                                                                     │   │
│   │   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐     │   │
│   │   │   Document   │─────▶│   Embedding  │─────▶│   Storage    │     │   │
│   │   │   Manager    │      │   Engine     │      │   Manager    │     │   │
│   │   │   文档管理    │      │   嵌入引擎    │      │   存储管理    │     │   │
│   │   └──────────────┘      └──────────────┘      └──────────────┘     │   │
│   │          │                     │                     │             │   │
│   │          ▼                     ▼                     ▼             │   │
│   │   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐     │   │
│   │   │  File I/O    │      │ MiniLM Model │      │   SQLite     │     │   │
│   │   │   文件IO     │      │   嵌入模型    │      │   Database   │     │   │
│   │   └──────────────┘      └──────────────┘      └──────────────┘     │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      Data Layer 数据层                               │   │
│   │                                                                     │   │
│   │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │   │
│   │   │   Documents     │  │    Vectors      │  │  Connections    │    │   │
│   │   │     文档表       │  │     向量表       │  │    关联表        │    │   │
│   │   │                 │  │                 │  │                 │    │   │
│   │   │ - id            │  │ - doc_id        │  │ - source_id     │    │   │
│   │   │ - file_path     │  │ - embedding     │  │ - target_id     │    │   │
│   │   │ - content       │  │   (384-dim)     │  │ - strength      │    │   │
│   │   │ - content_hash  │  │                 │  │                 │    │   │
│   │   │ - timestamps    │  │                 │  │                 │    │   │
│   │   └─────────────────┘  └─────────────────┘  └─────────────────┘    │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 数据流说明 Data Flow

### 1. 文档索引流程 Document Indexing Flow

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Input  │────▶│    Text     │────▶│   MiniLM    │────▶│   SQLite    │
│  File   │     │ Extraction  │     │  Embedding  │     │   Storage   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     │                │                   │                   │
     │                │                   │                   │
     ▼                ▼                   ▼                   ▼
  .md, .txt      Read Content       384-dim Vector      documents
  .py, .json     SHA256 Hash        float32 array       vectors
                                      ↓                   ↓
                                 ┌─────────┐        ┌─────────┐
                                 │  all-   │        │  BLOB   │
                                 │ MiniLM  │        │ Storage │
                                 │ -L6-v2  │        │         │
                                 └─────────┘        └─────────┘
```

**详细步骤 Detailed Steps:**

1. **文件读取** File Reading
   ```python
   with open(file_path, 'r', encoding='utf-8') as f:
       content = f.read()
   ```

2. **内容哈希** Content Hashing
   ```python
   content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
   ```

3. **变更检测** Change Detection
   ```sql
   SELECT content_hash FROM documents WHERE file_path = ?
   ```

4. **嵌入生成** Embedding Generation
   ```python
   embedding = model.encode(content, convert_to_numpy=True)
   # Shape: (384,) dtype: float32
   ```

5. **数据存储** Data Storage
   ```sql
   INSERT INTO documents (file_path, content, content_hash) VALUES (?, ?, ?);
   INSERT INTO document_vectors (doc_id, embedding) VALUES (?, ?);
   ```

### 2. 语义搜索流程 Semantic Search Flow

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Query  │────▶│   MiniLM    │────▶│   Vector    │────▶│   Ranking   │
│ String  │     │  Embedding  │     │  Compare    │     │   & Sort    │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     │                │                   │                   │
     │                │                   │                   │
     ▼                ▼                   ▼                   ▼
 "asyncio"      384-dim Vector      Cosine Similarity    Top K Results
  tutorial       float32 array       with all docs        (k=5 default)
                                      ↓
                               ┌─────────────┐
                               │  Similarity │
                               │    Score    │
                               │   (0-1)     │
                               └─────────────┘
```

**相似度计算 Similarity Calculation:**

```python
# 余弦相似度 Cosine Similarity
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 实际搜索实现
query_embedding = model.encode(query)
for doc in all_documents:
    doc_embedding = np.frombuffer(doc.embedding_bytes, dtype=np.float32)
    similarity = cosine_similarity(query_embedding, doc_embedding)
    results.append((doc, similarity))

# 按相似度排序
results.sort(key=lambda x: x[1], reverse=True)
return results[:top_k]
```

### 3. 关联发现流程 Related Discovery Flow

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Doc    │────▶│   Get Its   │────▶│   Compare   │────▶│   Return    │
│  ID     │     │  Embedding  │     │ with Others │     │   Top K     │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     │                │                   │                   │
     │                │                   │                   │
     ▼                ▼                   ▼                   ▼
    ID=1          384-dim Vector      Similarity with       Related Docs
                   from DB            all other docs        (excluding self)
```

---

## 📊 数据库结构 Database Schema

### 实体关系图 ER Diagram

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    documents    │◄───────│ document_vectors│         │   connections   │
├─────────────────┤   1:1   ├─────────────────┤         ├─────────────────┤
│ PK id           │◄────────│ PK doc_id       │         │ PK id           │
│    file_path    │         │    embedding    │         │ FK source_doc_id│──────┐
│    content      │         │    (BLOB)       │         │ FK target_doc_id│──────┼────┐
│    content_hash │         └─────────────────┘         │    strength     │      │    │
│    created_at   │                                     │    created_at   │      │    │
│    updated_at   │                                     └─────────────────┘      │    │
└─────────────────┘                                                              │    │
       ▲                                                                         │    │
       │                                                                         │    │
       └─────────────────────────────────────────────────────────────────────────┘    │
                                                                                      │
       └──────────────────────────────────────────────────────────────────────────────┘
```

### 表结构 Table Schemas

#### documents 文档表

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 文档唯一ID
    file_path TEXT UNIQUE NOT NULL,         -- 文件绝对路径
    content TEXT NOT NULL,                  -- 文档完整内容
    content_hash TEXT NOT NULL,             -- 内容SHA256哈希(前16位)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 更新时间
);

-- 索引 Indexes
CREATE INDEX idx_documents_path ON documents(file_path);
CREATE INDEX idx_documents_updated ON documents(updated_at);
```

**字段说明:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER | 主键，自增 |
| `file_path` | TEXT | 文件绝对路径，唯一约束 |
| `content` | TEXT | 文档完整内容 |
| `content_hash` | TEXT | SHA256哈希前16位，用于变更检测 |
| `created_at` | TIMESTAMP | 记录创建时间 |
| `updated_at` | TIMESTAMP | 记录更新时间 |

#### document_vectors 向量表

```sql
CREATE TABLE document_vectors (
    doc_id INTEGER PRIMARY KEY,             -- 文档ID（外键）
    embedding BLOB NOT NULL,                -- 384维float32向量
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
);
```

**存储格式:**

```python
# NumPy数组转BLOB
embedding = model.encode(text)  # np.ndarray shape=(384,), dtype=float32
embedding_bytes = embedding.astype(np.float32).tobytes()
# 存储到SQLite: 384 * 4 = 1536 bytes

# BLOB转NumPy数组
embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
```

#### connections 关联表

```sql
CREATE TABLE connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_doc_id INTEGER NOT NULL,         -- 源文档ID
    target_doc_id INTEGER NOT NULL,         -- 目标文档ID
    connection_type TEXT DEFAULT 'related', -- 关联类型
    strength REAL DEFAULT 1.0,              -- 关联强度(0-1)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_doc_id) REFERENCES documents(id),
    FOREIGN KEY (target_doc_id) REFERENCES documents(id),
    UNIQUE(source_doc_id, target_doc_id)    -- 避免重复关联
);

-- 索引
CREATE INDEX idx_connections_source ON connections(source_doc_id);
CREATE INDEX idx_connections_target ON connections(target_doc_id);
```

---

## ⚡ 性能特点 Performance Characteristics

### 时间复杂度 Time Complexity

| 操作 Operation | 复杂度 Complexity | 说明 Notes |
|--------------|------------------|-----------|
| 索引单个文档 | O(n) | n=token数量，模型前向传播 |
| 搜索 | O(m × d) | m=文档数, d=384维度 |
| 关联发现 | O(m × d) | 同搜索 |
| 插入 | O(1) | SQLite插入 |
| 删除 | O(1) | 级联删除 |

### 空间复杂度 Space Complexity

| 数据类型 Data | 大小 Size | 说明 Notes |
|-------------|----------|-----------|
| 单个向量 | 1,536 bytes | 384 × float32 |
| 文档元数据 | ~500 bytes | 取决于内容长度 |
| 每文档总计 | ~2KB | 向量 + 元数据 |
| 1万文档 | ~20MB | 预估 |
| 10万文档 | ~200MB | 预估 |

### 性能指标 Performance Metrics

```
┌─────────────────────────────────────────────────────────────┐
│                    Performance Benchmarks                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  索引性能 Indexing Performance                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  100 documents/min  (single-threaded)                 │  │
│  │  ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  搜索延迟 Search Latency                                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1,000 docs:  ~50ms                                   │  │
│  │  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  │
│  │  10,000 docs: ~200ms                                  │  │
│  │  ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  内存占用 Memory Usage                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Model:     ~100MB                                    │  │
│  │  ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  │
│  │  1K docs:   ~10MB                                     │  │
│  │  █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  │
│  │  10K docs:  ~100MB                                    │  │
│  │  ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 扩展性分析 Scalability Analysis

**当前架构限制 Current Limitations:**

1. **线性搜索** - 当前使用暴力搜索O(m)，适合万级文档
2. **单线程** - 模型推理和搜索都是单线程
3. **内存加载** - 搜索时需加载所有向量到内存

**未来优化方向 Future Optimizations:**

```
┌─────────────────────────────────────────────────────────────┐
│                  Potential Optimizations                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 向量索引 Vector Index                                    │
│     ┌─────────────────────────────────────────────────────┐ │
│     │  HNSW (Hierarchical Navigable Small World)         │ │
│     │  - 搜索复杂度: O(log m)                            │ │
│     │  - 适合百万级向量                                  │ │
│     │  - 可用: faiss, hnswlib                            │ │
│     └─────────────────────────────────────────────────────┘ │
│                                                              │
│  2. 批处理 Batch Processing                                  │
│     ┌─────────────────────────────────────────────────────┐ │
│     │  - 批量嵌入生成                                    │ │
│     │  - GPU加速 (CUDA)                                  │ │
│     │  - 多线程索引                                      │ │
│     └─────────────────────────────────────────────────────┘ │
│                                                              │
│  3. 分片存储 Sharded Storage                                 │
│     ┌─────────────────────────────────────────────────────┐ │
│     │  - 按类别/时间分片                                 │ │
│     │  - 减少单次搜索范围                                │ │
│     │  - 适合超大规模数据                                │ │
│     └─────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 技术选型 Technology Choices

### 为什么选SQLite Why SQLite

| 优势 | 说明 |
|------|------|
| 零配置 | 无需安装服务器，开箱即用 |
| 单文件 | 易于备份和迁移 |
| 跨平台 | Windows/Linux/macOS/嵌入式 |
| 成熟稳定 | 30年历史，经生产验证 |
| Python内置 | 无需额外依赖 |

### 为什么选MiniLM Why MiniLM

| 优势 | 说明 |
|------|------|
| 轻量 | 22M参数，80MB模型大小 |
| 快速 | CPU推理速度快 |
| 多语言 | 支持100+语言 |
| 高质量 | MTEB榜单表现优秀 |
| 开源 | Apache 2.0许可证 |

### 对比其他方案 Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    Alternative Solutions                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Current: SQLite + MiniLM                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ✅ 零依赖部署    ✅ 完全本地    ✅ 资源占用低          │   │
│  │ ❌ 规模受限      ❌ 无GPU加速   ❌ 单线程              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Alternative A: LanceDB + MiniLM                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ✅ 列式存储      ✅ 高性能      ✅ 多模态              │   │
│  │ ⚠️ 额外依赖      ⚠️ 学习成本                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Alternative B: Chroma + OpenAI                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ✅ 功能丰富      ✅ 生态好                               │   │
│  │ ❌ 需要API       ❌ 有成本      ❌ 数据出本地          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Alternative C: Qdrant + Local Model                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ✅ 企业级        ✅ 分布式      ✅ 高性能              │   │
│  │ ❌ 需要服务器    ❌ 资源占用高                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ 容错设计 Fault Tolerance

### 数据完整性 Data Integrity

```python
# 1. 事务保证 Transaction Guarantee
def index_file(self, file_path: str, content: str = None):
    conn = self._get_connection()
    try:
        conn.execute("BEGIN TRANSACTION")
        # ... 插入文档 ...
        # ... 插入向量 ...
        conn.execute("COMMIT")
    except Exception as e:
        conn.execute("ROLLBACK")
        raise

# 2. 外键约束 Foreign Key Constraints
# SQLite外键确保向量与文档一致性

# 3. 内容校验 Content Verification
content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
# 检测重复和变更
```

### 错误处理 Error Handling

| 错误类型 | 处理策略 |
|---------|---------|
| 文件读取失败 | 跳过并记录警告 |
| 模型加载失败 | 延迟加载，首次使用时初始化 |
| 数据库锁定 | 重试机制 |
| 内存不足 | 分批处理 |

---

## 📈 未来扩展 Future Extensions

### 路线图 Roadmap

```
Version 1.0 (Current)          Version 1.1                  Version 2.0
┌─────────────────────┐       ┌─────────────────────┐      ┌─────────────────────┐
│ ✅ SQLite Storage   │       │ 🔄 HNSW Index       │      │ 🔄 Vector Sharding  │
│ ✅ MiniLM Embed     │──────▶│ 🔄 Batch Process    │─────▶│ 🔄 GPU Acceleration │
│ ✅ Cosine Search    │       │ 🔄 Hybrid Search    │      │ 🔄 Distributed DB   │
│ ✅ Related Discovery│       │ 🔄 Metadata Filter  │      │ 🔄 Cloud Sync       │
└─────────────────────┘       └─────────────────────┘      └─────────────────────┘
```

### 计划功能 Planned Features

1. **混合搜索** - 向量搜索 + 关键词搜索 + 元数据过滤
2. **文档分块** - 长文档自动分块索引
3. **增量更新** - 只更新变更的部分
4. **多模态支持** - 图像、音频嵌入
5. **版本控制** - 文档历史版本管理

---

## 📚 参考 Reference

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Sentence Transformers](https://www.sbert.net/)
- [all-MiniLM-L6-v2 Model](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

---

*Last Updated: 2026-02-10*
