#!/usr/bin/env python3
"""
Command Center - Task Queue System (P0)
任务队列系统 - 核心组件

功能:
- SQLite持久化任务队列
- 优先级调度
- 指数退避重试
- 任务状态追踪
"""

import sqlite3
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Optional, List, Dict, Any

# 数据库路径
DB_PATH = Path("/root/.openclaw/workspace/data/task_queue.db")

class TaskStatus(Enum):
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"        # 失败
    RETRYING = "retrying"    # 重试中
    CANCELLED = "cancelled"  # 已取消

class TaskPriority(Enum):
    CRITICAL = 0   # 关键任务
    HIGH = 1       # 高优先级
    NORMAL = 2     # 普通
    LOW = 3        # 低优先级

class Task:
    """任务对象"""
    
    def __init__(self, 
                 task_id: str,
                 prompt: str,
                 node_id: Optional[str] = None,
                 priority: TaskPriority = TaskPriority.NORMAL,
                 task_type: str = "auto",
                 max_retries: int = 3,
                 timeout: int = 60,
                 metadata: Optional[Dict] = None):
        self.task_id = task_id
        self.prompt = prompt
        self.node_id = node_id
        self.priority = priority
        self.task_type = task_type
        self.max_retries = max_retries
        self.timeout = timeout
        self.metadata = metadata or {}
        
        # 状态
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.started_at = None
        self.completed_at = None
        self.retry_count = 0
        self.result = None
        self.error = None
        self.assigned_node = None
        
        # 重试退避
        self.next_retry_at = None
        self.backoff_delay = 1  # 初始1秒
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "node_id": self.node_id,
            "priority": self.priority.value,
            "task_type": self.task_type,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "metadata": json.dumps(self.metadata),
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "result": self.result,
            "error": self.error,
            "assigned_node": self.assigned_node,
            "next_retry_at": self.next_retry_at,
            "backoff_delay": self.backoff_delay
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        task = cls(
            task_id=data["task_id"],
            prompt=data["prompt"],
            node_id=data.get("node_id"),
            priority=TaskPriority(data["priority"]),
            task_type=data.get("task_type", "auto"),
            max_retries=data.get("max_retries", 3),
            timeout=data.get("timeout", 60),
            metadata=json.loads(data.get("metadata", "{}"))
        )
        task.status = TaskStatus(data["status"])
        task.created_at = data["created_at"]
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        task.retry_count = data.get("retry_count", 0)
        task.result = data.get("result")
        task.error = data.get("error")
        task.assigned_node = data.get("assigned_node")
        task.next_retry_at = data.get("next_retry_at")
        task.backoff_delay = data.get("backoff_delay", 1)
        return task
    
    def calculate_backoff(self):
        """计算指数退避延迟"""
        # 指数退避: 1s, 2s, 4s, 8s, 16s...
        delay = min(2 ** self.retry_count, 300)  # 最大5分钟
        self.backoff_delay = delay
        self.next_retry_at = (datetime.now().timestamp() + delay)
        return delay

