#!/usr/bin/env python3
"""
测试脚本 - 本地记忆系统
"""

import os
import sys
import tempfile

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from local_memory import LocalMemorySystem

def test_init():
    """测试初始化"""
    print("\n🧪 测试: 初始化系统")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = LocalMemorySystem(tmpdir)
        memory.init()
        
        assert os.path.exists(os.path.join(tmpdir, "memory.db"))
        print("✅ 初始化测试通过")

def test_index_and_search():
    """测试索引和搜索"""
    print("\n🧪 测试: 索引和搜索")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = LocalMemorySystem(tmpdir)
        memory.init()
        
        # 创建测试文件
        test_content_1 = """
# Python 异步编程

async def main():
    await asyncio.sleep(1)
    print("Hello, async world!")

asyncio.run(main())
"""
        
        test_content_2 = """
# JavaScript Promise

Promise 是 JavaScript 中处理异步操作的方式。
可以使用 async/await 语法糖来简化代码。

async function fetchData() {
    const data = await fetch('/api/data');
    return data.json();
}
"""
        
        test_content_3 = """
# 食谱: 红烧肉

材料:
- 五花肉 500g
- 生抽 2勺
- 老抽 1勺
- 冰糖 30g

步骤:
1. 五花肉切块焯水
2. 锅中放油炒糖色
3. 加入肉块翻炒上色
4. 加入调料和热水炖煮
"""
        
        # 写入临时文件
        file1 = os.path.join(tmpdir, "file1.md")
        file2 = os.path.join(tmpdir, "file2.md")
        file3 = os.path.join(tmpdir, "file3.md")
        
        with open(file1, 'w') as f:
            f.write(test_content_1)
        with open(file2, 'w') as f:
            f.write(test_content_2)
        with open(file3, 'w') as f:
            f.write(test_content_3)
        
        # 索引文件
        print("📄 索引文件 1: Python 异步编程")
        memory.index_file(file1)
        
        print("📄 索引文件 2: JavaScript Promise")
        memory.index_file(file2)
        
        print("📄 索引文件 3: 红烧肉食谱")
        memory.index_file(file3)
        
        # 测试搜索
        print("\n🔍 搜索 'async programming':")
        results = memory.search("async programming", top_k=3)
        assert len(results) >= 1
        for r in results:
            print(f"  - {r['file_path']} (相似度: {r.get('similarity', 'N/A'):.4f})")
        
        print("\n🔍 搜索 '如何烹饪':")
        results = memory.search("如何烹饪", top_k=3)
        for r in results:
            print(f"  - {r['file_path']}")
        
        print("\n🔍 关键词搜索 'JavaScript':")
        results = memory.search("JavaScript", top_k=3, use_vector=False)
        assert len(results) >= 1
        print("✅ 搜索测试通过")

def test_related():
    """测试关联发现"""
    print("\n🧪 测试: 关联发现")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = LocalMemorySystem(tmpdir)
        memory.init()
        
        # 创建两个相关的文件
        content1 = "Python 的 asyncio 库提供了异步编程支持。"
        content2 = "JavaScript 的 async/await 语法与 Python 类似。"
        content3 = "红烧肉是一道经典的中式菜肴。"
        
        file1 = os.path.join(tmpdir, "python-async.md")
        file2 = os.path.join(tmpdir, "js-async.md")
        file3 = os.path.join(tmpdir, "recipe.md")
        
        with open(file1, 'w') as f:
            f.write(content1)
        with open(file2, 'w') as f:
            f.write(content2)
        with open(file3, 'w') as f:
            f.write(content3)
        
        memory.index_file(file1)
        memory.index_file(file2)
        memory.index_file(file3)
        
        # 查找与文档 1 相关的文档
        print("🔗 查找与文档 1 (Python async) 相关的文档:")
        results = memory.find_related(1, top_k=2)
        for r in results:
            print(f"  - ID {r['id']}: {r['file_path']} (相似度: {r['similarity']:.4f})")
        
        # 验证文档2应该与文档1相关 (都是关于 async 编程)
        js_doc = [r for r in results if 'js-async' in r['file_path']]
        if js_doc:
            print("✅ 正确发现 JS async 与 Python async 相关")
        
        print("✅ 关联测试通过")

def test_list_and_stats():
    """测试列表和统计"""
    print("\n🧪 测试: 列表和统计")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = LocalMemorySystem(tmpdir)
        memory.init()
        
        # 索引几个文件
        for i in range(3):
            fpath = os.path.join(tmpdir, f"test{i}.md")
            with open(fpath, 'w') as f:
                f.write(f"Test content {i}")
            memory.index_file(fpath)
        
        # 测试列表
        docs = memory.list_documents()
        assert len(docs) == 3
        print(f"📄 列出 {len(docs)} 个文档")
        
        # 测试统计
        stats = memory.get_stats()
        print(f"📊 统计: {stats['document_count']} 文档, {stats['vector_count']} 向量")
        assert stats['document_count'] == 3
        assert stats['vector_count'] == 3
        
        print("✅ 列表和统计测试通过")

def main():
    print("=" * 50)
    print("🧠 本地记忆系统测试套件")
    print("=" * 50)
    
    try:
        test_init()
        test_index_and_search()
        test_related()
        test_list_and_stats()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过!")
        print("=" * 50)
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
