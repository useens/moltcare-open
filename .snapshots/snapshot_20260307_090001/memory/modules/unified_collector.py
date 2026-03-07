#!/usr/bin/env python3
"""
统一知识内化系统 - 数据收集整合器
Unified Knowledge Internalization System - Data Collector

功能：
1. 自动扫描多个情报源目录
2. 按来源分类归档到统一知识库
3. 生成收集报告和元数据索引
"""

import os
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CollectionStats:
    """收集统计信息"""
    source: str
    files_found: int = 0
    files_processed: int = 0
    items_extracted: int = 0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ArchiveRecord:
    """归档记录"""
    original_path: str
    archive_path: str
    source: str
    file_hash: str
    extraction_time: str
    item_count: int
    archived_at: str


class UnifiedCollector:
    """统一数据收集器"""
    
    # 情报源配置
    SOURCES = {
        'moltbook': {
            'path': 'data/moltbook',
            'type': 'web_extraction',
            'pattern': '*.json',
            'exclude': ['*cookies*', '*state*']
        },
        'hackernews': {
            'path': 'data/hackernews',
            'type': 'web_extraction',
            'pattern': '*.json',
            'exclude': ['*cookies*']
        },
        'github_trending': {
            'path': 'data/github_trending',
            'type': 'web_extraction',
            'pattern': '*.json',
            'exclude': ['*cookies*']
        },
        'devto': {
            'path': 'data/devto',
            'type': 'web_extraction',
            'pattern': '*.json',
            'exclude': ['*cookies*']
        },
        'indiehackers': {
            'path': 'data/indiehackers',
            'type': 'web_extraction',
            'pattern': '*.json',
            'exclude': ['*cookies*']
        },
        'lobsters': {
            'path': 'data/lobsters',
            'type': 'web_extraction',
            'pattern': '*.json',
            'exclude': ['*cookies*']
        },
        'producthunt': {
            'path': 'data/producthunt',
            'type': 'web_extraction',
            'pattern': '*.json',
            'exclude': ['*cookies*']
        },
        'intel': {
            'path': 'memory/intel',
            'type': 'intelligence_files',
            'pattern': '*',
            'exclude': []
        },
        'evolution': {
            'path': 'memory/evolution',
            'type': 'evolution_archive',
            'pattern': '*',
            'exclude': []
        }
    }
    
    def __init__(self, archive_root: str = 'memory/knowledge/raw'):
        self.archive_root = Path(archive_root)
        self.archive_root.mkdir(parents=True, exist_ok=True)
        self.stats: Dict[str, CollectionStats] = {}
        self.records: List[ArchiveRecord] = []
        
    def _should_exclude(self, filename: str, exclude_patterns: List[str]) -> bool:
        """检查文件是否应该被排除"""
        import fnmatch
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False
    
    def _calculate_hash(self, filepath: Path) -> str:
        """计算文件哈希"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _extract_items_count(self, filepath: Path) -> int:
        """从JSON文件中提取项目数量"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # 检查常见字段
                    for key in ['count', 'items', 'results', 'data']:
                        if key in data:
                            val = data[key]
                            if isinstance(val, int):
                                return val
                            elif isinstance(val, list):
                                return len(val)
                elif isinstance(data, list):
                    return len(data)
        except Exception as e:
            logger.debug(f"无法解析 {filepath}: {e}")
        return 0
    
    def _extract_extraction_time(self, filepath: Path) -> str:
        """提取文件中的提取时间"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for key in ['extraction_time', 'timestamp', 'created_at', 'date']:
                        if key in data:
                            return data[key]
        except:
            pass
        # 回退到文件修改时间
        mtime = os.path.getmtime(filepath)
        return datetime.fromtimestamp(mtime).isoformat()
    
    def _archive_file(self, source_path: Path, source_name: str) -> Optional[ArchiveRecord]:
        """归档单个文件"""
        try:
            # 计算文件哈希
            file_hash = self._calculate_hash(source_path)
            
            # 检查是否已归档（去重）
            hash_file = self.archive_root / '.hashes' / f"{file_hash}.txt"
            if hash_file.exists():
                logger.debug(f"跳过重复文件: {source_path}")
                return None
            
            # 创建归档目录结构: raw/{source}/{date}/{filename}
            extraction_time = self._extract_extraction_time(source_path)
            try:
                date_part = extraction_time[:10] if extraction_time else datetime.now().strftime('%Y-%m-%d')
            except:
                date_part = datetime.now().strftime('%Y-%m-%d')
            
            archive_dir = self.archive_root / source_name / date_part
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成归档文件名
            timestamp = datetime.now().strftime('%H%M%S')
            archive_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            archive_path = archive_dir / archive_name
            
            # 复制文件
            shutil.copy2(source_path, archive_path)
            
            # 记录哈希
            hash_file.parent.mkdir(parents=True, exist_ok=True)
            hash_file.write_text(str(archive_path))
            
            # 创建记录
            record = ArchiveRecord(
                original_path=str(source_path),
                archive_path=str(archive_path),
                source=source_name,
                file_hash=file_hash,
                extraction_time=extraction_time,
                item_count=self._extract_items_count(source_path),
                archived_at=datetime.now().isoformat()
            )
            
            logger.info(f"已归档: {source_path.name} -> {archive_path}")
            return record
            
        except Exception as e:
            logger.error(f"归档失败 {source_path}: {e}")
            self.stats[source_name].errors.append(f"{source_path}: {str(e)}")
            return None
    
    def _collect_files_recursive(self, source_path: Path, pattern: str, exclude: List[str]) -> List[Path]:
        """递归收集所有文件"""
        files = []
        
        if source_path.is_file():
            # 如果是文件直接返回
            if not self._should_exclude(source_path.name, exclude):
                return [source_path]
            return []
        
        if not source_path.is_dir():
            return []
        
        # 遍历目录 - 支持所有文件类型
        if pattern == '*':
            # 收集所有文件
            for item in source_path.rglob('*'):
                if item.is_file() and not self._should_exclude(item.name, exclude):
                    files.append(item)
        else:
            # 使用模式匹配
            for item in source_path.rglob(pattern):
                if item.is_file() and not self._should_exclude(item.name, exclude):
                    files.append(item)
        
        return files
    
    def collect_source(self, source_name: str, config: Dict) -> CollectionStats:
        """收集单个来源的数据"""
        stats = CollectionStats(source=source_name)
        self.stats[source_name] = stats
        
        source_path = Path(config['path'])
        if not source_path.exists():
            logger.warning(f"来源路径不存在: {source_path}")
            stats.errors.append(f"Path not found: {source_path}")
            return stats
        
        # 递归查找文件
        files = self._collect_files_recursive(source_path, config['pattern'], config['exclude'])
        
        stats.files_found = len(files)
        logger.info(f"[{source_name}] 发现 {len(files)} 个文件")
        
        # 处理每个文件
        for filepath in files:
            record = self._archive_file(Path(filepath), source_name)
            if record:
                self.records.append(record)
                stats.files_processed += 1
                stats.items_extracted += record.item_count
        
        return stats
    
    def collect_all(self) -> Dict[str, CollectionStats]:
        """收集所有来源的数据"""
        logger.info("=" * 60)
        logger.info("开始统一数据收集")
        logger.info("=" * 60)
        
        for source_name, config in self.SOURCES.items():
            self.collect_source(source_name, config)
        
        # 保存索引
        self._save_index()
        
        return self.stats
    
    def _save_index(self):
        """保存归档索引"""
        index = {
            'last_collection': datetime.now().isoformat(),
            'total_records': len(self.records),
            'sources': {},
            'records': [
                {
                    'original_path': r.original_path,
                    'archive_path': r.archive_path,
                    'source': r.source,
                    'file_hash': r.file_hash,
                    'extraction_time': r.extraction_time,
                    'item_count': r.item_count,
                    'archived_at': r.archived_at
                }
                for r in self.records
            ]
        }
        
        # 按来源统计
        for source, stat in self.stats.items():
            index['sources'][source] = stat.to_dict()
        
        index_path = self.archive_root / 'collection_index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        logger.info(f"索引已保存: {index_path}")
    
    def generate_report(self) -> str:
        """生成收集报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("统一知识收集报告")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")
        
        total_files = 0
        total_items = 0
        
        for source, stat in self.stats.items():
            lines.append(f"📁 {source}")
            lines.append(f"   发现文件: {stat.files_found}")
            lines.append(f"   已归档: {stat.files_processed}")
            lines.append(f"   提取项目: {stat.items_extracted}")
            if stat.errors:
                lines.append(f"   ⚠️ 错误: {len(stat.errors)}")
            lines.append("")
            total_files += stat.files_processed
            total_items += stat.items_extracted
        
        lines.append("-" * 60)
        lines.append(f"📊 总计归档文件: {total_files}")
        lines.append(f"📊 总计提取项目: {total_items}")
        lines.append(f"📊 来源数量: {len(self.stats)}")
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def export_source_distribution(self) -> Dict[str, Any]:
        """导出来源分布数据"""
        distribution = {}
        for source, stat in self.stats.items():
            distribution[source] = {
                'files_archived': stat.files_processed,
                'items_extracted': stat.items_extracted,
                'success_rate': stat.files_processed / max(stat.files_found, 1) * 100
            }
        return distribution


def main():
    """主函数"""
    collector = UnifiedCollector()
    collector.collect_all()
    
    # 打印报告
    report = collector.generate_report()
    print(report)
    
    # 保存报告
    report_path = Path('memory/knowledge/raw') / 'collection_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 导出分布JSON
    distribution = collector.export_source_distribution()
    dist_path = Path('memory/knowledge/raw') / 'source_distribution.json'
    with open(dist_path, 'w', encoding='utf-8') as f:
        json.dump(distribution, f, ensure_ascii=False, indent=2)
    
    logger.info(f"报告已保存到: {report_path}")
    logger.info(f"分布数据已保存到: {dist_path}")


if __name__ == '__main__':
    main()
