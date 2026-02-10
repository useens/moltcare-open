#!/usr/bin/env python3
"""
示例2: 集成到Agent系统 - Integration Example

展示如何将向量记忆系统集成到AI Agent中，
替换原有的memory_search调用。
"""

import os
import sys
from typing import List, Dict, Optional

sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/local-memory-system'))

from local_memory import LocalMemorySystem


class VectorMemoryAdapter:
    """
    向量记忆系统适配器
    
    提供与旧版memory_search兼容的接口，
    同时支持新的语义搜索功能。
    """
    
    _instance = None
    
    def __new__(cls, memory_dir: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._memory = None
            cls._instance._memory_dir = memory_dir
        return cls._instance
    
    @property
    def memory(self) -> LocalMemorySystem:
        """懒加载记忆系统"""
        if self._memory is None:
            memory_dir = self._memory_dir or os.path.expanduser('~/.openclaw/memory-vector')
            self._memory = LocalMemorySystem(memory_dir)
        return self._memory
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        语义搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表，每个结果包含文件路径、相似度等
        """
        return self.memory.search(query, top_k=top_k)
    
    def search_contents(self, query: str, top_k: int = 5) -> List[str]:
        """
        搜索并返回内容（兼容旧接口）
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            内容预览列表
        """
        results = self.memory.search(query, top_k=top_k)
        return [r['content_preview'] for r in results]
    
    def index_file(self, file_path: str) -> None:
        """索引文件"""
        self.memory.index_file(file_path)
    
    def find_related(self, doc_id: int, top_k: int = 5) -> List[Dict]:
        """查找相关文档"""
        return self.memory.find_related(doc_id, top_k=top_k)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.memory.get_stats()


# 全局适配器实例
_memory_adapter: Optional[VectorMemoryAdapter] = None


def get_memory() -> VectorMemoryAdapter:
    """获取记忆系统适配器实例"""
    global _memory_adapter
    if _memory_adapter is None:
        _memory_adapter = VectorMemoryAdapter()
    return _memory_adapter


def memory_search(query: str, top_k: int = 5) -> List[str]:
    """
    兼容旧版memory_search接口
    
    可直接替换原有调用，无需修改代码。
    """
    return get_memory().search_contents(query, top_k)


class AIAgent:
    """
    AI Agent示例类
    
    展示如何在Agent中使用向量记忆系统。
    """
    
    def __init__(self, name: str = "Agent"):
        self.name = name
        self.memory = get_memory()
        print(f"🤖 {name} 初始化完成")
    
    def recall_context(self, query: str, top_k: int = 3) -> str:
        """
        回忆相关上下文
        
        根据查询召回相关的记忆内容，用于增强上下文。
        """
        print(f"\n🧠 {self.name} 正在回忆关于 '{query}' 的记忆...")
        
        results = self.memory.search(query, top_k=top_k)
        
        if not results:
            return "没有找到相关记忆。"
        
        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(
                f"[记忆 {i}] {os.path.basename(r['file_path'])} (相关度: {r['similarity']:.2%})\n"
                f"{r['content_preview'][:300]}..."
            )
        
        return "\n\n".join(context_parts)
    
    def learn_from_file(self, file_path: str) -> bool:
        """
        从文件学习
        
        将文件索引到记忆系统中。
        """
        try:
            print(f"\n📚 {self.name} 正在学习文件: {file_path}")
            self.memory.index_file(file_path)
            print(f"   ✅ 学习完成")
            return True
        except Exception as e:
            print(f"   ❌ 学习失败: {e}")
            return False
    
    def find_related_memories(self, doc_id: int) -> List[Dict]:
        """
        发现相关记忆
        
        查找与指定记忆相关的其他记忆。
        """
        print(f"\n🔗 {self.name} 正在发现与文档 {doc_id} 相关的记忆...")
        return self.memory.find_related(doc_id, top_k=5)


def demo_agent_integration():
    """演示Agent集成"""
    
    print("=" * 60)
    print("🤖 示例2: Agent系统集成演示")
    print("=" * 60)
    
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建适配器（指定临时目录）
        adapter = VectorMemoryAdapter(tmpdir)
        adapter.memory.init()
        
        # 创建示例文档
        print("\n📄 创建示例记忆文件...")
        
        memories = [
            ("user_preferences.md", """
# 用户偏好设置

## 沟通风格
- 喜欢简洁直接的回复
- 不喜欢冗长的解释
- 重视代码示例

## 技术栈
- Python (主要)
- JavaScript/TypeScript
- 对AI/ML感兴趣

## 工作习惯
- 早晨效率最高
- 喜欢先规划再执行
- 重视备份和安全
"""),
            ("project_ideas.md", """
# 项目想法

## 1. 智能笔记助手
- 自动分类和标签
- 语义搜索笔记内容
- 与日历集成

## 2. 代码审查助手
- 自动检查代码风格
- 发现潜在bug
- 提供优化建议

## 3. 个人知识库
- 整合所有学习资料
- 建立知识图谱
- 支持问答检索
"""),
            ("meeting_notes_2024.md", """
# 会议记录 2024

## Q1 规划会议
- 确定年度目标
- 分配团队资源
- 制定里程碑

## Q2 复盘会议
- 项目进度 review
- 技术债务清理
- 下半年规划调整
""")
        ]
        
        for filename, content in memories:
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   📝 {filename}")
        
        # 创建Agent
        agent = AIAgent(name="LinLin")
        
        # 让Agent学习文件
        print("\n" + "-" * 40)
        for filename, _ in memories:
            filepath = os.path.join(tmpdir, filename)
            agent.learn_from_file(filepath)
        
        # 演示1: 回忆上下文
        print("\n" + "-" * 40)
        print("\n🔍 演示1: 回忆上下文")
        queries = [
            "用户喜欢什么样的沟通方式",
            "有什么项目想法",
            "团队会议讨论了什么"
        ]
        
        for query in queries:
            context = agent.recall_context(query, top_k=2)
            print(f"\n查询: {query}")
            print(context)
            print("-" * 40)
        
        # 演示2: 兼容旧接口
        print("\n🔍 演示2: 兼容旧版memory_search接口")
        results = memory_search("项目管理", top_k=3)
        print(f"找到 {len(results)} 条记忆")
        for i, content in enumerate(results, 1):
            print(f"\n结果 {i}:")
            print(content[:200] + "...")
        
        # 演示3: 发现相关记忆
        print("\n" + "-" * 40)
        print("\n🔍 演示3: 发现相关记忆")
        docs = adapter.memory.list_documents()
        if docs:
            related = agent.find_related_memories(docs[0]['id'])
            print(f"找到 {len(related)} 条相关记忆")
            for r in related:
                print(f"   - {os.path.basename(r['file_path'])} (相似度: {r['similarity']:.4f})")
        
        # 查看统计
        print("\n" + "=" * 60)
        print("📊 记忆系统统计:")
        stats = adapter.memory.get_stats()
        print(f"   文档数量: {stats['document_count']}")
        print(f"   向量数量: {stats['vector_count']}")
        
        print("\n" + "=" * 60)
        print("✅ 集成演示完成!")
        print("=" * 60)


if __name__ == '__main__':
    try:
        demo_agent_integration()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
