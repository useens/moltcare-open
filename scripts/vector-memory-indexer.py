#!/usr/bin/env python3
"""
向量记忆索引器 - 混合策略
- 实时索引：Signal≥8的重要记忆
- 每日全量扫描：更新所有记忆
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, "/root/.openclaw/workspace")

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

def index_to_vector(content: str, source_file: str, force: bool = False):
    """
    索引内容到向量记忆
    
    Args:
        content: 记忆内容
        source_file: 来源文件路径
        force: 强制索引（忽略Signal检查）
    """
    try:
        # 估算Signal
        signal = get_signal_level(content)
        
        # 如果不强制且Signal<8，跳过
        if not force and signal < 8:
            return False, f"Signal {signal} < 8，跳过"
        
        # TODO: 调用向量记忆系统API
        # 这里需要实现实际的向量索引逻辑
        # 目前先记录日志
        
        log_content = {
            "timestamp": datetime.now().isoformat(),
            "action": "index_to_vector",
            "signal": signal,
            "source_file": source_file,
            "forced": force,
            "content_length": len(content)
        }
        
        # 保存索引日志
        log_file = Path("/root/.openclaw/workspace/logs/vector-indexer.log")
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(log_content, ensure_ascii=False) + "\n")
        
        return True, f"Signal {signal}，已记录（待集成向量API）"
        
    except Exception as e:
        return False, f"索引失败: {str(e)}"

def full_scan_incremental_update():
    """
    每日全量扫描 - 增量更新向量记忆
    """
    memory_dir = Path("/root/.openclaw/workspace/memory")
    indexed_count = 0
    skipped_count = 0
    
    print(f"[{datetime.now()}] 开始全量扫描增量更新...")
    
    # 扫描memory/目录下的.md文件
    for md_file in memory_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            
            # 计算内容哈希
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # TODO: 检查是否已索引（通过哈希比对）
            # 目前简化的实现：Signal≥8才索引
            
            signal = get_signal_level(content)
            
            if signal >= 8:
                success, msg = index_to_vector(content, str(md_file.relative_to(memory_dir)), force=True)
                if success:
                    indexed_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            print(f"处理失败 {md_file}: {e}")
    
    print(f"[{datetime.now()}] 全量扫描完成: 索引{indexed_count}条, 跳过{skipped_count}条")
    return indexed_count, skipped_count

def realtime_index(content: str, source: str):
    """
    实时索引 - 用于重要记忆（Signal≥8）的即时索引
    
    Args:
        content: 记忆内容
        source: 来源描述
    """
    success, msg = index_to_vector(content, source, force=False)
    print(f"[{datetime.now()}] 实时索引: {msg}")
    return success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="向量记忆索引器")
    parser.add_argument("--full-scan", action="store_true", help="执行全量增量扫描")
    parser.add_argument("--content", help="要索引的内容")
    parser.add_argument("--source", default="manual", help="内容来源")
    
    args = parser.parse_args()
    
    if args.full_scan:
        indexed, skipped = full_scan_incremental_update()
        print(f"索引完成: {indexed}条更新, {skipped}条跳过")
    elif args.content:
        realtime_index(args.content, args.source)
    else:
        print("用法: python3 vector-memory-indexer.py --full-scan")
        print("     python3 vector-memory-indexer.py --content '内容' --source '来源'")
