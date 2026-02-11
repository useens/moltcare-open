#!/usr/bin/env python3
"""
林林自动化协调器 v1.0
统一协调所有自动化任务，避免重复执行和资源冲突
"""
import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import logging

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
STATE_FILE = WORKSPACE / "memory" / "meta" / "automation-state.json"
LOG_FILE = WORKSPACE / "logs" / "automation-coordinator.log"
LOCK_FILE = Path("/tmp/automation-coordinator.lock")

# 任务定义
AUTOMATION_TASKS = {
    "health_check": {
        "script": "scripts/health-check.sh",
        "interval_minutes": 120,
        "category": "health",
        "priority": 1,
        "silent": True
    },
    "memory_consolidation": {
        "script": "scripts/memory-system/auto_consolidate.py",
        "interval_minutes": 180,
        "category": "memory",
        "priority": 2,
        "silent": True
    },
    "vector_memory_check": {
        "script": "scripts/memory-guardian.py",
        "interval_minutes": 60,
        "category": "memory",
        "priority": 1,
        "silent": True
    },
    "log_cleanup": {
        "script": "scripts/log-cleanup.sh",
        "interval_minutes": 360,
        "category": "maintenance",
        "priority": 3,
        "silent": True
    },
    "backup_check": {
        "script": "scripts/backup-simple.sh",
        "interval_minutes": 360,
        "category": "backup",
        "priority": 1,
        "silent": True
    },
    "github_sync": {
        "script": None,  # 特殊处理
        "interval_minutes": 30,
        "category": "backup",
        "priority": 2,
        "silent": True
    }
}

@dataclass
class TaskExecution:
    task_name: str
    started_at: str
    completed_at: Optional[str]
    success: bool
    output: str
    duration_seconds: float

