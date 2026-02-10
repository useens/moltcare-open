#!/usr/bin/env python3
"""
修复记忆导入 - 手动分批导入所有记忆文件
"""
import os
import sys
import time

# 设置路径
sys.path.insert(0, '/root/.openclaw/workspace/core/vector_memory')

from vector_store import VectorStore
from embedder import Embedder
from memory_manager import MemoryManager, Chunk

# 文件路径配置
MEMORY_DIR = '/root/.openclaw/workspace/memory'
DB_PATH = os.path.join(MEMORY_DIR, 'vector/production')

# 统计
stats = {
    'files_processed': 0,
    'files_failed': 0,
    'chunks_created': 0,
    'errors': []
}

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """将文本分块"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

def import_markdown_files():
    """导入所有 markdown 记忆文件"""
    print("=" * 50)
    print("开始导入 Markdown 记忆文件")
    print("=" * 50)
    
    # 搜索所有 markdown 文件
    md_files = []
    for root, dirs, files in os.walk(MEMORY_DIR):
        # 跳过 vector 目录
        if 'vector' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))
    
    print(f"\n找到 {len(md_files)} 个 Markdown 文件")
    
    # 初始化
    mm = MemoryManager()
    
    # 处理每个文件
    for i, filepath in enumerate(md_files, 1):
        try:
            print(f"\n[{i}/{len(md_files)}] {filepath}...", end=" ")
            
            # 读取文件
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print("跳过（空文件）")
                continue
            
            # 分块
            text_chunks = chunk_text(content, chunk_size=500, overlap=50)
            
            # 创建 Chunk 对象并添加
            for j, text_chunk in enumerate(text_chunks):
                chunk = Chunk(
                    content=text_chunk,
                    source=os.path.relpath(filepath, MEMORY_DIR),
                    chunk_type="daily_memory",
                    timestamp=os.path.getmtime(filepath)
                )
                mm.add_memory(chunk)
                stats['chunks_created'] += 1
            
            stats['files_processed'] += 1
            print(f"✓ ({len(text_chunks)} 块)")
            
            # 每10个文件刷新一次
            if i % 10 == 0:
                current_count = mm.store.table.count_rows()
                print(f"  ↳ 数据库当前: {current_count} 条向量")
                
        except Exception as e:
            stats['files_failed'] += 1
            stats['errors'].append(f"{filepath}: {str(e)}")
            print(f"✗ 错误: {e}")
    
    # 最终统计
    final_count = mm.store.table.count_rows()
    print("\n" + "=" * 50)
    print("导入完成!")
    print("=" * 50)
    print(f"\n📊 统计:")
    print(f"  - 处理文件: {stats['files_processed']}")
    print(f"  - 失败文件: {stats['files_failed']}")
    print(f"  - 创建块数: {stats['chunks_created']}")
    print(f"  - 最终向量数: {final_count}")
    
    if stats['errors']:
        print(f"\n⚠️ 错误 ({len(stats['errors'])}):")
        for err in stats['errors'][:5]:
            print(f"  - {err}")
    
    return final_count

def test_queries():
    """测试查询性能"""
    print("\n" + "=" * 50)
    print("测试查询性能")
    print("=" * 50)
    
    mm = MemoryManager()
    test_queries_list = [
        "用户偏好",
        "自主进化",
        "Moltbook",
        "备份策略",
        "飞书配置",
        "向量记忆",
        "高可用架构"
    ]
    
    times = []
    for query in test_queries_list:
        start = time.time()
        results = mm.search_memories(query, k=3)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        print(f'  "{query}": {elapsed:.1f}ms - {len(results)}条结果')
    
    avg_time = sum(times) / len(times)
    print(f"\n📈 平均查询时间: {avg_time:.1f}ms")
    
    return avg_time

if __name__ == "__main__":
    # 步骤1: 导入
    final_count = import_markdown_files()
    
    # 步骤2: 测试查询
    if final_count > 0:
        avg_time = test_queries()
        
        print("\n" + "=" * 50)
        print("修复完成!")
        print("=" * 50)
        print(f"\n✅ 向量记忆系统已就绪")
        print(f"   - 数据库: {final_count} 条向量")
        print(f"   - 平均查询: {avg_time:.1f}ms")
    else:
        print("\n⚠️ 导入失败，数据库为空")
