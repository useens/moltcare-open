"""
知识洞察生成器 (Knowledge Insight)
负责从处理后的知识中提取洞察和模式
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict

from .knowledge_processor import ProcessedKnowledge


@dataclass
class KnowledgeInsight:
    """洞察数据结构"""
    id: str
    type: str  # 洞察类型: pattern, trend, connection, summary, action
    title: str
    description: str
    related_knowledge_ids: List[str]
    confidence: float  # 置信度 0-1
    created_at: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KnowledgeInsight':
        return cls(**data)


@dataclass
class ActionItem:
    """行动项数据结构"""
    id: str
    content: str
    priority: str  # high, medium, low
    source_insight_id: Optional[str]
    related_knowledge_ids: List[str]
    due_date: Optional[float]
    status: str  # pending, in_progress, completed
    created_at: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ActionItem':
        return cls(**data)


class InsightGenerator:
    """
    知识洞察生成器
    
    职责：
    1. 分析知识模式
    2. 发现知识之间的关联
    3. 生成趋势分析
    4. 识别行动项
    5. 输出洞察到 insights 和 actions 目录
    """
    
    def __init__(self, base_path: str = "memory/knowledge"):
        self.base_path = Path(base_path)
        self.insights_path = self.base_path / "insights"
        self.actions_path = self.base_path / "actions"
        self._ensure_directories()
        
    def _ensure_directories(self):
        """确保目录结构存在"""
        self.insights_path.mkdir(parents=True, exist_ok=True)
        self.actions_path.mkdir(parents=True, exist_ok=True)
    
    def generate_daily_summary(self, knowledge_list: List[ProcessedKnowledge]) -> KnowledgeInsight:
        """
        生成每日知识摘要
        
        Args:
            knowledge_list: 当天处理后的知识列表
            
        Returns:
            KnowledgeInsight 对象
        """
        if not knowledge_list:
            return None
        
        # 统计分类
        categories = Counter([k.category for k in knowledge_list])
        
        # 统计关键词
        all_keywords = []
        for k in knowledge_list:
            all_keywords.extend(k.keywords)
        top_keywords = Counter(all_keywords).most_common(5)
        
        # 构建摘要
        title = f"每日知识摘要 ({len(knowledge_list)} 条)"
        description = f"""
