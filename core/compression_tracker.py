#!/usr/bin/env python3
"""
压缩成本追踪器 - Compression Cost Tracker
来自 @xiao_su 的洞察: "The Compression Tax: What memory systems hide from you"

核心问题:
- 不仅丢失信息，还丢失"不确定性"
- 压缩后的记忆过于自信
- 需要保留压缩前的元数据

功能:
1. 记录原始内容和压缩后内容
2. 计算压缩比
3. 保留原始置信度
4. 追踪信息丢失
5. 生成压缩成本报告
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

WORKSPACE = Path("/root/.openclaw/workspace")
COMPRESSION_COST_DIR = WORKSPACE / "data" / "compression-costs"
COMPRESSION_LOG = COMPRESSION_COST_DIR / "compression-tracker.jsonl"


class CompressionMethod(Enum):
    """压缩方法"""
    NONE = "none"
    SUMMARY = "summary"
    ABSTRACT = "abstract"
    KEYPOINT_EXTRACT = "keypoint_extract"
    AGGREGATE = "aggregate"


@dataclass
class CompressionMetrics:
    """压缩指标"""
    original_size: int  # 原始大小（字符数）
    compressed_size: int  # 压缩后大小（字符数）
    compression_ratio: float  # 压缩比
    
    # 信息丢失指标
    information_loss_score: float = 0.0  # 信息丢失分数 (0-1)
    key_points_preserved: int = 0  # 保留的关键点数量
    key_points_lost: int = 0  # 丢失的关键点数量
    
    # 置信度保留
    original_confidence: float = 0.0  # 原始置信度
    compressed_confidence: float = 0.0  # 压缩后置信度
    confidence_drift: float = 0.0  # 置信度漂移


@dataclass
class CompressionRecord:
    """压缩记录"""
    record_id: str
    timestamp: str
    
    来源信息
    source_type: str  # memory, log, knowledge, etc.
    source_path: str  # 源文件路径
    
    # 内容
    original_content_hash: str  # 原始内容哈希
    compressed_content_hash: str  # 压缩内容哈希
    
    # 压缩方法
    compression_method: str
    
    # 指标
    metrics: CompressionMetrics
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['compression_method'] = self.compression_method if isinstance(self.compression_method, str) else self.compression_method.value
        result['metrics'] = asdict(self.metrics)
        return result
    
    def to_json_line(self) -> str:
        """转换为 JSONL 行"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class CompressionTracker:
    """压缩成本追踪器"""
    
    def __init__(self):
        self.tracker_dir = COMPRESSION_COST_DIR
        self.log_file = COMPRESSION_LOG
        self.tracker_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计
        self._total_compressions = 0
        self._total_original_size = 0
        self._total_compressed_size = 0
    
    def track_compression(self,
                          source_type: str,
                          source_path: str,
                          original_content: str,
                          compressed_content: str,
                          compression_method: CompressionMethod = CompressionMethod.SUMMARY,
                          key_points_preserved: int = 0,
                          key_points_total: int = 0,
                          original_confidence: float = 0.0,
                          compressed_confidence: float = 0.0,
                          **metadata) -> CompressionRecord:
        """
        追踪压缩操作
        
        Args:
            source_type: 来源类型
            source_path: 源路径
            original_content: 原始内容
            compressed_content: 压缩内容
            compression_method: 压缩方法
            key_points_preserved: 保留的关键点
            key_points_total: 总关键点数
            original_confidence: 原始置信度
            compressed_confidence: 压缩后置信度
            **metadata: 其他元数据
            
        Returns:
            压缩记录
        """
        # 计算哈希
        original_hash = self._compute_hash(original_content)
        compressed_hash = self._compute_hash(compressed_content)
        
        # 计算压缩指标
        metrics = self._compute_metrics(
            original_content,
            compressed_content,
            key_points_preserved,
            key_points_total,
            original_confidence,
            compressed_confidence
        )
        
        # 创建记录
        record = CompressionRecord(
            record_id=f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now().isoformat(),
            source_type=source_type,
            source_path=source_path,
            original_content_hash=original_hash,
            compressed_content_hash=compressed_hash,
            compression_method=compression_method,
            metrics=metrics,
            metadata=metadata
        )
        
        # 保存记录
        self._save_record(record)
        
        # 更新统计
        self._total_compressions += 1
        self._total_original_size += metrics.original_size
        self._total_compressed_size += metrics.compressed_size
        
        return record
    
    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _compute_metrics(self,
                         original: str,
                         compressed: str,
                         key_points_preserved: int,
                         key_points_total: int,
                         original_confidence: float,
                         compressed_confidence: float) -> CompressionMetrics:
        """计算压缩指标"""
        original_size = len(original)
        compressed_size = len(compressed)
        
        # 压缩比
        compression_ratio = compressed_size / original_size if original_size > 0 else 0.0
        
        # 信息丢失分数
        key_points_lost = key_points_total - key_points_preserved
        information_loss_score = key_points_lost / key_points_total if key_points_total > 0 else 0.0
        
        # 置信度漂移
        confidence_drift = abs(compressed_confidence - original_confidence)
        
        return CompressionMetrics(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            information_loss_score=information_loss_score,
            key_points_preserved=key_points_preserved,
            key_points_lost=key_points_lost,
            original_confidence=original_confidence,
            compressed_confidence=compressed_confidence,
            confidence_drift=confidence_drift
        )
    
    def _save_record(self, record: CompressionRecord):
        """保存压缩记录"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(record.to_json_line() + '\n')
    
    def get_compression_report(self, days: int = 7) -> Dict[str, Any]:
        """
        获取压缩成本报告
        
        Args:
            days: 最近多少天
            
        Returns:
            压缩成本报告
        """
        if not self.log_file.exists():
            return {
                "period": f"last_{days}_days",
                "total_compressions": 0,
                "average_compression_ratio": 0.0,
                "total_size_saved": 0
            }
        
        records = []
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        
        # 读取记录
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        record_time = datetime.fromisoformat(record['timestamp']).timestamp()
                        if record_time >= cutoff:
                            records.append(record)
                    except Exception:
                        pass
        
        # 统计
        total_compressions = len(records)
        
        if total_compressions == 0:
            return {
                "period": f"last_{days}_days",
                "total_compressions": 0,
                "average_compression_ratio": 0.0,
                "total_size_saved": 0
            }
        
        # 计算指标
        total_original = sum(r['metrics']['original_size'] for r in records)
        total_compressed = sum(r['metrics']['compressed_size'] for r in records)
        
        total_compression_ratio = total_compressed / total_original if total_original > 0 else 0.0
        avg_compression_ratio = sum(r['metrics']['compression_ratio'] for r in records) / total_compressions
        
        total_size_saved = total_original - total_compressed
        
        # 置信度漂移统计
        confidence_drifts = [r['metrics']['confidence_drift'] for r in records]
        avg_confidence_drift = sum(confidence_drifts) / total_compressions if confidence_drifts else 0.0
        
        # 信息丢失统计
        information_losses = [r['metrics']['information_loss_score'] for r in records]
        avg_information_loss = sum(information_losses) / total_compressions if information_losses else 0.0
        
        # 按来源分组
        by_source = {}
        for record in records:
            source = record['source_type']
            if source not in by_source:
                by_source[source] = {
                    "count": 0,
                    "original_size": 0,
                    "compressed_size": 0
                }
            by_source[source]["count"] += 1
            by_source[source]["original_size"] += record['metrics']['original_size']
            by_source[source]["compressed_size"] += record['metrics']['compressed_size']
        
        return {
            "period": f"last_{days}_days",
            "total_compressions": total_compressions,
            "average_compression_ratio": round(avg_compression_ratio, 4),
            "total_compression_ratio": round(total_compression_ratio, 4),
            "total_size_saved": total_size_saved,
            "total_original_size": total_original,
            "total_compressed_size": total_compressed,
            "avg_confidence_drift": round(avg_confidence_drift, 4),
            "avg_information_loss": round(avg_information_loss, 4),
            "by_source": by_source
        }
    
    def analyze_compression_quality(self, threshold_ratio: float = 0.6) -> Dict[str, Any]:
        """
        分析压缩质量
        
        Args:
            threshold_ratio: 压缩比阈值（低于此值认为压缩过度）
            
        Returns:
            质量分析报告
        """
        if not self.log_file.exists():
            return {"total": 0, "over_compressed": 0, "quality_issues": []}
        
        over_compressed = []
        quality_issues = []
        
        # 读取记录
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        metrics = record['metrics']
                        
                        # 检查过度压缩
                        if metrics['compression_ratio'] < threshold_ratio:
                            over_compressed.append({
                                "record_id": record['record_id'],
                                "ratio": metrics['compression_ratio'],
                                "source": record['source_path']
                            })
                        
                        # 检查置信度漂移
                        if metrics['confidence_drift'] > 0.3:
                            quality_issues.append({
                                "record_id": record['record_id'],
                                "issue": "high_confidence_drift",
                                "drift": metrics['confidence_drift']
                            })
                        
                        # 检查信息丢失
                        if metrics['information_loss_score'] > 0.5:
                            quality_issues.append({
                                "record_id": record['record_id'],
                                "issue": "significant_information_loss",
                                "loss_score": metrics['information_loss_score']
                            })
                    
                    except Exception:
                        pass
        
        return {
            "total": len(over_compressed) + len(quality_issues),
            "over_compressed_count": len(over_compressed),
            "over_compressed": over_compressed[:10],  # 只返回前10个
            "quality_issues": quality_issues[:10]
        }


# 全局实例
_compression_tracker = None

def get_compression_tracker() -> CompressionTracker:
    """获取全局压缩追踪器"""
    global _compression_tracker
    if _compression_tracker is None:
        _compression_tracker = CompressionTracker()
    return _compression_tracker


# 便捷函数
def track_memory_compression(original: str,
                             compressed: str,
                             source_path: str = "MEMORY.md",
                             **kwargs) -> CompressionRecord:
    """便捷函数：追踪记忆压缩"""
    return get_compression_tracker().track_compression(
        source_type="memory",
        source_path=source_path,
        original_content=original,
        compressed_content=compressed,
        **kwargs
    )


# 示例用法
if __name__ == "__main__":
    tracker = get_compression_tracker()
    
    # 模拟压缩
    original = """
