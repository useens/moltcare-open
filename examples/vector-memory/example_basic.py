#!/usr/bin/env python3
"""
示例1: 基础使用示例 - Basic Usage Example

展示向量记忆系统的核心功能：
- 初始化系统
- 索引文档
- 语义搜索
- 关联发现
"""

import os
import sys
import tempfile

# 添加local-memory-system到路径
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/local-memory-system'))

from local_memory import LocalMemorySystem


def demo_basic_usage():
    """基础使用演示"""
    
    print("=" * 60)
    print("🧠 向量记忆系统 - 基础使用示例")
    print("=" * 60)
    
    # 使用临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. 初始化系统
        print("\n1️⃣ 初始化记忆系统...")
        memory = LocalMemorySystem(tmpdir)
        memory.init()
        print(f"   ✅ 系统初始化完成: {tmpdir}")
        
        # 2. 创建示例文档
        print("\n2️⃣ 创建示例文档...")
        
        docs = [
            ("python_async.md", """
# Python 异步编程指南

asyncio 是 Python 标准库中的异步 I/O 框架。

核心概念:
- async/await 语法
- 事件循环 (Event Loop)
- 协程 (Coroutine)
- Task 和 Future

async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.example.com') as resp:
            return await resp.json()
"""),
            ("js_promise.md", """
# JavaScript Promise 完全指南

Promise 是 JavaScript 中处理异步操作的对象。

特点:
- 三种状态: pending, fulfilled, rejected
- 链式调用 .then() .catch()
- async/await 语法糖

async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Failed to fetch user:', error);
        throw error;
    }
}
"""),
            ("recipe_zh.md", """
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
"""),
            ("ml_intro.md", """
# 机器学习入门

机器学习是人工智能的一个分支，让计算机能够从数据中学习。

主要类型:
1. 监督学习 (Supervised Learning) - 有标签数据
2. 无监督学习 (Unsupervised Learning) - 无标签数据
3. 强化学习 (Reinforcement Learning) - 奖励机制

深度学习是机器学习的一个子集，使用神经网络处理复杂模式。
""")
        ]
        
        for filename, content in docs:
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   📝 创建: {filename}")
        
        # 3. 索引文档
        print("\n3️⃣ 索引文档到记忆系统...")
        for filename, _ in docs:
            filepath = os.path.join(tmpdir, filename)
            memory.index_file(filepath)
        print("   ✅ 所有文档索引完成")
        
        # 4. 语义搜索演示
        print("\n4️⃣ 语义搜索演示...")
        
        queries = [
            "如何编写异步代码",  # 中文查询
            "cooking Chinese food",  # 英文查询
            "neural networks and deep learning",  # 技术查询
        ]
        
        for query in queries:
            print(f"\n   🔍 查询: '{query}'")
            results = memory.search(query, top_k=2)
            
            for i, r in enumerate(results, 1):
                print(f"      {i}. {os.path.basename(r['file_path'])} (相似度: {r['similarity']:.4f})")
        
        # 5. 关联发现演示
        print("\n5️⃣ 关联发现演示...")
        
        # 获取Python文档的ID
        all_docs = memory.list_documents()
        python_doc = next((d for d in all_docs if 'python' in d['file_path']), None)
        
        if python_doc:
            print(f"\n   🔗 查找与 '{os.path.basename(python_doc['file_path'])}' 相关的文档:")
            related = memory.find_related(python_doc['id'], top_k=2)
            
            for r in related:
                print(f"      - {os.path.basename(r['file_path'])} (相似度: {r['similarity']:.4f})")
        
        # 6. 查看统计
        print("\n6️⃣ 系统统计:")
        stats = memory.get_stats()
        print(f"   📄 文档数量: {stats['document_count']}")
        print(f"   🔢 向量数量: {stats['vector_count']}")
        print(f"   💾 数据库大小: {stats['db_size'] / 1024:.2f} KB")
        
        print("\n" + "=" * 60)
        print("✅ 示例完成!")
        print("=" * 60)


if __name__ == '__main__':
    try:
        demo_basic_usage()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
