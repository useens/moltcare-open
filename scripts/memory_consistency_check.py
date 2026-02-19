#!/usr/bin/env python3
"""记忆一致性校验工具 (Phase 3)"""
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

def check_consistency(db_path="/root/.openclaw/workspace/data/vector_memory/memory.db"):
    """校验文件记忆与向量记忆一致性"""
    conn = sqlite3.connect(db_path)
    
    print("🔍 开始一致性校验...\n")
    
    # 1. 检查孤立向量
    cursor = conn.execute('''
        SELECT dv.doc_id FROM document_vectors dv 
        LEFT JOIN documents d ON dv.doc_id = d.id 
        WHERE d.id IS NULL
    ''')
    orphan_vectors = cursor.fetchall()
    if orphan_vectors:
        print(f"⚠️  发现 {len(orphan_vectors)} 个孤立向量")
    else:
        print("✅ 无孤立向量")
    
    # 2. 检查未索引文档
    cursor = conn.execute('''
        SELECT d.id, d.file_path FROM documents d 
        LEFT JOIN document_vectors dv ON d.id = dv.doc_id 
        WHERE dv.doc_id IS NULL
    ''')
    unindexed = cursor.fetchall()
    if unindexed:
        print(f"⚠️  发现 {len(unindexed)} 个未索引文档")
    else:
        print("✅ 所有文档已索引")
    
    # 3. 检查文件存在性
    cursor = conn.execute("SELECT id, file_path FROM documents")
    missing_files = []
    for doc_id, file_path in cursor:
        if not Path(file_path).exists():
            missing_files.append((doc_id, file_path))
    
    if missing_files:
        print(f"⚠️  发现 {len(missing_files)} 个缺失的源文件")
    else:
        print("✅ 所有源文件存在")
    
    # 4. 统计
    cursor = conn.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM document_vectors")
    vec_count = cursor.fetchone()[0]
    
    print(f"\n📊 统计:")
    print(f"  文档数: {doc_count}")
    print(f"  向量数: {vec_count}")
    print(f"  一致性: {'✅ 通过' if doc_count == vec_count else '❌ 异常'}")
    
    conn.close()
    return {
        "orphan_vectors": len(orphan_vectors),
        "unindexed": len(unindexed),
        "missing_files": len(missing_files),
        "doc_count": doc_count,
        "vec_count": vec_count,
        "consistent": doc_count == vec_count
    }

if __name__ == "__main__":
    check_consistency()
