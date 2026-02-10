# Vector Memory System Integration Guide 集成指南

> 如何将向量记忆系统集成到现有OpenClaw系统

---

## 📋 概述 Overview

本指南介绍如何将向量记忆系统集成到现有的OpenClaw AI代理系统中，包括如何替换现有的`memory_search`调用、迁移现有记忆数据和配置说明。

---

## 🔄 替换 memory_search 调用

### 现有调用方式 Legacy Approach

```python
# 旧方式：基于关键词的记忆搜索
def memory_search(query: str) -> List[str]:
    """关键词搜索记忆文件"""
    results = []
    for file in memory_files:
        if query.lower() in file.content.lower():
            results.append(file.content)
    return results
```

### 新调用方式 New Approach

```python
from local_memory import LocalMemorySystem

# 初始化向量记忆系统
memory = LocalMemorySystem()

def memory_search(query: str, top_k: int = 5) -> List[Dict]:
    """语义搜索记忆"""
    return memory.search(query, top_k=top_k)
```

### 迁移示例 Migration Example

**场景：搜索与用户偏好相关的记忆**

```python
# ========== 迁移前 Before ==========
def get_user_preferences():
    """获取用户偏好设置"""
    # 关键词搜索，可能遗漏语义相关的内容
    results = memory_search("preference")
    results.extend(memory_search("like"))
    results.extend(memory_search("prefer"))
    return results

# ========== 迁移后 After ==========
def get_user_preferences():
    """获取用户偏好设置"""
    # 语义搜索，理解查询意图
    results = memory.search("用户偏好和喜好设置", top_k=10)
    return [r['content_preview'] for r in results]
```

**场景：查找相关技术文档**

```python
# ========== 迁移前 Before ==========
def find_tech_docs(topic: str):
    """查找技术文档"""
    keywords = topic.split() + ["tech", "code", "programming"]
    results = []
    for kw in keywords:
        results.extend(memory_search(kw))
    return list(set(results))  # 去重

# ========== 迁移后 After ==========
def find_tech_docs(topic: str):
    """查找技术文档"""
    # 语义搜索自动理解技术概念
    results = memory.search(topic, top_k=10)
    
    # 还可以查找相关内容
    if results:
        related = memory.find_related(results[0]['id'], top_k=5)
        results.extend(related)
    
    return results
```

---

## 🚚 迁移现有记忆数据

### 迁移策略 Migration Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                  数据迁移流程 Data Migration Flow            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: 备份现有数据                                        │
│  ┌─────────────────────────────────────┐                    │
│  │  cp -r memory/ memory-backup-$(date │                    │
│  │  +%Y%m%d)/                          │                    │
│  └─────────────────────────────────────┘                    │
│                         │                                    │
│                         ▼                                    │
│  Step 2: 初始化向量系统                                      │
│  ┌─────────────────────────────────────┐                    │
│  │  python local_memory.py init         │                    │
│  └─────────────────────────────────────┘                    │
│                         │                                    │
│                         ▼                                    │
│  Step 3: 批量索引现有文件                                    │
│  ┌─────────────────────────────────────┐                    │
│  │  for file in memory/**/*.md:         │                    │
│  │      memory.index_file(file)         │                    │
│  └─────────────────────────────────────┘                    │
│                         │                                    │
│                         ▼                                    │
│  Step 4: 验证迁移                                          │
│  ┌─────────────────────────────────────┐                    │
│  │  python local_memory.py stats        │                    │
│  │  python local_memory.py list         │                    │
│  └─────────────────────────────────────┘                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 批量迁移脚本 Bulk Migration Script

