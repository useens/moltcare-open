#!/usr/bin/env python3
"""
修复记忆导入 - 直接使用 LanceDB 和 HuggingFace
"""
import os
import sys
import time
import json
from pathlib import Path

# 设置路径
os.chdir('/root/.openclaw/workspace/core/vector_memory')
sys.path.insert(0, '.')

# 直接导入基础组件（避免相对导入问题）
from vector_store import VectorStore
from embedder import Embedder, EmbeddingConfig
from memory_search import MemorySearch, SearchConfig

# 配置
MEMORY_DIR = Path('/root/.openclaw/workspace/memory')
DB_PATH = MEMORY_DIR / 'vector/production'

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """将文本分块"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():  # 只保留非空块
            chunks.append(chunk)
        start = end - overlap
    return chunks

def import_memories():
    """导入所有记忆文件"""
    print("=" * 60)
    print("🚀 开始修复记忆导入")
    print("=" * 60)
    
    # 1. 找到所有记忆文件
    md_files = []
    json_files = []
    
    for root, dirs, files in os.walk(MEMORY_DIR):
        # 跳过 vector 目录
        if 'vector' in root:
            continue
        for f in files:
            filepath = Path(root) / f
            if f.endswith('.md'):
                md_files.append(filepath)
            elif f.endswith('.json'):
                json_files.append(filepath)
    
    print(f"\n📁 找到文件:")
    print(f"   - Markdown: {len(md_files)} 个")
    print(f"   - JSON: {len(json_files)} 个")
    print(f"   - 总计: {len(md_files) + len(json_files)} 个")
    
    # 2. 初始化组件
    print("\n🔧 初始化嵌入模型...")
    embed_config = EmbeddingConfig(model_name="BAAI/bge-large-zh-v1.5", device="auto")
    embedder = Embedder(embed_config)
    
    print("🔧 初始化向量存储...")
    store = VectorStore(db_path=DB_PATH, table_name="memories", embedding_dim=1024)
    store.initialize()
    
    # 清空现有数据（重新导入）
    current_count = store.count()
    print(f"\n📊 当前数据库: {current_count} 条向量")
    if current_count > 0:
        print("⚠️  将清空后重新导入...")
        store.delete_all()
    
    # 3. 处理 Markdown 文件
    total_chunks = 0
    processed_files = 0
    errors = []
    
    print(f"\n📖 处理 Markdown 文件 ({len(md_files)} 个)...")
    for i, filepath in enumerate(md_files, 1):
        try:
            # 读取文件
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                continue
            
            # 分块
            chunks = chunk_text(content, chunk_size=500, overlap=50)
            
            if not chunks:
                continue
            
            # 批量编码
            embeddings = embedder.encode(chunks, show_progress=False)
            
            # 准备记录
            records = []
            for j, (chunk_text_content, embedding) in enumerate(zip(chunks, embeddings)):
                rel_path = str(filepath.relative_to(MEMORY_DIR))
                meta = {
                    "source": rel_path,
                    "chunk_index": j,
                    "total_chunks": len(chunks),
                    "file_mtime": filepath.stat().st_mtime
                }
                records.append((embedding, chunk_text_content, meta))
            
            # 批量添加
            if records:
                store.add_batch(records)
                total_chunks += len(records)
                processed_files += 1
                
                if i % 10 == 0:
                    print(f"   ✓ 已处理 {i}/{len(md_files)} 文件 ({total_chunks} 块)")
                else:
                    print(f"   ✓ {filepath.name} ({len(chunks)} 块)")
                    
        except Exception as e:
            errors.append((filepath, str(e)))
            print(f"   ✗ {filepath.name}: {e}")
    
    # 4. 处理 JSON 文件
    if json_files:
        print(f"\n📄 处理 JSON 文件 ({len(json_files)} 个)...")
        for i, filepath in enumerate(json_files, 1):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 尝试提取文本内容
                contents = []
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, str):
                            contents.append(item)
                        elif isinstance(item, dict):
                            content = item.get('content') or item.get('text') or str(item)
                            contents.append(content)
                elif isinstance(data, dict):
                    content = data.get('content') or data.get('text') or str(data)
                    contents.append(content)
                elif isinstance(data, str):
                    contents.append(data)
                
                # 过滤和分块
                all_chunks = []
                for content in contents:
                    if len(content) > 500:
                        all_chunks.extend(chunk_text(content))
                    else:
                        all_chunks.append(content)
                
                if all_chunks:
                    embeddings = embedder.encode(all_chunks, show_progress=False)
                    records = []
                    for j, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
                        rel_path = str(filepath.relative_to(MEMORY_DIR))
                        meta = {
                            "source": rel_path,
                            "chunk_index": j,
                            "type": "json"
                        }
                        records.append((embedding, chunk, meta))
                    
                    store.add_batch(records)
                    total_chunks += len(records)
                    processed_files += 1
                    print(f"   ✓ {filepath.name} ({len(records)} 块)")
                    
            except Exception as e:
                errors.append((filepath, str(e)))
                print(f"   ✗ {filepath.name}: {e}")
    
    # 5. 优化索引
    print("\n🔍 优化索引...")
    store.optimize()
    
    # 6. 最终统计
    final_count = store.count()
    print("\n" + "=" * 60)
    print("✅ 导入完成!")
    print("=" * 60)
    print(f"\n📊 统计:")
    print(f"   - 处理文件: {processed_files}")
    print(f"   - 总块数: {total_chunks}")
    print(f"   - 最终向量: {final_count}")
    print(f"   - 错误数: {len(errors)}")
    
    if errors:
        print(f"\n⚠️  错误详情 ({len(errors)}):")
        for filepath, err in errors[:5]:
            print(f"   - {filepath.name}: {err}")
    
    return store, embedder

def test_performance(store, embedder):
    """测试查询性能"""
    print("\n" + "=" * 60)
    print("🧪 测试查询性能")
    print("=" * 60)
    
    # 创建搜索器
    search_config = SearchConfig()
    searcher = MemorySearch(vector_store=store, embedder=embedder, config=search_config)
    
    # 测试查询
    test_queries = [
        "用户偏好",
        "自主进化",
        "Moltbook",
        "备份策略",
        "飞书配置",
        "向量记忆",
        "高可用架构",
        "永生计划"
    ]
    
    times = []
    for query in test_queries:
        start = time.time()
        results = searcher.semantic_search(query, top_k=3)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        print(f'   "{query}": {elapsed:.1f}ms - {len(results)}条结果')
    
    avg_time = sum(times) / len(times)
    print(f"\n📈 平均查询时间: {avg_time:.1f}ms")
    
    # 展示示例结果
    print("\n📝 示例查询结果 (\"自主进化\"):")
    results = searcher.semantic_search("自主进化", top_k=2)
    for i, r in enumerate(results, 1):
        preview = r.content[:100].replace('\n', ' ')
        print(f"   {i}. [{r.score:.3f}] {preview}...")
        print(f"      来源: {r.metadata.get('source', 'unknown')}")
    
    return avg_time

if __name__ == "__main__":
    # 执行导入
    store, embedder = import_memories()
    
    # 测试性能
    avg_time = test_performance(store, embedder)
    
    # 完成
    final_count = store.count()
    print("\n" + "=" * 60)
    print("🎉 修复完成!")
    print("=" * 60)
    print(f"\n✅ 向量记忆系统已就绪")
    print(f"   - 数据库: {final_count} 条向量")
    print(f"   - 平均查询: {avg_time:.1f}ms")
    
    if final_count < 100:
        print(f"\n⚠️  警告: 向量数较少，请检查文件路径")
