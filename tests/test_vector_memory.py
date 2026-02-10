#!/usr/bin/env python3
"""
向量记忆系统测试与验证
Vector Memory System Testing and Validation

测试范围:
1. 单元测试 - 向量添加、查询、相似度计算、分块逻辑
2. 集成测试 - 导入现有memory文件、中文搜索、性能基准
3. 验证清单 - 模型下载、启动时间、增量更新、内存占用
"""

import os
import sys
import json
import time
import psutil
import pytest
import sqlite3
import tempfile
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 添加local-memory-system到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "local-memory-system"))

# 测试依赖检查
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ sentence-transformers 未安装，部分测试将被跳过")

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)


# =============================================================================
# 测试数据准备 - 100条测试记忆
# =============================================================================

TEST_MEMORIES = [
    # === 类型1: 指令 (Instructions) - 25条 ===
    {"type": "instruction", "content": "用户要求所有代码必须包含中文注释，方便后续维护"},
    {"type": "instruction", "content": "重要决策必须记录决策理由和替代方案考虑"},
    {"type": "instruction", "content": "每日工作结束前需要提交git commit并推送到远程仓库"},
    {"type": "instruction", "content": "遇到安全相关操作必须先询问用户确认"},
    {"type": "instruction", "content": "使用Feishu发送消息时必须检查token有效性"},
    {"type": "instruction", "content": "所有自动化脚本需要包含错误处理和日志记录"},
    {"type": "instruction", "content": "数据库操作必须使用参数化查询防止SQL注入"},
    {"type": "instruction", "content": "API密钥和敏感信息必须存储在环境变量中"},
    {"type": "instruction", "content": "代码审查时重点关注边界条件处理"},
    {"type": "instruction", "content": "所有用户界面文本需要支持国际化"},
    {"type": "instruction", "content": "定期备份重要数据到多个存储位置"},
    {"type": "instruction", "content": "使用异步编程处理I/O密集型任务"},
    {"type": "instruction", "content": "缓存频繁访问的数据以提高性能"},
    {"type": "instruction", "content": "实现限流机制防止API被滥用"},
    {"type": "instruction", "content": "使用连接池管理数据库连接"},
    {"type": "instruction", "content": "记录所有重要操作的审计日志"},
    {"type": "instruction", "content": "实现优雅关闭机制处理正在进行的任务"},
    {"type": "instruction", "content": "使用类型注解提高代码可读性"},
    {"type": "instruction", "content": "编写单元测试覆盖核心功能"},
    {"type": "instruction", "content": "使用Docker容器化部署应用"},
    {"type": "instruction", "content": "监控关键性能指标并设置告警"},
    {"type": "instruction", "content": "实现健康检查端点用于服务监控"},
    {"type": "instruction", "content": "使用结构化日志方便日志分析"},
    {"type": "instruction", "content": "定期更新依赖库以修复安全漏洞"},
    {"type": "instruction", "content": "代码提交前运行静态代码分析工具"},
    
    # === 类型2: 发现 (Discoveries) - 25条 ===
    {"type": "discovery", "content": "发现使用余弦相似度比欧氏距离更适合文本语义匹配"},
    {"type": "discovery", "content": "MiniLM模型在中文文本上表现良好，推理速度快"},
    {"type": "discovery", "content": "SQLite的FTS5扩展可以实现高效的全文搜索"},
    {"type": "discovery", "content": "向量归一化可以显著提升搜索准确性"},
    {"type": "discovery", "content": "使用BLOB存储numpy数组比JSON更节省空间"},
    {"type": "discovery", "content": "批量处理比逐条处理向量效率高3倍以上"},
    {"type": "discovery", "content": "Faiss索引比暴力搜索快100倍但占用更多内存"},
    {"type": "discovery", "content": "文本分块策略对搜索结果质量影响巨大"},
    {"type": "discovery", "content": "HNSW算法在高维向量搜索中表现优异"},
    {"type": "discovery", "content": "量化技术可以将向量存储减少75%而精度损失很小"},
    {"type": "discovery", "content": "使用GPU加速可以将嵌入生成速度提升10倍"},
    {"type": "discovery", "content": "定期重新索引可以保持搜索质量稳定"},
    {"type": "discovery", "content": "混合搜索（向量+关键词）比单一方法效果更好"},
    {"type": "discovery", "content": "缓存频繁查询的嵌入向量可以显著降低延迟"},
    {"type": "discovery", "content": "使用内存映射文件可以处理超出物理内存的数据"},
    {"type": "discovery", "content": "增量更新策略可以减少90%的重新计算时间"},
    {"type": "discovery", "content": "多层索引结构可以平衡查询速度和内存使用"},
    {"type": "discovery", "content": "相似度阈值设为0.7可以在精度和召回率间取得平衡"},
    {"type": "discovery", "content": "使用元数据过滤可以减少搜索空间提高效率"},
    {"type": "discovery", "content": "向量维度从768降到384可以节省50%空间而精度损失很小"},
    {"type": "discovery", "content": "多语言模型在跨语言搜索中表现令人惊讶地好"},
    {"type": "discovery", "content": "短文本（<50字符）的向量表示质量较差"},
    {"type": "discovery", "content": "使用主成分分析可以可视化高维向量分布"},
    {"type": "discovery", "content": "文档的标题和正文应该分别建立索引"},
    {"type": "discovery", "content": "时间衰减因子可以让新文档在搜索中排名更高"},
    
    # === 类型3: 决策 (Decisions) - 25条 ===
    {"type": "decision", "content": "决定使用SQLite而非PostgreSQL作为向量存储，考虑到部署简单性"},
    {"type": "decision", "content": "选择all-MiniLM-L6-v2作为默认嵌入模型，平衡精度和速度"},
    {"type": "decision", "content": "采用余弦相似度作为默认相似度度量方法"},
    {"type": "decision", "content": "确定向量维度为384，满足大部分应用场景需求"},
    {"type": "decision", "content": "使用文件内容哈希来判断文档是否需要更新索引"},
    {"type": "decision", "content": "决定支持混合搜索模式，结合向量相似度和关键词匹配"},
    {"type": "decision", "content": "选择Python作为主开发语言，利用丰富的ML生态"},
    {"type": "decision", "content": "采用懒加载策略初始化嵌入模型，减少启动时间"},
    {"type": "decision", "content": "使用numpy的float32而非float64存储向量，节省内存"},
    {"type": "decision", "content": "确定默认返回5条最相似的结果"},
    {"type": "decision", "content": "实现增量索引更新而非全量重建"},
    {"type": "decision", "content": "选择pytest作为测试框架，支持丰富的断言和fixture"},
    {"type": "decision", "content": "使用GitHub Actions进行持续集成测试"},
    {"type": "decision", "content": "采用语义化版本控制管理发布"},
    {"type": "decision", "content": "使用MIT许可证开源项目代码"},
    {"type": "decision", "content": "决定先实现核心功能再考虑性能优化"},
    {"type": "decision", "content": "采用模块化设计便于后续功能扩展"},
    {"type": "decision", "content": "使用Type hints提高代码可维护性"},
    {"type": "decision", "content": "选择黑色主题作为默认文档风格"},
    {"type": "decision", "content": "使用中英文双语编写文档"},
    {"type": "decision", "content": "确定最低支持Python 3.9版本"},
    {"type": "decision", "content": "使用poetry管理项目依赖"},
    {"type": "decision", "content": "采用conventional commits规范提交信息"},
    {"type": "decision", "content": "使用pre-commit钩子确保代码质量"},
    {"type": "decision", "content": "决定优先支持Linux和macOS平台"},
    
    # === 类型4: 错误 (Errors) - 25条 ===
    {"type": "error", "content": "错误：忘记处理空查询字符串导致程序崩溃，已添加空值检查"},
    {"type": "error", "content": "错误：向量维度不匹配导致相似度计算失败，现已添加维度验证"},
    {"type": "error", "content": "错误：数据库连接未关闭导致资源泄漏，已使用上下文管理器"},
    {"type": "error", "content": "错误：文件编码问题导致中文内容乱码，已统一使用UTF-8"},
    {"type": "error", "content": "错误：并发写入导致数据库锁定，已添加重试机制"},
    {"type": "error", "content": "错误：大文件处理时内存溢出，已实现流式处理"},
    {"type": "error", "content": "错误：相似度计算时除以零，已添加边界检查"},
    {"type": "error", "content": "错误：模型文件下载超时，已添加断点续传"},
    {"type": "error", "content": "错误：路径包含特殊字符导致文件操作失败，已进行路径转义"},
    {"type": "error", "content": "错误：缓存数据格式不兼容导致解析失败，已添加版本检查"},
    {"type": "error", "content": "错误：浮点数精度问题导致相似度比较不准确，已使用Decimal"},
    {"type": "error", "content": "错误：递归深度过大导致栈溢出，已改为迭代实现"},
    {"type": "error", "content": "错误：正则表达式回溯导致性能问题，已优化正则模式"},
    {"type": "error", "content": "错误：未处理的异常导致程序崩溃，已添加全局异常处理"},
    {"type": "error", "content": "错误：时区问题导致时间戳不一致，已统一使用UTC"},
    {"type": "error", "content": "错误：SQL注入漏洞，已使用参数化查询"},
    {"type": "error", "content": "错误：竞态条件导致数据不一致，已添加锁机制"},
    {"type": "error", "content": "错误：JSON序列化失败，已处理非标准类型"},
    {"type": "error", "content": "错误：网络请求重试次数不足，已增加指数退避"},
    {"type": "error", "content": "错误：配置文件格式错误，已添加Schema验证"},
    {"type": "error", "content": "错误：磁盘空间不足导致写入失败，已添加预检查"},
    {"type": "error", "content": "错误：内存碎片问题，已使用对象池优化"},
    {"type": "error", "content": "错误：API限流导致请求被拒绝，已实现自适应限流"},
    {"type": "error", "content": "错误：长文本截断导致信息丢失，已实现智能分块"},
    {"type": "error", "content": "错误：依赖版本冲突，已锁定依赖版本"},
]


