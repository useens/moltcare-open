# 数据库设计

## 向量数据库选型

### 本地存储
- JSON文件: <1000 chunks
- SQLite + 向量扩展: <10000 chunks
- PostgreSQL + pgvector: >10000 chunks

## 索引结构

### HNSW
Hierarchical Navigable Small World
- 近似最近邻搜索
- 构建时间: O(n log n)
- 查询时间: O(log n)

### IVF
Inverted File Index
- 适合大规模数据
- 内存效率高
