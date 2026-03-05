#!/usr/bin/env python3
"""
Command Center - Intelligent Scheduler (P0)
智能调度器 - 核心组件

功能:
- 节点能力画像
- 智能任务分配
- 负载均衡
- 动态权重调整
"""

import json
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# 导入任务队列
import sys
sys.path.insert(0, str(Path(__file__).parent))
from task_queue import Task, TaskQueue, TaskStatus, TaskPriority, get_queue

# 节点配置
NANOBOTS = [
    {"id": "NB01", "port": 18801, "model": "step", "apikey": "nvapi-KK5wL7..."},
    {"id": "NB02", "port": 18802, "model": "step", "apikey": "nvapi-J3b15L..."},
    {"id": "NB03", "port": 18803, "model": "step", "apikey": "nvapi-IPtXI8..."},
    {"id": "NB04", "port": 18804, "model": "step", "apikey": "nvapi-K7bWEy..."},
    {"id": "NB05", "port": 18805, "model": "step", "apikey": "nvapi-NQj1GH..."},
    {"id": "NB06", "port": 18806, "model": "ds", "apikey": "nvapi-CvbuEv..."},
    {"id": "NB07", "port": 18807, "model": "ds", "apikey": "nvapi-gWHf6K..."},
    {"id": "NB08", "port": 18808, "model": "ds", "apikey": "nvapi-oyDy6F..."},
    {"id": "NB09", "port": 18809, "model": "ds", "apikey": "nvapi-RBDc9C..."},
    {"id": "NB10", "port": 18810, "model": "ds", "apikey": "nvapi-BzaCTX..."},
]

@dataclass
class NodeProfile:
    """节点能力画像"""
    node_id: str
    model: str  # step or ds
    
    # 性能指标
    success_count: int = 0
    fail_count: int = 0
    total_tasks: int = 0
    
    # 响应时间 (秒)
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    
    # 任务类型成功率
    task_type_success: Dict[str, Dict] = None
    
    # 负载
    current_load: float = 0.0  # 0-1
    last_heartbeat: Optional[str] = None
    status: str = "unknown"
    
    def __post_init__(self):
        if self.task_type_success is None:
            self.task_type_success = {}
    
    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 1.0  # 新节点默认100%
        return self.success_count / self.total_tasks
    
    @property
    def score(self) -> float:
        """综合评分 (0-1)"""
        # 成功率40% + 响应速度30% + 负载余量30%
        success_score = self.success_rate * 0.4
        
        # 响应速度 (假设5秒为理想)
        if self.avg_response_time > 0:
            speed_score = max(0, 1 - (self.avg_response_time / 10)) * 0.3
        else:
            speed_score = 0.3
        
        # 负载余量
        load_score = (1 - self.current_load) * 0.3
        
        return success_score + speed_score + load_score
    
    def update_response_time(self, duration: float):
        """更新响应时间统计"""
        self.min_response_time = min(self.min_response_time, duration)
        self.max_response_time = max(self.max_response_time, duration)
        
        # 移动平均
        if self.avg_response_time == 0:
            self.avg_response_time = duration
        else:
            self.avg_response_time = (self.avg_response_time * 0.7) + (duration * 0.3)
    
    def record_success(self, task_type: str, duration: float):
        """记录成功任务"""
        self.success_count += 1
        self.total_tasks += 1
        self.update_response_time(duration)
        
        # 更新任务类型统计
        if task_type not in self.task_type_success:
            self.task_type_success[task_type] = {"success": 0, "fail": 0}
        self.task_type_success[task_type]["success"] += 1
        
        self.status = "online"
        self.last_heartbeat = datetime.now().isoformat()
    
    def record_fail(self, task_type: str):
        """记录失败任务"""
        self.fail_count += 1
        self.total_tasks += 1
        
        if task_type not in self.task_type_success:
            self.task_type_success[task_type] = {"success": 0, "fail": 0}
        self.task_type_success[task_type]["fail"] += 1
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NodeProfile':
        return cls(**data)

