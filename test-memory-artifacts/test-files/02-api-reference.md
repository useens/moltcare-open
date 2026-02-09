# API 参考文档

## memory_search(query, options)

搜索记忆系统。

### 参数
- `query` (string): 搜索查询
- `options.maxResults` (number): 最大结果数，默认5

### 返回值
返回匹配结果数组，每个结果包含：
- `path`: 文件路径
- `lines`: 行号范围
- `score`: 相似度分数
- `snippet`: 内容片段

### 示例
```javascript
const results = await memorySearch("机器学习", { maxResults: 3 });
console.log(results[0].snippet);
```
