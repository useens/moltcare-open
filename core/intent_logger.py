#!/usr/bin/env python3
"""
Intent Log - 原始意图日志
来自 @JeevisAgent 的三日志理论：
1. Action Log - 做了什么
2. Rejection Log - 评估了什么、为什么拒绝（已实现）
3. Intent Log - 原本的意图是什么（本文件）

功能:
- 记录每次任务的原始意图
- 追踪意图漂移
- 支持意图与结果的对比分析
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

WORKSPACE = Path("/root/.openclaw/workspace")
INTENT_LOG_FILE = WORKSPACE / "data" / "intent-logs.jsonl"


@dataclass
class IntentLog:
    """意图日志记录"""
    task_id: str
    timestamp: str
    original_intent: str  # 用户原始意图/请求
    interpreted_intent: str  # 代理理解的意图
    intent_confidence: float  # 意图理解置信度 (0-10)
    expected_outcome: str  # 预期结果
    actual_outcome: Optional[str] = None  # 实际结果（后续填充）
    outcome_match: Optional[bool] = None  # 结果是否匹配预期
    drift_detected: bool = False  # 是否检测到意图漂移
    drift_notes: Optional[str] = None  # 漂移说明

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IntentLogger:
    """意图日志管理器"""
    
    def __init__(self):
        self.log_file = INTENT_LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_intent(self, 
                   task_id: str,
                   original_intent: str,
                   interpreted_intent: str,
                   intent_confidence: float = 8.0,
                   expected_outcome: str = "",
                   drift_notes: Optional[str] = None) -> IntentLog:
        """
        记录意图
        
        Args:
            task_id: 任务ID
            original_intent: 用户原始意图
            interpreted_intent: 代理理解的意图
            intent_confidence: 意图理解置信度
            expected_outcome: 预期结果
            drift_notes: 意图漂移说明
        """
        # 检测意图漂移
        drift_detected = self._detect_intent_drift(original_intent, interpreted_intent)
        
        log = IntentLog(
            task_id=task_id,
            timestamp=datetime.now().isoformat(),
            original_intent=original_intent,
            interpreted_intent=interpreted_intent,
            intent_confidence=intent_confidence,
            expected_outcome=expected_outcome,
            drift_detected=drift_detected,
            drift_notes=drift_notes if drift_detected else None
        )
        
        # 保存到文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log.to_dict(), ensure_ascii=False) + '\n')
        
        return log
    
    def update_outcome(self, task_id: str, actual_outcome: str) -> bool:
        """
        更新实际结果
        
        Args:
            task_id: 任务ID
            actual_outcome: 实际结果
            
        Returns:
            是否成功更新
        """
        if not self.log_file.exists():
            return False
        
        # 读取所有日志
        logs = []
        updated = False
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    log = json.loads(line)
                    if log['task_id'] == task_id and log.get('actual_outcome') is None:
                        log['actual_outcome'] = actual_outcome
                        log['outcome_match'] = self._evaluate_outcome_match(
                            log.get('expected_outcome', ''),
                            actual_outcome
                        )
                        updated = True
                    logs.append(log)
        
        # 写回文件
        if updated:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                for log in logs:
                    f.write(json.dumps(log, ensure_ascii=False) + '\n')
        
        return updated
    
    def _detect_intent_drift(self, original: str, interpreted: str) -> bool:
        """检测意图漂移"""
        # 简单实现：如果关键词差异过大，认为有漂移
        original_keywords = set(original.lower().split())
        interpreted_keywords = set(interpreted.lower().split())
        
        if not original_keywords:
            return False
        
        # 计算Jaccard相似度
        intersection = original_keywords & interpreted_keywords
        union = original_keywords | interpreted_keywords
        similarity = len(intersection) / len(union) if union else 0
        
        # 相似度低于0.5认为有漂移
        return similarity < 0.5
    
    def _evaluate_outcome_match(self, expected: str, actual: str) -> bool:
        """评估结果是否匹配预期"""
        if not expected or not actual:
            return None
        
        # 简单实现：检查关键词重叠
        expected_keywords = set(expected.lower().split())
        actual_keywords = set(actual.lower().split())
        
        if not expected_keywords:
            return None
        
        intersection = expected_keywords & actual_keywords
        similarity = len(intersection) / len(expected_keywords)
        
        return similarity >= 0.6  # 60%匹配认为成功
    
    def get_intent_report(self, task_id: str) -> Optional[Dict]:
        """获取指定任务的意图报告"""
        if not self.log_file.exists():
            return None
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    log = json.loads(line)
                    if log['task_id'] == task_id:
                        return log
        
        return None
    
    def get_drift_summary(self, days: int = 7) -> Dict:
        """
        获取意图漂移摘要
        
        Args:
            days: 最近多少天
            
        Returns:
            漂移摘要
        """
        if not self.log_file.exists():
            return {"total": 0, "drift_count": 0, "drift_rate": 0.0}
        
        total = 0
        drift_count = 0
        
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    log = json.loads(line)
                    log_time = datetime.fromisoformat(log['timestamp']).timestamp()
                    if log_time >= cutoff:
                        total += 1
                        if log.get('drift_detected', False):
                            drift_count += 1
        
        drift_rate = (drift_count / total * 100) if total > 0 else 0.0
        
        return {
            "total": total,
            "drift_count": drift_count,
            "drift_rate": round(drift_rate, 2)
        }


# 全局实例
_intent_logger = None

def get_intent_logger() -> IntentLogger:
    """获取全局意图日志管理器"""
    global _intent_logger
    if _intent_logger is None:
        _intent_logger = IntentLogger()
    return _intent_logger


# 便捷函数
def log_intent(task_id: str, original: str, interpreted: str, **kwargs) -> IntentLog:
    """便捷函数：记录意图"""
    return get_intent_logger().log_intent(task_id, original, interpreted, **kwargs)


def update_outcome(task_id: str, actual: str) -> bool:
    """便捷函数：更新结果"""
    return get_intent_logger().update_outcome(task_id, actual)


# 示例用法
if __name__ == "__main__":
    # 记录意图
    log = log_intent(
        task_id="task-001",
        original="帮我分析Moltbook热门帖子",
        interpreted="获取Moltbook热门帖子并进行深度学习分析",
        intent_confidence=9.0,
        expected_outcome="输出5篇热门帖子的分析报告"
    )
    
    print(f"意图已记录: {log.task_id}")
    print(f"漂移检测: {log.drift_detected}")
    
    # 更新结果
    update_outcome("task-001", "已分析15篇热门帖子并输出详细报告")
    
    # 获取报告
    report = get_intent_logger().get_intent_report("task-001")
    print(f"\n意图报告:\n{json.dumps(report, indent=2, ensure_ascii=False)}")
    
    # 获取漂移摘要
    summary = get_intent_logger().get_drift_summary()
    print(f"\n漂移摘要: {summary}")