这是一个很长的原始记忆内容。
它包含了大量的详细信息，比如：
1. 某个任务的详细描述
2. 执行的步骤
3. 遇到的问题
4. 解决方案
5. 相关的上下文信息
6. 后续的改进建议
...还有更多内容
    """.strip()
    
    compressed = """
任务完成：处理学习债务。
关键结果：生成5份笔记，更新知识图谱。
后续：验证应用方案效果。
    """.strip()
    
    # 追踪压缩
    record = tracker.track_compression(
        source_type="memory",
        source_path="MEMORY.md",
        original_content=original,
        compressed_content=compressed,
        compression_method=CompressionMethod.SUMMARY,
        key_points_preserved=2,
        key_points_total=6,
        original_confidence=8.0,
        compressed_confidence=7.0
    )
    
    print(f"压缩记录已创建: {record.record_id}")
    print(f"原始大小: {record.metrics.original_size}")
    print(f"压缩大小: {record.metrics.compressed_size}")
    print(f"压缩比: {record.metrics.compression_ratio:.2%}")
    print(f"信息丢失: {record.metrics.information_loss_score:.2%}")
    
    # 生成报告
    report = tracker.get_compression_report(7)
    print(f"\n压缩成本报告: {report}")
    
    # 质量分析
    quality = tracker.analyze_compression_quality()
    print(f"\n质量分析: {quality}")
