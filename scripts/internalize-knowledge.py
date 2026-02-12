#!/usr/bin/env python3
"""
知识内化脚本
将学习的内容内化到长期记忆系统中
"""

import json
from datetime import datetime
from pathlib import Path

def internalize_knowledge():
    """知识内化主流程"""
    print(f"\n{'='*60}")
    print("🧠 知识内化流程")
    print(f"{'='*60}\n")
    
    # 检查待内化的内容
    intel_dir = Path("memory/intel")
    if not intel_dir.exists():
        print("情报目录不存在")
        return
    
    # 查找最新的情报文件
    intel_files = sorted(intel_dir.glob("intel_*.json"), reverse=True)
    
    if not intel_files:
        print("没有待内化的情报文件")
        return
    
    # 处理最近的情报
    recent_files = intel_files[:3]  # 处理最近3个
    
    total_insights = 0
    for intel_file in recent_files:
        print(f"处理: {intel_file.name}")
        
        try:
            with open(intel_file, 'r', encoding='utf-8') as f:
                intel_data = json.load(f)
            
            high_signal_items = intel_data.get('high_signal_items', [])
            
            for item in high_signal_items:
                # 生成洞察
                insights = generate_insights(item)
                total_insights += len(insights)
                
                # 存储到知识库
                store_insight(item, insights)
                
        except Exception as e:
            print(f"   错误: {e}")
    
    # 更新记忆文件
    update_memory_files()
    
    print(f"\n{'='*60}")
    print(f"✅ 知识内化完成 - 生成 {total_insights} 条洞察")
    print(f"{'='*60}\n")

def generate_insights(item):
    """基于内容生成洞察"""
    insights = []
    
    title = item.get('title', '')
    content = item.get('deep_content', '') or item.get('description', '')
    signal = item.get('signal', 5)
    
    # 基于关键词生成洞察
    if 'agent' in title.lower() or 'agent' in content.lower():
        insights.append("Agent架构相关 - 可能涉及多Agent协作或自主决策")
    
    if 'memory' in title.lower() or 'memory' in content.lower():
        insights.append("记忆系统相关 - 可能涉及长期记忆、向量检索或知识图谱")
    
    if 'mcp' in title.lower():
        insights.append("MCP协议相关 - 可能涉及工具调用或上下文协议")
    
    if 'rag' in title.lower():
        insights.append("RAG技术相关 - 可能涉及检索增强生成")
    
    if signal >= 8:
        insights.append("极高Signal内容 - 需要优先关注和应用")
    
    return insights

def store_insight(item, insights):
    """存储洞察到知识库"""
    kg_file = Path("memory/knowledge-graph.md")
    kg_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(kg_file, 'a', encoding='utf-8') as f:
        f.write(f"\n### {datetime.now().strftime('%Y-%m-%d %H:%M')} - {item.get('title', 'Unknown')[:50]}\n")
        f.write(f"- **来源**: {item.get('url', 'N/A')}\n")
        f.write(f"- **Signal**: {item.get('signal', 5)}\n")
        f.write(f"- **洞察**:\n")
        for insight in insights:
            f.write(f"  - {insight}\n")

def update_memory_files():
    """更新核心记忆文件"""
    # 更新 core-archive.md 的最后更新时间
    archive_file = Path("memory/modules/core-archive.md")
    if archive_file.exists():
        with open(archive_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新最后内化时间
        if "**最后知识内化**" in content:
            import re
            content = re.sub(
                r'\*\*最后知识内化\*\*: .*',
                f"**最后知识内化**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content
            )
        else:
            content += f"\n**最后知识内化**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        with open(archive_file, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    internalize_knowledge()
