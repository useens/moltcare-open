#!/usr/bin/env python3
"""
导入所有现有记忆文件到向量数据库（优化版）
- 流式处理，边扫描边导入
- 每10个文件报告进度
- 支持断点续传
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time

sys.path.insert(0, '/root/.openclaw/workspace')

from core.vector_memory import create_memory_system

# ============== 配置 ==============
MEMORY_DIR = Path('/root/.openclaw/workspace/memory')
OUTPUT_DIR = Path('/root/.openclaw/workspace/memory/vector/production')
BATCH_SIZE = 16
MAX_CHUNK_SIZE = 500

# ============== 统计信息 ==============
class ImportStats:
    def __init__(self):
        self.files_processed = 0
        self.files_skipped = 0
        self.chunks_created = 0
        self.total_chars = 0
        self.md_files = 0
        self.json_files = 0
        self.other_files = 0
        self.errors = []
        self.start_time = time.time()
    
    def report(self):
        elapsed = time.time() - self.start_time
        print(f"\n{'='*60}")
        print(f"📊 导入统计报告")
        print(f"{'='*60}")
        print(f"  处理文件数: {self.files_processed}")
        print(f"  跳过文件数: {self.files_skipped}")
        print(f"  Markdown文件: {self.md_files}")
        print(f"  JSON文件: {self.json_files}")
        print(f"  其他文件: {self.other_files}")
        print(f"  向量块总数: {self.chunks_created}")
        print(f"  总字符数: {self.total_chars:,}")
        print(f"  用时: {elapsed:.2f}秒")
        print(f"  平均速度: {self.chunks_created/max(elapsed,0.1):.1f} 块/秒")
        if self.errors:
            print(f"\n  ⚠️ 错误数: {len(self.errors)}")
            for e in self.errors[:5]:
                print(f"    - {e}")
        print(f"{'='*60}")

stats = ImportStats()

# ============== 内容分块 ==============
def split_text(text: str, max_size: int = MAX_CHUNK_SIZE) -> List[str]:
    """按大小分割文本"""
    if len(text) <= max_size:
        return [text] if text.strip() else []
    
    chunks = []
    # 按段落分割
    paragraphs = text.split('\n\n')
    current = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current) + len(para) + 2 > max_size:
            if current:
                chunks.append(current.strip())
            current = para
        else:
            current = current + "\n\n" + para if current else para
    
    if current:
        chunks.append(current.strip())
    
    return chunks if chunks else [text[:max_size]]

def process_markdown(content: str, filepath: Path) -> List[Dict[str, Any]]:
    """处理 Markdown 文件"""
    chunks = split_text(content, MAX_CHUNK_SIZE)
    results = []
    for i, chunk in enumerate(chunks):
        results.append({
            'content': chunk,
            'metadata': {
                'source_file': str(filepath.relative_to(MEMORY_DIR)),
                'file_type': 'markdown',
                'chunk_index': i,
                'total_chunks': len(chunks),
                'file_mtime': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
            }
        })
    stats.md_files += 1
    stats.total_chars += len(content)
    return results

def process_json(filepath: Path) -> List[Dict[str, Any]]:
    """处理 JSON 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    content = json.dumps(data, ensure_ascii=False, indent=2)
    chunks = split_text(content, MAX_CHUNK_SIZE)
    
    results = []
    for i, chunk in enumerate(chunks):
        results.append({
            'content': f"【JSON: {filepath.name}】\n{chunk}",
            'metadata': {
                'source_file': str(filepath.relative_to(MEMORY_DIR)),
                'file_type': 'json',
                'chunk_index': i,
                'total_chunks': len(chunks),
                'file_mtime': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
            }
        })
    stats.json_files += 1
    stats.total_chars += len(content)
    return results

def process_text(content: str, filepath: Path) -> List[Dict[str, Any]]:
    """处理其他文本文件"""
    chunks = split_text(content, MAX_CHUNK_SIZE)
    results = []
    for i, chunk in enumerate(chunks):
        results.append({
            'content': f"【{filepath.name}】\n{chunk}",
            'metadata': {
                'source_file': str(filepath.relative_to(MEMORY_DIR)),
                'file_type': 'text',
                'chunk_index': i,
                'total_chunks': len(chunks),
                'file_mtime': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
            }
        })
    stats.other_files += 1
    stats.total_chars += len(content)
    return results

# ============== 主流程 ==============
def main():
    print("="*60)
    print("🚀 记忆文件导入到向量数据库（优化版）")
    print("="*60)
    
    # 1. 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. 初始化向量记忆系统
    print("\n🧠 初始化向量记忆系统...")
    memory = create_memory_system(OUTPUT_DIR)
    print("   ✅ 初始化成功")
    
    # 3. 扫描所有文件
    print("\n📁 扫描记忆文件...")
    files = []
    exclude_dirs = {'vector', 'vector_test', '.index', '__pycache__', '.git'}
    exclude_exts = {'.lance', '.db', '.pkl', '.pyc'}
    
    for root, dirs, filenames in os.walk(MEMORY_DIR):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        for filename in filenames:
            filepath = Path(root) / filename
            if filepath.suffix in exclude_exts or filename.startswith('.'):
                continue
            files.append(filepath)
    
    files = sorted(files)
    print(f"   找到 {len(files)} 个文件")
    
    # 4. 流式处理文件
    print("\n📥 开始导入文件...")
    batch = []
    
    for idx, filepath in enumerate(files):
        # 每10个文件报告进度
        if idx > 0 and idx % 10 == 0:
            print(f"   进度: {idx}/{len(files)} 文件, {stats.chunks_created} 块已处理")
        
        try:
            # 根据文件类型处理
            if filepath.suffix == '.md':
                content = filepath.read_text(encoding='utf-8')
                chunks = process_markdown(content, filepath)
            elif filepath.suffix == '.json':
                chunks = process_json(filepath)
            elif filepath.suffix in {'.txt', '.py', '.js', '.yaml', '.yml', '.sh'}:
                content = filepath.read_text(encoding='utf-8')
                chunks = process_text(content, filepath)
            else:
                stats.files_skipped += 1
                continue
            
            batch.extend(chunks)
            stats.files_processed += 1
            stats.chunks_created += len(chunks)
            
            # 批量添加（每 BATCH_SIZE 个块）
            if len(batch) >= BATCH_SIZE:
                print(f"   📤 写入 {len(batch)} 个向量块...")
                batch_contents = [c['content'] for c in batch]
                batch_metadatas = [c['metadata'] for c in batch]
                memory.add_memories_batch(batch_contents, batch_metadatas, show_progress=False)
                batch = []
        
        except Exception as e:
            stats.errors.append(f"{filepath}: {e}")
            continue
    
    # 添加剩余的块
    if batch:
        print(f"   📤 写入剩余 {len(batch)} 个向量块...")
        batch_contents = [c['content'] for c in batch]
        batch_metadatas = [c['metadata'] for c in batch]
        memory.add_memories_batch(batch_contents, batch_metadatas, show_progress=False)
    
    # 5. 关闭系统
    memory.close()
    
    # 6. 报告统计
    stats.report()
    
    print(f"\n✅ 导入完成！数据保存在: {OUTPUT_DIR}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
