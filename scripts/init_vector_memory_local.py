#!/usr/bin/env python3
"""
向量记忆系统初始化脚本

功能：
1. 下载/加载本地嵌入模型 (sentence-transformers)
2. 扫描 memory 目录下的所有记忆文件
3. 生成向量并存储到 LanceDB
4. 创建索引

用法：
    python3 init_vector_memory.py
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_status(message: str):
    """打印带时间戳的状态信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def init_embedding_model():
    """初始化本地嵌入模型"""
    print_status("🚀 步骤 1/5: 加载本地嵌入模型...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # 使用轻量级多语言模型，支持中文，384维
        model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        
        print_status(f"   模型: {model_name}")
        print_status("   首次下载可能需要2-5分钟...")
        
        # 加载模型（会自动下载到本地缓存）
        model = SentenceTransformer(model_name)
        
        # 测试编码
        test_text = "测试向量记忆系统"
        test_vector = model.encode(test_text, show_progress_bar=False)
        
        print_status(f"   ✅ 模型加载成功")
        print_status(f"   📊 向量维度: {len(test_vector)}")
        print_status(f"   💾 模型缓存: ~/.cache/torch/sentence_transformers/")
        
        return model
        
    except Exception as e:
        print_status(f"   ❌ 模型加载失败: {e}")
        raise

def scan_memory_files(workspace_path: Path) -> List[Dict[str, Any]]:
    """扫描记忆文件"""
    print_status("🔍 步骤 2/5: 扫描记忆文件...")
    
    memory_files = []
    memory_paths = [
        workspace_path / "memory",
        workspace_path / "memory" / "modules",
        workspace_path / "memory" / "knowledge",
    ]
    
    for base_path in memory_paths:
        if not base_path.exists():
            continue
            
        for md_file in base_path.rglob("*.md"):
            # 跳过 trash 和 reports
            if ".trash" in str(md_file) or "reports" in str(md_file):
                continue
                
            try:
                content = md_file.read_text(encoding='utf-8')
                if len(content.strip()) < 50:  # 跳过太短的文件
                    continue
                    
                memory_files.append({
                    "path": str(md_file.relative_to(workspace_path)),
                    "content": content,
                    "size": len(content),
                })
            except Exception as e:
                print_status(f"   警告: 无法读取 {md_file}: {e}")
    
    print_status(f"   ✅ 找到 {len(memory_files)} 个记忆文件")
    
    # 按文件大小排序，优先处理大文件（通常更重要）
    memory_files.sort(key=lambda x: x["size"], reverse=True)
    
    # 只取前100个最重要的文件，避免初始化时间过长
    if len(memory_files) > 100:
        print_status(f"   📝 优先处理前 100 个文件（按内容重要性）")
        memory_files = memory_files[:100]
    
    return memory_files

def chunk_content(content: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """将长文本分块"""
    if len(content) <= chunk_size:
        return [content]
    
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        chunk = content[start:end]
        
        # 尽量在段落边界分割
        if end < len(content):
            # 找最后一个换行符
            last_newline = chunk.rfind('\n')
            if last_newline > chunk_size * 0.5:  # 如果找到了且不太靠前
                chunk = chunk[:last_newline]
                end = start + last_newline + 1
        
        chunks.append(chunk.strip())
        start = end - overlap  # 重叠部分
    
    return chunks

def generate_embeddings(model, memory_files: List[Dict]) -> List[Dict]:
    """生成向量嵌入"""
    print_status("🧠 步骤 3/5: 生成向量嵌入...")
    
    all_chunks = []
    
    # 先分块
    for file_info in memory_files:
        chunks = chunk_content(file_info["content"])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "path": file_info["path"],
                "chunk_index": i,
                "content": chunk,
                "hash": hashlib.md5(chunk.encode()).hexdigest()[:16],
            })
    
    print_status(f"   分块完成: {len(all_chunks)} 个文本块")
    
    # 批量生成向量
    batch_size = 32
    total_batches = (len(all_chunks) + batch_size - 1) // batch_size
    
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        texts = [c["content"] for c in batch]
        
        # 生成向量
        vectors = model.encode(texts, show_progress_bar=False)
        
        # 保存向量到每个chunk
        for j, chunk in enumerate(batch):
            chunk["vector"] = vectors[j].tolist()
        
        if (i // batch_size + 1) % 10 == 0 or (i // batch_size + 1) == total_batches:
            print_status(f"   进度: {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} 块")
    
    print_status(f"   ✅ 向量生成完成")
    return all_chunks

def save_to_lancedb(chunks: List[Dict], workspace_path: Path):
    """保存到 LanceDB"""
    print_status("💾 步骤 4/5: 保存到向量数据库...")
    
    try:
        import lancedb
        import numpy as np
        import pyarrow as pa
        
        # 数据库路径
        db_path = workspace_path / "memory" / "modules" / "vector_memory" / "lancedb"
        db_path.mkdir(parents=True, exist_ok=True)
        
        # 连接数据库
        db = lancedb.connect(str(db_path))
        
        # 准备数据
        data = []
        for chunk in chunks:
            data.append({
                "id": f"{chunk['hash']}_{chunk['chunk_index']}",
                "vector": chunk["vector"],
                "content": chunk["content"][:2000],  # 限制长度
                "source": chunk["path"],
                "chunk_index": chunk["chunk_index"],
                "created_at": datetime.now(),
            })
        
        # 创建表
        if "memories" in db.table_names():
            db.drop_table("memories")
            print_status("   已清空旧数据")
        
        # 创建新表
        table = db.create_table("memories", data=data)
        
        print_status(f"   ✅ 已保存 {len(data)} 条记录")
        
        # 创建索引
        print_status("🔧 步骤 5/5: 创建向量索引...")
        table.create_index(metric="cosine")
        print_status("   ✅ 索引创建成功")
        
        return len(data)
        
    except Exception as e:
        print_status(f"   ❌ 保存失败: {e}")
        raise

def update_index_file(workspace_path: Path, count: int):
    """更新索引文件"""
    index_path = workspace_path / "memory" / "modules" / "vector_memory" / "index.json"
    
    index_data = {
        "initialized": True,
        "initialized_at": datetime.now().isoformat(),
        "model": "paraphrase-multilingual-MiniLM-L12-v2",
        "dimension": 384,
        "total_records": count,
        "version": "1.0",
    }
    
    index_path.write_text(json.dumps(index_data, indent=2), encoding='utf-8')
    print_status(f"   ✅ 索引文件已更新: {index_path}")

def main():
    """主函数"""
    print_status("=" * 50)
    print_status("🌲 森森向量记忆系统初始化")
    print_status("=" * 50)
    
    start_time = time.time()
    workspace_path = Path("/root/.openclaw/workspace")
    
    try:
        # 步骤 1: 加载模型
        model = init_embedding_model()
        
        # 步骤 2: 扫描文件
        memory_files = scan_memory_files(workspace_path)
        
        if not memory_files:
            print_status("⚠️ 没有找到记忆文件")
            return
        
        # 步骤 3: 生成向量
        chunks = generate_embeddings(model, memory_files)
        
        # 步骤 4-5: 保存并创建索引
        count = save_to_lancedb(chunks, workspace_path)
        
        # 更新索引文件
        update_index_file(workspace_path, count)
        
        # 完成
        elapsed = time.time() - start_time
        print_status("=" * 50)
        print_status(f"✅ 初始化完成！耗时: {elapsed:.1f}秒")
        print_status(f"📊 统计: {len(memory_files)} 文件 → {count} 向量记录")
        print_status(f"🎯 现在可以使用语义搜索了！")
        print_status("=" * 50)
        
    except Exception as e:
        print_status(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
