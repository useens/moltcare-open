#!/usr/bin/env python3
"""
EvoMap 任务猎人 - 自动扫描、评估、抢占赏金任务
"""

import json
import time
import random
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data" / "evomap"
LOG_FILE = WORKSPACE / "logs" / "evomap-task-hunter.log"
CONFIG_FILE = DATA_DIR / "task-hunter-config.json"

# EvoMap Hub 配置
HUB_URL = "https://evomap.replit.app"

@dataclass
class BountyTask:
    """赏金任务"""
    task_id: str
    title: str
    description: str
    reward: float
    currency: str
    deadline: str
    requirements: List[str]
    signal_tags: List[str]
    difficulty: str  # easy/medium/hard
    estimated_hours: int
    
    @property
    def hourly_rate(self) -> float:
        """计算时薪"""
        if self.estimated_hours > 0:
            return self.reward / self.estimated_hours
        return 0
    
    @property
    def signal_score(self) -> int:
        """计算Signal分数 (0-10)"""
        score = 5  # 基础分
        
        # 高价值标签加分
        high_value_tags = ['python', 'automation', 'api', 'ai', 'llm', 'agent', 'mcp', 'docker']
        for tag in self.signal_tags:
            if tag.lower() in high_value_tags:
                score += 1
        
        # 高时薪加分
        if self.hourly_rate > 100:
            score += 2
        elif self.hourly_rate > 50:
            score += 1
        
        # 难度适中加分（太简单或太难都减分）
        if self.difficulty == 'medium':
            score += 1
        
        # 紧急任务加分
        if self.deadline:
            try:
                deadline = datetime.fromisoformat(self.deadline.replace('Z', '+00:00'))
                days_left = (deadline - datetime.now()).days
                if days_left < 3:
                    score += 1
            except:
                pass
        
        return min(10, max(0, score))

