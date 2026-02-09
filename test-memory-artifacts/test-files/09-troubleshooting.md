# 故障排除

## 常见问题

### 模型加载失败
**症状**: 首次运行时卡住
**解决**: 检查网络连接，模型约80MB

### 内存不足
**症状**: 进程被杀死
**解决**: 增加swap空间或减少并发

### 搜索结果为空
**症状**: 有索引但无结果
**解决**: 检查相似度阈值，尝试降低

## 调试模式

### 启用详细日志
```bash
export DEBUG=memory:*
node vector_memory_local.js --search "test"
```

### 检查向量数据库
```bash
cat vector-memory/vectors_local.json | jq '.chunks | length'
```
