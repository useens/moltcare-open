#!/usr/bin/env python3
"""
导入所有现有记忆文件到向量数据库
- 扫描并导入所有记忆文件
- 处理 Markdown、JSON 等文件类型
- 添加元数据并批量存储
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
import time

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace')

from core.vector_memory import create_memory_system

# ============== 配置 ==============
MEMORY_DIR = Path('/root/.openclaw/workspace/memory')
OUTPUT_DIR = Path('/root/.openclaw/workspace/memory/vector/production')
BATCH_SIZE = 32
MAX_CHUNK_SIZE = 500  # 每段最大字符数

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

# ============== 文件扫描 ==============
def scan_memory_files() -> List[Path]:
    """扫描所有记忆文件"""
    files = []
    
    # 排除的目录和文件
    exclude_dirs = {'vector', 'vector_test', '.index', '__pycache__', '.git'}
    exclude_exts = {'.lance', '.db', '.pkl', '.pyc'}
    
    for root, dirs, filenames in os.walk(MEMORY_DIR):
        # 排除不需要的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for filename in filenames:
            filepath = Path(root) / filename
            
            # 跳过排除的文件类型
            if filepath.suffix in exclude_exts:
                continue
            if filename.startswith('.'):
                continue
            
            files.append(filepath)
    
    return sorted(files)

# ============== 内容分块 ==============
def split_markdown_by_headers(content: str, file_path: str) -> List[Dict[str, Any]]:
    """按 Markdown 标题分段"""
    chunks = []
    
    # 按标题分割 (##, ### 等)
    # 使用正则表达式匹配标题行
    pattern = r'^(#{1,6}\s+.+)$'
    parts = re.split(pattern, content, flags=re.MULTILINE)
    
    current_header = "无标题"
    
    for i, part in enumerate(parts):
        if not part.strip():
            continue
            
        # 检查是否是标题
        if re.match(pattern, part.strip()):
            current_header = part.strip().lstrip('#').strip()
            continue
        
        # 处理内容部分
        text = part.strip()
        if not text:
            continue
        
        # 如果内容太长，进一步分割
        if len(text) > MAX_CHUNK_SIZE:
            sub_chunks = split_by_size(text, MAX_CHUNK_SIZE)
            for j, sub in enumerate(sub_chunks):
                chunks.append({
                    'content': sub,
                    'header': current_header,
                    'chunk_index': j,
                    'total_chunks': len(sub_chunks)
                })
        else:
            chunks.append({
                'content': text,
                'header': current_header,
                'chunk_index': 0,
                'total_chunks': 1
            })
    
    # 如果没有按标题分块成功，按大小分块
    if not chunks and content.strip():
        sub_chunks = split_by_size(content.strip(), MAX_CHUNK_SIZE)
        for j, sub in enumerate(sub_chunks):
            chunks.append({
                'content': sub,
                'header': '全文',
                'chunk_index': j,
                'total_chunks': len(sub_chunks)
            })
    
    return chunks

def split_by_size(text: str, max_size: int) -> List[str]:
    """按大小分割文本，尽量在句子边界处分割"""
    chunks = []
    
    # 按段落分割
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # 如果当前段落超过最大大小，进一步分割
        if len(para) > max_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # 按句子分割
            sentences = re.split(r'([。！？.!?]\s*)', para)
            temp = ""
            for s in sentences:
                if len(temp) + len(s) > max_size:
                    if temp:
                        chunks.append(temp.strip())
                    temp = s
                else:
                    temp += s
            if temp:
                chunks.append(temp.strip())
        
        # 如果添加当前段落会超过限制
        elif len(current_chunk) + len(para) + 2 > max_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += para
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]

def extract_json_text(data: Any, prefix: str = "") -> List[Tuple[str, str]]:
    """递归提取 JSON 中的文本字段"""
    results = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(value, str):
                if len(value) > 20:  # 只保留有意义的文本
                    results.append((new_prefix, value))
            elif isinstance(value, (dict, list)):
                results.extend(extract_json_text(value, new_prefix))
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_prefix = f"{prefix}[{i}]"
            if isinstance(item, str):
                if len(item) > 20:
                    results.append((new_prefix, item))
            elif isinstance(item, (dict, list)):
                results.extend(extract_json_text(item, new_prefix))
    
    return results

# ============== 文件处理 ==============
def process_markdown_file(filepath: Path) -> List[Dict[str, Any]]:
    """处理 Markdown 文件"""
    try:
        content = filepath.read_text(encoding='utf-8')
        chunks = split_markdown_by_headers(content, str(filepath))
        
        results = []
        for chunk in chunks:
            results.append({
                'content': chunk['content'],
                'metadata': {
                    'source_file': str(filepath.relative_to(MEMORY_DIR.parent)),
                    'file_type': 'markdown',
                    'header': chunk['header'],
                    'chunk_index': chunk['chunk_index'],
                    'total_chunks': chunk['total_chunks'],
                    'file_mtime': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                }
            })
        
        stats.md_files += 1
        stats.total_chars += len(content)
        return results
    
    except Exception as e:
        stats.errors.append(f"Markdown {filepath}: {e}")
        return []

def process_json_file(filepath: Path) -> List[Dict[str, Any]]:
    """处理 JSON 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        text_fields = extract_json_text(data)
        results = []
        
        for path, text in text_fields:
            # 格式化 JSON 文本
            formatted = f"【{filepath.name} - {path}】\n{text}"
            
            # 如果文本太长，分割存储
            if len(formatted) > MAX_CHUNK_SIZE:
                sub_chunks = split_by_size(formatted, MAX_CHUNK_SIZE)
                for i, sub in enumerate(sub_chunks):
                    results.append({
                        'content': sub,
                        'metadata': {
                            'source_file': str(filepath.relative_to(MEMORY_DIR.parent)),
                            'file_type': 'json',
                            'json_path': path,
                            'chunk_index': i,
                            'total_chunks': len(sub_chunks),
                            'file_mtime': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                        }
                    })
            else:
                results.append({
                    'content': formatted,
                    'metadata': {
                        'source_file': str(filepath.relative_to(MEMORY_DIR.parent)),
                        'file_type': 'json',
                        'json_path': path,
                        'chunk_index': 0,
                        'total_chunks': 1,
                        'file_mtime': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                    }
                })
        
        # 如果没有提取到文本，存储整个 JSON 的摘要
        if not results:
            summary = f"【JSON 文件: {filepath.name}】\n{json.dumps(data, ensure_ascii=False, indent=2)[:MAX_CHUNK_SIZE]}"
            results.append({
                'content': summary,
                'metadata': {
                    'source_file': str(filepath.relative_to(MEMORY_DIR.parent)),
                    'file_type': 'json',
                    'json_path': 'root',
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'file_mtime': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                }
            })
        
        stats.json_files += 1
        stats.total_chars += len(json.dumps(data))
        return results
    
    except json.JSONDecodeError as e:
        stats.errors.append(f"JSON decode {filepath}: {e}")
        return []
    except Exception as e:
        stats.errors.append(f"JSON {filepath}: {e}")
        return []