class TaskQueue:
    """SQLite任务队列"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._lock = threading.RLock()
    
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    node_id TEXT,
                    priority INTEGER DEFAULT 2,
                    task_type TEXT DEFAULT 'auto',
                    max_retries INTEGER DEFAULT 3,
                    timeout INTEGER DEFAULT 60,
                    metadata TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    retry_count INTEGER DEFAULT 0,
                    result TEXT,
                    error TEXT,
                    assigned_node TEXT,
                    next_retry_at REAL,
                    backoff_delay INTEGER DEFAULT 1
                )
            """)
            
            # 索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON tasks(created_at)")
            conn.commit()
    
    def enqueue(self, task: Task) -> bool:
        """添加任务到队列"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    data = task.to_dict()
                    conn.execute("""
                        INSERT INTO tasks (
                            task_id, prompt, node_id, priority, task_type,
                            max_retries, timeout, metadata, status, created_at
                        ) VALUES (
                            :task_id, :prompt, :node_id, :priority, :task_type,
                            :max_retries, :timeout, :metadata, :status, :created_at
                        )
                    """, data)
                    conn.commit()
                    return True
            except Exception as e:
                print(f"❌  enqueue failed: {e}")
                return False
    
    def dequeue(self) -> Optional[Task]:
        """取出最高优先级的待处理任务"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # 查找待处理或需要重试的任务
                    cursor = conn.execute("""
                        SELECT * FROM tasks 
                        WHERE status IN ('pending', 'retrying')
                        AND (next_retry_at IS NULL OR next_retry_at <= ?)
                        ORDER BY priority ASC, created_at ASC
                        LIMIT 1
                    """, (datetime.now().timestamp(),))
                    
                    row = cursor.fetchone()
                    if row:
                        # 更新状态为running
                        conn.execute(
                            "UPDATE tasks SET status = 'running', started_at = ? WHERE task_id = ?",
                            (datetime.now().isoformat(), row[0])
                        )
                        conn.commit()
                        
                        # 构建Task对象
                        columns = [desc[0] for desc in cursor.description]
                        data = dict(zip(columns, row))
                        return Task.from_dict(data)
                    
                    return None
            except Exception as e:
                print(f"❌  dequeue failed: {e}")
                return None
    
    def complete(self, task_id: str, result: str, node_id: str):
        """标记任务完成"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE tasks 
                        SET status = 'completed', 
                            completed_at = ?,
                            result = ?,
                            assigned_node = ?
                        WHERE task_id = ?
                    """, (datetime.now().isoformat(), result, node_id, task_id))
                    conn.commit()
            except Exception as e:
                print(f"❌  complete failed: {e}")
    
    def fail(self, task_id: str, error: str, node_id: str):
        """标记任务失败，可能触发重试"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # 获取当前重试次数
                    cursor = conn.execute(
                        "SELECT retry_count, max_retries FROM tasks WHERE task_id = ?",
                        (task_id,)
                    )
                    row = cursor.fetchone()
                    if not row:
                        return
                    
                    retry_count, max_retries = row
                    
                    if retry_count < max_retries:
                        # 计算退避
                        new_retry_count = retry_count + 1
                        delay = min(2 ** new_retry_count, 300)
                        next_retry = datetime.now().timestamp() + delay
                        
                        # 更新为retrying状态
                        conn.execute("""
                            UPDATE tasks 
                            SET status = 'retrying',
                                retry_count = ?,
                                next_retry_at = ?,
                                backoff_delay = ?,
                                error = ?,
                                assigned_node = ?
                            WHERE task_id = ?
                        """, (new_retry_count, next_retry, delay, error, node_id, task_id))
                    else:
                        # 超过重试次数，标记为失败
                        conn.execute("""
                            UPDATE tasks 
                            SET status = 'failed',
                                completed_at = ?,
                                error = ?,
                                assigned_node = ?
                            WHERE task_id = ?
                        """, (datetime.now().isoformat(), error, node_id, task_id))
                    
                    conn.commit()
            except Exception as e:
                print(f"❌  fail failed: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """获取队列统计"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT status, COUNT(*) FROM tasks 
                        GROUP BY status
                    """)
                    stats = {row[0]: row[1] for row in cursor.fetchall()}
                    
                    # 总数
                    cursor = conn.execute("SELECT COUNT(*) FROM tasks")
                    stats['total'] = cursor.fetchone()[0]
                    
                    return stats
            except Exception as e:
                print(f"❌  get_stats failed: {e}")
                return {}
    
    def get_pending_tasks(self) -> List[Task]:
        """获取所有待处理任务"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT * FROM tasks 
                        WHERE status IN ('pending', 'retrying')
                        ORDER BY priority ASC, created_at ASC
                    """)
                    return [Task.from_dict(dict(row)) for row in cursor.fetchall()]
            except Exception as e:
                print(f"❌  get_pending_tasks failed: {e}")
                return []
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取指定任务"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(
                        "SELECT * FROM tasks WHERE task_id = ?",
                        (task_id,)
                    )
                    row = cursor.fetchone()
                    return Task.from_dict(dict(row)) if row else None
            except Exception as e:
                print(f"❌  get_task failed: {e}")
                return None
    
    def cleanup_old_tasks(self, days: int = 7):
        """清理旧任务"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        DELETE FROM tasks 
                        WHERE created_at < datetime('now', '-{} days')
                        AND status IN ('completed', 'failed', 'cancelled')
                    """.format(days))
                    conn.commit()
            except Exception as e:
                print(f"❌  cleanup failed: {e}")

# 全局队列实例
_queue_instance = None

def get_queue() -> TaskQueue:
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = TaskQueue()
    return _queue_instance

if __name__ == "__main__":
    # 测试
    queue = get_queue()
    
    # 添加测试任务
    task = Task(
        task_id=f"test_{int(time.time())}",
        prompt="测试任务",
        priority=TaskPriority.HIGH
    )
    
    if queue.enqueue(task):
        print(f"✅ 任务已入队: {task.task_id}")
    
    # 查看统计
    stats = queue.get_stats()
    print(f"📊 队列统计: {stats}")
    
    # 取出任务
    next_task = queue.dequeue()
    if next_task:
        print(f"📤 取出任务: {next_task.task_id}")
        
        # 模拟完成
        queue.complete(next_task.task_id, "测试结果", "NB01")
        print(f"✅ 任务完成")
    
    print("\n测试完成！")