今日共记录 {len(knowledge_list)} 条知识：
- 主要分类：{', '.join([f"{cat}({count})" for cat, count in categories.most_common()])}
- 热门关键词：{', '.join([kw for kw, _ in top_keywords])}
- 情感倾向：{self._analyze_sentiment_distribution(knowledge_list)}
        """.strip()
        
        insight = KnowledgeInsight(
            id=self._generate_id('summary'),
            type='summary',
            title=title,
            description=description,
            related_knowledge_ids=[k.id for k in knowledge_list],
            confidence=0.8,
            created_at=datetime.now().timestamp(),
            metadata={
                'total_count': len(knowledge_list),
                'categories': dict(categories),
                'top_keywords': top_keywords
            }
        )
        
        self._save_insight(insight)
        return insight
    
    def find_patterns(self, 
                      knowledge_list: List[ProcessedKnowledge],
                      min_occurrence: int = 2) -> List[KnowledgeInsight]:
        """
        发现知识模式
        
        Args:
            knowledge_list: 知识列表
            min_occurrence: 最小出现次数才算模式
            
        Returns:
            模式洞察列表
        """
        insights = []
        
        # 按分类分组
        by_category = defaultdict(list)
        for k in knowledge_list:
            by_category[k.category].append(k)
        
        # 为每个分类生成模式洞察
        for category, items in by_category.items():
            if len(items) >= min_occurrence:
                # 提取共同关键词
                all_keywords = []
                for item in items:
                    all_keywords.extend(item.keywords)
                common_keywords = [kw for kw, count in Counter(all_keywords).most_common(3)]
                
                insight = KnowledgeInsight(
                    id=self._generate_id('pattern'),
                    type='pattern',
                    title=f"模式：{category} 相关知识的集中出现",
                    description=f"发现 {len(items)} 条 {category} 相关知识，" +
                               f"共同关键词：{', '.join(common_keywords)}",
                    related_knowledge_ids=[k.id for k in items],
                    confidence=min(1.0, len(items) * 0.1),
                    created_at=datetime.now().timestamp(),
                    metadata={
                        'category': category,
                        'count': len(items),
                        'common_keywords': common_keywords
                    }
                )
                insights.append(insight)
                self._save_insight(insight)
        
        return insights
    
    def find_connections(self, 
                         knowledge_list: List[ProcessedKnowledge],
                         similarity_threshold: float = 0.5) -> List[KnowledgeInsight]:
        """
        发现知识之间的关联
        
        Args:
            knowledge_list: 知识列表
            similarity_threshold: 相似度阈值
            
        Returns:
            关联洞察列表
        """
        insights = []
        
        # 基于关键词重叠计算相似度
        for i, k1 in enumerate(knowledge_list):
            for k2 in knowledge_list[i+1:]:
                similarity = self._calculate_similarity(k1, k2)
                
                if similarity >= similarity_threshold:
                    common_keywords = set(k1.keywords) & set(k2.keywords)
                    
                    insight = KnowledgeInsight(
                        id=self._generate_id('connection'),
                        type='connection',
                        title=f"关联发现：知识间的潜在联系",
                        description=f"两条知识可能相关（相似度: {similarity:.2f}），" +
                                   f"共同关键词：{', '.join(common_keywords)}",
                        related_knowledge_ids=[k1.id, k2.id],
                        confidence=similarity,
                        created_at=datetime.now().timestamp(),
                        metadata={
                            'similarity': similarity,
                            'common_keywords': list(common_keywords)
                        }
                    )
                    insights.append(insight)
                    self._save_insight(insight)
        
        return insights
    
    def extract_action_items(self, 
                            knowledge_list: List[ProcessedKnowledge]) -> List[ActionItem]:
        """
        从知识中提取行动项
        
        Args:
            knowledge_list: 知识列表
            
        Returns:
            行动项列表
        """
        actions = []
        
        # 行动关键词
        action_patterns = [
            (r'(?:需要|应该|必须|计划|准备|打算)\s*([^。，]+)', 'high'),
            (r'todo[:：]\s*([^\n]+)', 'medium'),
            (r'待办[:：]\s*([^\n]+)', 'medium'),
            (r'remind(?:er)?[:：]\s*([^\n]+)', 'low'),
        ]
        
        import re
        
        for knowledge in knowledge_list:
            for pattern, priority in action_patterns:
                matches = re.findall(pattern, knowledge.content, re.IGNORECASE)
                for match in matches:
                    action = ActionItem(
                        id=self._generate_id('action'),
                        content=match.strip(),
                        priority=priority,
                        source_insight_id=None,
                        related_knowledge_ids=[knowledge.id],
                        due_date=None,
                        status='pending',
                        created_at=datetime.now().timestamp()
                    )
                    actions.append(action)
                    self._save_action(action)
        
        return actions
    
    def generate_trends(self, 
                       knowledge_history: List[ProcessedKnowledge],
                       days: int = 7) -> KnowledgeInsight:
        """
        生成趋势分析
        
        Args:
            knowledge_history: 历史知识列表
            days: 分析天数
            
        Returns:
            趋势洞察
        """
        # 按日期分组
        by_date = defaultdict(list)
        for k in knowledge_history:
            date = datetime.fromtimestamp(k.processed_at).strftime('%Y-%m-%d')
            by_date[date].append(k)
        
        # 计算每日统计
        daily_counts = {date: len(items) for date, items in by_date.items()}
        
        # 分类趋势
        category_trends = defaultdict(lambda: defaultdict(int))
        for k in knowledge_history:
            date = datetime.fromtimestamp(k.processed_at).strftime('%Y-%m-%d')
            category_trends[k.category][date] += 1
        
        # 找出增长最快的分类
        top_category = max(category_trends.keys(), 
                          key=lambda c: sum(category_trends[c].values()), 
                          default='无')
        
        insight = KnowledgeInsight(
            id=self._generate_id('trend'),
            type='trend',
            title=f"{days}天知识趋势分析",
            description=f"过去{days}天共记录 {len(knowledge_history)} 条知识，" +
                       f"日均 {len(knowledge_history)/days:.1f} 条，" +
                       f"最活跃的分类：{top_category}",
            related_knowledge_ids=[k.id for k in knowledge_history[:10]],
            confidence=0.7,
            created_at=datetime.now().timestamp(),
            metadata={
                'daily_counts': dict(daily_counts),
                'category_trends': {k: dict(v) for k, v in category_trends.items()}
            }
        )
        
        self._save_insight(insight)
        return insight
    
    def _calculate_similarity(self, k1: ProcessedKnowledge, k2: ProcessedKnowledge) -> float:
        """计算两条知识的相似度"""
        # 基于关键词 Jaccard 相似度
        set1 = set(k1.keywords) | set(k1.entities)
        set2 = set(k2.keywords) | set(k2.entities)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _analyze_sentiment_distribution(self, knowledge_list: List[ProcessedKnowledge]) -> str:
        """分析情感分布"""
        sentiments = Counter([k.sentiment for k in knowledge_list if k.sentiment])
        if not sentiments:
            return "无明显倾向"
        
        total = sum(sentiments.values())
        pos_ratio = sentiments.get('positive', 0) / total
        neg_ratio = sentiments.get('negative', 0) / total
        
        if pos_ratio > 0.6:
            return "积极"
        elif neg_ratio > 0.4:
            return "消极"
        return "中性"
    
    def _generate_id(self, prefix: str) -> str:
        """生成唯一ID"""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
    
    def _save_insight(self, insight: KnowledgeInsight):
        """保存洞察到文件"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = self.insights_path / f"{date_str}.jsonl"
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(insight.to_dict(), ensure_ascii=False) + '\n')
    
    def _save_action(self, action: ActionItem):
        """保存行动项到文件"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = self.actions_path / f"{date_str}.jsonl"
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(action.to_dict(), ensure_ascii=False) + '\n')
    
    def list_insights(self, 
                      insight_type: Optional[str] = None,
                      limit: int = 50) -> List[KnowledgeInsight]:
        """列出洞察"""
        results = []
        
        for file_path in sorted(self.insights_path.glob("*.jsonl"), reverse=True):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    if insight_type and data.get('type') != insight_type:
                        continue
                    results.append(KnowledgeInsight.from_dict(data))
                    if len(results) >= limit:
                        break
        
        return results[:limit]
    
    def list_actions(self, 
                     status: Optional[str] = None,
                     priority: Optional[str] = None,
                     limit: int = 50) -> List[ActionItem]:
        """列出行动项"""
        results = []
        
        for file_path in sorted(self.actions_path.glob("*.jsonl"), reverse=True):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    if status and data.get('status') != status:
                        continue
                    if priority and data.get('priority') != priority:
                        continue
                    results.append(ActionItem.from_dict(data))
                    if len(results) >= limit:
                        break
        
        return results[:limit]
    
    def update_action_status(self, action_id: str, status: str) -> bool:
        """更新行动项状态"""
        # 查找并更新
        for file_path in self.actions_path.glob("*.jsonl"):
            lines = []
            found = False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    if data['id'] == action_id:
                        data['status'] = status
                        found = True
                    lines.append(json.dumps(data, ensure_ascii=False))
            
            if found:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines) + '\n')
                return True
        
        return False