```python
#!/usr/bin/env python3
"""
bulk_migrate.py - 批量迁移现有记忆数据到向量系统
"""

import os
import sys
from pathlib import Path
from local_memory import LocalMemorySystem

def migrate_memory_system(source_dir: str, dry_run: bool = False):
    """
    迁移现有记忆文件到向量记忆系统
    
    Args:
        source_dir: 源记忆目录（如 memory/）
        dry_run: 是否仅预览，不实际执行
    """
    memory = LocalMemorySystem()
    
    # 统计信息
    stats = {
        'total_files': 0,
        'indexed': 0,
        'skipped': 0,
        'errors': 0
    }
    
    print(f"🔍 扫描目录: {source_dir}")
    print(f"📝 模式: {'预览' if dry_run else '实际迁移'}\n")
    
    # 支持的文件类型
    supported_extensions = {'.md', '.txt', '.rst', '.py', '.js', '.json'}
    
    source_path = Path(source_dir)
    
    for file_path in source_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in supported_extensions:
            stats['total_files'] += 1
            
            if dry_run:
                print(f"[预览] 将索引: {file_path}")
            else:
                try:
                    memory.index_file(str(file_path))
                    stats['indexed'] += 1
                except Exception as e:
                    print(f"❌ 错误: {file_path} - {e}")
                    stats['errors'] += 1
    
    print("\n" + "=" * 50)
    print("📊 迁移统计:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  成功索引: {stats['indexed']}")
    print(f"  跳过: {stats['skipped']}")
    print(f"  错误: {stats['errors']}")
    print("=" * 50)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='批量迁移记忆数据')
    parser.add_argument('--source', default='memory/', help='源记忆目录')
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    
    args = parser.parse_args()
    
    migrate_memory_system(args.source, args.dry_run)
```

### 迁移检查清单 Migration Checklist

- [ ] **备份现有数据** - 复制memory/目录到备份位置
- [ ] **安装依赖** - 确保sentence-transformers已安装
- [ ] **初始化向量系统** - 运行`python local_memory.py init`
- [ ] **执行迁移** - 运行批量迁移脚本
- [ ] **验证数据** - 检查文档数量和向量数量是否匹配
- [ ] **测试搜索** - 验证语义搜索功能正常
- [ ] **更新代码** - 替换memory_search调用
- [ ] **回滚计划** - 如遇到问题可快速回滚到关键词搜索

---

## ⚙️ 配置说明 Configuration

### 目录结构 Directory Structure

```
workspace/
├── local-memory-system/
│   ├── local_memory.py          # 核心模块
│   ├── requirements.txt         # 依赖
│   └── README.md               # 说明文档
├── docs/vector-memory/          # 本文档目录
├── examples/vector-memory/      # 示例代码
└── ~/.local-memory/            # 默认数据目录
    ├── memory.db               # SQLite数据库
    └── files/                  # 文件存储
```

### 配置文件 Configuration File

```python
# config/memory_config.py
"""向量记忆系统配置"""

MEMORY_CONFIG = {
    # 存储配置
    'memory_dir': '~/.local-memory',
    
    # 模型配置
    'model': {
        'name': 'all-MiniLM-L6-v2',
        'dimension': 384,
        'max_length': 256,
    },
    
    # 搜索配置
    'search': {
        'default_top_k': 5,
        'similarity_threshold': 0.5,  # 最低相似度阈值
    },
    
    # 索引配置
    'indexing': {
        'chunk_size': 1000,           # 文档分块大小
        'chunk_overlap': 100,         # 分块重叠大小
        'supported_extensions': [
            '.md', '.txt', '.rst', 
            '.py', '.js', '.json'
        ],
    }
}
```

### 环境配置 Environment Configuration

```bash
# ~/.bashrc 或 ~/.zshrc

# 向量记忆系统配置
export MEMORY_DIR="$HOME/.openclaw/memory-vector"
export MEMORY_MODEL="all-MiniLM-L6-v2"

# HuggingFace镜像（中国大陆）
export HF_ENDPOINT="https://hf-mirror.com"

# 模型缓存目录
export HF_HOME="$HOME/.cache/huggingface"
```

### OpenClaw 集成 Integration with OpenClaw

