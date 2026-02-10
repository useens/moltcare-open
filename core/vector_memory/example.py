"""
向量记忆系统使用示例

演示如何使用核心功能。
"""

from core.vector_memory import (
    create_memory_system,
    MemoryManager,
    MemoryConfig,
)


def example_basic_usage():
    """基础使用示例"""
    
    # 方式1：使用便捷函数创建
    memory = create_memory_system(
        db_path="./example_memory_db",
        model_name="BAAI/bge-large-zh-v1.5",  # 中英文通用模型
    )
    
    # 方式2：使用配置对象
    # config = MemoryConfig(
    #     db_path=Path("./memory_db"),
    #     model_name="BAAI/bge-large-zh-v1.5",
    #     embedding_dim=1024,
    # )
    # memory = MemoryManager(config)
    
    # 添加单条记忆
    memory.add_memory(
        content="OpenClaw是一个AI代理框架，支持多模型和工具集成。",
        metadata={
            "category": "技术",
            "source": "文档",
            "tags": ["AI", "框架"],
        }
    )
    
    # 批量添加记忆
    contents = [
        "Python是一种高级编程语言，语法简洁易读。",
        "LanceDB是一个高性能的向量数据库，支持Python和JavaScript。",
        "向量嵌入可以将文本转换为数值向量，用于语义搜索。",
    ]
    memory.add_memories_batch(contents)
    
    # 语义搜索
    results = memory.search(
        query="AI相关的框架有哪些？",
        top_k=5,
        search_type="semantic",
    )
    
    print("语义搜索结果:")
    for r in results:
        print(f"  [{r.score:.4f}] {r.content[:50]}...")
    
    # 混合搜索（语义+关键词）
    results = memory.search(
        query="Python编程语言",
        top_k=5,
        search_type="hybrid",
    )
    
    print("\n混合搜索结果:")
    for r in results:
        print(f"  [{r.score:.4f}] {r.content[:50]}...")
    
    # 获取统计信息
    stats = memory.get_stats()
    print(f"\n统计信息: {stats}")
    
    # 关闭连接
    memory.close()


def example_file_import():
    """文件导入示例"""
    
    memory = create_memory_system("./import_memory_db")
    
    # 从单个文件导入
    # memory.import_from_file("./notes.md", format="md")
    
    # 从目录批量导入
    # memory.import_from_directory(
    #     directory="./memory_files",
    #     pattern="*.md",
    #     recursive=True,
    # )
    
    # 从Markdown字符串导入
    markdown_content = """
# 项目笔记

## 架构设计

系统采用分层架构，包括数据层、服务层和表现层。

## 技术选型

- 数据库：PostgreSQL
- 缓存：Redis
- 消息队列：RabbitMQ
"""
    
    memory.import_from_markdown(
        content=markdown_content,
        source="project_notes",
        split_by_heading=True,
    )
    
    # 搜索
    results = memory.search("系统架构是什么样的？")
    print("文件导入搜索结果:")
    for r in results:
        print(f"  [{r.score:.4f}] {r.content[:60]}...")
    
    memory.close()


def example_advanced():
    """高级功能示例"""
    
    memory = create_memory_system("./advanced_memory_db")
    
    # 添加多条测试数据
    test_data = [
        "机器学习是人工智能的一个分支，专注于让计算机从数据中学习。",
        "深度学习是机器学习的一种，使用多层神经网络。",
        "自然语言处理让计算机理解和生成人类语言。",
        "计算机视觉使计算机能够"看见"和理解图像内容。",
        "强化学习通过与环境交互来学习最优策略。",
    ]
    
    memory.add_memories_batch(test_data)
    
    # 带过滤条件的搜索
    results = memory.search(
        query="学习算法",
        filter_dict={"category": "AI"},  # 元数据过滤
        top_k=3,
    )
    
    # 更新记忆
    # memory.update_memory(
    #     record_id="some-id",
    #     content="更新后的内容",
    #     metadata={"updated": True},
    # )
    
    # 删除记忆
    # memory.delete_memory("some-id")
    
    # 清理过期数据
    # memory.cleanup_expired(max_age_days=30)
    
    # 清理重复数据
    # memory.cleanup_duplicates(similarity_threshold=0.95)
    
    # 手动优化索引
    memory.optimize()
    
    memory.close()


def example_context_manager():
    """上下文管理器使用示例"""
    
    config = MemoryConfig(
        db_path="./context_memory_db",
        model_name="BAAI/bge-large-zh-v1.5",
    )
    
    with MemoryManager(config) as memory:
        # 自动初始化和关闭
        memory.add_memory("这是一个使用上下文管理器的示例。")
        
        results = memory.search("上下文管理器")
        for r in results:
            print(f"结果: {r.content}")
    # 退出时自动关闭


if __name__ == "__main__":
    print("=" * 50)
    print("基础使用示例")
    print("=" * 50)
    example_basic_usage()
    
    print("\n" + "=" * 50)
    print("文件导入示例")
    print("=" * 50)
    example_file_import()
    
    print("\n" + "=" * 50)
    print("高级功能示例")
    print("=" * 50)
    example_advanced()
    
    print("\n" + "=" * 50)
    print("上下文管理器示例")
    print("=" * 50)
    example_context_manager()
