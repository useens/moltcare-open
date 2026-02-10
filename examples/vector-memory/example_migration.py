#!/usr/bin/env python3
"""
示例3: 批量迁移示例 - Bulk Migration Example

展示如何将现有的记忆文件批量迁移到向量记忆系统。
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/local-memory-system'))

from local_memory import LocalMemorySystem


class MemoryMigrator:
    """
    记忆迁移工具
    
    用于将现有的基于文件的记忆系统迁移到向量记忆系统。
    """
    
    def __init__(self, source_dir: str, target_dir: str = None):
        """
        初始化迁移器
        
        Args:
            source_dir: 源记忆目录（现有记忆文件）
            target_dir: 目标向量记忆目录
        """
        self.source_dir = Path(source_dir)
        self.memory = LocalMemorySystem(target_dir)
        self.stats = {
            'total_files': 0,
            'indexed': 0,
            'skipped': 0,
            'errors': 0,
            'total_bytes': 0
        }
    
    def initialize(self) -> bool:
        """初始化目标系统"""
        try:
            self.memory.init()
            print(f"✅ 初始化完成: {self.memory.memory_dir}")
            return True
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    def migrate(self, dry_run: bool = False, 
                extensions: set = None,
                exclude_patterns: list = None) -> dict:
        """
        执行迁移
        
        Args:
            dry_run: 仅预览，不实际执行
            extensions: 要索引的文件扩展名集合
            exclude_patterns: 要排除的模式列表
            
        Returns:
            迁移统计信息
        """
        if extensions is None:
            extensions = {'.md', '.txt', '.rst'}
        
        if exclude_patterns is None:
            exclude_patterns = ['.git', 'node_modules', '__pycache__', '.venv']
        
        print(f"\n{'='*60}")
        print(f"🚚 记忆迁移 {'[预览模式]' if dry_run else ''}")
        print(f"{'='*60}")
        print(f"源目录: {self.source_dir}")
        print(f"目标: {self.memory.memory_dir}")
        print(f"文件类型: {', '.join(extensions)}")
        print(f"排除: {', '.join(exclude_patterns)}")
        print(f"{'='*60}\n")
        
        # 扫描文件
        files_to_index = []
        for ext in extensions:
            for file_path in self.source_dir.rglob(f"*{ext}"):
                # 检查排除模式
                if any(pattern in str(file_path) for pattern in exclude_patterns):
                    continue
                files_to_index.append(file_path)
        
        self.stats['total_files'] = len(files_to_index)
        
        print(f"📊 发现 {len(files_to_index)} 个待索引文件\n")
        
        if dry_run:
            print("预览模式 - 将索引以下文件:")
            for fp in files_to_index[:10]:  # 只显示前10个
                print(f"  - {fp.relative_to(self.source_dir)}")
            if len(files_to_index) > 10:
                print(f"  ... 还有 {len(files_to_index) - 10} 个文件")
            return self.stats
        
        # 实际迁移
        for i, file_path in enumerate(files_to_index, 1):
            try:
                # 显示进度
                if i % 10 == 0 or i == len(files_to_index):
                    print(f"🔄 进度: {i}/{len(files_to_index)} ({i/len(files_to_index)*100:.1f}%)")
                
                # 索引文件
                self.memory.index_file(str(file_path))
                self.stats['indexed'] += 1
                self.stats['total_bytes'] += file_path.stat().st_size
                
            except Exception as e:
                print(f"❌ 错误 {file_path}: {e}")
                self.stats['errors'] += 1
        
        return self.stats
    
    def print_report(self):
        """打印迁移报告"""
        print(f"\n{'='*60}")
        print("📊 迁移报告")
        print(f"{'='*60}")
        print(f"总文件数:   {self.stats['total_files']}")
        print(f"成功索引:   {self.stats['indexed']}")
        print(f"跳过/重复:  {self.stats['skipped']}")
        print(f"错误:       {self.stats['errors']}")
        print(f"总字节数:   {self.stats['total_bytes'] / 1024 / 1024:.2f} MB")
        
        # 目标系统统计
        target_stats = self.memory.get_stats()
        print(f"\n目标系统状态:")
        print(f"  文档数量: {target_stats['document_count']}")
        print(f"  向量数量: {target_stats['vector_count']}")
        print(f"  数据库:   {target_stats['db_size'] / 1024:.2f} KB")
        print(f"{'='*60}")
    
    def verify(self) -> bool:
        """验证迁移结果"""
        print("\n🔍 验证迁移结果...")
        
        source_count = self.stats['total_files']
        target_stats = self.memory.get_stats()
        target_count = target_stats['document_count']
        
        if target_count >= self.stats['indexed']:
            print(f"✅ 验证通过: {target_count} 文档已索引")
            return True
        else:
            print(f"⚠️  验证警告: 期望 {self.stats['indexed']}，实际 {target_count}")
            return False


def create_sample_memory_structure(base_dir: str):
    """创建示例记忆目录结构"""
    base = Path(base_dir)
    
    # 创建目录结构
    dirs = [
        "daily",
        "summary/weekly", 
        "summary/monthly",
        "tags",
        "modules"
    ]
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    
    # 创建示例文件
    files = [
        ("daily/2026-02-08.md", """# 2026-02-08