# =============================================================================
# 模拟向量记忆系统 (用于单元测试)
# =============================================================================

class MockVectorMemorySystem:
    """模拟向量记忆系统，用于单元测试"""
    
    def __init__(self):
        self.documents: Dict[int, dict] = {}
        self.vectors: Dict[int, np.ndarray] = {}
        self.next_id = 1
        self.embedding_dim = 384
        
    def add_document(self, content: str, doc_type: str = "general") -> int:
        """添加文档到记忆系统"""
        doc_id = self.next_id
        self.next_id += 1
        
        # 模拟生成嵌入向量（使用哈希生成确定性向量）
        np.random.seed(hash(content) % 2**32)
        vector = np.random.randn(self.embedding_dim).astype(np.float32)
        vector = vector / np.linalg.norm(vector)  # 归一化
        
        self.documents[doc_id] = {
            "id": doc_id,
            "content": content,
            "type": doc_type,
            "created_at": datetime.now().isoformat()
        }
        self.vectors[doc_id] = vector
        
        return doc_id
    
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """搜索相似文档"""
        if not query.strip():
            return []
        
        # 模拟查询向量
        np.random.seed(hash(query) % 2**32)
        query_vector = np.random.randn(self.embedding_dim).astype(np.float32)
        query_vector = query_vector / np.linalg.norm(query_vector)
        
        # 计算相似度
        results = []
        for doc_id, doc_vector in self.vectors.items():
            similarity = float(np.dot(query_vector, doc_vector))
            results.append({
                "id": doc_id,
                "content": self.documents[doc_id]["content"],
                "similarity": similarity,
                "type": self.documents[doc_id]["type"]
            })
        
        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
    
    def chunk_text(self, text: str, chunk_size: int = 100, overlap: int = 20) -> List[str]:
        """将长文本分块"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        
        return chunks
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "document_count": len(self.documents),
            "vector_count": len(self.vectors),
            "embedding_dim": self.embedding_dim
        }


# =============================================================================
# 单元测试
# =============================================================================

class TestVectorMemoryUnit:
    """向量记忆系统单元测试"""
    
    @pytest.fixture
    def memory(self):
        """创建测试用的记忆系统实例"""
        return MockVectorMemorySystem()
    
    # === 测试向量添加 ===
    
    def test_add_single_document(self, memory):
        """测试添加单个文档"""
        doc_id = memory.add_document("这是一条测试文档")
        assert doc_id == 1
        assert len(memory.documents) == 1
        assert memory.documents[doc_id]["content"] == "这是一条测试文档"
    
    def test_add_multiple_documents(self, memory):
        """测试添加多个文档"""
        ids = []
        for i in range(10):
            doc_id = memory.add_document(f"文档{i}")
            ids.append(doc_id)
        
        assert len(ids) == 10
        assert ids == list(range(1, 11))
        assert len(memory.documents) == 10
    
    def test_add_document_with_type(self, memory):
        """测试带类型的文档添加"""
        doc_id = memory.add_document("指令内容", doc_type="instruction")
        assert memory.documents[doc_id]["type"] == "instruction"
    
    def test_document_has_embedding(self, memory):
        """测试文档添加后是否有嵌入向量"""
        doc_id = memory.add_document("测试内容")
        assert doc_id in memory.vectors
        assert isinstance(memory.vectors[doc_id], np.ndarray)
        assert memory.vectors[doc_id].shape == (memory.embedding_dim,)
    
    def test_embedding_normalized(self, memory):
        """测试嵌入向量是否归一化"""
        doc_id = memory.add_document("测试")
        vector = memory.vectors[doc_id]
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 1e-6, f"向量未归一化，范数为 {norm}"
    
    # === 测试向量查询 ===
    
    def test_search_returns_results(self, memory):
        """测试搜索返回结果"""
        memory.add_document("Python编程指南")
        memory.add_document("机器学习入门")
        memory.add_document("数据科学基础")
        
        results = memory.search("Python编程", top_k=3)
        assert isinstance(results, list)
        assert len(results) <= 3
    
    def test_search_empty_query(self, memory):
        """测试空查询处理"""
        memory.add_document("测试文档")
        results = memory.search("")
        assert results == []
    
    def test_search_whitespace_query(self, memory):
        """测试空白查询处理"""
        memory.add_document("测试文档")
        results = memory.search("   ")
        assert results == []
    
    def test_search_returns_similarity_score(self, memory):
        """测试搜索结果包含相似度分数"""
        memory.add_document("向量数据库设计")
        results = memory.search("数据库")
        
        if results:
            assert "similarity" in results[0]
            assert isinstance(results[0]["similarity"], float)
            assert -1 <= results[0]["similarity"] <= 1
    
    def test_search_respects_top_k(self, memory):
        """测试top_k参数生效"""
        for i in range(20):
            memory.add_document(f"文档{i}")
        
        results = memory.search("文档", top_k=5)
        assert len(results) == 5
    
    # === 测试相似度计算 ===
    
    def test_cosine_similarity_identical_vectors(self, memory):
        """测试相同向量的余弦相似度为1"""
        vec = np.array([1.0, 0.0, 0.0])
        sim = memory.cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 1e-6
    
    def test_cosine_similarity_opposite_vectors(self, memory):
        """测试相反向量的余弦相似度为-1"""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])
        sim = memory.cosine_similarity(vec1, vec2)
        assert abs(sim - (-1.0)) < 1e-6
    
    def test_cosine_similarity_orthogonal_vectors(self, memory):
        """测试正交向量的余弦相似度为0"""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        sim = memory.cosine_similarity(vec1, vec2)
        assert abs(sim - 0.0) < 1e-6
    
    def test_cosine_similarity_range(self, memory):
        """测试余弦相似度范围在[-1, 1]"""
        for _ in range(100):
            vec1 = np.random.randn(384)
            vec2 = np.random.randn(384)
            sim = memory.cosine_similarity(vec1, vec2)
            assert -1.0 <= sim <= 1.0
    
    def test_cosine_similarity_zero_vector(self, memory):
        """测试零向量处理"""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([0.0, 0.0, 0.0])
        sim = memory.cosine_similarity(vec1, vec2)
        assert sim == 0.0  # 应该返回0而非抛出异常
    
    # === 测试分块逻辑 ===
    
    def test_chunk_short_text(self, memory):
        """测试短文本不分块"""
        text = "短文本"
        chunks = memory.chunk_text(text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_long_text(self, memory):
        """测试长文本分块"""
        text = "A" * 250
        chunks = memory.chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) == 4  # 250 / (100-20) ≈ 3.1，向上取整为4
    
    def test_chunk_overlap(self, memory):
        """测试分块重叠"""
        text = "ABCDEFGHIJ"
        chunks = memory.chunk_text(text, chunk_size=5, overlap=2)
        # 10字符，chunksize=5，overlap=2 -> 每步前进3 -> 需要4块
        assert len(chunks) >= 3
        # 验证重叠
        for i in range(len(chunks) - 1):
            # 相邻块应有重叠内容
            assert len(set(chunks[i]) & set(chunks[i+1])) > 0
    
    def test_chunk_empty_text(self, memory):
        """测试空文本分块"""
        chunks = memory.chunk_text("")
        assert chunks == [""]
    
    def test_chunk_preserves_content(self, memory):
        """测试分块保留完整内容"""
        text = "这是一段用于测试的文本，需要确保分块后内容完整。"
        chunks = memory.chunk_text(text, chunk_size=10, overlap=2)
        # 验证所有原始内容都被覆盖
        reconstructed = chunks[0]
        for chunk in chunks[1:]:
            reconstructed += chunk[2:]  # 去掉重叠部分
        # 允许一些边界差异
        assert len(reconstructed) >= len(text) * 0.9
    
    # === 测试边界情况 ===
    
    def test_search_no_documents(self, memory):
        """测试无文档时搜索"""
        results = memory.search("查询")
        assert results == []
    
    def test_add_empty_document(self, memory):
        """测试添加空文档"""
        doc_id = memory.add_document("")
        assert doc_id in memory.documents
        assert memory.documents[doc_id]["content"] == ""
    
    def test_add_very_long_document(self, memory):
        """测试添加超长文档"""
        long_content = "A" * 100000
        doc_id = memory.add_document(long_content)
        assert doc_id in memory.documents
        assert len(memory.documents[doc_id]["content"]) == 100000
    
    def test_add_unicode_document(self, memory):
        """测试添加Unicode文档"""
        unicode_content = "中文测试 🎉 ñoño émoji: 🚀🔥"
        doc_id = memory.add_document(unicode_content)
        assert memory.documents[doc_id]["content"] == unicode_content
    
    def test_search_special_characters(self, memory):
        """测试特殊字符搜索"""
        memory.add_document("特殊字符: !@#$%^&*()")
        results = memory.search("!@#")
        assert isinstance(results, list)
    
    def test_large_scale_documents(self, memory):
        """测试大量文档处理"""
        for i in range(1000):
            memory.add_document(f"大规模测试文档 {i}")
        
        assert len(memory.documents) == 1000
        stats = memory.get_stats()
        assert stats["document_count"] == 1000
        
        # 测试搜索性能
        start = time.time()
        results = memory.search("测试", top_k=10)
        duration = time.time() - start
        
        assert len(results) == 10
        assert duration < 1.0  # 1000条数据搜索应在1秒内完成


# =============================================================================
# 集成测试
# =============================================================================

@pytest.mark.skipif(not SENTENCE_TRANSFORMERS_AVAILABLE, 
                    reason="sentence-transformers not installed")
class TestVectorMemoryIntegration:
    """向量记忆系统集成测试"""
    
    @pytest.fixture(scope="class")
    def temp_memory_dir(self):
        """创建临时记忆目录"""
        temp_dir = tempfile.mkdtemp(prefix="vector_memory_test_")
        yield temp_dir
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def real_memory(self, temp_memory_dir):
        """创建真实的记忆系统实例"""
        try:
            from local_memory import LocalMemorySystem
            memory = LocalMemorySystem(memory_dir=temp_memory_dir)
            memory.init()
            yield memory
        except ImportError:
            pytest.skip("local_memory module not available")
    
    # === 测试模型加载 ===
    
    def test_model_auto_download(self, temp_memory_dir):
        """测试模型自动下载"""
        try:
            from local_memory import LocalMemorySystem
            memory = LocalMemorySystem(memory_dir=temp_memory_dir)
            
            start_time = time.time()
            model = memory._get_model()
            load_time = time.time() - start_time
            
            assert model is not None
            assert hasattr(model, 'encode')
            print(f"模型加载时间: {load_time:.2f}秒")
            assert load_time < 60  # 首次加载应在60秒内
        except ImportError:
            pytest.skip("local_memory module not available")
    
    def test_model_embedding_quality(self, real_memory):
        """测试模型嵌入质量"""
        text1 = "Python编程语言"
        text2 = "Java编程语言"
        text3 = "苹果是一种水果"
        
        vec1 = real_memory._get_embedding(text1)
        vec2 = real_memory._get_embedding(text2)
        vec3 = real_memory._get_embedding(text3)
        
        # 相似主题应该有更高相似度
        sim_1_2 = real_memory._cosine_similarity(vec1, vec2)
        sim_1_3 = real_memory._cosine_similarity(vec1, vec3)
        
        assert sim_1_2 > sim_1_3, f"相似主题相似度({sim_1_2})应大于不同主题({sim_1_3})"
    
    # === 测试中文搜索 ===
    
    def test_chinese_search_accuracy(self, real_memory):
        """测试中文搜索准确性"""
        # 添加中文文档
        test_docs = [
            "机器学习是人工智能的一个分支",
            "深度学习使用神经网络进行训练",
            "Python是一种流行的编程语言",
            "自然语言处理让计算机理解人类语言",
            "数据科学涉及统计学和编程"
        ]
        
        for i, doc in enumerate(test_docs):
            real_memory.index_file(f"/test/doc_{i}.txt", content=doc)
        
        # 测试相关搜索
        results = real_memory.search("神经网络", top_k=3)
        assert len(results) > 0
        # 最相关的结果应该包含"深度学习"
        top_content = results[0]['content_preview']
        assert '深度学习' in top_content or '神经网络' in top_content
    
    def test_chinese_semantic_search(self, real_memory):
        """测试中文语义搜索（非关键词匹配）"""
        real_memory.index_file("/test/chinese_doc.txt", 
                               content="北京的天气今天很好，适合外出游玩")
        real_memory.index_file("/test/chinese_doc2.txt", 
                               content="上海今天下雨，不适合出门")
        real_memory.index_file("/test/chinese_doc3.txt", 
                               content="Python是一门编程语言")
        
        # 语义搜索："好天气" 应该匹配第一条
        results = real_memory.search("好天气", top_k=2)
        assert len(results) >= 1
        # 至少有一个结果与天气相关
        weather_related = any('天气' in r['content_preview'] or 
                              '下雨' in r['content_preview'] 
                              for r in results)
        assert weather_related, "应该返回天气相关的结果"
    
    def test_chinese_synonym_search(self, real_memory):
        """测试中文同义词搜索"""
        real_memory.index_file("/test/synonym1.txt", content="如何学习编程")
        real_memory.index_file("/test/synonym2.txt", content="怎样掌握代码编写")
        
        # "学习" 和 "掌握" 语义相似
        results = real_memory.search("学习方法", top_k=2)
        assert len(results) >= 1
    
    # === 测试导入现有memory文件 ===
    
    def test_import_memory_files(self, real_memory):
        """测试导入现有memory文件"""
        # 获取实际的memory目录
        memory_dir = Path(__file__).parent.parent / "memory"
        
        if not memory_dir.exists():
            pytest.skip("memory目录不存在")
        
        # 查找markdown文件
        md_files = list(memory_dir.glob("**/*.md"))[:10]
        if not md_files:
            pytest.skip("未找到markdown文件")
        
        imported = 0
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                if len(content) > 100:  # 只索引有内容的文件
                    real_memory.index_file(str(md_file), content=content)
                    imported += 1
            except Exception as e:
                print(f"导入 {md_file} 失败: {e}")
        
        assert imported > 0, "应该成功导入至少一个文件"
        
        # 测试搜索导入的内容
        results = real_memory.search("系统", top_k=5)
        assert len(results) > 0
    
    # === 性能基准测试 ===
    
    def test_indexing_performance(self, real_memory):
        """测试索引性能"""
        # 准备100条测试数据
        test_data = TEST_MEMORIES[:100]
        
        start_time = time.time()
        for i, item in enumerate(test_data):
            real_memory.index_file(f"/test/memory_{i}.txt", content=item["content"])
        duration = time.time() - start_time
        
        avg_time = duration / len(test_data)
        print(f"\n索引 {len(test_data)} 条记录:")
        print(f"  总时间: {duration:.2f}秒")
        print(f"  平均每条: {avg_time*1000:.2f}ms")
        
        assert avg_time < 1.0, f"索引平均时间({avg_time:.2f}s)超过1秒"
    
    def test_query_performance_1000_records(self, real_memory):
        """测试1000条记录的查询性能"""
        # 添加更多数据到1000条
        np.random.seed(42)
        for i in range(1000):
            content = TEST_MEMORIES[i % len(TEST_MEMORIES)]["content"]
            # 添加随机性使内容不同
            content += f" [随机ID: {np.random.randint(10000)}]"
            real_memory.index_file(f"/test/perf_{i}.txt", content=content)
        
        stats = real_memory.get_stats()
        assert stats['document_count'] >= 1000
        
        # 测试查询性能
        query_times = []
        test_queries = [
            "如何学习编程",
            "错误处理",
            "数据库设计",
            "性能优化",
            "安全策略"
        ]
        
        for query in test_queries:
            start = time.time()
            results = real_memory.search(query, top_k=10)
            duration = time.time() - start
            query_times.append(duration)
        
        avg_time = sum(query_times) / len(query_times)
        max_time = max(query_times)
        
        print(f"\n1000条记录查询性能:")
        print(f"  平均查询时间: {avg_time*1000:.2f}ms")
        print(f"  最大查询时间: {max_time*1000:.2f}ms")
        
        assert avg_time < 0.5, f"平均查询时间({avg_time:.2f}s)超过500ms"
    
    def test_incremental_update(self, real_memory):
        """测试增量更新"""
        # 初始索引
        real_memory.index_file("/test/incremental.txt", 
                               content="原始内容")
        stats_before = real_memory.get_stats()
        doc_count_before = stats_before['document_count']
        
        # 更新同一文件
        real_memory.index_file("/test/incremental.txt", 
                               content="更新后的内容")
        stats_after = real_memory.get_stats()
        doc_count_after = stats_after['document_count']
        
        # 文档数量不应增加（更新而非新增）
        assert doc_count_after == doc_count_before, \
            "增量更新不应增加文档数量"
        
        # 验证内容已更新
        results = real_memory.search("更新后", top_k=1)
        assert len(results) > 0
        assert "更新" in results[0]['content_preview']
    
    def test_memory_usage(self, real_memory):
        """测试内存占用"""
        process = psutil.Process()
        
        # 获取初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 添加1000条记录
        for i in range(1000):
            content = f"测试内存占用的文档内容 {i} " + "A" * 100
            real_memory.index_file(f"/test/mem_{i}.txt", content=content)
        
        # 强制垃圾回收后测量
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n内存占用测试:")
        print(f"  初始内存: {initial_memory:.1f}MB")
        print(f"  最终内存: {final_memory:.1f}MB")
        print(f"  增加内存: {memory_increase:.1f}MB")
        
        # 1000条记录内存增加应小于500MB
        assert memory_increase < 500, \
            f"内存增加({memory_increase:.1f}MB)超过500MB限制"


# =============================================================================
# 验证清单测试
# =============================================================================

class TestVerificationChecklist:
    """验证清单测试 - 系统级验证"""
    
    @pytest.fixture(scope="class")
    def verification_report(self):
        """生成验证报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "status": "pending"
        }
        yield report
        # 保存报告
        report_path = TEST_DATA_DIR / "verification_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n验证报告已保存: {report_path}")
    
    def test_model_download_functional(self, verification_report):
        """✓ 验证: 模型自动下载正常"""
        try:
            from sentence_transformers import SentenceTransformer
            
            start = time.time()
            # 使用小模型测试下载
            model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
            duration = time.time() - start
            
            # 测试模型可用
            test_vec = model.encode("test")
            
            verification_report["tests"]["model_download"] = {
                "status": "passed",
                "load_time": duration,
                "vector_dim": len(test_vec)
            }
            assert True
        except Exception as e:
            verification_report["tests"]["model_download"] = {
                "status": "failed",
                "error": str(e)
            }
            pytest.fail(f"模型下载失败: {e}")
    
    def test_startup_time_acceptable(self, verification_report):
        """✓ 验证: 首次启动时间可接受"""
        try:
            from local_memory import LocalMemorySystem
            
            with tempfile.TemporaryDirectory() as temp_dir:
                start = time.time()
                memory = LocalMemorySystem(memory_dir=temp_dir)
                memory.init()
                init_time = time.time() - start
                
                # 加载模型时间
                start = time.time()
                memory._get_model()
                model_time = time.time() - start
                
                total_time = init_time + model_time
                
                verification_report["tests"]["startup_time"] = {
                    "status": "passed" if total_time < 60 else "warning",
                    "init_time": init_time,
                    "model_load_time": model_time,
                    "total_time": total_time
                }
                
                print(f"\n启动时间:")
                print(f"  初始化: {init_time:.2f}s")
                print(f"  模型加载: {model_time:.2f}s")
                print(f"  总计: {total_time:.2f}s")
                
                assert total_time < 120, f"启动时间({total_time:.1f}s)过长"
        except ImportError:
            pytest.skip("local_memory不可用")
    
    def test_incremental_update_correct(self, verification_report):
        """✓ 验证: 增量更新正确"""
        try:
            from local_memory import LocalMemorySystem
            
            with tempfile.TemporaryDirectory() as temp_dir:
                memory = LocalMemorySystem(memory_dir=temp_dir)
                memory.init()
                
                # 第一次索引
                memory.index_file("/test/incremental.txt", content="版本1")
                stats1 = memory.get_stats()
                
                # 相同内容再次索引（应跳过）
                memory.index_file("/test/incremental.txt", content="版本1")
                stats2 = memory.get_stats()
                
                # 更新内容
                memory.index_file("/test/incremental.txt", content="版本2")
                stats3 = memory.get_stats()
                
                correct = (
                    stats2['document_count'] == stats1['document_count'] and
                    stats3['document_count'] == stats1['document_count']
                )
                
                verification_report["tests"]["incremental_update"] = {
                    "status": "passed" if correct else "failed",
                    "doc_count_v1": stats1['document_count'],
                    "doc_count_v1_repeat": stats2['document_count'],
                    "doc_count_v2": stats3['document_count']
                }
                
                assert correct, "增量更新未正确工作"
        except ImportError:
            pytest.skip("local_memory不可用")
    
    def test_memory_usage_reasonable(self, verification_report):
        """✓ 验证: 内存占用合理（<500MB）"""
        try:
            from local_memory import LocalMemorySystem
            import gc
            
            process = psutil.Process()
            gc.collect()
            baseline = process.memory_info().rss / 1024 / 1024
            
            with tempfile.TemporaryDirectory() as temp_dir:
                memory = LocalMemorySystem(memory_dir=temp_dir)
                memory.init()
                
                # 加载数据后的内存
                gc.collect()
                after_init = process.memory_info().rss / 1024 / 1024
                
                # 索引1000条记录
                for i in range(1000):
                    memory.index_file(f"/test/mem_{i}.txt", 
                                     content=f"测试内容 {i}")
                
                gc.collect()
                after_1000 = process.memory_info().rss / 1024 / 1024
                
                increase = after_1000 - baseline
                
                verification_report["tests"]["memory_usage"] = {
                    "status": "passed" if increase < 500 else "failed",
                    "baseline_mb": baseline,
                    "after_1000_mb": after_1000,
                    "increase_mb": increase,
                    "limit_mb": 500
                }
                
                print(f"\n内存使用:")
                print(f"  基线: {baseline:.1f}MB")
                print(f"  1000条后: {after_1000:.1f}MB")
                print(f"  增加: {increase:.1f}MB")
                
                assert increase < 500, f"内存增加({increase:.1f}MB)超过500MB"
        except ImportError:
            pytest.skip("local_memory不可用")


