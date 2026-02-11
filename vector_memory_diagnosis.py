#!/usr/bin/env python3
"""向量记忆系统深度诊断脚本"""

import os
import sys
import pickle
import json
from pathlib import Path
from datetime import datetime

# 向量记忆系统路径
VECTOR_MEMORY_DIR = Path("/root/.openclaw/workspace/memory/vector")
PKL_FILE = VECTOR_MEMORY_DIR / "memory_vectors.pkl"
LONG_TERM_FILE = VECTOR_MEMORY_DIR / "long_term_memories.json"
COMPRESSION_LOG = VECTOR_MEMORY_DIR / "compression_log.json"
ARCHIVED_FILE = VECTOR_MEMORY_DIR / "archived_memories.pkl"
LANCE_DB_DIR = Path("/root/.openclaw/workspace/memory/knowledge/vector_db")

def check_file_exists_and_size(filepath):
    """检查文件是否存在及大小"""
    if not filepath.exists():
        return False, 0, "不存在"
    size = filepath.stat().st_size
    status = "正常" if size > 0 else "空文件"
    return True, size, status

def read_pkl_vectors():
    """读取pkl向量文件"""
    try:
        with open(PKL_FILE, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception as e:
        return {"error": str(e)}

def read_json_file(filepath):
    """读取JSON文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

def check_lancedb():
    """检查LanceDB数据库"""
    results = {}
    try:
        import lancedb
        if LANCE_DB_DIR.exists():
            db = lancedb.connect(str(LANCE_DB_DIR))
            tables = db.table_names()
            results["tables"] = tables
            results["table_count"] = len(tables)
            
            for table_name in tables:
                table = db.open_table(table_name)
                results[f"{table_name}_count"] = len(table.to_pandas())
    except Exception as e:
        results["error"] = str(e)
    return results

def test_semantic_search():
    """测试语义检索功能"""
    results = {"status": "unknown", "details": ""}
    try:
        sys.path.insert(0, str(VECTOR_MEMORY_DIR.parent.parent / "core" / "vector_memory"))
        from memory_search import MemorySearch
        
        searcher = MemorySearch()
        if hasattr(searcher, 'search'):
            test_results = searcher.search("测试查询", top_k=3)
            results["status"] = "正常"
            results["test_query_results"] = len(test_results) if isinstance(test_results, list) else 0
            results["details"] = "语义检索功能正常"
        else:
            results["status"] = "异常"
            results["details"] = "MemorySearch没有search方法"
    except Exception as e:
        results["status"] = "错误"
        results["details"] = str(e)
    return results

def main():
    print("=" * 60)
    print("向量记忆系统深度诊断报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 检查核心文件
    print("\n【1. 向量文件完整性检查】")
    files_to_check = [
        ("PKL向量文件", PKL_FILE),
        ("长期记忆JSON", LONG_TERM_FILE),
        ("压缩日志", COMPRESSION_LOG),
        ("归档记忆", ARCHIVED_FILE),
    ]
    
    for name, filepath in files_to_check:
        exists, size, status = check_file_exists_and_size(filepath)
        icon = "✅" if exists and status == "正常" else "❌"
        print(f"  {icon} {name}: {size} bytes - {status}")
    
    # 2. 统计向量数据
    print("\n【2. 向量数据统计】")
    pkl_data = read_pkl_vectors()
    if "error" in pkl_data:
        print(f"  ❌ PKL文件读取失败: {pkl_data['error']}")
        vector_count = 0
    else:
        vector_count = len(pkl_data) if isinstance(pkl_data, (list, dict)) else 0
        print(f"  ✅ PKL向量数量: {vector_count}")
    
    # 长期记忆统计
    long_term_data = read_json_file(LONG_TERM_FILE)
    if "error" in long_term_data:
        print(f"  ❌ 长期记忆读取失败: {long_term_data['error']}")
        long_term_count = 0
    else:
        long_term_count = len(long_term_data) if isinstance(long_term_data, list) else 0
        print(f"  ✅ 长期记忆数量: {long_term_count}")
    
    # 压缩日志统计
    compression_data = read_json_file(COMPRESSION_LOG)
    if "error" not in compression_data:
        print(f"  ✅ 压缩记录: {len(compression_data) if isinstance(compression_data, list) else 'N/A'}")
    
    # 3. LanceDB检查
    print("\n【3. LanceDB向量数据库检查】")
    lance_results = check_lancedb()
    if "error" in lance_results:
        print(f"  ❌ LanceDB检查失败: {lance_results['error']}")
    else:
        print(f"  ✅ 数据表: {lance_results.get('tables', [])}")
        for key, value in lance_results.items():
            if key.endswith("_count"):
                print(f"  ✅ {key}: {value} 条记录")
    
    # 4. 检查模型文件
    print("\n【4. 嵌入模型检查】")
    try:
        from sentence_transformers import SentenceTransformer
        # 尝试加载模型
        model = SentenceTransformer("BAAI/bge-large-zh-v1.5", device="cpu")
        dim = model.get_sentence_embedding_dimension()
        print(f"  ✅ 模型 BAAI/bge-large-zh-v1.5 加载成功")
        print(f"  ✅ 嵌入维度: {dim}")
        model_status = "正常"
    except Exception as e:
        print(f"  ❌ 模型加载失败: {e}")
        dim = 0
        model_status = "异常"
    
    # 5. 测试语义检索
    print("\n【5. 语义检索功能测试】")
    search_results = test_semantic_search()
    icon = "✅" if search_results["status"] == "正常" else "❌"
    print(f"  {icon} 状态: {search_results['status']}")
    print(f"  📋 详情: {search_results['details']}")
    
    # 6. 输出汇总报告
    print("\n" + "=" * 60)
    print("【诊断汇总报告】")
    print("=" * 60)
    
    # 计算健康度
    health_score = 0
    total_checks = 5
    
    if PKL_FILE.exists() and PKL_FILE.stat().st_size > 0:
        health_score += 1
    if LONG_TERM_FILE.exists() and LONG_TERM_FILE.stat().st_size > 0:
        health_score += 1
    if "error" not in lance_results:
        health_score += 1
    if model_status == "正常":
        health_score += 1
    if search_results["status"] == "正常":
        health_score += 1
    
    health_pct = (health_score / total_checks) * 100
    
    print(f"""
| 指标 | 数值 | 状态 |
|------|------|------|
| 向量记忆数 (PKL) | {vector_count} 条 | {'✅' if vector_count > 0 else '❌'} |
| 长期记忆数 (JSON) | {long_term_count} 条 | {'✅' if long_term_count > 0 else '❌'} |
| LanceDB表 | {lance_results.get('table_count', 0)} 个 | {'✅' if 'error' not in lance_results else '❌'} |
| 嵌入模型 | BAAI/bge-large-zh-v1.5 ({dim}维) | {'✅' if model_status == '正常' else '❌'} |
| 语义检索 | {search_results['status']} | {'✅' if search_results['status'] == '正常' else '❌'} |
| 系统健康度 | {health_pct:.0f}% | {'✅' if health_pct >= 80 else '⚠️' if health_pct >= 50 else '❌'} |
""")
    
    # 优化建议
    print("【优化建议】")
    if vector_count == 0:
        print("  ⚠️ 向量记忆为空，建议重新构建向量索引")
    if long_term_count == 0:
        print("  ⚠️ 长期记忆为空，建议检查记忆导入流程")
    if search_results["status"] != "正常":
        print(f"  ⚠️ 语义检索功能异常: {search_results['details']}")
    if health_pct >= 80:
        print("  ✅ 系统整体健康，建议定期维护")
    elif health_pct >= 50:
        print("  ⚠️ 系统存在部分问题，建议针对性修复")
    else:
        print("  ❌ 系统健康度较低，建议全面检查和重建")
    
    return health_pct

if __name__ == "__main__":
    main()
