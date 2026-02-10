"""
统一知识内化系统 - 使用示例
"""

from core.knowledge import KnowledgeCollector, KnowledgeProcessor, KnowledgeInsight
from core.knowledge.knowledge_insight import InsightGenerator


def demo():
    """演示知识内化系统的完整流程"""
    
    # 1. 初始化组件
    print("=== 初始化知识内化系统 ===")
    collector = KnowledgeCollector()
    processor = KnowledgeProcessor()
    insight_gen = InsightGenerator()
    
    # 2. 收集知识
    print("\n=== 收集原始知识 ===")
    
    raw_items = [
        collector.collect(
            content="学习了 Python 的 asyncio 库，了解了 async/await 的基本用法，可以用于提高 I/O 密集型任务的性能。",
            source="chat",
            tags=["技术", "Python", "学习"]
        ),
        collector.collect(
            content="发现了一个很好的在线学习资源：fast.ai，提供了免费的深度学习课程。",
            source="web",
            metadata={"url": "https://fast.ai"},
            tags=["资源", "深度学习", "学习"]
        ),
        collector.collect(
            content="需要完成项目报告，截止日期是本周五。应该优先处理数据可视化部分。",
            source="chat",
            tags=["工作", "待办"]
        ),
    ]
    
    for item in raw_items:
        print(f"  ✓ 收集: {item.id} [{item.source}]")
    
    # 3. 处理知识
    print("\n=== 处理知识 ===")
    processed_items = processor.process_batch(raw_items)
    
    for item in processed_items:
        print(f"  ✓ 处理: {item.id}")
        print(f"    分类: {item.category}")
        print(f"    摘要: {item.summary[:50]}...")
        print(f"    关键词: {', '.join(item.keywords[:5])}")
    
    # 4. 生成洞察
    print("\n=== 生成洞察 ===")
    
    # 每日摘要
    daily_summary = insight_gen.generate_daily_summary(processed_items)
    if daily_summary:
        print(f"  ✓ 每日摘要: {daily_summary.title}")
    
    # 模式发现
    patterns = insight_gen.find_patterns(processed_items)
    print(f"  ✓ 发现 {len(patterns)} 个模式")
    for p in patterns:
        print(f"    - {p.title}")
    
    # 关联发现
    connections = insight_gen.find_connections(processed_items, similarity_threshold=0.1)
    print(f"  ✓ 发现 {len(connections)} 个关联")
    
    # 提取行动项
    actions = insight_gen.extract_action_items(processed_items)
    print(f"  ✓ 提取 {len(actions)} 个行动项")
    for a in actions:
        print(f"    - [{a.priority}] {a.content}")
    
    # 5. 查询结果
    print("\n=== 系统状态 ===")
    all_raw = collector.list_raw(limit=100)
    all_processed = processor.list_processed(limit=100)
    all_insights = insight_gen.list_insights(limit=100)
    all_actions = insight_gen.list_actions(limit=100)
    
    print(f"  原始知识: {len(all_raw)} 条")
    print(f"  处理后知识: {len(all_processed)} 条")
    print(f"  洞察: {len(all_insights)} 条")
    print(f"  行动项: {len(all_actions)} 条")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    demo()
