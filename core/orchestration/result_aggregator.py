"""
结果聚合器模块 - 智能结果合并、冲突解决、质量评估
"""

import re
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set, Union
from datetime import datetime
from collections import defaultdict
import logging
import difflib

logger = logging.getLogger(__name__)


class AggregationStrategy(Enum):
    """结果聚合策略"""
    CONCATENATE = "concatenate"      # 简单拼接
    SMART_MERGE = "smart_merge"      # 智能合并（去重、排序）
    VOTE = "vote"                    # 投票选择
    CONSENSUS = "consensus"          # 共识算法
    HIERARCHICAL = "hierarchical"    # 层级合并
    SUMMARIZE = "summarize"          # 摘要汇总
    CUSTOM = "custom"                # 自定义策略


class ResultQuality(Enum):
    """结果质量等级"""
    EXCELLENT = 5   # 优秀
    GOOD = 4        # 良好
    ACCEPTABLE = 3  # 可接受
    POOR = 2        # 较差
    INVALID = 1     # 无效


@dataclass
class ResultItem:
    """单个结果项"""
    source: str                      # 来源标识
    content: Any                     # 结果内容
    confidence: float = 1.0          # 置信度 (0-1)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0       # 质量评分
    
    def __post_init__(self):
        if self.quality_score == 0.0:
            self.quality_score = self._calculate_quality()
    
    def _calculate_quality(self) -> float:
        """计算质量评分"""
        score = self.confidence * 100
        
        # 内容长度评分
        if isinstance(self.content, str):
            length = len(self.content)
            if length > 100:
                score += 10
            elif length < 20:
                score -= 10
        
        # 时效性评分
        age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600
        if age_hours > 24:
            score -= 5
        
        return max(0, min(100, score))


@dataclass
class AggregationContext:
    """聚合上下文"""
    task_id: str
    strategy: AggregationStrategy
    expected_format: Optional[str] = None  # 期望输出格式
    merge_fields: Optional[List[str]] = None  # 需要合并的字段
    deduplicate: bool = True
    sort_by: Optional[str] = None
    custom_weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class AggregationResult:
    """聚合结果"""
    success: bool
    content: Any
    strategy_used: AggregationStrategy
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.0
    quality: ResultQuality = ResultQuality.ACCEPTABLE
    conflicts_resolved: int = 0
    items_merged: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0


