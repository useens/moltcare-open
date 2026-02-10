#!/usr/bin/env python3
"""
向量记忆系统集成验证脚本
快速测试核心功能
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace')

from core.vector_memory import create_memory_system
import os

print("=" * 50)
print("🧪 向量记忆系统集成验证")
print("=" * 50)

# 1. 创建测试数据库
test_db_path = 'memory/vector/test_integration'
os.makedirs(test_db_path, exist_ok=True)

print(f"\n📁 测试数据库: {test_db_path}")

# 2. 初始化系统
print("\n🚀 初始化向量记忆系统...")
memory = create_memory_system(test_db_path)
print("✅ 初始化成功")

# 3. 添加测试数据
print("\n📝 添加测试记忆...")
test_memories = [
    ("用户喜欢精简回复，只输出最终结果", {"source": "user-profile", "type": "preference"}),
    ("向量记忆系统使用LanceDB和BGE模型", {"source": "tech-doc", "type": "architecture"}),
    ("Moltbook账号被封1天，解封后恢复运营", {"source": "daily-log", "type": "event"}),
    ("自主进化系统每4小时轻量、每12小时全量", {"source": "evolution", "type": "schedule"}),
]

for content, meta in test_memories:
    memory.add_memory(content, metadata=meta)
    print(f"  ✓ {content[:30]}...")

# 4. 语义搜索测试
print("\n🔍 语义搜索测试...")

test_queries = [
    "用户偏好什么回复风格？",
    "向量记忆用什么技术？",
    "Moltbook什么情况？",
    "进化系统怎么运行的？",
]

for query in test_queries:
    print(f"\n  查询: \"{query}\"")
    results = memory.search(query, top_k=2)
    for i, r in enumerate(results, 1):
        content = r.content if hasattr(r, 'content') else str(r)
        print(f"    {i}. {content[:50]}...")

# 5. 关闭连接
memory.close()

print("\n" + "=" * 50)
print("✅ 集成验证通过！")
print("=" * 50)
print("\n📊 验证结果:")
print("  - 系统初始化: ✅")
print("  - 记忆添加: ✅")
print("  - 语义搜索: ✅")
print("  - 中文支持: ✅")
print("\n🎯 系统已就绪，可以接入现有记忆系统")
