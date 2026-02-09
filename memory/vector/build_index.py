#!/usr/bin/env python3
"""简化版索引构建脚本 - 用于快速测试"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer

print("="*50)
print("向量记忆索引构建器")
print("="*50)

# 配置
MODULES_DIR = Path("../modules")
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

print(f"模块目录: {MODULES_DIR}")
print(f"数据目录: {DATA_DIR}")

# 1. 加载模型
print("\n[1/4] 加载嵌入模型...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(f"模型维度: {model.get_sentence_embedding_dimension()}")

# 2. 扫描文件
print("\n[2/4] 扫描MD文件...")
md_files = list(MODULES_DIR.rglob("*.md"))
print(f"找到 {len(md_files)} 个文件")

# 3. 处理文件
print("\n[3/4] 处理文件...")
all_chunks = []
file_hashes = {}

for i, filepath in enumerate(md_files, 1):
    print(f"  [{i}/{len(md_files)}] {filepath.name}")
    
    # 读取内容
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"    错误: {e}")
        continue
    
    # 计算哈希
    file_hashes[str(filepath)] = hashlib.md5(content.encode()).hexdigest()
    
    # 提取标题
    title = filepath.stem
    for line in content.split('\n'):
        if line.startswith('# '):
            title = line[2:].strip()
            break
    
    # 简单分块 (按字符数)
    chunk_size = 512
    chunks_text = []
    for j in range(0, len(content), chunk_size):
        chunk_text = content[j:j+chunk_size]
        if len(chunk_text) > 50:  # 忽略太短的块
            chunks_text.append(chunk_text)
    
    if not chunks_text:
        chunks_text = [content[:chunk_size]]
    
    # 创建块记录
    for idx, text in enumerate(chunks_text):
        record = {
            'id': f"{filepath.stem}_{idx}",
            'file_path': str(filepath.relative_to(MODULES_DIR.parent)),
            'file_name': filepath.name,
            'chunk_index': idx,
            'total_chunks': len(chunks_text),
            'title': title,
            'text': text[:500],  # 限制存储长度
            'char_count': len(text)
        }
        all_chunks.append(record)

print(f"\n总共 {len(all_chunks)} 个文本块")

# 4. 编码向量
print("\n[4/4] 向量化...")
texts = [chunk['text'] for chunk in all_chunks]
vectors = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
vectors = vectors.astype(np.float32)

print(f"向量形状: {vectors.shape}")

# 5. 保存索引
print("\n保存索引...")
np.save(DATA_DIR / "vectors.npy", vectors)

metadata = {
    'chunks': all_chunks,
    'file_hashes': file_hashes,
    'updated_at': datetime.now().isoformat(),
    'version': '1.0'
}
with open(DATA_DIR / "metadata.json", 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

# 计算存储大小
vec_size = (DATA_DIR / "vectors.npy").stat().st_size
meta_size = (DATA_DIR / "metadata.json").stat().st_size

print("\n" + "="*50)
print("✅ 索引构建完成!")
print("="*50)
print(f"向量数量: {len(vectors)}")
print(f"向量维度: {vectors.shape[1]}")
print(f"文件数量: {len(set(c['file_path'] for c in all_chunks))}")
print(f"向量文件: {vec_size/1024:.1f} KB")
print(f"元数据文件: {meta_size/1024:.1f} KB")