```python
# ~/.openclaw/workspace/modules/vector_memory_adapter.py
"""
向量记忆系统适配器 - 集成到OpenClaw
"""

import sys
import os

# 添加local-memory-system到路径
sys.path.insert(0, os.path.expanduser(
    '~/.openclaw/workspace/local-memory-system'
))

from local_memory import LocalMemorySystem

class VectorMemoryAdapter:
    """OpenClaw向量记忆适配器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._memory = None
        return cls._instance
    
    @property
    def memory(self):
        """懒加载记忆系统"""
        if self._memory is None:
            memory_dir = os.environ.get(
                'MEMORY_DIR', 
                os.path.expanduser('~/.openclaw/memory-vector')
            )
            self._memory = LocalMemorySystem(memory_dir)
        return self._memory
    
    def search(self, query: str, top_k: int = 5):
        """搜索记忆 - 替换原有memory_search"""
        return self.memory.search(query, top_k=top_k)
    
    def index_file(self, file_path: str):
        """索引文件"""
        return self.memory.index_file(file_path)
    
    def find_related(self, doc_id: int, top_k: int = 5):
        """查找相关文档"""
        return self.memory.find_related(doc_id, top_k=top_k)

# 全局实例
def get_memory() -> VectorMemoryAdapter:
    """获取记忆系统实例"""
    return VectorMemoryAdapter()

# 兼容旧接口
def memory_search(query: str, top_k: int = 5):
    """兼容旧版memory_search接口"""
    adapter = get_memory()
    results = adapter.search(query, top_k)
    return [r['content_preview'] for r in results]
```

### 使用示例 Usage Example

```python
# 在Agent代码中使用
from modules.vector_memory_adapter import get_memory, memory_search

class MyAgent:
    def __init__(self):
        self.memory = get_memory()
    
    def recall_context(self, query: str):
        """回忆相关上下文"""
        # 新方法：语义搜索
        results = self.memory.search(query, top_k=5)
        
        # 或兼容旧方法
        results = memory_search(query, top_k=5)
        
        return results
    
    def learn_from_file(self, file_path: str):
        """从文件学习"""
        self.memory.index_file(file_path)
```

---

## 🔍 回滚方案 Rollback Plan

### 快速回滚 Quick Rollback

如遇到问题，可快速切换回关键词搜索：

```python
# config/feature_flags.py
USE_VECTOR_MEMORY = False  # 设为False回滚到关键词搜索

# memory_search.py
def memory_search(query: str, top_k: int = 5):
    if USE_VECTOR_MEMORY:
        from modules.vector_memory_adapter import get_memory
        return get_memory().search(query, top_k)
    else:
        return legacy_keyword_search(query, top_k)
```

### 数据安全 Data Safety

- 向量系统**不会修改**原始记忆文件
- 所有向量数据存储在独立目录（默认`~/.local-memory/`）
- 可随时删除向量数据而不影响原始文件

---

## 📊 性能对比 Performance Comparison

| 场景 Scenario | 关键词搜索 | 向量搜索 | 提升 |
|--------------|-----------|---------|------|
| "Python异步" 找 "asyncio" | ❌ 找不到 | ✅ 找到 | 语义理解 |
| "如何做饭" 找 "食谱" | ❌ 找不到 | ✅ 找到 | 语义关联 |
| "机器学习" 找 "ML" | ❌ 找不到 | ✅ 找到 | 同义词识别 |
| 多语言混合查询 | ❌ 有限支持 | ✅ 支持 | 跨语言检索 |

---

## 🆘 故障排除 Troubleshooting

### 常见问题 Common Issues

**Q: 模型下载慢/失败**
```bash
# 设置镜像
export HF_ENDPOINT=https://hf-mirror.com
```

**Q: 内存不足**
```python
# 使用更小的模型
memory._get_model = lambda: SentenceTransformer('paraphrase-MiniLM-L3-v2')
```

**Q: 搜索结果不准确**
```python
# 调整相似度阈值
results = [r for r in results if r['similarity'] > 0.7]
```

---

## 📚 参考文档 Reference

- [README.md](./README.md) - 快速开始和API参考
- [architecture.md](./architecture.md) - 架构详细说明
- [../examples/](../examples/) - 使用示例

---

*Last Updated: 2026-02-10*
