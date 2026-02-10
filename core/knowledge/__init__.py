"""
统一知识内化系统 - 核心模块
Unified Knowledge Internalization System - Core Module
"""

from .knowledge_collector import KnowledgeCollector
from .knowledge_processor import KnowledgeProcessor
from .knowledge_insight import KnowledgeInsight

__all__ = [
    'KnowledgeCollector',
    'KnowledgeProcessor', 
    'KnowledgeInsight',
]

__version__ = '0.1.0'
