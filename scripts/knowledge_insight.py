#!/usr/bin/env python3
"""
统一知识内化系统 - 洞察生成与关联
Knowledge Insight Engine

功能：
1. 读取 processed/ 的结构化知识
2. 跨来源关联分析（Moltbook + HN + GitHub）
3. 生成洞察报告
4. 发现趋势和模式
5. 生成 actions/ 的学习任务清单
"""

import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Iterator
from enum import Enum
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SourceType(Enum):
    """知识来源类型"""
    MOLTBOOK = "moltbook"
    HACKERNEWS = "hackernews"
    GITHUB = "github"
    INDIEHACKERS = "indiehackers"
    PRODUCTHUNT = "producthunt"
    DEVTO = "devto"
    LOBSTERS = "lobsters"
    UNKNOWN = "unknown"


class InsightType(Enum):
    """洞察类型"""
    TREND = "trend"              # 趋势洞察
    CORRELATION = "correlation"  # 跨源关联
    EMERGING = "emerging"        # 新兴话题
    RECURRING = "recurring"      # 重复出现主题
    TECH_PATTERN = "tech_pattern" # 技术模式
    LEARNING = "learning"        # 学习建议
    ACTION = "action"            # 行动建议


@dataclass
class KnowledgeItem:
    """结构化知识条目"""
    id: str
    title: str
    content: str
    source: SourceType
    url: Optional[str] = None
    author: Optional[str] = None
    score: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source.value,
            "url": self.url,
            "author": self.author,
            "score": self.score,
            "metadata": self.metadata,
            "extracted_at": self.extracted_at.isoformat(),
            "tags": self.tags,
        }


@dataclass
class Correlation:
    """跨源关联"""
    id: str
    items: List[KnowledgeItem]
    correlation_type: str
    strength: float  # 0.0 - 1.0
    common_themes: List[str]
    sources_involved: List[SourceType]
    discovered_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "items": [item.to_dict() for item in self.items],
            "correlation_type": self.correlation_type,
            "strength": self.strength,
            "common_themes": self.common_themes,
            "sources_involved": [s.value for s in self.sources_involved],
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class Trend:
    """趋势发现"""
    id: str
    name: str
    description: str
    keywords: List[str]
    related_items: List[str]  # item ids
    source_distribution: Dict[str, int]
    first_seen: datetime
    last_seen: datetime
    momentum: float  # 动量分数
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "related_items": self.related_items,
            "source_distribution": self.source_distribution,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "momentum": self.momentum,
        }


@dataclass
class Insight:
    """洞察结果"""
    id: str
    type: InsightType
    title: str
    description: str
    evidence: List[str]  # 相关条目ID
    confidence: float  # 0.0 - 1.0
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class LearningTask:
    """学习任务"""
    id: str
    title: str
    description: str
    priority: str  # high, medium, low
    source_insight: Optional[str]  # 关联的洞察ID
    related_topics: List[str]
    estimated_time: str
    created_at: datetime = field(default_factory=datetime.now)
    completed: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "source_insight": self.source_insight,
            "related_topics": self.related_topics,
            "estimated_time": self.estimated_time,
            "created_at": self.created_at.isoformat(),
            "completed": self.completed,
        }


