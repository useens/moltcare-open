#!/usr/bin/env python3
"""
测试用例 - 向量记忆系统

运行所有测试:
    python test.py

运行特定测试:
    python test.py TestChunker
    python test.py TestIndexer
    python test.py TestSearch
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List
import numpy as np

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from indexer import TextChunker, MemoryIndexer, Config
from search import MemorySearch, SearchResult, format_results


class TestChunker:
    """测试文本分块器"""
    
    def test_small_text(self):
        """测试短文本不分块"""
        chunker = TextChunker(chunk_size=100)
        text = "这是一个短文本。"
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1, f"期望1个块，得到{len(chunks)}个"
        assert chunks[0] == text
        print("✓ test_small_text 通过")
    
    def test_large_text(self):
        """测试长文本分块"""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "A" * 200  # 200个字符
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1, "长文本应该被分块"
        
        # 检查总长度
        total_len = sum(len(c) for c in chunks)
        # 因为有重叠，总长度应该大于原长度
        assert total_len >= len(text) - 50  # 允许最后一个块较小
        print(f"✓ test_large_text 通过 (分成{len(chunks)}个块)")
    
    def test_sentence_boundary(self):
        """测试句子边界分割"""
        chunker = TextChunker(chunk_size=30)
        text = "这是第一句。这是第二句。这是第三句。这是第四句。"
        chunks = chunker.chunk_text(text)
        
        # 检查是否在句子边界分割
        for chunk in chunks:
            # 除了最后一个块，其他块应该以句号结束
            if chunk != chunks[-1]:
                assert chunk.rstrip().endswith('。'), f"块应该在句子边界结束: {chunk}"
        
        print("✓ test_sentence_boundary 通过")
    
    def run_all(self):
        """运行所有测试"""
        print("\n=== 测试 TextChunker ===")
        self.test_small_text()
        self.test_large_text()
        self.test_sentence_boundary()


class TestIndexer:
    """测试索引器"""
    
    def setup_temp_dir(self):
        """创建临时测试目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.modules_dir = Path(self.temp_dir) / "modules"
        self.modules_dir.mkdir()
        return self.temp_dir
    
    def teardown_temp_dir(self):
        """清理临时目录"""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, name: str, content: str):
        """创建测试MD文件"""
        filepath = self.modules_dir / name
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_extract_metadata(self):
        """测试元数据提取"""
        self.setup_temp_dir()
        
        try:
            indexer = MemoryIndexer(modules_dir=str(self.modules_dir))
            
            content = """# 测试标题

## 元数据
- 类型: 测试

这是正文内容 #标签1 #标签2

[[相关文档]]
"""
            filepath = self.create_test_file("test.md", content)
            meta = indexer._extract_metadata(content, filepath)
            
            assert meta['title'] == "测试标题", f"标题提取错误: {meta['title']}"
            assert '标签1' in meta['tags'], f"标签提取错误: {meta['tags']}"
            assert '标签2' in meta['tags'], f"标签提取错误: {meta['tags']}"
            assert '相关文档' in meta['links'], f"链接提取错误: {meta['links']}"
            
            print("✓ test_extract_metadata 通过")
        finally:
            self.teardown_temp_dir()
    
    def test_file_hash(self):
        """测试文件哈希计算"""
        self.setup_temp_dir()
        
        try:
            indexer = MemoryIndexer(modules_dir=str(self.modules_dir))
            
            content = "测试内容"
            filepath = self.create_test_file("hash_test.md", content)
            
            hash1 = indexer._compute_file_hash(filepath)
            hash2 = indexer._compute_file_hash(filepath)
            
            assert hash1 == hash2, "相同文件应该产生相同哈希"
            assert len(hash1) == 32, f"MD5哈希应该是32字符: {hash1}"
            
            print("✓ test_file_hash 通过")
        finally:
            self.teardown_temp_dir()
    
    def test_process_file(self):
        """测试文件处理"""
        self.setup_temp_dir()
        
        try:
            indexer = MemoryIndexer(
                modules_dir=str(self.modules_dir),
                chunk_size=50
            )
            
            # 创建长文档
            content = "# 长文档\n\n" + "这是一句话。" * 20
            filepath = self.create_test_file("long_doc.md", content)
            
            chunks = indexer._process_file(filepath)
            
            assert len(chunks) > 0, "应该提取到块"
            assert all('id' in c for c in chunks), "每个块应该有id"
            assert all('text' in c for c in chunks), "每个块应该有text"
            assert all(c['title'] == '长文档' for c in chunks), "标题应该一致"
            
            print(f"✓ test_process_file 通过 (提取{len(chunks)}个块)")
        finally:
            self.teardown_temp_dir()
    
    def run_all(self):
        """运行所有测试"""
        print("\n=== 测试 MemoryIndexer ===")
        self.test_extract_metadata()
        self.test_file_hash()
        self.test_process_file()


