#!/usr/bin/env python3
"""
向量记忆索引器 - 混合策略 v2.0
- 实时索引：Signal≥8的重要记忆，立即入库
- 每日全量扫描：更新所有记忆

集成: local-memory-system (MiniLM + SQLite)
"""
import os
import sys
import json
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime

# 添加local-memory-system路径
sys.path.insert(0, "/root/.openclaw/workspace/local-memory-system")

try:
    from local_memory import LocalMemorySystem
except ImportError as e:
    print(f"❌ 导入LocalMemorySystem失败: {e}")
    print("请确保sentence-transformers已安装: pip install sentence-transformers")
    sys.exit(1)

# 全局记忆系统实例
_memory_system = None

def get_memory_system():
    """获取或创建记忆系统实例（单例模式）"""
    global _memory_system
    if _memory_system is None:
        # 使用统一的向量记忆目录
        memory_dir = "/root/.openclaw/workspace/data/vector_memory"
        _memory_system = LocalMemorySystem(memory_dir)
        # 确保初始化（创建表结构）
        _memory_system.init()
    return _memory_system

def get_signal_level(content: str) -> int:
    """
    估算内容的Signal等级
    简单启发式：基于关键词、长度、结构
    """
    signal_score = 5  # 默认5分
    
    # 检查重要关键词
    high_signal_keywords = [
        "关键", "重要", "紧急", "必须", "核心",
        "critical", "important", "urgent", "must", "core",
        "创新", "突破", "发现", "insight", "breakthrough", "discovery",
        "决策", "策略", "战略", "decision", "strategy",
        "安全", "风险", "security", "risk"
    ]
    
    for keyword in high_signal_keywords:
        if keyword in content.lower():
            signal_score += 1
    
    # 检测代码/技术内容
    if "```" in content or "def " in content or "class " in content:
        signal_score += 2
    
    # 检测Markdown深度
    if content.count("#") >= 3:
        signal_score += 1
    
    # 限制范围1-10
    return max(1, min(10, signal_score))

def index_to_vector_memory(content: str, source_file: str, force: bool = False) -> tuple:
    """
    索引内容到向量记忆系统（真正入库）
    
    Args:
        content: 记忆内容
        source_file: 来源文件路径（用于标识）
        force: 强制索引（忽略Signal检查）
        
    Returns:
        (success: bool, message: str, doc_id: int or None)
    """
    try:
        # 估算Signal
        signal = get_signal_level(content)
        
        # 如果不强制且Signal<8，跳过
        if not force and signal < 8:
            return False, f"Signal {signal} < 8，跳过", None
        
        # 获取记忆系统
        memory = get_memory_system()
        
        # 创建临时文件来存储内容（因为index_file需要file_path）
        # 使用source_file的哈希作为文件名，确保唯一性
        source_hash = hashlib.sha256(source_file.encode()).hexdigest()[:16]
        temp_dir = Path("/root/.openclaw/workspace/data/vector_memory/realtime")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file = temp_dir / f"{source_hash}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # 写入内容（添加元数据头）
        metadata = f"""---
source: {source_file}
signal: {signal}
indexed_at: {datetime.now().isoformat()}
content_hash: {hashlib.sha256(content.encode()).hexdigest()[:16]}
---

"""
        temp_file.write_text(metadata + content, encoding="utf-8")
        
        # 索引到向量记忆系统
        memory.index_file(str(temp_file))
        
        # 获取文档ID（通过查询）
        conn = memory._get_connection()
        cursor = conn.execute(
            "SELECT id FROM documents WHERE file_path = ?",
            (str(temp_file.absolute()),)
        )
        result = cursor.fetchone()
        doc_id = result[0] if result else None
        
        # 记录日志
        log_content = {
            "timestamp": datetime.now().isoformat(),
            "action": "index_to_vector",
            "signal": signal,
            "source_file": source_file,
            "temp_file": str(temp_file),
            "doc_id": doc_id,
            "forced": force,
            "content_length": len(content)
        }
        
        log_file = Path("/root/.openclaw/workspace/logs/vector-indexer.log")
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(log_content, ensure_ascii=False) + "\n")
        
        return True, f"Signal {signal}，已入库 (doc_id: {doc_id})", doc_id
        
    except Exception as e:
        import traceback
        error_msg = f"索引失败: {str(e)}\n{traceback.format_exc()}"
        return False, error_msg, None