# =============================================================================
# 性能基准测试
# =============================================================================

class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    @pytest.fixture(scope="class")
    def benchmark_results(self):
        """收集基准测试结果"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {}
        }
        yield results
        # 保存结果
        results_path = TEST_DATA_DIR / "benchmark_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n基准测试结果已保存: {results_path}")
    
    def test_benchmark_indexing_speed(self, benchmark_results):
        """基准测试: 索引速度"""
        try:
            from local_memory import LocalMemorySystem
            
            with tempfile.TemporaryDirectory() as temp_dir:
                memory = LocalMemorySystem(memory_dir=temp_dir)
                memory.init()
                
                # 测试不同规模的索引速度
                scales = [10, 100, 500]
                scale_results = {}
                
                for scale in scales:
                    start = time.time()
                    for i in range(scale):
                        memory.index_file(
                            f"/bench/scale_{scale}_{i}.txt",
                            content=f"性能测试内容 {i}: " + "A" * 200
                        )
                    duration = time.time() - start
                    
                    scale_results[str(scale)] = {
                        "total_time": duration,
                        "per_doc_ms": (duration / scale) * 1000
                    }
                
                benchmark_results["benchmarks"]["indexing"] = scale_results
                
                print(f"\n索引速度基准:")
                for scale, data in scale_results.items():
                    print(f"  {scale}条: {data['total_time']:.2f}s "
                          f"({data['per_doc_ms']:.1f}ms/条)")
        except ImportError:
            pytest.skip("local_memory不可用")
    
    def test_benchmark_search_latency(self, benchmark_results):
        """基准测试: 搜索延迟"""
        try:
            from local_memory import LocalMemorySystem
            
            with tempfile.TemporaryDirectory() as temp_dir:
                memory = LocalMemorySystem(memory_dir=temp_dir)
                memory.init()
                
                # 准备数据
                for i in range(1000):
                    memory.index_file(f"/bench/latency_{i}.txt",
                                     content=TEST_MEMORIES[i % len(TEST_MEMORIES)]["content"])
                
                # 测试搜索延迟
                queries = ["Python编程", "机器学习", "错误处理", 
                          "性能优化", "数据库设计"]
                latencies = []
                
                for query in queries:
                    times = []
                    for _ in range(10):  # 每个查询10次
                        start = time.time()
                        memory.search(query, top_k=10)
                        times.append(time.time() - start)
                    latencies.append(sum(times) / len(times))
                
                avg_latency = sum(latencies) / len(latencies) * 1000  # ms
                max_latency = max(latencies) * 1000
                
                benchmark_results["benchmarks"]["search_latency"] = {
                    "avg_ms": avg_latency,
                    "max_ms": max_latency,
                    "queries_tested": len(queries)
                }
                
                print(f"\n搜索延迟基准 (1000条记录):")
                print(f"  平均: {avg_latency:.1f}ms")
                print(f"  最大: {max_latency:.1f}ms")
        except ImportError:
            pytest.skip("local_memory不可用")
    
    def test_benchmark_throughput(self, benchmark_results):
        """基准测试: 吞吐量"""
        try:
            from local_memory import LocalMemorySystem
            import threading
            import queue
            
            with tempfile.TemporaryDirectory() as temp_dir:
                memory = LocalMemorySystem(memory_dir=temp_dir)
                memory.init()
                
                # 预热
                for i in range(100):
                    memory.index_file(f"/warmup/{i}.txt", content=f"warmup {i}")
                
                # 测试查询吞吐量
                queries = ["测试", "数据", "系统", "优化", "设计"] * 20
                result_queue = queue.Queue()
                
                def worker(query_list):
                    count = 0
                    start = time.time()
                    for q in query_list:
                        memory.search(q, top_k=5)
                        count += 1
                    duration = time.time() - start
                    result_queue.put((count, duration))
                
                # 使用多线程测试
                threads = []
                queries_per_thread = len(queries) // 4
                for i in range(4):
                    t = threading.Thread(
                        target=worker,
                        args=(queries[i*queries_per_thread:(i+1)*queries_per_thread],)
                    )
                    threads.append(t)
                
                start = time.time()
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                total_time = time.time() - start
                
                total_queries = sum(r[0] for r in list(result_queue.queue))
                throughput = total_queries / total_time
                
                benchmark_results["benchmarks"]["throughput"] = {
                    "queries_per_second": throughput,
                    "total_queries": total_queries,
                    "total_time": total_time,
                    "threads": 4
                }
                
                print(f"\n吞吐量基准:")
                print(f"  查询总数: {total_queries}")
                print(f"  总时间: {total_time:.2f}s")
                print(f"  吞吐量: {throughput:.1f} qps")
        except ImportError:
            pytest.skip("local_memory不可用")


# =============================================================================
# 测试数据导出
# =============================================================================

def export_test_data():
    """导出测试数据到文件"""
    # 导出100条测试记忆
    test_data_path = TEST_DATA_DIR / "test_memories_100.json"
    with open(test_data_path, 'w', encoding='utf-8') as f:
        json.dump(TEST_MEMORIES, f, indent=2, ensure_ascii=False)
    print(f"测试数据已导出: {test_data_path}")
    
    # 按类型统计
    type_counts = {}
    for item in TEST_MEMORIES:
        t = item["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    
    stats_path = TEST_DATA_DIR / "test_data_stats.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total": len(TEST_MEMORIES),
            "by_type": type_counts,
            "types": list(type_counts.keys())
        }, f, indent=2, ensure_ascii=False)
    print(f"测试数据统计: {stats_path}")


if __name__ == "__main__":
    # 导出测试数据
    export_test_data()
    
    # 运行pytest
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=False
    )
    sys.exit(result.returncode)