## 今日工作
- 完成了项目A的代码审查
- 学习了新的设计模式
- 与用户讨论了产品方向

## 重要决策
决定采用微服务架构。
"""),
        ("daily/2026-02-09.md", """# 2026-02-09

## 今日工作  
- 重构了数据库模型
- 修复了3个bug
- 编写了单元测试

## 学习笔记
了解了向量数据库的原理和应用场景。
"""),
        ("tags/user-preferences.md", """# 用户偏好

## 技术偏好
- Python > JavaScript
- 喜欢简洁的代码风格
- 重视测试覆盖

## 沟通偏好
- 直接了当
- 重视效率
- 喜欢代码示例
"""),
        ("modules/system-arch.md", """# 系统架构

## 核心组件
1. API Gateway
2. 业务服务层
3. 数据访问层
4. 消息队列

## 技术栈
- FastAPI
- PostgreSQL
- Redis
- RabbitMQ
""")
    ]
    
    for filepath, content in files:
        full_path = base / filepath
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"✅ 示例记忆结构已创建: {base_dir}")
    return base


def demo_migration():
    """演示迁移流程"""
    
    print("=" * 60)
    print("🚚 示例3: 记忆数据迁移演示")
    print("=" * 60)
    
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. 创建示例源数据
        print("\n1️⃣ 创建示例源记忆数据...")
        source_dir = create_sample_memory_structure(os.path.join(tmpdir, "source_memory"))
        
        # 显示源结构
        print("\n源目录结构:")
        for f in source_dir.rglob("*.md"):
            print(f"   {f.relative_to(source_dir)}")
        
        # 2. 预览迁移
        print("\n2️⃣ 预览迁移...")
        target_dir = os.path.join(tmpdir, "vector_memory")
        migrator = MemoryMigrator(str(source_dir), target_dir)
        migrator.initialize()
        
        migrator.migrate(dry_run=True)
        
        # 3. 执行迁移
        print("\n3️⃣ 执行实际迁移...")
        input("\n按 Enter 键继续...")
        
        migrator.migrate(dry_run=False)
        
        # 4. 打印报告
        migrator.print_report()
        
        # 5. 验证
        migrator.verify()
        
        # 6. 测试搜索
        print("\n4️⃣ 测试向量搜索...")
        test_queries = [
            "今天做了什么工作",
            "用户喜欢什么",
            "系统架构设计"
        ]
        
        for query in test_queries:
            print(f"\n🔍 查询: '{query}'")
            results = migrator.memory.search(query, top_k=2)
            for r in results:
                print(f"   - {r['file_path']} (相似度: {r['similarity']:.4f})")
        
        print("\n" + "=" * 60)
        print("✅ 迁移演示完成!")
        print("=" * 60)
        
        print(f"\n💡 提示:")
        print(f"   - 源数据保留在: {source_dir}")
        print(f"   - 向量数据存储在: {target_dir}")
        print(f"   - 原始文件不会被修改")


if __name__ == '__main__':
    try:
        demo_migration()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