def process_text_file(filepath: Path) -> List[Dict[str, Any]]:
    """处理其他文本文件"""
    try:
        content = filepath.read_text(encoding='utf-8')
        chunks = split_by_size(content, MAX_CHUNK_SIZE)
        
        results = []
        for i, chunk in enumerate(chunks):
            results.append({
                'content': f"【{filepath.name}】\n{chunk}",
                'metadata': {
                    'source_file': str(filepath.relative_to(MEMORY_DIR.parent)),
                    'file_type': 'text',
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'file_mtime': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                }
            })
        
        stats.other_files += 1
        stats.total_chars += len(content)
        return results
    
    except Exception as e:
        stats.errors.append(f"Text {filepath}: {e}")
        return []

# ============== 主流程 ==============
def main():
    print("="*60)
    print("🚀 记忆文件导入到向量数据库")
    print("="*60)
    
    # 1. 扫描文件
    print("\n📁 扫描记忆文件...")
    files = scan_memory_files()
    print(f"   找到 {len(files)} 个文件")
    
    # 2. 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 3. 初始化向量记忆系统
    print("\n🧠 初始化向量记忆系统...")
    memory = create_memory_system(OUTPUT_DIR)
    print("   ✅ 初始化成功")
    
    # 4. 处理所有文件
    print("\n📥 开始导入文件...")
    
    all_chunks = []
    
    for idx, filepath in enumerate(files):
        # 每10个文件报告进度
        if idx > 0 and idx % 10 == 0:
            print(f"   进度: {idx}/{len(files)} 文件, {stats.chunks_created} 块已处理")
        
        # 根据文件类型处理
        if filepath.suffix == '.md':
            chunks = process_markdown_file(filepath)
        elif filepath.suffix == '.json':
            chunks = process_json_file(filepath)
        elif filepath.suffix in {'.txt', '.py', '.js', '.yaml', '.yml', '.sh'}:
            chunks = process_text_file(filepath)
        else:
            stats.files_skipped += 1
            continue
        
        all_chunks.extend(chunks)
        stats.files_processed += 1
        stats.chunks_created += len(chunks)
        
        # 批量添加（每 BATCH_SIZE * 5 个块）
        if len(all_chunks) >= BATCH_SIZE * 5:
            batch_contents = [c['content'] for c in all_chunks]
            batch_metadatas = [c['metadata'] for c in all_chunks]
            memory.add_memories_batch(batch_contents, batch_metadatas, show_progress=False)
            all_chunks = []
    
    # 添加剩余的块
    if all_chunks:
        batch_contents = [c['content'] for c in all_chunks]
        batch_metadatas = [c['metadata'] for c in all_chunks]
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
