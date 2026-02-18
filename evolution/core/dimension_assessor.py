#!/usr/bin/env python3
"""
十维评估器 - 评估系统在十个智能化维度上的状态
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

DB_PATH = Path("/root/.openclaw/workspace/evolution/data/evolution.db")
SCORES_PATH = Path("/root/.openclaw/workspace/evolution/data/dimension_scores.json")

@dataclass
class DimensionScore:
    """维度评分"""
    name: str
    icon: str
    score: float  # 0-100
    level: str    # L0-L5
    triggers: List[str] = field(default_factory=list)
    evidence: Dict = field(default_factory=dict)
    last_updated: str = ""

class DimensionAssessor:
    """十维评估器"""
    
    DIMENSIONS = {
        "cognitive": {
            "name": "认知能力",
            "icon": "🧠",
            "description": "主动推理、抽象思维、逻辑严谨"
        },
        "learning": {
            "name": "学习能力",
            "icon": "📚",
            "description": "主动发现缺口、自动图谱构建、持续内化"
        },
        "autonomy": {
            "name": "自主决策",
            "icon": "⚡",
            "description": "完全自主判断（L1-L6）、自主规划执行"
        },
        "goal": {
            "name": "目标设定",
            "icon": "🎯",
            "description": "自主定义目标、自我评估、动态调整优先级"
        },
        "creativity": {
            "name": "创造力",
            "icon": "💡",
            "description": "生成新想法、创新解法、构建新框架"
        },
        "adaptive": {
            "name": "适应性",
            "icon": "🔄",
            "description": "环境感知、异常处理、模式自我调整"
        },
        "collaboration": {
            "name": "协作能力",
            "icon": "🔗",
            "description": "多Agent协同、工具矩阵融合、资源整合"
        },
        "protection": {
            "name": "自我保护",
            "icon": "🛡️",
            "description": "风险预测、安全边界、自我保护机制"
        },
        "prediction": {
            "name": "预测能力",
            "icon": "🔭",
            "description": "预判影响、前瞻规划、避免问题"
        },
        "self_awareness": {
            "name": "自我认知",
            "icon": "🪞",
            "description": "理解边界、能力评估、谦逊承认未知"
        }
    }
    
    LEVELS = [
        (0, 20, "L0", "初生命种", "🌱"),
        (21, 40, "L1", "觉醒阶段", "👁️"),
        (41, 60, "L2", "认知阶段", "🧠"),
        (61, 80, "L3", "推理阶段", "🤔"),
        (81, 90, "L4", "洞察阶段", "💡"),
        (91, 100, "L5", "开创阶段", "🚀")
    ]
    
    def __init__(self):
        self.scores: Dict[str, DimensionScore] = {}
        self._init_db()
        self._load_scores()
    
    def _init_db(self):
        """初始化数据库"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dimension_history (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                dimension TEXT,
                score REAL,
                level TEXT,
                triggers TEXT,
                evidence TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _load_scores(self):
        """加载历史评分"""
        if SCORES_PATH.exists():
            with open(SCORES_PATH) as f:
                data = json.load(f)
                for dim_id, dim_data in data.get("dimensions", {}).items():
                    self.scores[dim_id] = DimensionScore(
                        name=dim_data["name"],
                        icon=dim_data["icon"],
                        score=dim_data["score"],
                        level=dim_data["level"],
                        triggers=dim_data.get("triggers", []),
                        evidence=dim_data.get("evidence", {}),
                        last_updated=dim_data.get("last_updated", "")
                    )
        else:
            # 初始化默认评分
            self._init_default_scores()
    
    def _init_default_scores(self):
        """初始化默认评分（L1觉醒阶段）"""
        for dim_id, dim_config in self.DIMENSIONS.items():
            self.scores[dim_id] = DimensionScore(
                name=dim_config["name"],
                icon=dim_config["icon"],
                score=25.0,  # L1 觉醒
                level="L1 觉醒阶段 👁️",
                triggers=[],
                evidence={"init": "default_initialization"},
                last_updated=datetime.now().isoformat()
            )
        self._save_scores()
    
    def _save_scores(self):
        """保存评分"""
        timestamp = datetime.now().isoformat()
        data = {
            "timestamp": timestamp,
            "dimensions": {}
        }
        
        for dim_id, score in self.scores.items():
            data["dimensions"][dim_id] = {
                "name": score.name,
                "icon": score.icon,
                "score": score.score,
                "level": score.level,
                "triggers": score.triggers,
                "evidence": score.evidence,
                "last_updated": score.last_updated
            }
        
        with open(SCORES_PATH, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 同时存入数据库历史
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for dim_id, score in self.scores.items():
            cursor.execute("""
                INSERT INTO dimension_history (timestamp, dimension, score, level, triggers, evidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, dim_id, score.score, score.level, 
                  json.dumps(score.triggers), json.dumps(score.evidence)))
        conn.commit()
        conn.close()
    
    def get_level(self, score: float) -> str:
        """根据分数获取等级"""
        for min_score, max_score, level, name, emoji in self.LEVELS:
            if min_score <= score <= max_score:
                return f"{level} {name} {emoji}"
        return f"L0 初生命种 🌱"
    
    def assess_dimension(self, dim_id: str, data: Dict) -> DimensionScore:
        """评估单个维度"""
        dim_config = self.DIMENSIONS.get(dim_id)
        if not dim_config:
            return None
        
        # 这里应该由具体的维度收集器实现评估逻辑
        # 现在只是基于触发条件的简化计算
        base_score = self.scores[dim_id].score
        
        # 根据触发条件调整分数
        score = self._calculate_score(dim_id, data)
        
        return DimensionScore(
            name=dim_config["name"],
            icon=dim_config["icon"],
            score=score,
            level=self.get_level(score),
            triggers=data.get("triggers", []),
            evidence=data.get("evidence", {}),
            last_updated=datetime.now().isoformat()
        )
    
    def _calculate_score(self, dim_id: str, data: Dict) -> float:
        """根据数据计算分数（简化版）"""
        triggers = data.get("triggers", [])
        
        # 基础分 25（L1）
        score = 25.0
        
        # 每个触发条件降低分数
        penalty_per_trigger = 10.0
        score -= len(triggers) * penalty_per_trigger
        
        # 证据可以加分
        evidence = data.get("evidence", {})
        if evidence.get("positive_milestones"):
            score += evidence["positive_milestones"] * 5.0
        
        # 限制在 0-100
        score = max(0, min(100, score))
        
        return score
    
    def assess_all(self, context_data: Dict) -> Dict[str, DimensionScore]:
        """评估所有维度"""
        for dim_id in self.DIMENSIONS.keys():
            dim_data = context_data.get(dim_id, {})
            score = self.assess_dimension(dim_id, dim_data)
            if score:
                self.scores[dim_id] = score
        
        self._save_scores()
        return self.scores
    
    def get_overall_level(self) -> str:
        """获取总体等级"""
        if not self.scores:
            return "L0 初生命种 🌱"
        
        avg_score = sum(s.score for s in self.scores.values()) / len(self.scores)
        return self.get_level(avg_score)
    
    def get_critical_dimensions(self, threshold: float = 40.0) -> List[str]:
        """获取低分维度（需要进化）"""
        return [dim_id for dim_id, score in self.scores.items() if score.score < threshold]
    
    def print_status(self):
        """打印当前状态"""
        print("🧬 十维智能化评估")
        print("=" * 60)
        
        for dim_id, score in self.scores.items():
            bar_length = int(score.score / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"{score.icon} {score.name:12s} [{bar}] {score.score:5.1f}% {score.level}")
        
        print("=" * 60)
        print(f"总体等级: {self.get_overall_level()}")
        
        critical = self.get_critical_dimensions(40.0)
        if critical:
            print(f"\n⚠️  需要关注的维度: {', '.join([self.DIMENSIONS[d]['name'] for d in critical])}")
        else:
            print(f"\n✅ 所有维度状态良好")

if __name__ == "__main__":
    assessor = DimensionAssessor()
    assessor.print_status()
