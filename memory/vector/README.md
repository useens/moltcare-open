# 向量记忆系统 v1.0

基于语义相似度的记忆检索系统，让林林能够从记忆文件中基于语义搜索，而非仅靠关键词匹配。

## 架构概述

```
┌─────────────────────────────────────────────────────────────┐
│                     向量记忆系统 v1.0                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  MD文件收集  │───→│  文本分块    │───→│  向量化     │     │
│  │  (modules/) │    │  (chunks)   │    │  (384-dim)  │     │
│  └─────────────┘    └─────────────┘    └──────┬──────┘     │
│                                               │             │
│  ┌─────────────┐    ┌─────────────┐    ┌──────▼──────┐     │
│  │  搜索结果    │←───│  相似度计算  │←───│  向量存储   │     │
│  │  (ranked)   │    │  (cosine)   │    │  (faiss/np) │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                               ↑             │
│  ┌─────────────┐    ┌─────────────┐         │             │
│  │  增量更新    │───→│  元数据管理  │─────────┘             │
│  │  (hash/mtime)│    │  (JSON)     │                       │
│  └─────────────┘    └─────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. indexer.py - 索引器
负责扫描、处理和向量化记忆文件：
- 递归扫描 `memory/modules/` 下的所有 `.md` 文件
- 提取文档元数据（标题、标签、链接）
- 将长文档分块处理（默认512字符）
- 使用 `sentence-transformers/all-MiniLM-L6-v2` 生成384维向量
- 增量更新机制（基于文件哈希）

### 2. search.py - 搜索模块
提供语义搜索功能：
- 查询向量化
- 余弦相似度计算
- 结果排序和相关性评分
- 支持过滤（按标签、文档类型）

### 3. storage.py - 存储层
本地存储实现：
- 向量：NumPy数组 (`.npy`)
- 元数据：JSON文件 (`.json`)
- 索引映射：块ID到文档路径的映射

## 技术规格

| 项目 | 规格 |
|------|------|
| 嵌入模型 | sentence-transformers/all-MiniLM-L6-v2 |
| 向量维度 | 384 |
| 距离度量 | 余弦相似度 |
| 分块大小 | 512 字符（可配置） |
| 重叠大小 | 128 字符（可配置） |
| 存储格式 | NumPy + JSON |
| 支持文件 | `.md` 文件 |

## 快速开始

### 1. 初始化索引
```bash
cd memory/vector
python indexer.py
```

### 2. 执行搜索
```python
from search import MemorySearch

search = MemorySearch()
results = search.query("用户偏好设置", top_k=5)

for r in results:
    print(f"[{r['score']:.3f}] {r['title']}")
    print(f"    {r['snippet']}")
```

### 3. 增量更新
```bash
python indexer.py --incremental
```

## 文件结构

```
memory/vector/
├── README.md          # 本文件
├── indexer.py         # 索引脚本
├── search.py          # 搜索模块
├── storage.py         # 存储抽象层
├── test.py            # 测试用例
├── config.json        # 配置
└── data/              # 数据目录（自动生成）
    ├── vectors.npy    # 向量数据
    ├── metadata.json  # 元数据
    └── index.json     # 索引映射
```

## API参考

### Indexer 类
```python
from indexer import MemoryIndexer

indexer = MemoryIndexer(
    modules_dir="../modules",
    model_name="all-MiniLM-L6-v2",
    chunk_size=512,
    chunk_overlap=128
)

# 完整重建索引
indexer.build_index()

# 增量更新
indexer.incremental_update()

# 获取统计
stats = indexer.get_stats()
```

### Search 类
```python
from search import MemorySearch

search = MemorySearch()

# 基础搜索
results = search.query("安全审计流程", top_k=5)

# 带过滤的搜索
results = search.query(
    "配置优化",
    top_k=5,
    filters={"tags": ["技能", "配置"]}
)
```

## 增量更新机制

系统使用文件哈希检测变更：
1. 计算每个文件的MD5哈希
2. 与上次索引时的哈希对比
3. 仅处理新增或修改的文件
4. 删除已移除文件的向量

```python
# 在Python中调用
indexer.incremental_update()

# 或通过命令行
python indexer.py --incremental
```

## 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 索引速度 | ~100 docs/min | 取决于文档大小 |
| 搜索延迟 | < 100ms | 1000文档以内 |
| 内存占用 | ~50MB | 包含模型 |
| 向量文件 | ~1.5KB/文档 | 384维float32 |

## 扩展计划

### v1.1 (计划中)
- [ ] 多语言支持（中文优化模型）
- [ ] 混合搜索（语义 + 关键词）
- [ ] 搜索结果重排序

### v1.2 (规划中)
- [ ] FAISS集成（大规模加速）
- [ ] 实时索引更新
- [ ] 搜索结果缓存

## 注意事项

1. **首次索引较慢**：需要下载模型（~80MB）
2. **中文支持**：MiniLM对中文支持良好，但非最优
3. **文件变更**：大量文件变更时建议重建索引
4. **内存限制**：超过10000文档建议启用FAISS

## 依赖

```
sentence-transformers>=2.0.0
numpy>=1.20.0
```

## 许可

MIT License - 作为Moltbot/OpenClaw生态的一部分
