#!/usr/bin/env python3
"""
本地记忆搜索系统 - 不依赖外部API
使用关键词匹配 + 简单相似度计算
"""
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

MEMORY_FILE = Path("/root/.openclaw/workspace/memory/vector/long_term_memories.json")

def load_memories() -> List[Dict[str, Any]]:
    """加载记忆数据"""
    if not MEMORY_FILE.exists():
        return []
    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def tokenize(text: str) -> set:
    """简单分词"""
    # 转为小写，提取中文字符和英文单词
    text = text.lower()
    chinese_chars = set(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = set(re.findall(r'[a-z]+', text))
    return chinese_chars | english_words

def calculate_score(query: str, memory: Dict[str, Any]) -> float:
    """计算查询与记忆的相关性分数"""
    query_tokens = tokenize(query)
    
    # 从记忆提取文本字段
    content = memory.get('content', '')
    tags = memory.get('tags', [])
    source = memory.get('source', '')
    
    content_tokens = tokenize(content)
    tag_tokens = set()
    for tag in tags:
        tag_tokens.update(tokenize(tag))
    source_tokens = tokenize(source)
    
    # 计算匹配分数
    score = 0.0
    
    # 内容匹配（权重最高）
    content_matches = len(query_tokens & content_tokens)
    score += content_matches * 1.0
    
    # 标签匹配
    tag_matches = len(query_tokens & tag_tokens)
    score += tag_matches * 2.0  # 标签匹配权重更高
    
    # 来源匹配
    source_matches = len(query_tokens & source_tokens)
    score += source_matches * 0.5
    
    # 重要性加成
    importance = memory.get('importance', 5)
    score *= (1 + importance / 10)  # importance 1-10，分数提升10%-100%
    
    # 访问次数加成（被频繁访问的记忆更相关）
    access_count = memory.get('access_count', 0)
    score *= (1 + min(access_count, 10) / 20)  # 最多提升50%
    
    return score

def search_memories(query: str, max_results: int = 5, min_score: float = 0.5) -> List[Dict[str, Any]]:
    """搜索记忆"""
    memories = load_memories()
    if not memories:
        return []
    
    # 计算每条记忆的分数
    scored_memories = []
    for memory in memories:
        score = calculate_score(query, memory)
        if score >= min_score:
            scored_memories.append((score, memory))
    
    # 按分数排序
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    
    # 返回top结果
    results = []
    for score, memory in scored_memories[:max_results]:
        result = {
            "id": memory.get('id', ''),
            "content": memory.get('content', ''),
            "source": memory.get('source', ''),
            "tags": memory.get('tags', []),
            "importance": memory.get('importance', 5),
            "score": round(score, 2),
            "path": f"memory/{memory.get('source', '')}"
        }
        results.append(result)
    
    return results

def format_results(results: List[Dict[str, Any]]) -> str:
    """格式化结果为markdown"""
    if not results:
        return "未找到相关记忆。"
    
    lines = [f"找到 {len(results)} 条相关记忆：\n"]
    
    for i, r in enumerate(results, 1):
        lines.append(f"**{i}.** [{r['content'][:80]}...]")
        lines.append(f"   - 来源: `{r['path']}`")
        lines.append(f"   - 标签: {', '.join(r['tags'])}")
        lines.append(f"   - 重要性: {r['importance']}/10 | 相关度: {r['score']}")
        lines.append("")
    
    return '\n'.join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 local_memory_search.py <查询关键词>")
        print("示例: python3 local_memory_search.py '完全自主进化'")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    results = search_memories(query, max_results=5)
    print(format_results(results))