class AutomationCoordinator:
    """自动化协调器"""
    
    def __init__(self):
        self.state = self._load_state()
        self._setup_logging()
        
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('automation-coordinator')
        
    def _load_state(self) -> Dict:
        """加载状态"""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {
            "last_executions": {},
            "execution_history": [],
            "stats": {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0
            }
        }
    
    def _save_state(self):
        """保存状态"""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _is_task_due(self, task_name: str) -> bool:
        """检查任务是否到期"""
        task_config = AUTOMATION_TASKS[task_name]
        last_execution = self.state["last_executions"].get(task_name)
        
        if not last_execution:
            return True
            
        last_time = datetime.fromisoformat(last_execution)
        interval = timedelta(minutes=task_config["interval_minutes"])
        
        return datetime.now() - last_time >= interval
    
    def _execute_task(self, task_name: str) -> TaskExecution:
        """执行单个任务"""
        task_config = AUTOMATION_TASKS[task_name]
        script_path = task_config["script"]
        
        start_time = datetime.now()
        
        try:
            if task_name == "github_sync":
                # 特殊处理GitHub同步
                result = self._execute_github_sync()
            else:
                # 执行脚本
                full_script_path = WORKSPACE / script_path
                result = subprocess.run(
                    ["bash", str(full_script_path)] if str(full_script_path).endswith('.sh') else ["python3", str(full_script_path)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            execution = TaskExecution(
                task_name=task_name,
                started_at=start_time.isoformat(),
                completed_at=datetime.now().isoformat(),
                success=result.returncode == 0,
                output=result.stdout if hasattr(result, 'stdout') else result.get('output', ''),
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            execution = TaskExecution(
                task_name=task_name,
                started_at=start_time.isoformat(),
                completed_at=datetime.now().isoformat(),
                success=False,
                output=str(e),
                duration_seconds=duration
            )
        
        return execution
    
    def _execute_github_sync(self) -> Dict:
        """执行GitHub同步"""
        try:
            os.chdir(WORKSPACE)
            subprocess.run(["git", "add", "-A"], capture_output=True, timeout=30)
            subprocess.run(
                ["git", "commit", "-m", f"auto: {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
                capture_output=True, timeout=30
            )
            result = subprocess.run(
                ["git", "push", "origin", "main"],
                capture_output=True, text=True, timeout=60
            )
            return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as e:
            return {"returncode": 1, "stdout": "", "stderr": str(e)}
    
    def _update_state(self, execution: TaskExecution):
        """更新状态"""
        self.state["last_executions"][execution.task_name] = execution.started_at
        self.state["execution_history"].append(asdict(execution))
        
        # 保留最近100条历史
        if len(self.state["execution_history"]) > 100:
            self.state["execution_history"] = self.state["execution_history"][-100:]
        
        self.state["stats"]["total_executions"] += 1
        if execution.success:
            self.state["stats"]["successful_executions"] += 1
        else:
            self.state["stats"]["failed_executions"] += 1
        
        self._save_state()
    
    def run_due_tasks(self):
        """运行所有到期任务"""
        # 检查锁
        if LOCK_FILE.exists():
            lock_time = datetime.fromtimestamp(LOCK_FILE.stat().st_mtime)
            if datetime.now() - lock_time < timedelta(minutes=5):
                self.logger.info("协调器已在运行，跳过")
                return
        
        LOCK_FILE.touch()
        
        try:
            due_tasks = []
            for task_name, config in sorted(
                AUTOMATION_TASKS.items(),
                key=lambda x: x[1]["priority"]
            ):
                if self._is_task_due(task_name):
                    due_tasks.append(task_name)
            
            if not due_tasks:
                self.logger.debug("无到期任务")
                return
            
            self.logger.info(f"发现 {len(due_tasks)} 个到期任务: {', '.join(due_tasks)}")
            
            for task_name in due_tasks:
                self.logger.info(f"执行任务: {task_name}")
                execution = self._execute_task(task_name)
                self._update_state(execution)
                
                if execution.success:
                    self.logger.info(f"✅ {task_name} 完成 ({execution.duration_seconds:.1f}s)")
                else:
                    self.logger.warning(f"❌ {task_name} 失败: {execution.output[:200]}")
                
                # 任务间短暂延迟，避免资源冲突
                time.sleep(2)
            
            self.logger.info(f"本轮协调完成，执行 {len(due_tasks)} 个任务")
            
        finally:
            LOCK_FILE.unlink(missing_ok=True)
    
    def get_status(self) -> Dict:
        """获取协调器状态"""
        return {
            "state": self.state,
            "tasks_config": AUTOMATION_TASKS,
            "next_executions": {
                task: datetime.fromisoformat(self.state["last_executions"].get(
                    task, "1970-01-01T00:00:00"
                )) + timedelta(minutes=config["interval_minutes"])
                for task, config in AUTOMATION_TASKS.items()
            }
        }
    
    def generate_report(self) -> str:
        """生成执行报告"""
        stats = self.state["stats"]
        history = self.state["execution_history"][-20:]  # 最近20条
        
        report = []
        report.append("=" * 60)
        report.append("🤖 自动化协调器报告")
        report.append("=" * 60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("📊 执行统计")
        report.append(f"  总执行次数: {stats['total_executions']}")
        report.append(f"  成功次数: {stats['successful_executions']}")
        report.append(f"  失败次数: {stats['failed_executions']}")
        success_rate = (stats['successful_executions'] / stats['total_executions'] * 100) if stats['total_executions'] > 0 else 0
        report.append(f"  成功率: {success_rate:.1f}%")
        report.append("")
        report.append("📝 最近执行记录")
        for exec_record in reversed(history):
            status = "✅" if exec_record["success"] else "❌"
            report.append(f"  {status} {exec_record['task_name']} - {exec_record['completed_at'][:19]}")
        report.append("")
        report.append("⏰ 下次执行时间")
        for task, next_time in self.get_status()["next_executions"].items():
            report.append(f"  {task}: {next_time.strftime('%H:%M:%S')}")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """主函数"""
    coordinator = AutomationCoordinator()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            print(coordinator.generate_report())
        elif sys.argv[1] == "--run":
            coordinator.run_due_tasks()
            print(coordinator.generate_report())
        else:
            print(f"用法: {sys.argv[0]} [--status|--run]")
    else:
        # 默认：运行到期任务
        coordinator.run_due_tasks()


if __name__ == "__main__":
    main()
