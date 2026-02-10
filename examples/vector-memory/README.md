# Vector Memory System Examples 使用示例

> 向量记忆系统的实用代码示例

---

## 📁 示例列表

| 示例 | 文件名 | 说明 |
|------|--------|------|
| 基础使用 | `example_basic.py` | 展示核心API使用 |
| Agent集成 | `example_agent_integration.py` | 与AI Agent系统集成 |
| 数据迁移 | `example_migration.py` | 批量迁移现有数据 |

---

## 🚀 运行示例

### 前置条件 Prerequisites

```bash
# 确保已安装依赖
pip install sentence-transformers numpy

# 设置Python路径
export PYTHONPATH="$HOME/.openclaw/workspace/local-memory-system:$PYTHONPATH"
```

### 运行基础示例 Run Basic Example

```bash
cd ~/.openclaw/workspace/examples/vector-memory

python example_basic.py
```

**预期输出:**
```
============================================================
🧠 向量记忆系统 - 基础使用示例
============================================================

1️⃣ 初始化记忆系统...
   ✅ 系统初始化完成: /tmp/...

2️⃣ 创建示例文档...
   📝 创建: python_async.md
   📝 创建: js_promise.md
   ...

3️⃣ 索引文档到记忆系统...
   ✅ 所有文档索引完成

4️⃣ 语义搜索演示...

   🔍 查询: '如何编写异步代码'
      1. python_async.md (相似度: 0.8234)
      2. js_promise.md (相似度: 0.6789)

5️⃣ 关联发现演示...
   🔗 查找与 'python_async.md' 相关的文档:
      - js_promise.md (相似度: 0.7234)
```

### 运行Agent集成示例 Run Agent Integration

```bash
python example_agent_integration.py
```

**展示内容:**
- 如何封装适配器类
- 兼容旧版`memory_search`接口
- 在Agent中使用语义搜索
- 发现相关记忆

### 运行迁移示例 Run Migration Example

```bash
python example_migration.py
```

**展示内容:**
- 预览迁移（dry-run模式）
- 批量索引文件
- 验证迁移结果
- 搜索测试

---

## 📖 示例代码说明

### 基础使用 Basic Usage

```python
from local_memory import LocalMemorySystem

# 初始化
memory = LocalMemorySystem()
memory.init()

# 索引文件
memory.index_file("path/to/document.md")

# 语义搜索
results = memory.search("your query", top_k=5)
for r in results:
    print(f"{r['file_path']}: {r['similarity']:.4f}")
```

### 适配器模式 Adapter Pattern

```python
class VectorMemoryAdapter:
    """兼容旧接口的适配器"""
    
    def __init__(self):
        self.memory = LocalMemorySystem()
    
    def search(self, query, top_k=5):
        return self.memory.search(query, top_k)
    
    # 兼容旧接口
    def search_contents(self, query, top_k=5):
        results = self.memory.search(query, top_k)
        return [r['content_preview'] for r in results]
```

### 批量迁移 Bulk Migration

```python
migrator = MemoryMigrator(
    source_dir="memory/",
    target_dir="~/.openclaw/memory-vector"
)

# 预览
migrator.migrate(dry_run=True)

# 执行
migrator.migrate(dry_run=False)

# 验证
migrator.verify()
```

---

## 🔧 自定义示例

### 创建自己的示例

```python
#!/usr/bin/env python3
"""自定义示例"""

import sys
import os
sys.path.insert(0, os.path.expanduser(
    '~/.openclaw/workspace/local-memory-system'
))

from local_memory import LocalMemorySystem

def my_example():
    memory = LocalMemorySystem()
    memory.init()
    
    # 你的代码...
    results = memory.search("your query")
    print(results)

if __name__ == '__main__':
    my_example()
```

---

## 🐛 故障排除

### 模块找不到

```bash
# 添加路径
export PYTHONPATH="$HOME/.openclaw/workspace/local-memory-system:$PYTHONPATH"

# 或在代码中添加
import sys
sys.path.insert(0, os.path.expanduser(
    '~/.openclaw/workspace/local-memory-system'
))
```

### 模型下载慢

```bash
# 设置镜像
export HF_ENDPOINT=https://hf-mirror.com
```

---

## 📚 更多资源

- [README.md](../../docs/vector-memory/README.md) - 完整文档
- [integration-guide.md](../../docs/vector-memory/integration-guide.md) - 集成指南
- [architecture.md](../../docs/vector-memory/architecture.md) - 架构说明

---

*Last Updated: 2026-02-10*