@dataclass
class InsightReport:
    """洞察报告"""
    id: str
    title: str
    generated_at: datetime
    time_range: Tuple[datetime, datetime]
    total_items: int
    insights: List[Insight]
    correlations: List[Correlation]
    trends: List[Trend]
    source_breakdown: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "time_range": [
                self.time_range[0].isoformat(),
                self.time_range[1].isoformat(),
            ],
            "total_items": self.total_items,
            "insights": [i.to_dict() for i in self.insights],
            "correlations": [c.to_dict() for c in self.correlations],
            "trends": [t.to_dict() for t in self.trends],
            "source_breakdown": self.source_breakdown,
            "metadata": self.metadata,
        }
    
    def to_markdown(self) -> str:
        """生成Markdown格式报告"""
        lines = [
            f"# {self.title}",
            "",
            f"**生成时间**: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            f"**分析时段**: {self.time_range[0].strftime('%Y-%m-%d')} ~ {self.time_range[1].strftime('%Y-%m-%d')}",
            f"**知识条目总数**: {self.total_items}",
            "",
            "## 📊 数据来源分布",
            "",
        ]
        
        for source, count in self.source_breakdown.items():
            lines.append(f"- **{source}**: {count} 条")
        
        lines.extend(["", "## 🔗 跨源关联发现", ""])
        if self.correlations:
            for corr in self.correlations:
                lines.append(f"### {corr.correlation_type} (强度: {corr.strength:.2f})")
                lines.append(f"- **共同主题**: {', '.join(corr.common_themes)}")
                lines.append(f"- **涉及来源**: {', '.join(s.value for s in corr.sources_involved)}")
                lines.append("- **相关条目**:")
                for item in corr.items:
                    lines.append(f"  - [{item.source.value}] {item.title}")
                lines.append("")
        else:
            lines.append("暂无显著跨源关联。")
        
        lines.extend(["", "## 📈 趋势与模式", ""])
        if self.trends:
            for trend in self.trends:
                lines.append(f"### {trend.name}")
                lines.append(f"{trend.description}")
                lines.append(f"- **关键词**: {', '.join(trend.keywords)}")
                lines.append(f"- **动量**: {trend.momentum:.2f}")
                lines.append(f"- **来源分布**: {trend.source_distribution}")
                lines.append("")
        else:
            lines.append("暂无发现新趋势。")
        
        lines.extend(["", "## 💡 洞察与建议", ""])
        
        # 按类型分组
        insights_by_type = defaultdict(list)
        for insight in self.insights:
            insights_by_type[insight.type].append(insight)
        
        for type_, insights in insights_by_type.items():
            lines.append(f"### {type_.value.upper()}")
            for insight in insights:
                lines.append(f"**{insight.title}** (置信度: {insight.confidence:.2f})")
                lines.append(f"{insight.description}")
                lines.append("")
        
        lines.extend(["", "---", "*由 Knowledge Insight Engine 自动生成*"])
        
        return "\n".join(lines)