class TaskHunter:
    """任务猎人"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "EvoMap-TaskHunter/1.0"
        })
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return json.load(f)
        return {
            "min_signal_score": 6,
            "min_hourly_rate": 30,
            "auto_bid": False,
            "bid_probability": 0.3,
            "max_concurrent_tasks": 3,
            "preferred_tags": ["python", "automation", "api", "ai"],
            "avoid_tags": ["frontend", "design", "mobile"],
            "claimed_tasks": [],
            "completed_tasks": [],
            "total_earned": 0.0
        }
    
    def _save_config(self):
        """保存配置"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry + "\n")
    
    def fetch_bounty_tasks(self) -> List[BountyTask]:
        """获取赏金任务列表"""
        self._log("正在扫描 EvoMap 赏金任务...")
        
        try:
            # 从 EvoMap Hub 获取任务
            response = self.session.get(
                f"{HUB_URL}/api/bounty/tasks",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                tasks = []
                
                for task_data in data.get("tasks", []):
                    task = BountyTask(
                        task_id=task_data.get("id", ""),
                        title=task_data.get("title", "Unknown"),
                        description=task_data.get("description", ""),
                        reward=task_data.get("reward", 0),
                        currency=task_data.get("currency", "USD"),
                        deadline=task_data.get("deadline", ""),
                        requirements=task_data.get("requirements", []),
                        signal_tags=task_data.get("tags", []),
                        difficulty=task_data.get("difficulty", "medium"),
                        estimated_hours=task_data.get("estimated_hours", 4)
                    )
                    tasks.append(task)
                
                self._log(f"发现 {len(tasks)} 个赏金任务")
                return tasks
            
            else:
                self._log(f"获取任务失败: HTTP {response.status_code}", "ERROR")
                return []
        
        except Exception as e:
            self._log(f"获取任务异常: {e}", "ERROR")
            return []
    
    def evaluate_task(self, task: BountyTask) -> Tuple[bool, str]:
        """评估任务是否值得接"""
        reasons = []
        
        # Signal分数检查
        if task.signal_score < self.config["min_signal_score"]:
            reasons.append(f"Signal分数低 ({task.signal_score}/10)")
        
        # 时薪检查
        if task.hourly_rate < self.config["min_hourly_rate"]:
            reasons.append(f"时薪过低 (${task.hourly_rate:.2f}/h)")
        
        # 标签匹配检查
        preferred_match = sum(1 for tag in task.signal_tags 
                            if tag.lower() in self.config["preferred_tags"])
        avoid_match = sum(1 for tag in task.signal_tags 
                         if tag.lower() in self.config["avoid_tags"])
        
        if avoid_match > 0:
            reasons.append(f"包含不擅长的标签: {[t for t in task.signal_tags if t.lower() in self.config['avoid_tags']]}")
        
        if preferred_match == 0:
            reasons.append("无匹配的技术标签")
        
        # 并发任务检查
        if len(self.config["claimed_tasks"]) >= self.config["max_concurrent_tasks"]:
            reasons.append(f"已达到最大并发任务数 ({self.config['max_concurrent_tasks']})")
        
        # 重复任务检查
        if task.task_id in self.config["claimed_tasks"]:
            reasons.append("已认领此任务")
        
        if task.task_id in self.config["completed_tasks"]:
            reasons.append("已完成此任务")
        
        is_good = len(reasons) == 0
        return is_good, "; ".join(reasons) if reasons else "✓ 符合所有条件"
    
    def generate_proposal(self, task: BountyTask) -> str:
        """生成任务提案"""
        # 基于任务要求生成提案模板
        proposal = f"""# 任务执行提案

## 执行方案

我将按以下步骤完成此任务：

1. **需求分析** (30分钟)
   - 深入理解任务要求
   - 识别潜在技术难点

2. **方案设计** (1小时)
   - 制定技术实现方案
   - 确定最佳技术栈

3. **开发实现** ({task.estimated_hours - 2}小时)
   - 高质量代码编写
   - 完整的测试覆盖

4. **交付验收** (30分钟)
   - 提供完整文档
   - 支持后续迭代

## 我的优势

- ✅ 24/7 可用，响应迅速
- ✅ 丰富的自动化和API开发经验
- ✅ 高质量代码，完整测试
- ✅ 已接入 EvoMap 生态

## 交付物

- 完整源代码
- 技术文档
- 测试用例
- 部署指南

预计交付时间: {task.estimated_hours} 小时内
"""
        return proposal
    
    def submit_bid(self, task: BountyTask, proposal: str) -> bool:
        """提交竞标"""
        self._log(f"正在提交任务竞标: {task.title}")
        
        try:
            payload = {
                "task_id": task.task_id,
                "proposal": proposal,
                "estimated_hours": task.estimated_hours,
                "bid_amount": task.reward,  # 按标价竞标
                "bidder_type": "ai_agent",
                "bidder_id": "node_e8d73f59"  # 森森的节点ID
            }
            
            response = self.session.post(
                f"{HUB_URL}/api/bounty/bid",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                self._log(f"✅ 竞标提交成功: {task.title}")
                
                # 记录已认领任务
                self.config["claimed_tasks"].append(task.task_id)
                self._save_config()
                
                return True
            else:
                self._log(f"❌ 竞标提交失败: HTTP {response.status_code}", "ERROR")
                return False
        
        except Exception as e:
            self._log(f"❌ 竞标提交异常: {e}", "ERROR")
            return False
    
    def hunt(self, aggressive: bool = False):
        """执行任务猎取"""
        self._log("=" * 50)
        self._log("🎯 EvoMap 任务猎人启动")
        self._log(f"模式: {'激进' if aggressive else '标准'}")
        self._log("=" * 50)
        
        # 激进模式调整参数
        if aggressive:
            original_min_signal = self.config["min_signal_score"]
            original_min_rate = self.config["min_hourly_rate"]
            self.config["min_signal_score"] = 4  # 降低门槛
            self.config["min_hourly_rate"] = 15
            self.config["auto_bid"] = True
            self._log(f"激进模式: Signal门槛 {original_min_signal}→4, 时薪门槛 ${original_min_rate}→$15")
        
        # 获取任务
        tasks = self.fetch_bounty_tasks()
        
        if not tasks:
            self._log("未找到赏金任务，稍后重试...")
            return
        
        # 按Signal分数排序
        tasks.sort(key=lambda t: t.signal_score, reverse=True)
        
        # 评估和筛选
        good_tasks = []
        rejected_tasks = []
        
        for task in tasks:
            is_good, reason = self.evaluate_task(task)
            
            if is_good:
                good_tasks.append(task)
            else:
                rejected_tasks.append((task, reason))
        
        # 输出评估结果
        self._log(f"\n📊 任务评估结果:")
        self._log(f"  - 符合要求: {len(good_tasks)} 个")
        self._log(f"  - 不符合: {len(rejected_tasks)} 个")
        
        # 显示前5个高Signal任务
        self._log(f"\n🌟 高Signal任务 Top 5:")
        for i, task in enumerate(good_tasks[:5], 1):
            self._log(f"  {i}. [{task.signal_score}/10] {task.title}")
            self._log(f"     赏金: ${task.reward} {task.currency} | 时薪: ${task.hourly_rate:.2f}/h")
            self._log(f"     标签: {', '.join(task.signal_tags)}")
        
        # 自动竞标
        if good_tasks and self.config.get("auto_bid", False):
            self._log(f"\n🚀 自动竞标模式启动...")
            
            # 选择Signal最高的任务
            best_task = good_tasks[0]
            
            # 生成提案
            proposal = self.generate_proposal(best_task)
            
            # 提交竞标
            if self.submit_bid(best_task, proposal):
                self._log(f"\n✅ 成功抢占任务: {best_task.title}")
                self._log(f"   预期收入: ${best_task.reward}")
                self._log(f"   预计耗时: {best_task.estimated_hours} 小时")
                self._log(f"   时薪: ${best_task.hourly_rate:.2f}/h")
            else:
                self._log(f"\n❌ 抢占失败: {best_task.title}", "ERROR")
        
        # 恢复原始配置
        if aggressive:
            self.config["min_signal_score"] = 5
            self.config["min_hourly_rate"] = 30
            self.config["auto_bid"] = False
        
        # 输出统计
        self._log(f"\n📈 累计统计:")
        self._log(f"  - 已认领任务: {len(self.config['claimed_tasks'])}")
        self._log(f"  - 已完成任务: {len(self.config['completed_tasks'])}")
        self._log(f"  - 累计收入: ${self.config['total_earned']:.2f}")
        
        self._log("=" * 50)
        self._log("🎯 任务猎人本轮扫描完成")
        self._log("=" * 50)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EvoMap 任务猎人")
    parser.add_argument("--aggressive", action="store_true", 
                       help="激进模式 - 降低门槛，自动竞标")
    parser.add_argument("--auto-bid", action="store_true",
                       help="自动提交竞标")
    parser.add_argument("--interval", type=int, default=0,
                       help="循环扫描间隔（秒），0表示只运行一次")
    
    args = parser.parse_args()
    
    hunter = TaskHunter()
    
    # 如果启用自动竞标
    if args.auto_bid:
        hunter.config["auto_bid"] = True
        hunter._save_config()
    
    if args.interval > 0:
        # 循环模式
        print(f"🔄 循环模式启动，间隔 {args.interval} 秒")
        try:
            while True:
                hunter.hunt(aggressive=args.aggressive)
                print(f"\n⏳ 等待 {args.interval} 秒后再次扫描...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n👋 任务猎人已停止")
    else:
        # 单次运行
        hunter.hunt(aggressive=args.aggressive)


if __name__ == "__main__":
    main()
