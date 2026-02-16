#!/usr/bin/env python3
"""
本地向量语义搜索

使用 sentence-transformers + LanceDB 进行纯本地语义搜索
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

def load_model():
    """加载本地嵌入模型"""
    print_status("🧠 加载本地嵌入模型...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print_status(f"   ✅ 模型加载完成 (维度: {model.get_sentence_embedding_dimension()})")
    return model

def perform_search(query: str, top_k: int = 5):
    """执行语义搜索"""
    import lancedb
    import numpy as np
    
    workspace = Path("/root/.openclaw/workspace")
    db_path = workspace / "memory" / "modules" / "vector_memory" / "lancedb"
    
    # 检查数据库是否存在
    if not db_path.exists():
        print_status("   ❌ 向量数据库未初始化")
        print_status("      请运行: python3 scripts/init_vector_memory_local.py")
        return []
    
    # 连接数据库
    db = lancedb.connect(str(db_path))
    
    # 尝试打开表（兼容新旧 API）
    try:
        table = db.open_table("memories")
    except Exception as e:
        print_status(f"   ❌ 向量表不存在: {e}")
        return []
    
    # 获取模型
    model = load_model()
    
    # 生成查询向量
    print_status(f"🔍 搜索: {query}")
    query_vector = model.encode(query)
    
    # 执行搜索
    results = table.search(query_vector).limit(top_k).to_pandas()
    
    return results

def print_status(message: str):
    """打印带时间戳的消息"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def format_results(results):
    """格式化搜索结果"""
    if not results or len(results) == 0:
        return "未找到相关记忆"
    
    output = []
    output.append(f"📊 找到 {len(results)} 条相关记忆：")
    output.append("")
    
    # LanceDB 返回的是一个特殊的记录列表
    for idx, row in enumerate(results):
        score = getattr(row, '_score', 0.0)
        content = row.get('content', '')
        source = row.get('source', '')
        
        output.append(f"【{idx+1}】相关性: {score:.4f}")
        output.append(f"   来源: {source}")
        output.append(f"   内容: {content[:300]}...")
        output.append("")
    
    return "\n".join(output)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 vector-memory-search.py <query> [top_k]")
        print("示例: python3 vector-memory-search.py '夜间进化模式' 5")
        sys.exit(1)
    
    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print_status("=" * 50)
    print_status("🌲 森森本地向量语义搜索")
    print_status("=" * 50)
    
    # 执行搜索
    results = perform_search(query, top_k)
    
    # 格式化输出
    if hasattr(results, 'empty') and not results.empty:
        print(format_results(results))
    elif results and len(results) > 0:
        print(format_results(results))
    else:
        print("未找到相关记忆")
        print("")
        print("提示：")
        print("1. 确保向量数据库已初始化")
        print("2. 使用更通用的搜索词")
        print("3. 运行: python3 scripts/init_vector_memory_local.py 重新初始化")
    
    print_status("=" * 50)

if __name__ == "__main__":
    main()
