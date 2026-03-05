#!/usr/bin/env python3
"""
Command Center - Task Router (Delegation System)
智能任务路由系统 - 什么任务交给小弟，什么自己处理

策略:
- 小弟处理: 简单、重复、标准化、可并行的任务
- 自己处理: 复杂决策、关键判断、需要深度思考的任务
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class TaskComplexity(Enum):
    SIMPLE = "simple"       # 简单 -> 给小弟
    MODERATE = "moderate"   # 中等 -> 视情况
    COMPLEX = "complex"     # 复杂 -> 自己处理

class TaskType(Enum):
    # 给小弟的任务
    DATA_COLLECTION = "data_collection"     # 数据收集
    CODE_EXECUTION = "code_execution"       # 代码执行/测试
    CONTENT_GENERATION = "content_generation" # 内容生成
    MONITORING = "monitoring"               # 监控检查
    BATCH_PROCESSING = "batch_processing"   # 批处理
    
    # 自己处理的任务
    DECISION_MAKING = "decision_making"     # 决策判断
    STRATEGY_PLANNING = "strategy_planning" # 策略规划
    CRITICAL_ANALYSIS = "critical_analysis" # 关键分析
    USER_INTERACTION = "user_interaction"   # 用户交互
    SYSTEM_DESIGN = "system_design"         # 系统设计

@dataclass
class TaskRouter:
    """任务路由器"""
    
    # 给小弟的任务关键词
    DELEGATE_KEYWORDS = {
        "fetch", "get", "collect", "scrape", "download",  # 数据收集
        "test", "run", "execute", "check", "verify",       # 执行检查
        "generate", "create", "write", "draft",            # 内容生成
        "monitor", "watch", "track", "poll",               # 监控
        "batch", "bulk", "mass", "parallel",               # 批处理
        "simple", "basic", "standard", "routine",          # 常规任务
    }
    
    # 自己处理的任务关键词
    RETAIN_KEYWORDS = {
        "decide", "decision", "choose", "select",          # 决策
        "strategy", "plan", "design", "architecture",      # 规划设计
        "analyze", "analysis", "evaluate", "assess",       # 深度分析
        "why", "how to", "should we", "recommend",         # 建议判断
        "critical", "important", "key", "crucial",         # 关键任务
        "review", "approve", "confirm", "validate",        # 审核确认
        "optimize", "improve", "refactor", "redesign",     # 优化重构
    }
    
    # 需要多视角的任务 (给自己，触发Multi-Agent)
    MULTI_AGENT_TRIGGERS = [
        "对比", "比较", "选择", "权衡",
        "设计", "架构", "策略",
        "评估", "推荐",
    ]
    
    def analyze_task(self, prompt: str) -> Tuple[TaskType, TaskComplexity, float]:
        """
        分析任务，决定交给谁处理
        
        返回: (任务类型, 复杂度, 给自己处理的置信度 0-1)
        """
        prompt_lower = prompt.lower()
        
        # 1. 检查是否是多视角决策任务 (强制给自己)
        for trigger in self.MULTI_AGENT_TRIGGERS:
            if trigger in prompt:
                return TaskType.DECISION_MAKING, TaskComplexity.COMPLEX, 0.95
        
        # 2. 计算关键词匹配
        delegate_score = sum(1 for kw in self.DELEGATE_KEYWORDS if kw in prompt_lower)
        retain_score = sum(1 for kw in self.RETAIN_KEYWORDS if kw in prompt_lower)
        
        # 3. 任务长度判断 (长任务通常更复杂)
        length_factor = min(len(prompt) / 500, 1.0)  # 500字符以上视为复杂
        
        # 4. 特定模式识别
        
        # 数据收集类
        if any(kw in prompt_lower for kw in ["fetch", "collect", "scrape", "download", "get data"]):
            return TaskType.DATA_COLLECTION, TaskComplexity.SIMPLE, 0.1
        
        # 代码执行类
        if any(kw in prompt_lower for kw in ["test", "run", "execute", "check status"]):
            return TaskType.CODE_EXECUTION, TaskComplexity.SIMPLE, 0.15
        
        # 内容生成类
        if any(kw in prompt_lower for kw in ["generate", "create", "write", "draft"]):
            return TaskType.CONTENT_GENERATION, TaskComplexity.MODERATE, 0.3
        
        # 监控类
        if any(kw in prompt_lower for kw in ["monitor", "watch", "check health"]):
            return TaskType.MONITORING, TaskComplexity.SIMPLE, 0.1
        
        # 批处理类
        if any(kw in prompt_lower for kw in ["batch", "bulk", "process all"]):
            return TaskType.BATCH_PROCESSING, TaskComplexity.SIMPLE, 0.2
        
        # 决策类
        if any(kw in prompt_lower for kw in ["decide", "choose", "should we", "recommend"]):
            return TaskType.DECISION_MAKING, TaskComplexity.COMPLEX, 0.9
        
        # 策略规划类
        if any(kw in prompt_lower for kw in ["plan", "strategy", "design", "architecture"]):
            return TaskType.STRATEGY_PLANNING, TaskComplexity.COMPLEX, 0.85
        
        # 深度分析类
        if any(kw in prompt_lower for kw in ["analyze", "evaluate", "assess", "review"]):
            return TaskType.CRITICAL_ANALYSIS, TaskComplexity.COMPLEX, 0.8
        
        # 5. 基于关键词得分判断
        total_score = delegate_score + retain_score
        if total_score == 0:
            # 无明显关键词，根据长度判断
            if length_factor > 0.7:
                return TaskType.USER_INTERACTION, TaskComplexity.MODERATE, 0.6
            else:
                return TaskType.CONTENT_GENERATION, TaskComplexity.SIMPLE, 0.3
        
        # 计算给自己处理的概率
        retain_prob = retain_score / total_score if total_score > 0 else 0.5
        retain_prob = retain_prob * 0.7 + length_factor * 0.3  # 结合长度因素
        
        # 判断复杂度
        if retain_prob > 0.7:
            complexity = TaskComplexity.COMPLEX
        elif retain_prob > 0.4:
            complexity = TaskComplexity.MODERATE
        else:
            complexity = TaskComplexity.SIMPLE
        
        # 判断任务类型
        if retain_prob > 0.7:
            task_type = TaskType.CRITICAL_ANALYSIS
        elif retain_prob > 0.4:
            task_type = TaskType.CONTENT_GENERATION
        else:
            task_type = TaskType.BATCH_PROCESSING
        
        return task_type, complexity, retain_prob
    
    def route_task(self, prompt: str, user_context: Optional[Dict] = None) -> Dict:
        """
        路由任务，返回处理建议
        
        Returns:
            {
                "action": "delegate" | "retain",
                "handler": str,  # 如果delegate，指定哪个/哪些节点
                "reason": str,
                "task_type": TaskType,
                "complexity": TaskComplexity,
                "confidence": float
            }
        """
        task_type, complexity, retain_prob = self.analyze_task(prompt)
        
        # 决策逻辑
        if retain_prob > 0.7:
            # 自己处理
            return {
                "action": "retain",
                "handler": "self",
                "reason": f"复杂任务({complexity.value})，需要深度思考或关键决策",
                "task_type": task_type,
                "complexity": complexity,
                "confidence": retain_prob
            }
        
        elif retain_prob > 0.4:
            # 中等复杂度，可以交给小弟但需要我审核
            return {
                "action": "delegate",
                "handler": "any",  # 任一节点
                "review_required": True,
                "reason": f"中等复杂度任务，交给小弟处理，结果需审核",
                "task_type": task_type,
                "complexity": complexity,
                "confidence": 1 - retain_prob
            }
        
        else:
            # 简单任务，完全交给小弟
            # 根据任务类型选择节点组
            if task_type == TaskType.DATA_COLLECTION:
                handler = "all"  # 广播到所有节点收集数据
            elif task_type == TaskType.CODE_EXECUTION:
                handler = "ds"  # DeepSeek组处理代码
            elif task_type == TaskType.CONTENT_GENERATION:
                handler = "step"  # Step组快速生成
            else:
                handler = "any"
            
            return {
                "action": "delegate",
                "handler": handler,
                "review_required": False,
                "reason": f"标准化任务({task_type.value})，完全交给小弟处理",
                "task_type": task_type,
                "complexity": complexity,
                "confidence": 1 - retain_prob
            }
    
    def batch_route(self, tasks: List[str]) -> List[Dict]:
        """批量路由多个任务"""
        results = []
        for task in tasks:
            result = self.route_task(task)
            results.append({"task": task, "route": result})
        
        # 统计
        delegate_count = sum(1 for r in results if r["route"]["action"] == "delegate")
        retain_count = len(results) - delegate_count
        
        print(f"📊 批量路由结果: {delegate_count}个给小弟, {retain_count}个自己处理")
        
        return results

# 全局路由器
_router = None

def get_router():
    global _router
    if _router is None:
        _router = TaskRouter()
    return _router

def should_delegate(prompt: str) -> bool:
    """快速判断是否应该交给小弟"""
    router = get_router()
    route = router.route_task(prompt)
    return route["action"] == "delegate"

def main():
    """测试"""
    router = get_router()
    
    # 测试任务
    test_tasks = [
        "测试所有节点的连接状态",                    # 监控 -> 给小弟
        "收集这10个网站的标题",                      # 数据收集 -> 给小弟
        "分析这个错误日志并找出问题",                # 分析 -> 自己
        "生成一份周报模板",                          # 内容生成 -> 给小弟
        "帮我决定使用哪种架构方案",                  # 决策 -> 自己
        "并行处理这100条数据",                       # 批处理 -> 给小弟
        "为什么这个策略更好？",                      # 分析 -> 自己
        "写一个简单的Python脚本",                    # 代码 -> 给小弟
    ]
    
    print("=" * 70)
    print("🎯 任务路由测试")
    print("=" * 70)
    
    for task in test_tasks:
        route = router.route_task(task)
        action_icon = "🤖" if route["action"] == "delegate" else "🧠"
        print(f"\n{action_icon} {task[:40]}")
        print(f"   决定: {'给小弟' if route['action'] == 'delegate' else '自己处理'}")
        print(f"   类型: {route['task_type'].value}")
        print(f"   复杂度: {route['complexity'].value}")
        print(f"   原因: {route['reason']}")
        if route["action"] == "delegate":
            print(f"   目标: {route['handler']}")
    
    print("\n" + "=" * 70)
    
    # 批量统计
    results = router.batch_route(test_tasks)
    delegate_pct = sum(1 for r in results if r["route"]["action"] == "delegate") / len(results) * 100
    print(f"\n📈 给小弟处理的比例: {delegate_pct:.0f}%")

if __name__ == "__main__":
    main()
