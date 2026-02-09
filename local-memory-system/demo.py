#!/usr/bin/env python3
"""
快速演示 - 本地记忆系统
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from local_memory import LocalMemorySystem

def demo():
    print("=" * 60)
    print("🧠 本地记忆系统演示")
    print("=" * 60)
    
    # 使用临时目录演示
    demo_dir = "/tmp/local-memory-demo"
    os.makedirs(demo_dir, exist_ok=True)
    
    memory = LocalMemorySystem(demo_dir)
    
    # 1. 初始化
    print("\n1️⃣ 初始化系统...")
    memory.init()
    
    # 2. 创建并索引一些文档
    print("\n2️⃣ 创建并索引文档...")
    
    docs = [
        ("python-async.md", """
# Python 异步编程指南

asyncio 是 Python 标准库中的异步 I/O 框架。

核心概念:
- async/await 语法
- 事件循环
- 协程 (Coroutine)
- Task 和 Future

示例代码:
```python
import asyncio

async def main():
    await asyncio.sleep(1)
    print("Hello, async world!")

asyncio.run(main())
```
"""),
        ("js-promise.md", """
# JavaScript Promise 完全指南

Promise 是 JavaScript 中处理异步操作的对象。

特点:
- 三种状态: pending, fulfilled, rejected
- 链式调用 .then() .catch()
- async/await 语法糖

示例:
```javascript
async function fetchData() {
    try {
        const data = await fetch('/api/data');
        return await data.json();
    } catch (error) {
        console.error('Error:', error);
    }
}
```
"""),
        ("ml-intro.md", """
# 机器学习入门

机器学习是人工智能的一个分支，让计算机能够从数据中学习。

主要类型:
1. 监督学习 (Supervised Learning)
2. 无监督学习 (Unsupervised Learning)
3. 强化学习 (Reinforcement Learning)

常用算法:
- 线性回归
- 决策树
- 神经网络
- 支持向量机
"""),
        ("recipe-red-cooked-pork.md", """
# 红烧肉食谱

经典中式菜肴，肥而不腻，入口即化。

材料:
- 五花肉 500g
- 生抽 2勺
- 老抽 1勺
- 冰糖 30g
- 料酒 2勺
- 生姜 3片
- 八角 2个

步骤:
1. 五花肉切块，冷水下锅焯水去腥
2. 锅中放少许油，加入冰糖炒出糖色
3. 下肉块翻炒至上色
4. 加入生抽、老抽、料酒、姜片、八角
5. 加入热水没过肉块，大火烧开后转小火炖煮1小时
6. 大火收汁，装盘即可
""")
    ]
    
    for filename, content in docs:
        filepath = os.path.join(demo_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"\n📝 索引: {filename}")
        memory.index_file(filepath)
    
    # 3. 搜索演示
    print("\n3️⃣ 搜索演示...")
    
    queries = [
        "异步编程教程",
        "如何烹饪红烧肉",
        "machine learning algorithms"
    ]
    
    for query in queries:
        print(f"\n🔍 搜索: '{query}'")
        results = memory.search(query, top_k=3)
        for i, r in enumerate(results[:2], 1):
            print(f"  {i}. {os.path.basename(r['file_path'])} (相似度: {r['similarity']:.4f})")
    
    # 4. 关联发现演示
    print("\n4️⃣ 关联发现演示...")
    print("🔍 查找与 Python 异步编程相关的文档:")
    
    # 找到 Python 文档的 ID
    docs_list = memory.list_documents()
    python_doc = [d for d in docs_list if 'python' in d['file_path']][0]
    
    related = memory.find_related(python_doc['id'], top_k=2)
    for r in related:
        print(f"  - {os.path.basename(r['file_path'])} (相似度: {r['similarity']:.4f})")
    
    # 5. 统计信息
    print("\n5️⃣ 系统统计:")
    stats = memory.get_stats()
    print(f"  📄 文档数量: {stats['document_count']}")
    print(f"  🔢 向量数量: {stats['vector_count']}")
    print(f"  💾 数据库大小: {stats['db_size'] / 1024:.2f} KB")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)
    print(f"\n演示数据保存在: {demo_dir}")

if __name__ == '__main__':
    demo()