def full_scan_incremental_update():
    """
    每日全量扫描 - 增量更新向量记忆
    """
    memory_dir = Path("/root/.openclaw/workspace/memory")
    indexed_count = 0
    skipped_count = 0
    failed_count = 0
    
    print(f"[{datetime.now()}] 开始全量扫描增量更新...")
    
    # 初始化记忆系统
    memory = get_memory_system()
    
    # 扫描memory/目录下的.md文件
    for md_file in memory_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            
            # Signal≥8才索引
            signal = get_signal_level(content)
            
            if signal >= 8:
                success, msg, doc_id = index_to_vector_memory(
                    content, 
                    str(md_file.relative_to(memory_dir)), 
                    force=True
                )
                if success:
                    indexed_count += 1
                    print(f"  ✅ {md_file.name}: {msg}")
                else:
                    failed_count += 1
                    print(f"  ❌ {md_file.name}: {msg}")
            else:
                skipped_count += 1
                
        except Exception as e:
            print(f"  ❌ 处理失败 {md_file}: {e}")
            failed_count += 1
    
    print(f"[{datetime.now()}] 全量扫描完成:")
    print(f"  - 索引: {indexed_count}条")
    print(f"  - 跳过: {skipped_count}条")
    print(f"  - 失败: {failed_count}条")
    
    return indexed_count, skipped_count, failed_count

def realtime_index(content: str, source: str) -> bool:
    """
    实时索引 - 用于重要记忆（Signal≥8）的即时索引
    
    Args:
        content: 记忆内容
        source: 来源描述
        
    Returns:
        bool: 是否成功
    """
    success, msg, doc_id = index_to_vector_memory(content, source, force=False)
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if success:
        print(f"[{timestamp}] 🧠 实时索引: {msg}")
    else:
        print(f"[{timestamp}] ⏭️  {msg}")
    
    return success

def search_memory(query: str, top_k: int = 5):
    """
    搜索向量记忆
    
    Args:
        query: 搜索查询
        top_k: 返回结果数量
    """
    memory = get_memory_system()
    results = memory.search(query, top_k=top_k)
    
    print(f"\n🔍 搜索结果: '{query}'")
    print("=" * 60)
    
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['file_path']}")
        print(f"   相似度: {r['similarity']:.4f}")
        preview = r.get('content_preview', '')[:200]
        print(f"   预览: {preview}...")
    
    return results

def show_stats():
    """显示向量记忆统计"""
    memory = get_memory_system()
    conn = memory._get_connection()
    
    # 获取统计
    cursor = conn.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM document_vectors")
    vector_count = cursor.fetchone()[0]
    
    print(f"\n📊 向量记忆统计")
    print("=" * 40)
    print(f"  文档数: {doc_count}")
    print(f"  向量数: {vector_count}")
    print(f"  存储位置: {memory.memory_dir}")
    print(f"  数据库: {memory.db_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="向量记忆索引器 v2.0")
    parser.add_argument("--full-scan", action="store_true", help="执行全量增量扫描")
    parser.add_argument("--content", help="要索引的内容")
    parser.add_argument("--source", default="manual", help="内容来源")
    parser.add_argument("--search", help="搜索向量记忆")
    parser.add_argument("--stats", action="store_true", help="显示统计")
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats()
    elif args.search:
        search_memory(args.search)
    elif args.full_scan:
        indexed, skipped, failed = full_scan_incremental_update()
        print(f"\n总计: {indexed}条索引, {skipped}条跳过, {failed}条失败")
    elif args.content:
        success = realtime_index(args.content, args.source)
        sys.exit(0 if success else 1)
    else:
        print("用法:")
        print("  python3 vector-memory-indexer.py --full-scan")
        print("  python3 vector-memory-indexer.py --content '重要内容' --source '来源'")
        print("  python3 vector-memory-indexer.py --search '查询词'")
        print("  python3 vector-memory-indexer.py --stats")
        
        # 显示当前统计
        show_stats()