class NodeProfileDB:
    """节点画像数据库"""
    
    def __init__(self, db_path: Path = Path("/root/.openclaw/workspace/data/node_profiles.db")):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS node_profiles (
                    node_id TEXT PRIMARY KEY,
                    model TEXT,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    total_tasks INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    min_response_time REAL DEFAULT 999999,
                    max_response_time REAL DEFAULT 0,
                    task_type_success TEXT DEFAULT '{}',
                    current_load REAL DEFAULT 0,
                    last_heartbeat TEXT,
                    status TEXT DEFAULT 'unknown',
                    updated_at TEXT
                )
            """)
            conn.commit()
    
    def save_profile(self, profile: NodeProfile):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO node_profiles (
                    node_id, model, success_count, fail_count, total_tasks,
                    avg_response_time, min_response_time, max_response_time,
                    task_type_success, current_load, last_heartbeat, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.node_id, profile.model, profile.success_count,
                profile.fail_count, profile.total_tasks, profile.avg_response_time,
                profile.min_response_time, profile.max_response_time,
                json.dumps(profile.task_type_success), profile.current_load,
                profile.last_heartbeat, profile.status, datetime.now().isoformat()
            ))
            conn.commit()
    
    def load_profile(self, node_id: str) -> Optional[NodeProfile]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM node_profiles WHERE node_id = ?",
                (node_id,)
            )
            row = cursor.fetchone()
            
            if row:
                data = dict(row)
                data['task_type_success'] = json.loads(data['task_type_success'])
                return NodeProfile(**{k: v for k, v in data.items() 
                                      if k in NodeProfile.__dataclass_fields__})
            return None
    
    def load_all_profiles(self) -> Dict[str, NodeProfile]:
        profiles = {}
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM node_profiles")
            for row in cursor.fetchall():
                data = dict(row)
                data['task_type_success'] = json.loads(data['task_type_success'])
                profile = NodeProfile(**{k: v for k, v in data.items()
                                        if k in NodeProfile.__dataclass_fields__})
                profiles[profile.node_id] = profile
        return profiles

class IntelligentScheduler:
    """智能调度器"""
    
    def __init__(self):
        self.queue = get_queue()
        self.profile_db = NodeProfileDB()
        self.profiles: Dict[str, NodeProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """加载所有节点画像"""
        self.profiles = self.profile_db.load_all_profiles()
        
        # 为新节点创建默认画像
        for node in NANOBOTS:
            if node["id"] not in self.profiles:
                self.profiles[node["id"]] = NodeProfile(
                    node_id=node["id"],
                    model=node["model"]
                )
    
    def classify_task(self, prompt: str) -> str:
        """任务分类"""
        prompt_lower = prompt.lower()
        
        # 代码相关
        if any(kw in prompt_lower for kw in ['code', '编程', 'python', 'function', 'debug', 'error']):
            return "code"
        
        # 快速简单任务
        if any(kw in prompt_lower for kw in ['hi', 'hello', '你好', 'test', '测试', 'ping']):
            return "quick"
        
        # 推理分析任务
        if any(kw in prompt_lower for kw in ['analyze', '分析', 'why', '为什么', 'explain', '解释']):
            return "reasoning"
        
        # 创意写作
        if any(kw in prompt_lower for kw in ['write', '写', 'create', '生成', 'story']):
            return "creative"
        
        return "general"
    
    def select_node(self, task: Task) -> Optional[str]:
        """智能选择节点"""
        # 如果指定了节点，直接返回
        if task.node_id:
            return task.node_id
        
        # 任务分类
        task_type = self.classify_task(task.prompt)
        
        # 根据任务类型选择节点组
        if task_type in ["quick", "general"]:
            preferred_model = "step"
        elif task_type in ["code", "reasoning"]:
            preferred_model = "ds"
        else:
            preferred_model = None
        
        # 筛选候选节点
        candidates = []
        for node_id, profile in self.profiles.items():
            # 检查节点是否在线
            if profile.status == "offline":
                continue
            
            # 模型匹配加分
            model_match = 1.0 if preferred_model and profile.model == preferred_model else 0.5
            
            # 综合评分
            score = profile.score * model_match
            
            candidates.append((node_id, score))
        
        if not candidates:
            # 没有在线节点，随机选择一个
            import random
            return random.choice([n["id"] for n in NANOBOTS])
        
        # 按评分排序，选择最高分
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def submit_task(self, prompt: str, 
                   priority: TaskPriority = TaskPriority.NORMAL,
                   node_id: Optional[str] = None,
                   task_type: str = "auto") -> Task:
        """提交任务"""
        # 生成任务ID
        task_id = f"task_{int(time.time() * 1000)}"
        
        # 自动分类
        if task_type == "auto":
            task_type = self.classify_task(prompt)
        
        # 创建任务
        task = Task(
            task_id=task_id,
            prompt=prompt,
            node_id=node_id,
            priority=priority,
            task_type=task_type,
            max_retries=3,
            timeout=60
        )
        
        # 如果没有指定节点，由调度器选择
        if not node_id:
            task.node_id = self.select_node(task)
        
        # 入队
        if self.queue.enqueue(task):
            print(f"✅ 任务已提交: {task_id} -> {task.node_id} (类型: {task_type})")
        else:
            print(f"❌ 任务提交失败: {task_id}")
        
        return task
    
    def record_result(self, node_id: str, task_type: str, 
                     success: bool, duration: float):
        """记录任务结果，更新节点画像"""
        profile = self.profiles.get(node_id)
        if not profile:
            return
        
        if success:
            profile.record_success(task_type, duration)
        else:
            profile.record_fail(task_type)
        
        # 保存到数据库
        self.profile_db.save_profile(profile)
    
    def get_node_stats(self) -> Dict[str, Any]:
        """获取节点统计"""
        stats = {}
        for node_id, profile in self.profiles.items():
            stats[node_id] = {
                "model": profile.model,
                "success_rate": f"{profile.success_rate:.1%}",
                "avg_time": f"{profile.avg_response_time:.1f}s",
                "score": f"{profile.score:.2f}",
                "status": profile.status,
                "total_tasks": profile.total_tasks
            }
        return stats

# 全局调度器
_scheduler_instance = None

def get_scheduler() -> IntelligentScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = IntelligentScheduler()
    return _scheduler_instance

if __name__ == "__main__":
    scheduler = get_scheduler()
    
    print("=== 智能调度器测试 ===\n")
    
    # 测试任务分类
    test_prompts = [
        "Hello, how are you?",
        "Write a Python function to sort list",
        "Analyze why this code fails",
        "Generate a story about AI",
        "Test connection"
    ]
    
    print("📋 任务分类测试:")
    for prompt in test_prompts:
        task_type = scheduler.classify_task(prompt)
        print(f"  '{prompt[:30]}...' -> {task_type}")
    
    print("\n📊 节点画像:")
    stats = scheduler.get_node_stats()
    for node_id, stat in stats.items():
        print(f"  {node_id}: {stat['model']}, 成功率{stat['success_rate']}, 评分{stat['score']}")
    
    print("\n✅ 调度器就绪！")
