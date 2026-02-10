"""
知识处理器 (Knowledge Processor)
负责将原始知识处理成结构化格式
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict

from .knowledge_collector import RawKnowledge


@dataclass
class ProcessedKnowledge:
    """结构化知识数据结构"""
    id: str
    raw_id: str  # 关联的原始知识ID
    content: str  # 清洗后的内容
    summary: Optional[str]  # 摘要
    category: str  # 分类
    entities: List[str]  # 提取的实体
    keywords: List[str]  # 关键词
    sentiment: Optional[str]  # 情感倾向
    processed_at: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProcessedKnowledge':
        return cls(**data)


class KnowledgeProcessor:
    """
    知识处理器
    
    职责：
    1. 清洗原始知识内容
    2. 生成摘要
    3. 提取实体和关键词
    4. 分类知识
    5. 存储到 processed 目录
    """
    
    # 默认分类标签
    CATEGORIES = [
        '技术', '学习', '工作', '生活', 
        '想法', '资源', '待办', '其他'
    ]
    
    def __init__(self, base_path: str = "memory/knowledge"):
        self.base_path = Path(base_path)
        self.processed_path = self.base_path / "processed"
        self._ensure_directories()
        
    def _ensure_directories(self):
        """确保目录结构存在"""
        self.processed_path.mkdir(parents=True, exist_ok=True)
    
    def process(self, raw: RawKnowledge) -> ProcessedKnowledge:
        """
        处理单条原始知识
        
        Args:
            raw: 原始知识对象
            
        Returns:
            ProcessedKnowledge 对象
        """
        # 清洗内容
        cleaned_content = self._clean_content(raw.content)
        
        # 生成摘要
        summary = self._generate_summary(cleaned_content)
        
        # 提取关键词
        keywords = self._extract_keywords(cleaned_content)
        
        # 提取实体
        entities = self._extract_entities(cleaned_content)
        
        # 分类
        category = self._classify(cleaned_content, raw.tags)
        
        # 情感分析
        sentiment = self._analyze_sentiment(cleaned_content)
        
        processed = ProcessedKnowledge(
            id=self._generate_id(raw.id),
            raw_id=raw.id,
            content=cleaned_content,
            summary=summary,
            category=category,
            entities=entities,
            keywords=keywords,
            sentiment=sentiment,
            processed_at=datetime.now().timestamp()
        )
        
        self._save_processed(processed)
        return processed
    
    def process_batch(self, raw_items: List[RawKnowledge]) -> List[ProcessedKnowledge]:
        """
        批量处理原始知识
        
        Args:
            raw_items: 原始知识列表
            
        Returns:
            ProcessedKnowledge 列表
        """
        return [self.process(item) for item in raw_items]
    
    def _clean_content(self, content: str) -> str:
        """
        清洗内容
        
        - 去除多余空白
        - 标准化换行
        - 去除特殊字符
        """
        # 标准化换行
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # 去除多余空白行
        lines = [line.strip() for line in content.split('\n')]
        lines = [line for line in lines if line]
        
        # 重新组合
        content = '\n'.join(lines)
        
        # 去除多余空格
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def _generate_summary(self, content: str, max_length: int = 200) -> Optional[str]:
        """
        生成摘要
        
        简单实现：取前 max_length 个字符，在句号处截断
        """
        if len(content) <= max_length:
            return content
        
        # 在 max_length 范围内找最后一个句号
        truncated = content[:max_length]
        last_period = truncated.rfind('。')
        
        if last_period > 0:
            return truncated[:last_period + 1]
        
        return truncated + "..."
    
    def _extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """
        提取关键词
        
        简单实现：基于词频和停用词过滤
        （可扩展为使用 NLP 库如 jieba/spacy）
        """
        # 基础停用词
        stopwords = {'的', '是', '在', '和', '了', '有', '我', '都', '个', '与', 
                     '也', '对', '为', '能', '很', '可以', '就', '不', '会', '要',
                     '没有', '我们', '这', '那', '有', '个', '之', '它', '他', '她'}
        
        # 简单分词（按非字符分割）
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', content)
        
        # 统计词频
        word_freq = {}
        for word in words:
            word = word.lower()
            if len(word) > 1 and word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in sorted_words[:max_keywords]]
    
    def _extract_entities(self, content: str) -> List[str]:
        """
        提取命名实体
        
        简单实现：识别大写单词、引号内容、URL 等
        （可扩展为使用 NER 模型）
        """
        entities = []
        
        # 识别 URL
        urls = re.findall(r'https?://[^\s<>"{}|\\^`[\]]+', content)
        entities.extend(urls)
        
        # 识别引号内容
        quoted = re.findall(r'[""]([^""]+)[""]', content)
        entities.extend([q for q in quoted if len(q) > 2])
        
        # 识别大驼峰命名（可能是专有名词）
        camel_case = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+', content)
        entities.extend(camel_case)
        
        return list(set(entities))  # 去重
    
    def _classify(self, content: str, tags: List[str]) -> str:
        """
        分类知识
        
        简单实现：基于关键词匹配
        """
        content_lower = content.lower()
        
        # 基于内容的分类规则
        rules = {
            '技术': ['代码', '编程', 'python', 'javascript', 'api', '数据库', '算法', 
                    '代码', 'bug', 'debug', 'github', 'docker', '服务器'],
            '学习': ['学习', '课程', '教程', '书籍', '笔记', '研究', '论文', '知识'],
            '工作': ['项目', '会议', '任务', 'deadline', '邮件', '客户', '需求'],
            '生活': ['健康', '运动', '饮食', '旅行', '家庭', '朋友', '购物'],
            '想法': ['想法', '思考', '感悟', '观点', '灵感', '创意'],
            '资源': ['链接', '工具', '软件', '网站', 'app', '推荐'],
            '待办': ['todo', '待办', '计划', '目标', '提醒', '安排'],
        }
        
        for category, keywords in rules.items():
            if any(kw in content_lower for kw in keywords):
                return category
        
        # 检查标签
        for tag in tags:
            if tag in self.CATEGORIES:
                return tag
        
        return '其他'
    
    def _analyze_sentiment(self, content: str) -> Optional[str]:
        """
        简单情感分析
        
        Returns: 'positive' | 'neutral' | 'negative'
        """
        positive_words = ['好', '棒', '优秀', '成功', '喜欢', '感谢', '开心', '满意', 'love', 'good', 'great']
        negative_words = ['坏', '差', '失败', '讨厌', '问题', '错误', '难过', '失望', 'bad', 'error', 'fail']
        
        pos_count = sum(1 for w in positive_words if w in content.lower())
        neg_count = sum(1 for w in negative_words if w in content.lower())
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        return 'neutral'
    
    def _generate_id(self, raw_id: str) -> str:
        """生成处理后的知识ID"""
        import uuid
        return f"proc_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
    
    def _save_processed(self, knowledge: ProcessedKnowledge):
        """保存处理后的知识到文件"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = self.processed_path / f"{date_str}.jsonl"
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(knowledge.to_dict(), ensure_ascii=False) + '\n')
    
    def list_processed(self, 
                       date: Optional[str] = None, 
                       category: Optional[str] = None,
                       limit: int = 100) -> List[ProcessedKnowledge]:
        """
        列出处理后的知识
        
        Args:
            date: 日期过滤
            category: 分类过滤
            limit: 最大返回数量
        """
        results = []
        
        if date:
            files = [self.processed_path / f"{date}.jsonl"]
        else:
            files = sorted(self.processed_path.glob("*.jsonl"), reverse=True)
        
        for file_path in files:
            if not file_path.exists():
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    knowledge = ProcessedKnowledge.from_dict(data)
                    
                    if category and knowledge.category != category:
                        continue
                    
                    results.append(knowledge)
                    if len(results) >= limit:
                        break
        
        return results[:limit]