class TestSearch:
    """测试搜索模块"""
    
    def setup_temp_dir(self):
        """创建临时测试目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir()
        return self.temp_dir
    
    def teardown_temp_dir(self):
        """清理临时目录"""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir)
    
    def create_mock_index(self):
        """创建模拟索引数据"""
        # 创建模拟向量 (3个文档，384维)
        vectors = np.random.randn(3, 384).astype(np.float32)
        # 归一化
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        
        np.save(self.data_dir / "vectors.npy", vectors)
        
        # 创建模拟元数据
        metadata = {
            "chunks": [
                {
                    "id": "doc1_0",
                    "file_path": "modules/doc1.md",
                    "file_name": "doc1.md",
                    "title": "用户配置文档",
                    "text": "这是关于用户配置的文档内容",
                    "tags": ["配置", "用户"],
                    "chunk_index": 0,
                    "total_chunks": 1
                },
                {
                    "id": "doc2_0",
                    "file_path": "modules/doc2.md",
                    "file_name": "doc2.md",
                    "title": "安全审计指南",
                    "text": "这是关于安全审计的文档内容",
                    "tags": ["安全", "审计"],
                    "chunk_index": 0,
                    "total_chunks": 1
                },
                {
                    "id": "doc3_0",
                    "file_path": "modules/doc3.md",
                    "file_name": "doc3.md",
                    "title": "技能安装手册",
                    "text": "这是关于安装技能的操作指南",
                    "tags": ["技能", "安装"],
                    "chunk_index": 0,
                    "total_chunks": 1
                }
            ]
        }
        
        with open(self.data_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False)
        
        return metadata
    
    def test_load_index(self):
        """测试索引加载"""
        self.setup_temp_dir()
        
        try:
            self.create_mock_index()
            
            # 需要真正的模型，这里使用mock
            # 由于需要模型，这个测试需要实际环境
            print("⚠ test_load_index 跳过 (需要sentence-transformers模型)")
        finally:
            self.teardown_temp_dir()
    
    def test_cosine_similarity(self):
        """测试余弦相似度计算"""
        # 创建两个归一化的向量
        v1 = np.array([1, 0, 0], dtype=np.float32)
        v2 = np.array([1, 0, 0], dtype=np.float32)  # 相同方向
        v3 = np.array([0, 1, 0], dtype=np.float32)  # 正交
        v4 = np.array([-1, 0, 0], dtype=np.float32)  # 相反方向
        
        # 计算相似度
        sim_same = np.dot(v1, v2)
        sim_orth = np.dot(v1, v3)
        sim_opp = np.dot(v1, v4)
        
        assert abs(sim_same - 1.0) < 0.001, "相同向量相似度应为1"
        assert abs(sim_orth - 0.0) < 0.001, "正交向量相似度应为0"
        assert abs(sim_opp - (-1.0)) < 0.001, "相反向量相似度应为-1"
        
        print("✓ test_cosine_similarity 通过")
    
    def test_search_result_format(self):
        """测试结果格式化"""
        results = [
            SearchResult(
                id="test_0",
                score=0.95,
                title="测试文档",
                file_path="modules/test.md",
                file_name="test.md",
                text="这是测试内容",
                tags=["测试", "示例"],
                chunk_index=0,
                total_chunks=1
            )
        ]
        
        formatted = format_results(results)
        
        assert "测试文档" in formatted
        assert "0.950" in formatted
        assert "test.md" in formatted
        
        print("✓ test_search_result_format 通过")
    
    def run_all(self):
        """运行所有测试"""
        print("\n=== 测试 MemorySearch ===")
        self.test_cosine_similarity()
        self.test_search_result_format()
        self.test_load_index()


class TestIntegration:
    """集成测试 - 需要完整环境"""
    
    def test_end_to_end(self):
        """端到端测试"""
        print("\n=== 集成测试 (端到端) ===")
        
        # 检查是否有实际的modules目录
        modules_dir = Path(__file__).parent.parent / "modules"
        if not modules_dir.exists():
            print("⚠ 跳过集成测试 (modules目录不存在)")
            return
        
        # 创建临时数据目录
        temp_dir = tempfile.mkdtemp()
        data_dir = Path(temp_dir) / "data"
        
        try:
            print("1. 构建索引...")
            indexer = MemoryIndexer(
                modules_dir=str(modules_dir),
                chunk_size=512
            )
            indexer.build_index(force=True)
            
            stats = indexer.get_stats()
            print(f"   索引统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
            
            print("\n2. 执行搜索...")
            search = MemorySearch(data_dir=str(indexer.config.data_dir))
            
            # 测试搜索
            queries = [
                "用户偏好",
                "安全审计",
                "技能安装"
            ]
            
            for query in queries:
                print(f"\n   搜索: '{query}'")
                results = search.search(query, top_k=3)
                
                if results:
                    print(f"   找到 {len(results)} 个结果:")
                    for r in results[:2]:  # 只显示前2个
                        print(f"   - [{r['score']:.3f}] {r['title']}")
                else:
                    print("   没有找到结果")
            
            print("\n✓ 集成测试通过!")
            
        except Exception as e:
            print(f"\n✗ 集成测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            shutil.rmtree(temp_dir)
    
    def run_all(self):
        """运行所有集成测试"""
        self.test_end_to_end()


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("向量记忆系统测试套件")
    print("=" * 60)
    
    # 运行单元测试
    TestChunker().run_all()
    TestIndexer().run_all()
    TestSearch().run_all()
    
    # 运行集成测试
    TestIntegration().run_all()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='测试向量记忆系统')
    parser.add_argument('test_class', nargs='?', help='指定测试类 (TestChunker/TestIndexer/TestSearch)')
    
    args = parser.parse_args()
    
    if args.test_class:
        # 运行指定测试类
        test_map = {
            'TestChunker': TestChunker,
            'TestIndexer': TestIndexer,
            'TestSearch': TestSearch,
            'TestIntegration': TestIntegration
        }
        
        if args.test_class in test_map:
            test_map[args.test_class]().run_all()
        else:
            print(f"未知测试类: {args.test_class}")
            print(f"可用: {', '.join(test_map.keys())}")
    else:
        # 运行所有测试
        run_all_tests()
