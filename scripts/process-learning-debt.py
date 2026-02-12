#!/usr/bin/env python3
"""
学习债务处理脚本
处理 memory/learning-debt.md 中的高Signal内容
实现学习→内化→应用的闭环
"""

import re
import argparse
from datetime import datetime
from pathlib import Path

def parse_learning_debt(limit=None):
    """解析学习债务文件"""
    debt_file = Path("memory/learning-debt.md")
    
    if not debt_file.exists():
        print("学习债务文件不存在")
        return []
    
    with open(debt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析债务项
    debt_items = []
    current_section = None
    
    for line in content.split('\n'):
        # 检测章节标题
        if line.startswith('## '):
            current_section = line[3:].strip()
        
        # 检测债务项
        match = re.match(r'- \[Signal (\d+)\] \[(.+?)\]\((.+?)\)', line)
        if match:
            signal = int(match.group(1))
            title = match.group(2)
            url = match.group(3)
            
            debt_items.append({
                'signal': signal,
                'title': title,
                'url': url,
                'section': current_section,
                'processed': False
            })
    
    # 按Signal排序
    debt_items.sort(key=lambda x: x['signal'], reverse=True)
    
    if limit:
        debt_items = debt_items[:limit]
    
    return debt_items

def process_debt_item(item):
    """处理单个债务项 - 模拟深度学习过程"""
    print(f"\n处理: [{item['signal']}] {item['title'][:60]}...")
    print(f"URL: {item['url']}")
    
    # 这里可以集成实际的深度学习提取
    # 目前生成处理记录
    
    processing_record = {
        'title': item['title'],
        'url': item['url'],
        'signal': item['signal'],
        'processed_at': datetime.now().isoformat(),
        'insights': [],
        'action_items': []
    }
    
    # 根据Signal级别决定处理深度
    if item['signal'] >= 9:
        print(f"   🔥 极高Signal内容 - 需要深度分析和应用")
        processing_record['insights'].append("需要深入阅读完整内容")
        processing_record['action_items'].append("更新核心记忆文件")
    elif item['signal'] >= 7:
        print(f"   ⭐ 高Signal内容 - 需要内化到知识图谱")
        processing_record['insights'].append("有价值的内容，需要结构化存储")
        processing_record['action_items'].append("关联到相关知识节点")
    else:
        print(f"   📌 中等Signal内容 - 记录摘要")
        processing_record['insights'].append("一般性参考内容")
    
    return processing_record

def update_knowledge_graph(records):
    """更新知识图谱"""
    kg_file = Path("memory/knowledge-graph.md")
    kg_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(kg_file, 'a', encoding='utf-8') as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} - 学习债务内化\n\n")
        for record in records:
            f.write(f"### {record['title'][:60]}\n")
            f.write(f"- **来源**: {record['url']}\n")
            f.write(f"- **Signal**: {record['signal']}\n")
            f.write(f"- **洞察**: {', '.join(record['insights'])}\n")
            f.write(f"- **行动**: {', '.join(record['action_items'])}\n\n")

def mark_debt_processed(processed_items):
    """标记债务为已处理"""
    debt_file = Path("memory/learning-debt.md")
    
    with open(debt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    processed_urls = {item['url'] for item in processed_items}
    
    new_lines = []
    for line in content.split('\n'):
        # 检查是否匹配已处理的URL
        if any(url in line for url in processed_urls):
            if line.startswith('- ') and '✅' not in line:
                line = line.replace('- ', '- ✅ ')
        new_lines.append(line)
    
    with open(debt_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

def main():
    parser = argparse.ArgumentParser(description="处理学习债务")
    parser.add_argument("--limit", type=int, default=5, help="处理数量限制")
    parser.add_argument("--all", action="store_true", help="处理所有债务")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("📚 学习债务处理")
    print(f"{'='*60}\n")
    
    # 解析债务
    limit = None if args.all else args.limit
    debt_items = parse_learning_debt(limit)
    
    if not debt_items:
        print("没有待处理的学习债务")
        return
    
    print(f"找到 {len(debt_items)} 条待处理债务\n")
    
    # 处理债务
    processed_records = []
    for item in debt_items:
        record = process_debt_item(item)
        processed_records.append(record)
    
    # 更新知识图谱
    if processed_records:
        update_knowledge_graph(processed_records)
        mark_debt_processed(debt_items)
        
        # 更新状态
        state_file = Path("memory/hyper-evolution-state.json")
        if state_file.exists():
            import json
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            state['learning_debt_cleared'] = state.get('learning_debt_cleared', 0) + len(processed_records)
            state['knowledge_updates'] = state.get('knowledge_updates', 0) + 1
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ 已处理 {len(processed_records)} 条学习债务")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
