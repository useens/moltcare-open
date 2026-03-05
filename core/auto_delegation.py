#!/usr/bin/env python3
"""
Command Center - Auto Delegation Executor
自动委托执行系统

功能:
1. 接收任务
2. 智能路由决策
3. 给小弟: 提交到P0队列
4. 给自己: 触发Multi-Agent思考
5. 结果汇总
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Optional

# 导入核心组件
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from task_router import get_router, TaskComplexity
from task_queue import TaskPriority, get_queue
from scheduler import get_scheduler

class AutoDelegationExecutor:
    """自动委托执行器"""
    
    def __init__(self):
        self.router = get_router()
        self.queue = get_queue()
        self.scheduler = get_scheduler()
        
        # 统计
        self.stats = {
            "delegated": 0,  # 给小弟
            "retained": 0,   # 自己处理
            "total": 0
        }
    
    def execute(self, prompt: str, context: Optional[Dict] = None) -> Dict:
        """
        执行任务，自动决定交给谁
        
        Returns:
            {
                "action": "delegate" | "retain",
                "result": str,
                "handler": str,
                "task_id": str (if delegate)
            }
        """
        self.stats["total"] += 1
        
        # 1. 路由决策
        route = self.router.route_task(prompt, context)
        
        print(f"🎯 任务路由: {route['action']}")
        print(f"   原因: {route['reason']}")
        
        if route["action"] == "delegate":
            # 交给小弟处理
            return self._delegate_to_minions(prompt, route)
        else:
            # 自己处理
            return self._handle_myself(prompt, route)
    
    def _delegate_to_minions(self, prompt: str, route: Dict) -> Dict:
        """交给10个小弟处理"""
        self.stats["delegated"] += 1
        
        handler = route["handler"]
        task_type = route["task_type"].value
        
        print(f"🤖 交给小弟处理 ({handler})")
        
        # 根据目标选择策略
        if handler == "all":
            # 广播到所有节点
            print(f"   广播到所有10个节点...")
            # 这里可以并行提交到所有节点
            task_ids = []
            for node in ["NB01", "NB02", "NB03", "NB04", "NB05", "NB06", "NB07", "NB08", "NB09", "NB10"]:
                task_id = self._submit_to_node(prompt, node, task_type)
                task_ids.append(task_id)
            
            return {
                "action": "delegate",
                "handler": "all_nodes",
                "task_ids": task_ids,
                "result": f"已广播到10个节点",
                "review_required": route.get("review_required", False)
            }
        
        elif handler == "ds":
            # 使用DeepSeek组
            node = self._select_best_node("ds", task_type)
            task_id = self._submit_to_node(prompt, node, task_type)
            return {
                "action": "delegate",
                "handler": node,
                "task_id": task_id,
                "result": f"已分配给{node}(DeepSeek)",
                "review_required": route.get("review_required", False)
            }
        
        elif handler == "step":
            # 使用Step组
            node = self._select_best_node("step", task_type)
            task_id = self._submit_to_node(prompt, node, task_type)
            return {
                "action": "delegate",
                "handler": node,
                "task_id": task_id,
                "result": f"已分配给{node}(Step)",
                "review_required": route.get("review_required", False)
            }
        
        else:  # any
            # 智能选择最佳节点
            node = self._select_best_node("any", task_type)
            task_id = self._submit_to_node(prompt, node, task_type)
            return {
                "action": "delegate",
                "handler": node,
                "task_id": task_id,
                "result": f"已分配给{node}",
                "review_required": route.get("review_required", False)
            }
    
    def _submit_to_node(self, prompt: str, node_id: str, task_type: str) -> str:
        """提交任务到指定节点"""
        # 使用P0系统的智能调度器
        priority = TaskPriority.NORMAL
        task = self.scheduler.submit_task(prompt, priority, node_id, task_type)
        return task.task_id
    
    def _select_best_node(self, group: str, task_type: str) -> str:
        """选择最佳节点"""
        if group == "ds":
            candidates = ["NB06", "NB07", "NB08", "NB09", "NB10"]
        elif group == "step":
            candidates = ["NB01", "NB02", "NB03", "NB04", "NB05"]
        else:
            candidates = ["NB01", "NB02", "NB03", "NB04", "NB05", 
                         "NB06", "NB07", "NB08", "NB09", "NB10"]
        
        # 获取节点统计，选择评分最高的
        stats = self.scheduler.get_node_stats()
        best_node = None
        best_score = -1
        
        for node_id in candidates:
            if node_id in stats:
                # 解析评分
                score_str = stats[node_id].get("score", "0.00")
                try:
                    score = float(score_str)
                    if score > best_score:
                        best_score = score
                        best_node = node_id
                except:
                    pass
        
        return best_node or candidates[0]
    
    def _handle_myself(self, prompt: str, route: Dict) -> Dict:
        """自己处理（触发Multi-Agent）"""
        self.stats["retained"] += 1
        
        print(f"🧠 自己处理 (触发Multi-Agent深度思考)")
        print(f"   复杂度: {route['complexity'].value}")
        
        # 返回指示，由上层调用Multi-Agent
        return {
            "action": "retain",
            "handler": "self",
            "result": "需要Multi-Agent深度思考",
            "prompt": prompt,
            "reason": route["reason"],
            "complexity": route["complexity"].value,
            "multi_agent_required": True
        }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total = self.stats["total"]
        if total == 0:
            return {"delegated_pct": 0, "retained_pct": 0}
        
        return {
            "total": total,
            "delegated": self.stats["delegated"],
            "retained": self.stats["retained"],
            "delegated_pct": self.stats["delegated"] / total * 100,
            "retained_pct": self.stats["retained"] / total * 100
        }
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {"delegated": 0, "retained": 0, "total": 0}

def main():
    """测试自动委托执行"""
    executor = AutoDelegationExecutor()
    
    print("=" * 70)
    print("🎯 自动委托执行系统测试")
    print("=" * 70)
    
    # 测试任务
    test_tasks = [
        "测试所有节点的连接状态",
        "分析这个错误日志并找出根本原因",
        "帮我决定使用哪种架构方案",
        "并行处理这100条数据",
        "为什么这个策略更好？",
        "生成一份周报模板",
    ]
    
    for task in test_tasks:
        print(f"\n📋 任务: {task}")
        print("-" * 70)
        result = executor.execute(task)
        print(f"   结果: {result['result']}")
        if result.get("task_id"):
            print(f"   任务ID: {result['task_id']}")
        print()
    
    # 统计
    stats = executor.get_stats()
    print("=" * 70)
    print("📊 执行统计:")
    print(f"   总任务: {stats['total']}")
    print(f"   给小弟: {stats['delegated']} ({stats['delegated_pct']:.0f}%)")
    print(f"   自己处理: {stats['retained']} ({stats['retained_pct']:.0f}%)")
    print("=" * 70)

if __name__ == "__main__":
    main()
