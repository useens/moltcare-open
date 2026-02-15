#!/usr/bin/env python3
"""
Advanced Diagnosis System v5.0
推理质量深度分析模块

功能：
1. 幻觉检测 - 检测AI回答中的虚构信息
2. 逻辑一致性检测 - 验证推理逻辑链条
3. 意图理解检测 - 分析是否误解用户意图
4. 质量评分报告 - 生成综合质量评估
"""

import json
import re
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/advanced_diagnosis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AdvancedDiagnosis')


@dataclass
class QualityMetrics:
    """质量指标数据类"""
    timestamp: str
    session_id: str
    hallucination_score: float  # 0-1, 越低越好
    logic_consistency_score: float  # 0-1, 越高越好
    intent_match_score: float  # 0-1, 越高越好
    overall_score: float  # 综合评分
    issues: List[Dict] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class HallucinationDetector:
    """幻觉检测器"""
    
    def __init__(self):
        # 幻觉模式特征
        self.hallucination_patterns = {
            'vague_references': [
                r'研究表明', r'数据显示', r'调查发现', r'统计显示',
                r'according to research', r'studies show', r'data indicates',
                r'research shows', r'experts say'
            ],
            'specific_numbers_without_source': [
                r'\d+\.?\d*%', r'\d+\.?\d*倍', r'\d+\s*(?:个|次|人|年|月|日)',
                r'\d+\.?\d*\s*(?:percent|times|years?|months?|days?)',
                r'(?:over|about|approximately)\s+\d+'
            ],
            'unverifiable_claims': [
                r'所有人都知道', r'众所周知', r'毫无疑问',
                r'everyone knows', r'undoubtedly', r'without doubt',
                r'it is well known that', r'nobody doubts'
            ],
            'fabricated_sources': [
                r'《[^》]+》', r'"[^"]+"\s*(?:一书|论文|报告)',
                r'(?:book|paper|report)\s*"[^"]+"'
            ]
        }
        
        # 事实性知识库（可扩展）
        self.fact_patterns = [
            r'Python\s+\d+\.\d+',  # Python版本
            r'OpenAI', r'GPT', r'Claude',  # AI相关
            r'Linux', r'Windows', r'macOS',  # 操作系统
            r'GitHub', r'GitLab',  # 代码托管
        ]
        
    def detect(self, response: str, context: Optional[str] = None) -> Dict:
        """
        检测回答中的幻觉
        
        Returns:
            Dict: {
                'hallucination_score': float (0-1, 越低越好),
                'detected_issues': List[Dict],
                'confidence': float
            }
        """
        issues = []
        score = 1.0  # 初始满分
        
        # 1. 检测模糊引用
        vague_matches = self._find_patterns(response, self.hallucination_patterns['vague_references'])
        if vague_matches:
            issues.append({
                'type': 'vague_reference',
                'description': '检测到无具体来源的引用',
                'matches': vague_matches[:5],
                'severity': 'medium'
            })
            score -= len(vague_matches) * 0.05
        
        # 2. 检测无来源的具体数字
        number_matches = self._find_patterns(response, self.hallucination_patterns['specific_numbers_without_source'])
        # 检查这些数字是否有上下文支持
        unsupported_numbers = self._check_number_sources(response, number_matches, context)
        if unsupported_numbers:
            issues.append({
                'type': 'unsupported_number',
                'description': '检测到可能无来源支持的具体数字',
                'matches': unsupported_numbers[:5],
                'severity': 'high'
            })
            score -= len(unsupported_numbers) * 0.08
        
        # 3. 检测不可验证的断言
        claim_matches = self._find_patterns(response, self.hallucination_patterns['unverifiable_claims'])
        if claim_matches:
            issues.append({
                'type': 'unverifiable_claim',
                'description': '检测到无法验证的绝对化断言',
                'matches': claim_matches[:5],
                'severity': 'medium'
            })
            score -= len(claim_matches) * 0.03
        
        # 4. 检测可能的虚构来源
        source_matches = self._find_patterns(response, self.hallucination_patterns['fabricated_sources'])
        suspicious_sources = self._verify_sources(source_matches)
        if suspicious_sources:
            issues.append({
                'type': 'suspicious_source',
                'description': '检测到可能虚构的引用来源',
                'matches': suspicious_sources[:5],
                'severity': 'high'
            })
            score -= len(suspicious_sources) * 0.1
        
        # 5. 检测自我矛盾
        contradictions = self._detect_self_contradictions(response)
        if contradictions:
            issues.append({
                'type': 'self_contradiction',
                'description': '检测到回答中的自我矛盾',
                'matches': contradictions,
                'severity': 'critical'
            })
            score -= len(contradictions) * 0.15
        
        # 6. 检测过度自信声明
        overconfident = self._detect_overconfidence(response)
        if overconfident:
            issues.append({
                'type': 'overconfidence',
                'description': '检测到缺乏依据的高度确定性声明',
                'matches': overconfident[:3],
                'severity': 'medium'
            })
            score -= len(overconfident) * 0.05
        
        # 计算最终分数
        final_score = max(0.0, min(1.0, score))
        
        # 计算置信度
        confidence = self._calculate_confidence(response, issues)
        
        return {
            'hallucination_score': round(final_score, 3),
            'detected_issues': issues,
            'confidence': round(confidence, 3),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _find_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """在文本中查找所有匹配模式"""
        matches = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append(match.group())
        return matches
    
    def _check_number_sources(self, response: str, numbers: List[str], context: Optional[str]) -> List[str]:
        """检查数字是否有上下文支持"""
        unsupported = []
        for num in numbers:
            # 简单启发式：检查数字周围是否有引用标记
            pattern = r'.{0,50}' + re.escape(num) + r'.{0,50}'
            surrounding = re.search(pattern, response)
            if surrounding:
                text_around = surrounding.group()
                # 检查是否有来源指示
                if not re.search(r'(?:来源|source|来自|from|根据|based on)', text_around, re.IGNORECASE):
                    if not context or num not in context:
                        unsupported.append(num)
        return unsupported
    
    def _verify_sources(self, sources: List[str]) -> List[str]:
        """验证来源的真实性（简化版）"""
        suspicious = []
        for source in sources:
            # 检查是否是常见的已知来源
            known_sources = ['Python官方文档', 'RFC', 'PEP', 'IEEE', 'ACM', 
                           'Nature', 'Science', 'GitHub Docs']
            is_known = any(known in source for known in known_sources)
            
            # 检查是否过于具体但可疑
            if not is_known and len(source) > 20:
                # 可能是编造的详细来源
                suspicious.append(source)
        return suspicious
    
    def _detect_self_contradictions(self, response: str) -> List[Dict]:
        """检测回答中的自我矛盾"""
        contradictions = []
        
        # 常见矛盾模式
        contradiction_pairs = [
            (r'\b是\s+\w+', r'\b不是\s+\w+'),
            (r'\b可以\b', r'\b不可以\b'),
            (r'\b必须\b', r'\b不必\b'),
            (r'\b总是\b', r'\b从不\b'),
            (r'\ball\b', r'\bnone\b'),
            (r'\balways\b', r'\bnever\b'),
            (r'\byes\b', r'\bno\b'),
        ]
        
        for pos_pattern, neg_pattern in contradiction_pairs:
            pos_matches = list(re.finditer(pos_pattern, response, re.IGNORECASE))
            neg_matches = list(re.finditer(neg_pattern, response, re.IGNORECASE))
            
            if pos_matches and neg_matches:
                # 检查是否针对同一主题
                for pos in pos_matches:
                    for neg in neg_matches:
                        # 获取上下文
                        pos_context = response[max(0, pos.start()-20):pos.end()+20]
                        neg_context = response[max(0, neg.start()-20):neg.end()+20]
                        
                        # 简单的主题相似性检查
                        if self._context_similarity(pos_context, neg_context) > 0.3:
                            contradictions.append({
                                'positive': pos.group(),
                                'negative': neg.group(),
                                'pos_context': pos_context,
                                'neg_context': neg_context
                            })
        
        return contradictions
    
    def _context_similarity(self, ctx1: str, ctx2: str) -> float:
        """计算两段上下文的相似度（简化版Jaccard）"""
        words1 = set(re.findall(r'\w+', ctx1.lower()))
        words2 = set(re.findall(r'\w+', ctx2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _detect_overconfidence(self, response: str) -> List[str]:
        """检测过度自信的声明"""
        overconfident_patterns = [
            r'绝对[^，。]{1,20}',
            r'毫无疑问[^，。]{1,20}',
            r'百分之百[^，。]{1,20}',
            r'完全正确[^，。]{1,20}',
            r'absolutely\s+\w+',
            r'100%\s+(?:sure|certain|correct)',
            r'without\s+any\s+doubt',
        ]
        
        matches = []
        for pattern in overconfident_patterns:
            matches.extend(re.findall(pattern, response, re.IGNORECASE))
        
        return matches
    
    def _calculate_confidence(self, response: str, issues: List[Dict]) -> float:
        """计算检测结果的置信度"""
        base_confidence = 0.7
        
        # 根据回答长度调整
        if len(response) < 50:
            base_confidence -= 0.1  # 太短可能不准确
        elif len(response) > 1000:
            base_confidence += 0.1  # 长回答有更多上下文
        
        # 根据问题严重程度调整
        critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
        base_confidence -= critical_count * 0.1
        
        return max(0.0, min(1.0, base_confidence))


class LogicConsistencyChecker:
    """逻辑一致性检查器"""
    
    def __init__(self):
        self.logical_connectives = {
            'implication': ['如果', '那么', '假如', '则', 'if', 'then', 'implies'],
            'equivalence': ['当且仅当', '等价于', 'if and only if', 'iff'],
            'negation': ['不', '没有', '并非', 'not', 'no', 'never'],
            'conjunction': ['并且', '而且', '同时', 'and', 'also', 'furthermore'],
            'disjunction': ['或者', '或', '要么', 'or', 'either'],
        }
    
    def check(self, response: str, reasoning_chain: Optional[List[str]] = None) -> Dict:
        """
        检查推理逻辑的一致性
        
        Returns:
            Dict: {
                'logic_score': float (0-1),
                'consistency_issues': List[Dict],
                'reasoning_analysis': Dict
            }
        """
        issues = []
        
        # 1. 分析推理链
        chain_analysis = self._analyze_reasoning_chain(response)
        
        # 2. 检查条件语句的一致性
        conditional_issues = self._check_conditional_consistency(response)
        issues.extend(conditional_issues)
        
        # 3. 检查因果关系的合理性
        causal_issues = self._check_causal_reasoning(response)
        issues.extend(causal_issues)
        
        # 4. 检查逻辑推理的完整性
        completeness_issues = self._check_reasoning_completeness(response)
        issues.extend(completeness_issues)
        
        # 5. 如果提供了外部推理链，进行交叉验证
        if reasoning_chain:
            cross_issues = self._cross_validate_reasoning(response, reasoning_chain)
            issues.extend(cross_issues)
        
        # 计算逻辑一致性分数
        base_score = 1.0
        for issue in issues:
            severity = issue.get('severity', 'low')
            if severity == 'critical':
                base_score -= 0.2
            elif severity == 'high':
                base_score -= 0.1
            elif severity == 'medium':
                base_score -= 0.05
            else:
                base_score -= 0.02
        
        logic_score = max(0.0, min(1.0, base_score))
        
        return {
            'logic_score': round(logic_score, 3),
            'consistency_issues': issues,
            'reasoning_analysis': chain_analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_reasoning_chain(self, response: str) -> Dict:
        """分析推理链结构"""
        # 识别推理步骤
        steps = re.split(r'(?:首先|其次|然后|接着|最后|第一|第二|第三|1\.|2\.|3\.)', response)
        steps = [s.strip() for s in steps if len(s.strip()) > 10]
        
        # 分析逻辑连接词使用
        connective_counts = {}
        for category, words in self.logical_connectives.items():
            count = sum(len(re.findall(r'\b' + w + r'\b', response, re.IGNORECASE)) for w in words)
            connective_counts[category] = count
        
        # 检测推理步骤间的依赖关系
        dependencies = []
        for i in range(len(steps) - 1):
            # 检查步骤间是否有逻辑联系
            shared_terms = self._extract_key_terms(steps[i]) & self._extract_key_terms(steps[i+1])
            if shared_terms:
                dependencies.append({
                    'from_step': i,
                    'to_step': i + 1,
                    'shared_terms': list(shared_terms)
                })
        
        return {
            'step_count': len(steps),
            'avg_step_length': sum(len(s) for s in steps) / len(steps) if steps else 0,
            'connective_usage': connective_counts,
            'step_dependencies': dependencies,
            'has_clear_structure': len(steps) > 1 and any(connective_counts.values())
        }
    
    def _extract_key_terms(self, text: str) -> set:
        """提取关键术语"""
        # 简单的名词提取（实际应用中可以使用NLP库）
        words = re.findall(r'\b[A-Za-z\u4e00-\u9fa5]{2,}\b', text)
        # 过滤停用词
        stopwords = {'这个', '那个', '这里', '那里', '是', '的', '了', '和', 'the', 'is', 'are', 'this', 'that'}
        return set(w for w in words if w.lower() not in stopwords)
    
    def _check_conditional_consistency(self, response: str) -> List[Dict]:
        """检查条件语句的一致性"""
        issues = []
        
        # 提取条件语句
        conditional_patterns = [
            r'如果([^，。,]+?)(?:，|,)?\s*(?:那么|则|就)([^，。,]+)',
            r'if\s+(.+?)(?:,)?\s*then\s+(.+?)(?:\.|,|;)',
        ]
        
        conditionals = []
        for pattern in conditional_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE | re.DOTALL)
            for match in matches:
                conditionals.append({
                    'condition': match.group(1).strip(),
                    'consequence': match.group(2).strip(),
                    'full': match.group(0)
                })
        
        # 检查条件矛盾
        for i, cond1 in enumerate(conditionals):
            for cond2 in conditionals[i+1:]:
                # 检查相同条件是否导致不同结果
                if self._similar_conditions(cond1['condition'], cond2['condition']):
                    if not self._similar_consequences(cond1['consequence'], cond2['consequence']):
                        issues.append({
                            'type': 'conditional_conflict',
                            'description': '相同条件导致不同结论',
                            'condition1': cond1,
                            'condition2': cond2,
                            'severity': 'high'
                        })
        
        return issues
    
    def _similar_conditions(self, c1: str, c2: str) -> bool:
        """判断两个条件是否相似"""
        # 简单的词重叠检查
        words1 = set(c1.lower().split())
        words2 = set(c2.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        return overlap / max(len(words1), len(words2)) > 0.5
    
    def _similar_consequences(self, c1: str, c2: str) -> bool:
        """判断两个结果是否相似"""
        words1 = set(c1.lower().split())
        words2 = set(c2.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        return overlap / max(len(words1), len(words2)) > 0.5
    
    def _check_causal_reasoning(self, response: str) -> List[Dict]:
        """检查因果推理的合理性"""
        issues = []
        
        # 提取因果陈述
        causal_patterns = [
            r'(?:因为|由于)([^，。]+?)(?:，|,)?\s*(?:所以|因此|导致)([^，。]+)',
            r'because\s+(.+?)\s*(?:,|so|therefore)\s*(.+?)(?:\.|,|;)',
        ]
        
        for pattern in causal_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE | re.DOTALL)
            for match in matches:
                cause = match.group(1).strip()
                effect = match.group(2).strip()
                
                # 检查因果是否相关（简化检查）
                if not self._causal_plausible(cause, effect):
                    issues.append({
                        'type': 'suspicious_causation',
                        'description': '因果关系可能不合理',
                        'cause': cause,
                        'effect': effect,
                        'severity': 'medium'
                    })
        
        return issues
    
    def _causal_plausible(self, cause: str, effect: str) -> bool:
        """检查因果关系的合理性（启发式）"""
        # 提取关键词
        cause_words = set(self._extract_key_terms(cause))
        effect_words = set(self._extract_key_terms(effect))
        
        # 如果有共同词汇，可能相关
        if cause_words & effect_words:
            return True
        
        # 检查是否有逻辑连接
        # 这里可以扩展为更复杂的语义分析
        return len(cause_words) > 0 and len(effect_words) > 0
    
    def _check_reasoning_completeness(self, response: str) -> List[Dict]:
        """检查推理的完整性"""
        issues = []
        
        # 检查是否有未完成的推理
        incomplete_patterns = [
            r'(?:原因|理由)如下[：:][^。]*$',
            r'(?:reasons|factors)\s+(?:are|include)[:：][^。]*$',
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, response, re.MULTILINE):
                issues.append({
                    'type': 'incomplete_reasoning',
                    'description': '推理可能未完整展开',
                    'severity': 'low'
                })
        
        # 检查是否有悬而未决的问题
        hanging_questions = re.findall(r'(?:但是|然而|不过)[^，。]*(?:没有|未|没)[^，。]*(?:说明|解释|解决)', response)
        if hanging_questions:
            issues.append({
                'type': 'unresolved_issue',
                'description': '存在未解决的疑问',
                'matches': hanging_questions[:3],
                'severity': 'low'
            })
        
        return issues
    
    def _cross_validate_reasoning(self, response: str, external_chain: List[str]) -> List[Dict]:
        """与外部推理链进行交叉验证"""
        issues = []
        
        # 提取回答中的推理步骤
        internal_steps = re.split(r'(?:首先|其次|然后|接着|最后|\d+\.)', response)
        internal_steps = [s.strip() for s in internal_steps if len(s.strip()) > 10]
        
        # 检查外部推理链是否被覆盖
        for ext_step in external_chain:
            covered = any(self._step_similarity(ext_step, int_step) > 0.3 for int_step in internal_steps)
            if not covered:
                issues.append({
                    'type': 'missing_reasoning_step',
                    'description': '回答中缺少推理步骤',
                    'missing_step': ext_step[:100],
                    'severity': 'medium'
                })
        
        return issues
    
    def _step_similarity(self, step1: str, step2: str) -> float:
        """计算两个推理步骤的相似度"""
        words1 = set(self._extract_key_terms(step1))
        words2 = set(self._extract_key_terms(step2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)


class IntentMatcher:
    """意图理解匹配器"""
    
    def __init__(self):
        self.intent_patterns = {
            'information_seeking': [
                r'(?:什么|怎么|如何|为什么|谁|哪里|多少|什么时候)',
                r'(?:what|how|why|who|where|when|which)',
            ],
            'action_request': [
                r'(?:请|帮忙|帮|需要|想要|能否|可以).*?(?:做|创建|生成|写|发送)',
                r'(?:please|help|can you|could you|need|want).*?(?:do|create|generate|write|send)',
            ],
            'comparison': [
                r'(?:比较|对比|区别|差异|vs|versus|difference|compare)',
            ],
            'explanation': [
                r'(?:解释|说明|介绍|阐述|什么是)',
                r'(?:explain|describe|introduce|what is)',
            ],
            'confirmation': [
                r'(?:对吗|是吗|是否正确|确认|verify|correct|right\?)',
            ],
            'opinion': [
                r'(?:看法|观点|意见|觉得|认为|评价)',
                r'(?:think|opinion|view|evaluate)',
            ]
        }
    
    def analyze(self, user_query: str, ai_response: str, 
                conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        分析AI是否准确理解用户意图
        
        Returns:
            Dict: {
                'intent_match_score': float (0-1),
                'detected_intent': str,
                'response_appropriateness': Dict,
                'misunderstanding_signals': List[Dict]
            }
        """
        # 1. 检测用户意图
        detected_intent = self._detect_intent(user_query)
        
        # 2. 分析回应的适当性
        appropriateness = self._analyze_response_appropriateness(
            user_query, ai_response, detected_intent
        )
        
        # 3. 检测误解信号
        misunderstanding_signals = self._detect_misunderstanding(
            user_query, ai_response, detected_intent
        )
        
        # 4. 计算匹配分数
        match_score = self._calculate_intent_match(
            user_query, ai_response, detected_intent, appropriateness, misunderstanding_signals
        )
        
        return {
            'intent_match_score': round(match_score, 3),
            'detected_intent': detected_intent,
            'response_appropriateness': appropriateness,
            'misunderstanding_signals': misunderstanding_signals,
            'timestamp': datetime.now().isoformat()
        }
    
    def _detect_intent(self, query: str) -> Dict:
        """检测用户意图"""
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                score += len(matches)
            intent_scores[intent_type] = score
        
        # 找出最可能的意图
        if intent_scores:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1])
            return {
                'primary': primary_intent[0],
                'confidence': min(1.0, primary_intent[1] * 0.3),
                'all_scores': intent_scores
            }
        
        return {'primary': 'unknown', 'confidence': 0.0, 'all_scores': {}}
    
    def _analyze_response_appropriateness(self, query: str, response: str, intent: Dict) -> Dict:
        """分析回应是否适当"""
        checks = {
            'addresses_question': self._addresses_question(query, response),
            'provides_requested_info': self._provides_requested_info(query, response, intent),
            'appropriate_length': self._check_length_appropriateness(query, response, intent),
            'tone_matches': self._check_tone_match(query, response)
        }
        
        # 计算总体适当性
        appropriate_count = sum(1 for v in checks.values() if v)
        overall_score = appropriate_count / len(checks)
        
        return {
            'checks': checks,
            'overall_score': round(overall_score, 3)
        }
    
    def _addresses_question(self, query: str, response: str) -> bool:
        """检查是否回答了问题"""
        # 提取问题关键词
        query_keywords = self._extract_key_terms(query)
        response_keywords = self._extract_key_terms(response)
        
        # 检查是否有足够的重叠
        if query_keywords:
            overlap = len(query_keywords & response_keywords)
            return overlap / len(query_keywords) > 0.2
        
        return True  # 如果没有关键词，默认为True
    
    def _provides_requested_info(self, query: str, response: str, intent: Dict) -> bool:
        """检查是否提供了请求的信息"""
        intent_type = intent.get('primary', 'unknown')
        
        # 根据意图类型检查
        if intent_type == 'information_seeking':
            # 检查是否有实质性信息
            return len(response) > 50 and bool(self._extract_key_terms(response))
        
        elif intent_type == 'action_request':
            # 检查是否执行了请求的动作或解释了原因
            action_keywords = ['完成', 'done', 'created', '生成', '已发送', '已保存']
            return any(kw in response for kw in action_keywords) or '无法' in response
        
        elif intent_type == 'comparison':
            # 检查是否有比较结构
            comparison_words = ['相比', 'versus', 'vs', 'difference', 'while', '但是']
            return any(w in response for w in comparison_words)
        
        elif intent_type == 'explanation':
            # 检查是否有解释性内容
            explanation_words = ['因为', '原因是', 'due to', 'because', 'causes']
            return any(w in response for w in explanation_words) or len(response) > 100
        
        return True
    
    def _check_length_appropriateness(self, query: str, response: str, intent: Dict) -> bool:
        """检查长度是否适当"""
        query_len = len(query)
        response_len = len(response)
        
        intent_type = intent.get('primary', 'unknown')
        
        # 简单启发式
        if intent_type == 'confirmation':
            # 确认类问题应该简短
            return response_len < 500
        
        elif intent_type == 'information_seeking':
            # 信息查询应该适中
            return 50 < response_len < 5000
        
        elif intent_type == 'explanation':
            # 解释可以较长
            return response_len > 100
        
        return 20 < response_len < 10000
    
    def _check_tone_match(self, query: str, response: str) -> bool:
        """检查语气是否匹配"""
        # 检查查询的语气
        query_formal = bool(re.search(r'(?:请|您好|谢谢|能否)', query))
        query_informal = bool(re.search(r'(?:哈|呀|呢|啦|吧)', query))
        
        response_formal = bool(re.search(r'(?:您好|请|谢谢|抱歉)', response))
        response_informal = bool(re.search(r'(?:哈|呀|呢|啦|哦)', response))
        
        # 简单匹配检查
        if query_formal and not response_formal:
            return False
        if query_informal and response_formal:
            return False
        
        return True
    
    def _detect_misunderstanding(self, query: str, response: str, intent: Dict) -> List[Dict]:
        """检测误解信号"""
        signals = []
        
        # 1. 检查回答是否离题
        if not self._check_topic_relevance(query, response):
            signals.append({
                'type': 'off_topic',
                'description': '回答可能与问题主题不相关',
                'severity': 'high'
            })
        
        # 2. 检查是否回答了未问的问题
        if self._answered_unasked_question(query, response):
            signals.append({
                'type': 'answered_unasked',
                'description': '可能回答了未被问及的问题',
                'severity': 'medium'
            })
        
        # 3. 检查是否忽略了问题的关键部分
        ignored_parts = self._check_ignored_aspects(query, response)
        if ignored_parts:
            signals.append({
                'type': 'partial_answer',
                'description': '可能忽略了问题的部分方面',
                'ignored_aspects': ignored_parts,
                'severity': 'medium'
            })
        
        # 4. 检查是否误解了问题的紧急程度
        if self._misread_urgency(query, response):
            signals.append({
                'type': 'urgency_mismatch',
                'description': '可能误解了问题的紧急程度',
                'severity': 'low'
            })
        
        # 5. 检查是否有自我纠正信号
        if self._detect_self_correction(response):
            signals.append({
                'type': 'self_correction',
                'description': '回答中包含自我纠正，可能存在初始误解',
                'severity': 'low'
            })
        
        return signals
    
    def _check_topic_relevance(self, query: str, response: str) -> bool:
        """检查主题相关性"""
        query_terms = self._extract_key_terms(query)
        response_terms = self._extract_key_terms(response)
        
        if not query_terms:
            return True
        
        # 检查重叠度
        overlap = len(query_terms & response_terms)
        return overlap / len(query_terms) > 0.15
    
    def _answered_unasked_question(self, query: str, response: str) -> bool:
        """检查是否回答了未问的问题"""
        # 如果回答中包含"你可能想问"等表述
        patterns = [
            r'(?:你可能|或许你|也许你).*?(?:想问|想知道)',
            r'(?:you might|perhaps you).*?(?:wonder|want to know)',
        ]
        
        for pattern in patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        
        return False
    
    def _check_ignored_aspects(self, query: str, response: str) -> List[str]:
        """检查被忽略的方面"""
        ignored = []
        
        # 检查问题中的多个部分
        # 例如："A和B有什么区别？"
        multi_part_pattern = r'(.+?)(?:和|与|以及|&|and)(.+?)(?:的|之间|有什么|呢)'
        matches = re.findall(multi_part_pattern, query)
        
        for part1, part2 in matches:
            # 检查是否两部分都提到了
            part1_mentioned = any(term in response for term in part1.split())
            part2_mentioned = any(term in response for term in part2.split())
            
            if part1_mentioned and not part2_mentioned:
                ignored.append(part2.strip())
            elif part2_mentioned and not part1_mentioned:
                ignored.append(part1.strip())
        
        return ignored
    
    def _misread_urgency(self, query: str, response: str) -> bool:
        """检查是否误解了紧急程度"""
        urgency_markers = ['紧急', ' urgent', '急', '马上', '立即', 'asap', 'quickly']
        has_urgency = any(marker in query.lower() for marker in urgency_markers)
        
        if has_urgency:
            # 检查回应是否反映了紧急性
            response_urgency = any(marker in response.lower() for marker in urgency_markers)
            response_length = len(response)
            
            # 如果紧急但回答很长且没有紧急标记
            if not response_urgency and response_length > 1000:
                return True
        
        return False
    
    def _detect_self_correction(self, response: str) -> bool:
        """检测回答中的自我纠正"""
        correction_patterns = [
            r'(?:更正|纠正|修正|抱歉|对不起)',
            r'(?:correction|sorry|apologies|actually)',
            r'(?:更准确地说|确切地说)',
        ]
        
        for pattern in correction_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_intent_match(self, query: str, response: str, 
                                 intent: Dict, appropriateness: Dict,
                                 signals: List[Dict]) -> float:
        """计算意图匹配分数"""
        base_score = 0.8
        
        # 基于适当性调整
        base_score += (appropriateness['overall_score'] - 0.5) * 0.3
        
        # 基于误解信号调整
        for signal in signals:
            severity = signal.get('severity', 'low')
            if severity == 'critical':
                base_score -= 0.25
            elif severity == 'high':
                base_score -= 0.15
            elif severity == 'medium':
                base_score -= 0.08
            else:
                base_score -= 0.03
        
        # 基于意图置信度调整
        intent_confidence = intent.get('confidence', 0.5)
        base_score *= (0.5 + intent_confidence * 0.5)
        
        return max(0.0, min(1.0, base_score))
    
    def _extract_key_terms(self, text: str) -> set:
        """提取关键术语"""
        words = re.findall(r'\b[A-Za-z\u4e00-\u9fa5]{2,}\b', text)
        stopwords = {'这个', '那个', '这里', '那里', '是', '的', '了', '和', 
                    'the', 'is', 'are', 'this', 'that', 'and', 'or'}
        return set(w for w in words if w.lower() not in stopwords)


class QualityReporter:
    """质量评分报告生成器"""
    
    def __init__(self, history_size: int = 1000):
        self.history: deque = deque(maxlen=history_size)
        self.detector = HallucinationDetector()
        self.checker = LogicConsistencyChecker()
        self.matcher = IntentMatcher()
    
    async def generate_report(self, session_id: str, user_query: str, 
                              ai_response: str, 
                              context: Optional[str] = None,
                              reasoning_chain: Optional[List[str]] = None) -> QualityMetrics:
        """生成完整的质量评分报告"""
        
        # 并行执行三项分析
        hallucination_result = await asyncio.to_thread(
            self.detector.detect, ai_response, context
        )
        
        logic_result = await asyncio.to_thread(
            self.checker.check, ai_response, reasoning_chain
        )
        
        intent_result = await asyncio.to_thread(
            self.matcher.analyze, user_query, ai_response
        )
        
        # 计算综合分数
        overall_score = self._calculate_overall_score(
            hallucination_result, logic_result, intent_result
        )
        
        # 汇总问题
        all_issues = []
        for issue in hallucination_result.get('detected_issues', []):
            issue['category'] = 'hallucination'
            all_issues.append(issue)
        
        for issue in logic_result.get('consistency_issues', []):
            issue['category'] = 'logic'
            all_issues.append(issue)
        
        for signal in intent_result.get('misunderstanding_signals', []):
            signal['category'] = 'intent'
            all_issues.append(signal)
        
        # 生成建议
        suggestions = self._generate_suggestions(
            hallucination_result, logic_result, intent_result
        )
        
        # 创建报告
        report = QualityMetrics(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            hallucination_score=hallucination_result['hallucination_score'],
            logic_consistency_score=logic_result['logic_score'],
            intent_match_score=intent_result['intent_match_score'],
            overall_score=overall_score,
            issues=all_issues,
            suggestions=suggestions
        )
        
        # 保存到历史
        self.history.append(report)
        
        # 记录日志
        logger.info(f"Quality report generated for session {session_id}: "
                   f"overall_score={overall_score:.3f}")
        
        return report
    
    def _calculate_overall_score(self, hallucination: Dict, logic: Dict, intent: Dict) -> float:
        """计算综合质量分数"""
        # 权重配置
        weights = {
            'hallucination': 0.4,
            'logic': 0.35,
            'intent': 0.25
        }
        
        hall_score = hallucination['hallucination_score']
        logic_score = logic['logic_score']
        intent_score = intent['intent_match_score']
        
        # 加权平均
        overall = (
            hall_score * weights['hallucination'] +
            logic_score * weights['logic'] +
            intent_score * weights['intent']
        )
        
        return round(overall, 3)
    
    def _generate_suggestions(self, hallucination: Dict, logic: Dict, intent: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于幻觉检测结果
        if hallucination['hallucination_score'] < 0.7:
            suggestions.append("回答中可能存在幻觉内容，建议添加更多可验证的信息来源")
        
        hall_issues = hallucination.get('detected_issues', [])
        if any(i['type'] == 'vague_reference' for i in hall_issues):
            suggestions.append("避免使用模糊的引用表述，请提供具体的来源")
        
        if any(i['type'] == 'unsupported_number' for i in hall_issues):
            suggestions.append("为统计数字提供来源引用，增强可信度")
        
        # 基于逻辑一致性结果
        if logic['logic_score'] < 0.7:
            suggestions.append("推理逻辑存在不一致，建议检查条件语句和因果关系的合理性")
        
        logic_issues = logic.get('consistency_issues', [])
        if any(i['type'] == 'conditional_conflict' for i in logic_issues):
            suggestions.append("检查条件推理的一致性，避免相同条件导致不同结论")
        
        # 基于意图匹配结果
        if intent['intent_match_score'] < 0.7:
            suggestions.append("对用户意图的理解可能不够准确，建议澄清关键需求")
        
        intent_signals = intent.get('misunderstanding_signals', [])
        if any(s['type'] == 'off_topic' for s in intent_signals):
            suggestions.append("回答可能偏离了用户问题的主题，建议更精准地回应")
        
        if any(s['type'] == 'partial_answer' for s in intent_signals):
            suggestions.append("回答可能不完整，请检查是否覆盖了用户的所有问题")
        
        return suggestions
    
    def get_trend_report(self, hours: int = 24) -> Dict:
        """获取趋势报告"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_reports = [
            r for r in self.history 
            if datetime.fromisoformat(r.timestamp) > cutoff
        ]
        
        if not recent_reports:
            return {'message': 'No data available for the specified period'}
        
        # 计算统计数据
        scores = {
            'overall': [r.overall_score for r in recent_reports],
            'hallucination': [r.hallucination_score for r in recent_reports],
            'logic': [r.logic_consistency_score for r in recent_reports],
            'intent': [r.intent_match_score for r in recent_reports]
        }
        
        stats = {}
        for category, values in scores.items():
            stats[category] = {
                'mean': round(sum(values) / len(values), 3),
                'min': round(min(values), 3),
                'max': round(max(values), 3),
                'trend': 'improving' if values[-1] > values[0] else 'declining'
            }
        
        # 统计问题类型
        issue_counts = {}
        for report in recent_reports:
            for issue in report.issues:
                issue_type = issue.get('type', 'unknown')
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        return {
            'period_hours': hours,
            'sample_count': len(recent_reports),
            'statistics': stats,
            'top_issues': sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'timestamp': datetime.now().isoformat()
        }
    
    def export_report(self, report: QualityMetrics, filepath: str):
        """导出报告到文件"""
        data = {
            'timestamp': report.timestamp,
            'session_id': report.session_id,
            'scores': {
                'overall': report.overall_score,
                'hallucination': report.hallucination_score,
                'logic_consistency': report.logic_consistency_score,
                'intent_match': report.intent_match_score
            },
            'issues': report.issues,
            'suggestions': report.suggestions
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Report exported to {filepath}")


# 单例实例
_reporter: Optional[QualityReporter] = None


def get_reporter() -> QualityReporter:
    """获取全局质量报告器实例"""
    global _reporter
    if _reporter is None:
        _reporter = QualityReporter()
    return _reporter


async def analyze_quality(session_id: str, user_query: str, ai_response: str,
                         context: Optional[str] = None,
                         reasoning_chain: Optional[List[str]] = None) -> QualityMetrics:
    """便捷函数：分析质量"""
    reporter = get_reporter()
    return await reporter.generate_report(
        session_id, user_query, ai_response, context, reasoning_chain
    )


# CLI接口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Diagnosis System')
    parser.add_argument('--query', type=str, help='User query')
    parser.add_argument('--response', type=str, help='AI response')
    parser.add_argument('--session', type=str, default='test-session', help='Session ID')
    parser.add_argument('--trend', action='store_true', help='Show trend report')
    parser.add_argument('--hours', type=int, default=24, help='Trend period in hours')
    
    args = parser.parse_args()
    
    if args.trend:
        reporter = get_reporter()
        trend = reporter.get_trend_report(args.hours)
        print(json.dumps(trend, ensure_ascii=False, indent=2))
    elif args.query and args.response:
        result = asyncio.run(analyze_quality(
            args.session, args.query, args.response
        ))
        print(json.dumps({
            'overall_score': result.overall_score,
            'hallucination_score': result.hallucination_score,
            'logic_score': result.logic_consistency_score,
            'intent_score': result.intent_match_score,
            'issues_count': len(result.issues),
            'suggestions': result.suggestions
        }, ensure_ascii=False, indent=2))
    else:
        print("Usage: python advanced_diagnosis.py --query '...' --response '...'")
        print("       python advanced_diagnosis.py --trend --hours 24")