class ResultAggregator:
    """
    结果聚合器
    支持多种聚合策略、冲突解决、质量评估
    """
    
    def __init__(self):
        self._custom_strategies: Dict[str, Callable] = {}
        self._quality_threshold: float = 0.3
        self._similarity_threshold: float = 0.85  # 去重相似度阈值
        
    def register_strategy(self, name: str, handler: Callable):
        """注册自定义聚合策略"""
        self._custom_strategies[name] = handler
        logger.info(f"Custom strategy '{name}' registered")
    
    async def aggregate(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> AggregationResult:
        """
        执行结果聚合
        """
        import time
        start_time = time.time()
        
        if not results:
            return AggregationResult(
                success=False,
                content=None,
                strategy_used=context.strategy,
                quality=ResultQuality.INVALID
            )
        
        # 过滤低质量结果
        filtered_results = self._filter_quality(results)
        
        if not filtered_results:
            return AggregationResult(
                success=False,
                content="All results failed quality check",
                strategy_used=context.strategy,
                quality=ResultQuality.INVALID
            )
        
        # 根据策略执行聚合
        if context.strategy == AggregationStrategy.CONCATENATE:
            result = self._concatenate(filtered_results, context)
        elif context.strategy == AggregationStrategy.SMART_MERGE:
            result = self._smart_merge(filtered_results, context)
        elif context.strategy == AggregationStrategy.VOTE:
            result = self._vote(filtered_results, context)
        elif context.strategy == AggregationStrategy.CONSENSUS:
            result = self._consensus(filtered_results, context)
        elif context.strategy == AggregationStrategy.HIERARCHICAL:
            result = self._hierarchical_merge(filtered_results, context)
        elif context.strategy == AggregationStrategy.SUMMARIZE:
            result = self._summarize(filtered_results, context)
        elif context.strategy == AggregationStrategy.CUSTOM:
            result = await self._custom_aggregate(filtered_results, context)
        else:
            result = self._smart_merge(filtered_results, context)
        
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        
        return result
    
    def _filter_quality(self, results: List[ResultItem]) -> List[ResultItem]:
        """过滤低质量结果"""
        filtered = [
            r for r in results 
            if r.quality_score >= self._quality_threshold * 100
        ]
        
        # 按质量排序
        filtered.sort(key=lambda x: x.quality_score, reverse=True)
        return filtered
    
    def _concatenate(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> AggregationResult:
        """简单拼接策略"""
        contents = []
        sources = []
        
        for item in results:
            content = self._format_content(item.content)
            if content:
                contents.append(content)
                sources.append(item.source)
        
        separator = "\n\n---\n\n" if context.expected_format == "markdown" else "\n"
        merged_content = separator.join(contents)
        
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return AggregationResult(
            success=True,
            content=merged_content,
            strategy_used=AggregationStrategy.CONCATENATE,
            sources=sources,
            confidence=avg_confidence,
            quality=self._assess_quality(avg_confidence, len(results)),
            items_merged=len(results)
        )
    
    def _smart_merge(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> AggregationResult:
        """
        智能合并策略
        - 去重
        - 按相关性排序
        - 合并重叠内容
        """
        if not results:
            return AggregationResult(
                success=False,
                content=None,
                strategy_used=AggregationStrategy.SMART_MERGE
            )
        
        # 去重
        if context.deduplicate:
            results = self._deduplicate_results(results)
        
        # 处理不同类型内容
        first_content = results[0].content
        
        if isinstance(first_content, str):
            merged = self._merge_text_results(results, context)
        elif isinstance(first_content, (list, dict)):
            merged = self._merge_structured_results(results, context)
        else:
            merged = self._concatenate(results, context)
            merged.strategy_used = AggregationStrategy.SMART_MERGE
            return merged
        
        sources = list(set(r.source for r in results))
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return AggregationResult(
            success=True,
            content=merged,
            strategy_used=AggregationStrategy.SMART_MERGE,
            sources=sources,
            confidence=avg_confidence,
            quality=self._assess_quality(avg_confidence, len(results)),
            items_merged=len(results),
            conflicts_resolved=self._count_conflicts(results)
        )
    
    def _deduplicate_results(self, results: List[ResultItem]) -> List[ResultItem]:
        """去重：移除相似度高的结果"""
        unique_results = []
        
        for result in results:
            is_duplicate = False
            for existing in unique_results:
                similarity = self._calculate_similarity(result.content, existing.content)
                if similarity > self._similarity_threshold:
                    is_duplicate = True
                    # 保留质量更高的
                    if result.quality_score > existing.quality_score:
                        existing.content = result.content
                        existing.confidence = result.confidence
                    break
            
            if not is_duplicate:
                unique_results.append(result)
        
        return unique_results
    
    def _calculate_similarity(self, content1: Any, content2: Any) -> float:
        """计算内容相似度"""
        if type(content1) != type(content2):
            return 0.0
        
        if isinstance(content1, str):
            return difflib.SequenceMatcher(None, content1, content2).ratio()
        elif isinstance(content1, (list, dict)):
            str1 = json.dumps(content1, sort_keys=True)
            str2 = json.dumps(content2, sort_keys=True)
            return difflib.SequenceMatcher(None, str1, str2).ratio()
        
        return 1.0 if content1 == content2 else 0.0
    
    def _merge_text_results(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> str:
        """合并文本结果"""
        sections = []
        
        # 按来源分组
        for result in results:
            content = str(result.content)
            
            # 提取关键段落
            paragraphs = self._extract_key_paragraphs(content)
            
            for para in paragraphs:
                sections.append({
                    'text': para,
                    'source': result.source,
                    'confidence': result.confidence,
                    'quality': result.quality_score
                })
        
        # 按质量排序
        sections.sort(key=lambda x: x['quality'], reverse=True)
        
        # 合并去重
        seen_paragraphs = set()
        unique_sections = []
        
        for section in sections:
            normalized = self._normalize_text(section['text'])
            if normalized not in seen_paragraphs:
                seen_paragraphs.add(normalized)
                unique_sections.append(section['text'])
        
        return '\n\n'.join(unique_sections)
    
    def _merge_structured_results(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> Union[List, Dict]:
        """合并结构化结果（列表或字典）"""
        first_content = results[0].content
        
        if isinstance(first_content, list):
            merged = []
            seen = set()
            
            for result in results:
                for item in result.content:
                    item_key = self._get_item_key(item)
                    if item_key not in seen:
                        seen.add(item_key)
                        merged.append(item)
            
            # 排序
            if context.sort_by:
                try:
                    merged.sort(key=lambda x: x.get(context.sort_by, ''))
                except (KeyError, TypeError):
                    pass
            
            return merged
        
        elif isinstance(first_content, dict):
            merged = {}
            
            for result in results:
                for key, value in result.content.items():
                    if key not in merged:
                        merged[key] = value
                    else:
                        # 冲突解决：选择置信度更高的
                        if result.confidence > 0.7:
                            merged[key] = value
            
            return merged
        
        return first_content
    
    def _vote(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> AggregationResult:
        """投票策略 - 选择最一致的结果"""
        if len(results) == 1:
            return AggregationResult(
                success=True,
                content=results[0].content,
                strategy_used=AggregationStrategy.VOTE,
                sources=[results[0].source],
                confidence=results[0].confidence,
                quality=self._assess_quality(results[0].confidence, 1)
            )
        
        # 计算每对结果之间的相似度
        votes = defaultdict(float)
        
        for i, result1 in enumerate(results):
            for j, result2 in enumerate(results):
                if i >= j:
                    continue
                
                similarity = self._calculate_similarity(result1.content, result2.content)
                
                if similarity > 0.8:  # 高度相似
                    votes[result1.source] += result1.confidence * similarity
                    votes[result2.source] += result2.confidence * similarity
        
        if not votes:
            # 没有达成一致，返回置信度最高的
            best = max(results, key=lambda x: x.confidence)
            return AggregationResult(
                success=True,
                content=best.content,
                strategy_used=AggregationStrategy.VOTE,
                sources=[best.source],
                confidence=best.confidence
            )
        
        # 选择得票最多的
        winner_source = max(votes.items(), key=lambda x: x[1])[0]
        winner = next(r for r in results if r.source == winner_source)
        
        return AggregationResult(
            success=True,
            content=winner.content,
            strategy_used=AggregationStrategy.VOTE,
            sources=list(votes.keys()),
            confidence=winner.confidence,
            items_merged=len(results)
        )
    
    def _consensus(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> AggregationResult:
        """共识策略 - 寻找所有结果的共同点"""
        if not results:
            return AggregationResult(
                success=False,
                content=None,
                strategy_used=AggregationStrategy.CONSENSUS
            )
        
        if len(results) == 1:
            return AggregationResult(
                success=True,
                content=results[0].content,
                strategy_used=AggregationStrategy.CONSENSUS,
                sources=[results[0].source],
                confidence=results[0].confidence
            )
        
        # 对文本结果，找共同子串/段落
        if isinstance(results[0].content, str):
            common_parts = self._find_common_parts([r.content for r in results])
            content = '\n'.join(common_parts) if common_parts else results[0].content
        else:
            # 结构化数据：找共同键值
            content = self._find_common_structured(results)
        
        sources = [r.source for r in results]
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return AggregationResult(
            success=True,
            content=content,
            strategy_used=AggregationStrategy.CONSENSUS,
            sources=sources,
            confidence=avg_confidence,
            items_merged=len(results)
        )
    
    def _find_common_parts(self, texts: List[str]) -> List[str]:
        """找出多个文本的共同点"""
        if not texts:
            return []
        
        # 简化的共同部分检测
        common = set(self._extract_key_paragraphs(texts[0]))
        
        for text in texts[1:]:
            paragraphs = set(self._extract_key_paragraphs(text))
            common = common & paragraphs
        
        return list(common)
    
    def _find_common_structured(self, results: List[ResultItem]) -> Dict:
        """找出结构化数据的共同部分"""
        if not results or not isinstance(results[0].content, dict):
            return {}
        
        common = {}
        first = results[0].content
        
        for key, value in first.items():
            if all(r.content.get(key) == value for r in results[1:] if isinstance(r.content, dict)):
                common[key] = value
        
        return common
    
    def _hierarchical_merge(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> AggregationResult:
        """层级合并策略 - 按优先级分层合并"""
        # 按权重分组
        tiers = defaultdict(list)
        
        for result in results:
            weight = context.custom_weights.get(result.source, 1.0)
            tier = int(10 - weight * 10)  # 权重高的tier小（优先）
            tiers[tier].append(result)
        
        # 从高层级开始合并
        merged_content = None
        sources_used = []
        
        for tier in sorted(tiers.keys()):
            tier_results = tiers[tier]
            
            if merged_content is None:
                merged_content = tier_results[0].content
                sources_used.append(tier_results[0].source)
            else:
                # 将低层级内容合并到高层级
                merged_content = self._merge_into_base(
                    merged_content, 
                    tier_results[0].content
                )
                sources_used.append(tier_results[0].source)
        
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return AggregationResult(
            success=True,
            content=merged_content,
            strategy_used=AggregationStrategy.HIERARCHICAL,
            sources=sources_used,
            confidence=avg_confidence,
            items_merged=len(results)
        )
    
    def _merge_into_base(self, base: Any, new: Any) -> Any:
        """将新内容合并到基础内容"""
        if isinstance(base, dict) and isinstance(new, dict):
            result = base.copy()
            result.update(new)
            return result
        elif isinstance(base, list) and isinstance(new, list):
            return base + [x for x in new if x not in base]
        elif isinstance(base, str) and isinstance(new, str):
            return base + '\n\n' + new
        return new
    
    def _summarize(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> AggregationResult:
        """摘要汇总策略"""
        all_texts = [self._format_content(r.content) for r in results if r.content]
        combined_text = '\n\n'.join(all_texts)
        
        # 提取关键点
        key_points = self._extract_key_paragraphs(combined_text)
        
        # 生成摘要（简化版）
        summary = self._generate_summary(key_points)
        
        sources = [r.source for r in results]
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return AggregationResult(
            success=True,
            content=summary,
            strategy_used=AggregationStrategy.SUMMARIZE,
            sources=sources,
            confidence=avg_confidence,
            items_merged=len(results)
        )
    
    async def _custom_aggregate(
        self,
        results: List[ResultItem],
        context: AggregationContext
    ) -> AggregationResult:
        """使用自定义策略"""
        strategy_name = context.metadata.get('custom_strategy_name')
        handler = self._custom_strategies.get(strategy_name)
        
        if handler:
            if asyncio.iscoroutinefunction(handler):
                return await handler(results, context)
            else:
                return handler(results, context)
        
        # 回退到智能合并
        return self._smart_merge(results, context)
    
    def _extract_key_paragraphs(self, text: str, max_paragraphs: int = 10) -> List[str]:
        """提取关键段落"""
        if not text:
            return []
        
        # 按段落分割
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # 按长度和关键词重要性排序
        def importance(p):
            score = len(p)
            # 包含列表、数字、引用的段落更重要
            if re.search(r'^[\d\-\*]', p):
                score += 50
            if '"' in p or '"' in p:
                score += 30
            return score
        
        paragraphs.sort(key=importance, reverse=True)
        return paragraphs[:max_paragraphs]
    
    def _generate_summary(self, key_points: List[str]) -> str:
        """生成摘要"""
        if not key_points:
            return ""
        
        # 简单摘要：连接前几个要点
        summary_parts = []
        for i, point in enumerate(key_points[:5], 1):
            # 清理和截断
            clean_point = point.replace('\n', ' ').strip()
            if len(clean_point) > 200:
                clean_point = clean_point[:197] + '...'
            summary_parts.append(f"{i}. {clean_point}")
        
        return '\n'.join(summary_parts)
    
    def _format_content(self, content: Any) -> str:
        """格式化内容为字符串"""
        if isinstance(content, str):
            return content
        elif isinstance(content, (dict, list)):
            return json.dumps(content, ensure_ascii=False, indent=2)
        return str(content)
    
    def _normalize_text(self, text: str) -> str:
        """标准化文本用于比较"""
        return re.sub(r'\s+', ' ', text.lower().strip())
    
    def _get_item_key(self, item: Any) -> str:
        """获取列表项的唯一键"""
        if isinstance(item, dict):
            return json.dumps(item, sort_keys=True)
        return str(item)
    
    def _count_conflicts(self, results: List[ResultItem]) -> int:
        """统计结果间的冲突数"""
        conflicts = 0
        for i, r1 in enumerate(results):
            for r2 in results[i+1:]:
                if isinstance(r1.content, dict) and isinstance(r2.content, dict):
                    for key in set(r1.content.keys()) & set(r2.content.keys()):
                        if r1.content[key] != r2.content[key]:
                            conflicts += 1
        return conflicts
    
    def _assess_quality(self, confidence: float, num_sources: int) -> ResultQuality:
        """评估结果质量"""
        score = confidence * 60 + min(num_sources * 10, 40)
        
        if score >= 90:
            return ResultQuality.EXCELLENT
        elif score >= 75:
            return ResultQuality.GOOD
        elif score >= 50:
            return ResultQuality.ACCEPTABLE
        elif score >= 30:
            return ResultQuality.POOR
        return ResultQuality.INVALID
    
    def set_quality_threshold(self, threshold: float):
        """设置质量阈值 (0-1)"""
        self._quality_threshold = max(0, min(1, threshold))
    
    def set_similarity_threshold(self, threshold: float):
        """设置相似度阈值 (0-1)"""
        self._similarity_threshold = max(0, min(1, threshold))


# 全局聚合器实例
_default_aggregator: Optional[ResultAggregator] = None


def get_aggregator() -> ResultAggregator:
    """获取全局结果聚合器实例"""
    global _default_aggregator
    if _default_aggregator is None:
        _default_aggregator = ResultAggregator()
    return _default_aggregator