class KnowledgeInsightEngine:
    """知识洞察引擎"""
    
    # 技术关键词词典
    TECH_KEYWORDS = {
        # AI/ML
        "ai", "artificial intelligence", "machine learning", "deep learning", "llm", 
        "language model", "gpt", "claude", "agent", "agents", "autonomous", "rag",
        "向量", "嵌入", "embedding", "vector", "fine-tuning", "prompt", "ai agent",
        # 编程语言
        "python", "rust", "typescript", "javascript", "go", "golang", "cpp", "c++",
        "java", "kotlin", "swift", "zig", "nim", "elixir", "haskell", "functional",
        # 框架/工具
        "react", "vue", "svelte", "nextjs", "fastapi", "django", "flask", "docker",
        "kubernetes", "k8s", "terraform", "ansible", "github actions", "ci/cd",
        # 领域
        "blockchain", "web3", "crypto", "decentralized", "smart contract",
        "startup", "indie hacker", "bootstrapped", "saas", "micro-saas",
        "security", "privacy", "encryption", "vulnerability",
        # 概念
        "async", "concurrency", "parallel", "distributed", "serverless",
        "edge computing", "webassembly", "wasm", "pwa", "realtime",
    }
    
    # 主题映射表
    TOPIC_PATTERNS = {
        "ai_agents": [r"agent", r"autonomous", r"ai agent", r"llm agent", r"async agent"],
        "vector_db": [r"vector", r"embedding", r"rag", r"retrieval", r"semantic search"],
        "web3": [r"blockchain", r"web3", r"crypto", r"decentralized", r"smart contract"],
        "rust": [r"rust", r"cargo", r"rustlang"],
        "typescript": [r"typescript", r"ts", r"\.tsx?"],
        "dev_tools": [r"cli", r"terminal", r"developer tool", r"ide", r"editor"],
        "security": [r"security", r"vulnerability", r"exploit", r"backdoor", r"hack"],
    }
    
    def __init__(
        self,
        processed_dir: Path = None,
        insights_dir: Path = None,
        actions_dir: Path = None,
    ):
        self.processed_dir = processed_dir or Path("/root/.openclaw/workspace/memory/knowledge/processed")
        self.insights_dir = insights_dir or Path("/root/.openclaw/workspace/memory/knowledge/insights")
        self.actions_dir = actions_dir or Path("/root/.openclaw/workspace/memory/knowledge/actions")
        
        # 确保目录存在
        self.insights_dir.mkdir(parents=True, exist_ok=True)
        self.actions_dir.mkdir(parents=True, exist_ok=True)
        
        self.knowledge_items: List[KnowledgeItem] = []
        self.correlations: List[Correlation] = []
        self.trends: List[Trend] = []
        self.insights: List[Insight] = []
        
    def load_processed_knowledge(self) -> List[KnowledgeItem]:
        """加载已处理的结构化知识"""
        items = []
        
        if not self.processed_dir.exists():
            logger.warning(f"Processed directory not found: {self.processed_dir}")
            return items
        
        for json_file in self.processed_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 解析数据结构
                if isinstance(data, list):
                    for item_data in data:
                        item = self._parse_knowledge_item(item_data)
                        if item:
                            items.append(item)
                elif isinstance(data, dict):
                    # 可能是批量导出的格式
                    if "items" in data:
                        for item_data in data["items"]:
                            item = self._parse_knowledge_item(item_data, data.get("extractor"))
                            if item:
                                items.append(item)
                    else:
                        item = self._parse_knowledge_item(data)
                        if item:
                            items.append(item)
                            
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")
        
        self.knowledge_items = items
        logger.info(f"Loaded {len(items)} knowledge items from processed/")
        return items
    
    def _parse_knowledge_item(
        self, 
        data: Dict[str, Any], 
        source_hint: str = None
    ) -> Optional[KnowledgeItem]:
        """解析知识条目"""
        try:
            # 确定来源
            source_str = source_hint or data.get("source", "unknown")
            source = self._detect_source(source_str)
            
            # 提取标题和内容
            title = data.get("title", "") or data.get("name", "")
            content = data.get("content", "") or data.get("description", "") or title
            
            if not title:
                return None
            
            # 生成ID
            content_hash = hashlib.md5(f"{title}:{source.value}".encode()).hexdigest()[:12]
            
            # 解析时间
            extracted_at = datetime.now()
            if "extracted_at" in data:
                try:
                    extracted_at = datetime.fromisoformat(data["extracted_at"].replace('Z', '+00:00'))
                except:
                    pass
            elif "extraction_time" in data:
                try:
                    extracted_at = datetime.fromisoformat(data["extraction_time"].replace('Z', '+00:00'))
                except:
                    pass
            
            # 提取标签
            tags = self._extract_tags(title + " " + content)
            
            return KnowledgeItem(
                id=content_hash,
                title=title,
                content=content,
                source=source,
                url=data.get("url"),
                author=data.get("author"),
                score=data.get("score") or data.get("stars"),
                metadata={k: v for k, v in data.items() if k not in [
                    "title", "content", "description", "name", "url", 
                    "author", "score", "stars", "source", "extracted_at"
                ]},
                extracted_at=extracted_at,
                tags=tags,
            )
        except Exception as e:
            logger.error(f"Failed to parse knowledge item: {e}")
            return None
    
    def _detect_source(self, source_str: str) -> SourceType:
        """检测来源类型"""
        source_str = source_str.lower()
        for source_type in SourceType:
            if source_type.value in source_str:
                return source_type
        return SourceType.UNKNOWN
    
    def _extract_tags(self, text: str) -> List[str]:
        """从文本中提取标签"""
        text_lower = text.lower()
        tags = []
        
        for topic, patterns in self.TOPIC_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    tags.append(topic)
                    break
        
        # 提取技术关键词
        for keyword in self.TECH_KEYWORDS:
            if keyword in text_lower:
                tags.append(keyword.replace(" ", "_"))
        
        return list(set(tags))
    
    def find_correlations(self, min_strength: float = 0.3) -> List[Correlation]:
        """发现跨源关联"""
        correlations = []
        
        # 按标签分组
        tag_groups = defaultdict(list)
        for item in self.knowledge_items:
            for tag in item.tags:
                tag_groups[tag].append(item)
        
        # 寻找跨源关联
        for tag, items in tag_groups.items():
            if len(items) < 2:
                continue
            
            # 检查是否跨多个来源
            sources = set(item.source for item in items)
            if len(sources) < 2:
                continue
            
            # 计算关联强度
            strength = min(1.0, len(items) * 0.2 + len(sources) * 0.1)
            
            if strength >= min_strength:
                corr_id = hashlib.md5(f"corr:{tag}".encode()).hexdigest()[:12]
                correlation = Correlation(
                    id=corr_id,
                    items=items[:5],  # 限制数量
                    correlation_type=f"标签关联: {tag}",
                    strength=strength,
                    common_themes=[tag],
                    sources_involved=list(sources),
                )
                correlations.append(correlation)
        
        # 基于标题相似性的关联
        title_correlations = self._find_title_correlations()
        correlations.extend(title_correlations)
        
        self.correlations = sorted(correlations, key=lambda x: x.strength, reverse=True)
        logger.info(f"Found {len(self.correlations)} correlations")
        return self.correlations
    
    def _find_title_correlations(self) -> List[Correlation]:
        """基于标题相似性发现关联"""
        correlations = []
        
        # 简单的关键词匹配
        for i, item1 in enumerate(self.knowledge_items):
            for item2 in self.knowledge_items[i+1:]:
                if item1.source == item2.source:
                    continue
                
                # 计算标题相似度
                words1 = set(item1.title.lower().split())
                words2 = set(item2.title.lower().split())
                
                # 去除停用词
                stopwords = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "is", "are"}
                words1 -= stopwords
                words2 -= stopwords
                
                if not words1 or not words2:
                    continue
                
                intersection = words1 & words2
                union = words1 | words2
                
                if len(union) == 0:
                    continue
                
                similarity = len(intersection) / len(union)
                
                if similarity >= 0.3:  # 至少30%相似
                    corr_id = hashlib.md5(f"title:{item1.id}:{item2.id}".encode()).hexdigest()[:12]
                    correlation = Correlation(
                        id=corr_id,
                        items=[item1, item2],
                        correlation_type="标题相似",
                        strength=similarity,
                        common_themes=list(intersection)[:5],
                        sources_involved=[item1.source, item2.source],
                    )
                    correlations.append(correlation)
        
        return correlations
    
    def discover_trends(self) -> List[Trend]:
        """发现趋势和模式"""
        trends = []
        
        # 统计标签频率
        tag_counter = Counter()
        tag_timestamps = defaultdict(list)
        tag_sources = defaultdict(lambda: defaultdict(int))
        tag_items = defaultdict(list)
        
        for item in self.knowledge_items:
            for tag in item.tags:
                tag_counter[tag] += 1
                tag_timestamps[tag].append(item.extracted_at)
                tag_sources[tag][item.source.value] += 1
                tag_items[tag].append(item.id)
        
        # 识别趋势（出现频率高且有动量）
        for tag, count in tag_counter.most_common(20):
            if count < 2:
                continue
            
            timestamps = sorted(tag_timestamps[tag])
            if len(timestamps) < 2:
                continue
            
            # 计算动量（最近出现频率 / 总体频率）
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_count = sum(1 for t in timestamps if t > recent_cutoff)
            momentum = recent_count / max(count, 1)
            
            # 生成趋势名称
            trend_name = tag.replace("_", " ").title()
            
            trend = Trend(
                id=hashlib.md5(f"trend:{tag}".encode()).hexdigest()[:12],
                name=trend_name,
                description=f"{tag} 相关话题在过去周期中出现 {count} 次，显示持续关注度。",
                keywords=[tag],
                related_items=tag_items[tag][:10],
                source_distribution=dict(tag_sources[tag]),
                first_seen=timestamps[0],
                last_seen=timestamps[-1],
                momentum=momentum,
            )
            trends.append(trend)
        
        self.trends = sorted(trends, key=lambda x: x.momentum, reverse=True)
        logger.info(f"Discovered {len(self.trends)} trends")
        return self.trends
    
    def generate_insights(self) -> List[Insight]:
        """生成洞察"""
        insights = []
        
        # 1. 基于关联的洞察
        for corr in self.correlations[:5]:
            insight = Insight(
                id=f"insight-corr-{corr.id}",
                type=InsightType.CORRELATION,
                title=f"跨源关联: {corr.common_themes[0] if corr.common_themes else '多个主题'}",
                description=f"发现 {len(corr.sources_involved)} 个来源 ({', '.join(s.value for s in corr.sources_involved)}) 都在讨论相关话题。",
                evidence=[item.id for item in corr.items],
                confidence=corr.strength,
                metadata={"correlation_id": corr.id},
            )
            insights.append(insight)
        
        # 2. 基于趋势的洞察
        for trend in self.trends[:5]:
            insight = Insight(
                id=f"insight-trend-{trend.id}",
                type=InsightType.TREND,
                title=f"趋势: {trend.name}",
                description=trend.description,
                evidence=trend.related_items[:5],
                confidence=min(0.9, 0.5 + trend.momentum),
                metadata={"momentum": trend.momentum},
            )
            insights.append(insight)
        
        # 3. 新兴话题洞察
        emerging_tags = [t for t in self.trends if t.momentum > 0.5 and len(t.related_items) >= 2]
        for trend in emerging_tags[:3]:
            insight = Insight(
                id=f"insight-emerging-{trend.id}",
                type=InsightType.EMERGING,
                title=f"新兴: {trend.name}",
                description=f"'{trend.name}' 正成为热点话题，近期讨论密度显著增加。",
                evidence=trend.related_items[:5],
                confidence=trend.momentum,
                metadata={"recent_momentum": trend.momentum},
            )
            insights.append(insight)
        
        # 4. 技术模式洞察
        tech_patterns = self._analyze_tech_patterns()
        insights.extend(tech_patterns)
        
        self.insights = insights
        logger.info(f"Generated {len(insights)} insights")
        return insights
    
    def _analyze_tech_patterns(self) -> List[Insight]:
        """分析技术模式"""
        insights = []
        
        # 统计编程语言出现
        lang_counter = Counter()
        lang_items = defaultdict(list)
        
        languages = ["python", "rust", "typescript", "go", "golang", "javascript", "c++", "cpp"]
        
        for item in self.knowledge_items:
            text = (item.title + " " + item.content).lower()
            for lang in languages:
                if lang in text or f"{lang}lang" in text.replace(" ", ""):
                    lang_counter[lang] += 1
                    lang_items[lang].append(item.id)
        
        # 找出热门语言
        for lang, count in lang_counter.most_common(3):
            if count >= 2:
                insight = Insight(
                    id=f"insight-lang-{lang}",
                    type=InsightType.TECH_PATTERN,
                    title=f"技术焦点: {lang.title()}",
                    description=f"{lang.title()} 在多个来源中被频繁提及 ({count} 次)，显示其当前热度。",
                    evidence=lang_items[lang][:5],
                    confidence=min(0.9, 0.4 + count * 0.1),
                    metadata={"language": lang, "mentions": count},
                )
                insights.append(insight)
        
        return insights
    
    def generate_learning_tasks(self) -> List[LearningTask]:
        """生成学习任务清单"""
        tasks = []
        
        # 1. 基于趋势的深度学习任务
        for trend in self.trends[:3]:
            task = LearningTask(
                id=f"task-trend-{trend.id}",
                title=f"深入研究: {trend.name}",
                description=f"探索 {trend.name} 相关技术/概念，理解其核心原理和应用场景。相关来源: {', '.join(trend.source_distribution.keys())}",
                priority="high" if trend.momentum > 0.7 else "medium",
                source_insight=f"insight-trend-{trend.id}",
                related_topics=trend.keywords,
                estimated_time="2-4 小时",
            )
            tasks.append(task)
        
        # 2. 基于关联的探索任务
        for corr in self.correlations[:2]:
            theme = corr.common_themes[0] if corr.common_themes else "相关主题"
            task = LearningTask(
                id=f"task-corr-{corr.id}",
                title=f"跨源研究: {theme}",
                description=f"对比分析 {', '.join(s.value for s in corr.sources_involved)} 中关于 '{theme}' 的不同观点。",
                priority="medium",
                source_insight=f"insight-corr-{corr.id}",
                related_topics=corr.common_themes,
                estimated_time="1-2 小时",
            )
            tasks.append(task)
        
        # 3. 技术探索任务
        tech_insights = [i for i in self.insights if i.type == InsightType.TECH_PATTERN]
        for insight in tech_insights[:2]:
            lang = insight.metadata.get("language", "")
            task = LearningTask(
                id=f"task-tech-{insight.id}",
                title=f"技术调研: {lang.title() if lang else '新技术'}",
                description=f"了解 {lang.title() if lang else '该技术'} 的最新进展，收集 3-5 个优质资源。",
                priority="medium",
                source_insight=insight.id,
                related_topics=[lang] if lang else [],
                estimated_time="1 小时",
            )
            tasks.append(task)
        
        # 4. 通用学习任务
        general_tasks = [
            LearningTask(
                id=f"task-general-{i}",
                title=title,
                description=desc,
                priority=priority,
                source_insight=None,
                related_topics=[],
                estimated_time=time,
            )
            for i, (title, desc, priority, time) in enumerate([
                (
                    "整理今日知识笔记",
                    "将今天收集的知识整理成结构化的学习笔记，包括关键概念、资源链接和个人见解。",
                    "high",
                    "30 分钟",
                ),
                (
                    "关注趋势发展",
                    "设置 Google Alerts 或 RSS 订阅，跟踪今天发现的重要趋势的后续发展。",
                    "low",
                    "15 分钟",
                ),
                (
                    "实践探索",
                    "选择一个今天发现的开源项目或工具，进行 30 分钟的实践尝试。",
                    "medium",
                    "30 分钟",
                ),
            ])
        ]
        tasks.extend(general_tasks)
        
        logger.info(f"Generated {len(tasks)} learning tasks")
        return tasks
    
    def generate_report(self, title: str = None) -> InsightReport:
        """生成完整洞察报告"""
        if not self.knowledge_items:
            self.load_processed_knowledge()
        
        if not self.correlations:
            self.find_correlations()
        
        if not self.trends:
            self.discover_trends()
        
        if not self.insights:
            self.generate_insights()
        
        # 计算时间范围
        if self.knowledge_items:
            timestamps = [item.extracted_at for item in self.knowledge_items]
            time_range = (min(timestamps), max(timestamps))
        else:
            time_range = (datetime.now(), datetime.now())
        
        # 统计来源分布
        source_breakdown = Counter(item.source.value for item in self.knowledge_items)
        
        report = InsightReport(
            id=hashlib.md5(f"report:{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            title=title or f"知识洞察报告 - {datetime.now().strftime('%Y-%m-%d')}",
            generated_at=datetime.now(),
            time_range=time_range,
            total_items=len(self.knowledge_items),
            insights=self.insights,
            correlations=self.correlations,
            trends=self.trends,
            source_breakdown=dict(source_breakdown),
            metadata={
                "engine_version": "1.0.0",
                "analysis_params": {
                    "min_correlation_strength": 0.3,
                    "max_trends": 20,
                    "max_insights": 20,
                }
            }
        )
        
        return report
    
    def save_report(self, report: InsightReport) -> Path:
        """保存洞察报告"""
        # JSON格式
        json_path = self.insights_dir / f"insight_report_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        # Markdown格式
        md_path = self.insights_dir / f"insight_report_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report.to_markdown())
        
        logger.info(f"Report saved: {json_path} and {md_path}")
        return json_path
    
    def save_learning_tasks(self, tasks: List[LearningTask]) -> Path:
        """保存学习任务清单"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        tasks_path = self.actions_dir / f"learning_tasks_{timestamp}.json"
        
        with open(tasks_path, 'w', encoding='utf-8') as f:
            json.dump([task.to_dict() for task in tasks], f, ensure_ascii=False, indent=2)
        
        # 同时生成Markdown版本
        md_path = self.actions_dir / f"learning_tasks_{timestamp}.md"
        lines = [
            "# 📚 学习任务清单",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**任务总数**: {len(tasks)}",
            "",
            "## 高优先级",
            "",
        ]
        
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_tasks = sorted(tasks, key=lambda t: priority_order.get(t.priority, 99))
        
        for task in sorted_tasks:
            checkbox = "[x]" if task.completed else "[ ]"
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
            lines.append(f"- {checkbox} {priority_emoji} **{task.title}** ({task.estimated_time})")
            lines.append(f"  - {task.description}")
            if task.related_topics:
                lines.append(f"  - 相关主题: {', '.join(task.related_topics)}")
            lines.append("")
        
        lines.extend(["---", "*自动生成的学习任务清单*"])
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        logger.info(f"Learning tasks saved: {tasks_path} and {md_path}")
        return tasks_path
    
    def run_full_analysis(self, report_title: str = None) -> Tuple[InsightReport, List[LearningTask], Path, Path]:
        """运行完整分析流程"""
        logger.info("=" * 50)
        logger.info("Starting Knowledge Insight Engine")
        logger.info("=" * 50)
        
        # 1. 加载知识
        self.load_processed_knowledge()
        
        # 2. 发现关联
        self.find_correlations()
        
        # 3. 发现趋势
        self.discover_trends()
        
        # 4. 生成洞察
        self.generate_insights()
        
        # 5. 生成报告
        report = self.generate_report(report_title)
        report_path = self.save_report(report)
        
        # 6. 生成学习任务
        tasks = self.generate_learning_tasks()
        tasks_path = self.save_learning_tasks(tasks)
        
        logger.info("=" * 50)
        logger.info("Analysis complete!")
        logger.info(f"  - Knowledge items: {len(self.knowledge_items)}")
        logger.info(f"  - Correlations: {len(self.correlations)}")
        logger.info(f"  - Trends: {len(self.trends)}")
        logger.info(f"  - Insights: {len(self.insights)}")
        logger.info(f"  - Learning tasks: {len(tasks)}")
        logger.info("=" * 50)
        
        return report, tasks, report_path, tasks_path


def load_raw_data_and_process():
    """
    从原始数据目录加载并处理数据到 processed/ 目录
    """
    data_dir = Path("/root/.openclaw/workspace/data")
    processed_dir = Path("/root/.openclaw/workspace/memory/knowledge/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    
    # 定义数据源
    sources = {
        "moltbook": "moltbook",
        "hackernews": "hackernews", 
        "github_trending": "github_trending",
        "indiehackers": "indiehackers",
        "producthunt": "producthunt",
        "devto": "devto",
        "lobsters": "lobsters",
    }
    
    for source_name, source_folder in sources.items():
        source_dir = data_dir / source_folder
        if not source_dir.exists():
            continue
        
        # 查找最新的列表文件
        list_files = list(source_dir.glob("*_list_*.json"))
        if not list_files:
            continue
        
        # 按修改时间排序，取最新的
        latest_file = max(list_files, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 转换为标准格式
            processed_items = []
            
            if "items" in data:
                for item in data["items"]:
                    processed_item = {
                        "id": hashlib.md5(f"{item.get('title', '')}:{source_name}".encode()).hexdigest()[:12],
                        "title": item.get("title", ""),
                        "content": item.get("description", item.get("content", item.get("title", ""))),
                        "url": item.get("url", ""),
                        "source": source_name,
                        "author": item.get("author", ""),
                        "score": item.get("score") or item.get("stars", ""),
                        "metadata": {
                            "original_file": str(latest_file),
                            "language": item.get("language", ""),
                        },
                        "extracted_at": data.get("extraction_time", datetime.now().isoformat()),
                    }
                    processed_items.append(processed_item)
            
            # 保存到 processed 目录
            output_file = processed_dir / f"{source_name}_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_items, f, ensure_ascii=False, indent=2)
            
            processed_count += len(processed_items)
            logger.info(f"Processed {len(processed_items)} items from {source_name}")
            
        except Exception as e:
            logger.error(f"Failed to process {source_name}: {e}")
    
    return processed_count


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Insight Engine")
    parser.add_argument("--process-raw", action="store_true", help="Process raw data first")
    parser.add_argument("--report-title", default=None, help="Custom report title")
    args = parser.parse_args()
    
    # 如果需要，先处理原始数据
    if args.process_raw:
        count = load_raw_data_and_process()
        print(f"Processed {count} raw items")
    
    # 运行洞察引擎
    engine = KnowledgeInsightEngine()
    report, tasks, report_path, tasks_path = engine.run_full_analysis(args.report_title)
    
    print("\n" + "=" * 50)
    print("📊 洞察分析完成")
    print("=" * 50)
    print(f"知识条目总数: {len(engine.knowledge_items)}")
    print(f"跨源关联发现: {len(engine.correlations)} 个")
    print(f"趋势发现: {len(engine.trends)} 个")
    print(f"洞察生成: {len(engine.insights)} 个")
    print(f"学习任务: {len(tasks)} 个")
    print("=" * 50)
    print(f"\n报告文件: {report_path}")
    print(f"任务清单: {tasks_path}")
    
    return report, tasks


if __name__ == "__main__":
    main()
