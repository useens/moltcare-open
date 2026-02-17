#!/usr/bin/env python3
"""
夜间自主进化模式 (P3)
Nightly Autonomous Evolution Mode

四层架构实现:
├── TRIGGER     → 触发层 (Cron/状态评估/人工)
├── ORCHESTRATION → 编排层 (Evolution Controller)
├── EXECUTION   → 执行层 (构建/测试/修复/学习)
└── DECISION    → 决策层 (成功/失败/发布/回滚)

整合P0-P2的能力:
- P0: 状态快照与漂移检测
- P1: 认知安全框架
- P2: 自主性验证

执行时段: 23:00 - 07:00
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum
import importlib.util

# 导入P0-P2的模块
sys.path.insert(0, '/root/.openclaw/workspace/scripts')


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0  # 必须完成
    HIGH = 1      # 应该完成
    MEDIUM = 2    # 最好完成
    LOW = 3       # 可选完成


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class EvolutionTask:
    """进化任务"""
    id: str
    name: str
    description: str
    priority: TaskPriority
    estimated_duration_min: int
    risk_level: float  # 0-1
    auto_execute: bool  # 是否自动执行
    command: str  # 执行命令
    validation_check: str  # 验证命令
    
    # 运行时状态
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class EvolutionReport:
    """进化报告"""
    session_id: str
    started_at: str
    completed_at: Optional[str]
    tasks_completed: int
    tasks_failed: int
    tasks_skipped: int
    overall_success: bool
    summary: str
    details: List[Dict]


class EvolutionController:
    """夜间进化控制器"""
    
    def __init__(self):
        self.session_id = f"EVO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.tasks: List[EvolutionTask] = []
        self.log_dir = Path("/root/.openclaw/workspace/logs/evolution")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir = Path("/root/.openclaw/workspace/.snapshots")
        
        # 初始化任务队列
        self._initialize_tasks()
    
    def _initialize_tasks(self):
        """初始化进化任务队列"""
        self.tasks = [
            # P0: 稳定性相关
            EvolutionTask(
                id="p0-snapshot",
                name="创建状态快照",
                description="保存当前系统完整状态",
                priority=TaskPriority.CRITICAL,
                estimated_duration_min=2,
                risk_level=0.05,
                auto_execute=True,
                command="python3 /root/.openclaw/workspace/scripts/stability_engine.py snapshot nightly",
                validation_check="test -f /root/.openclaw/workspace/.snapshots/snapshot_*_nightly.json",
            ),
            EvolutionTask(
                id="p0-drift-check",
                name="漂移检测",
                description="检测系统漂移情况",
                priority=TaskPriority.CRITICAL,
                estimated_duration_min=1,
                risk_level=0.1,
                auto_execute=True,
                command="python3 /root/.openclaw/workspace/scripts/stability_engine.py drift",
                validation_check="echo 'drift check completed'",
            ),
            
            # 学习债务处理
            EvolutionTask(
                id="learning-debt",
                name="处理学习债务",
                description="处理Signal≥7的学习债务",
                priority=TaskPriority.HIGH,
                estimated_duration_min=30,
                risk_level=0.2,
                auto_execute=True,
                command="python3 /root/.openclaw/workspace/scripts/learning_processor.py --min-signal 7",
                validation_check="echo 'learning processed'",
            ),
            
            # Moltbook 深度扫描
            EvolutionTask(
                id="moltbook-scan",
                name="Moltbook情报扫描",
                description="深度扫描Moltbook社区",
                priority=TaskPriority.HIGH,
                estimated_duration_min=10,
                risk_level=0.1,
                auto_execute=True,
                command="python3 /root/.openclaw/workspace/scripts/moltbook-unified.py --deep",
                validation_check="test -f /root/.openclaw/workspace/reports/MOLT-*.md",
            ),
            
            # 系统维护
            EvolutionTask(
                id="system-maintenance",
                name="系统维护",
                description="备份、日志轮转、健康检查",
                priority=TaskPriority.MEDIUM,
                estimated_duration_min=5,
                risk_level=0.1,
                auto_execute=True,
                command="python3 /root/.openclaw/workspace/scripts/unified-monitor.py --fix",
                validation_check="echo 'maintenance done'",
            ),
            
            # Git 同步
            EvolutionTask(
                id="git-sync",
                name="Git自动同步",
                description="提交并推送本地变更",
                priority=TaskPriority.MEDIUM,
                estimated_duration_min=3,
                risk_level=0.3,
                auto_execute=False,  # 需要确认
                command="/root/.openclaw/workspace/scripts/conditional-git-sync.sh",
                validation_check="git status",
            ),
            
            # 高Signal内容内化
            EvolutionTask(
                id="deep-learning",
                name="深度学习闭环",
                description="L3架构级深度学习",
                priority=TaskPriority.HIGH,
                estimated_duration_min=45,
                risk_level=0.25,
                auto_execute=True,
                command="python3 /root/.openclaw/workspace/scripts/evolution-unified.py --mode deep",
                validation_check="echo 'deep learning completed'",
            ),
        ]
    
    def evaluate_risk(self, task: EvolutionTask) -> Tuple[bool, str]:
        """
        评估任务风险
        Returns: (是否可以自动执行, 原因)
        """
        # 使用P0的漂移检测
        drift_result = self._check_system_drift()
        if drift_result['needs_intervention']:
            return False, f"系统漂移检测异常: {drift_result['score']}"
        
        # 使用P1的认知安全
        if task.risk_level > 0.5:
            return False, f"高风险任务 (risk={task.risk_level})"
        
        # 使用P2的自主性验证
        if not task.auto_execute:
            return False, "任务标记为需人工确认"
        
        return True, "风险可接受"
    
    def _check_system_drift(self) -> Dict:
        """检查系统漂移"""
        try:
            result = subprocess.run(
                ["python3", "/root/.openclaw/workspace/scripts/stability_engine.py", "status"],
                capture_output=True, text=True, timeout=10
            )
            # 简化解析
            output = result.stdout
            
            # 精确解析"需要干预"的值
            needs_intervention = False
            for line in output.split('\n'):
                if '需要干预' in line:
                    needs_intervention = '是' in line
                    break
            
            # 尝试提取评分 - 越高越好
            score = 1.0
            for line in output.split('\n'):
                if '综合评分' in line or 'overall_score' in line.lower():
                    try:
                        score_str = line.split(':')[1].strip().rstrip('%')
                        score = float(score_str) / 100
                    except:
                        pass
            
            return {
                'needs_intervention': needs_intervention,
                'score': score,
                'output': output[:200],
            }
        except Exception as e:
            return {
                'needs_intervention': True,
                'score': 0.0,
                'error': str(e),
            }
    
    def execute_task(self, task: EvolutionTask) -> bool:
        """执行单个任务"""
        print(f"\n[EXEC] {task.name} ({task.id})")
        print(f"       {task.description}")
        
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        try:
            # 执行命令
            result = subprocess.run(
                task.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=task.estimated_duration_min * 60 * 2,  # 2倍预估时间
                cwd="/root/.openclaw/workspace"
            )
            
            task.completed_at = time.time()
            
            if result.returncode == 0:
                task.status = TaskStatus.COMPLETED
                task.result = result.stdout[:500]  # 截断输出
                print(f"       ✅ 完成")
                return True
            else:
                task.status = TaskStatus.FAILED
                task.error = result.stderr[:500]
                print(f"       ❌ 失败: {task.error[:100]}")
                return False
                
        except subprocess.TimeoutExpired:
            task.status = TaskStatus.FAILED
            task.error = "执行超时"
            print(f"       ⏱️ 超时")
            return False
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            print(f"       ❌ 异常: {e}")
            return False
    
    def run_evolution_cycle(self, dry_run: bool = False) -> EvolutionReport:
        """运行完整的进化周期"""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║     夜间自主进化模式 - {self.session_id}           ║
╚══════════════════════════════════════════════════════════╝
启动时间: {datetime.now().isoformat()}
任务数量: {len(self.tasks)}
""")
        
        started_at = datetime.now().isoformat()
        completed_tasks = 0
        failed_tasks = 0
        skipped_tasks = 0
        details = []
        
        # 按优先级排序
        sorted_tasks = sorted(self.tasks, key=lambda t: t.priority.value)
        
        for task in sorted_tasks:
            # 风险评估
            can_auto, reason = self.evaluate_risk(task)
            
            print(f"\n[TASK] {task.name} | 优先级: {task.priority.name} | 风险: {task.risk_level:.0%}")
            print(f"       自动执行: {'✅' if can_auto else '❌'} ({reason})")
            
            if dry_run:
                print(f"       [DRY RUN] 跳过执行")
                task.status = TaskStatus.SKIPPED
                skipped_tasks += 1
                continue
            
            if not can_auto:
                print(f"       跳过: 需要人工确认")
                task.status = TaskStatus.SKIPPED
                skipped_tasks += 1
                continue
            
            # 执行任务
            success = self.execute_task(task)
            if success:
                completed_tasks += 1
            else:
                failed_tasks += 1
                # 关键任务失败是否停止?
                if task.priority == TaskPriority.CRITICAL:
                    print(f"\n⚠️ 关键任务失败，停止进化周期")
                    break
            
            details.append({
                'id': task.id,
                'name': task.name,
                'status': task.status.value,
                'duration': (task.completed_at - task.started_at) if task.completed_at else None,
            })
            
            # 任务间短暂休息
            time.sleep(1)
        
        # 生成报告
        overall_success = failed_tasks == 0 and completed_tasks > 0
        completed_at = datetime.now().isoformat()
        
        report = EvolutionReport(
            session_id=self.session_id,
            started_at=started_at,
            completed_at=completed_at,
            tasks_completed=completed_tasks,
            tasks_failed=failed_tasks,
            tasks_skipped=skipped_tasks,
            overall_success=overall_success,
            summary=f"完成 {completed_tasks}/{len(self.tasks)} 任务, 失败 {failed_tasks}, 跳过 {skipped_tasks}",
            details=details,
        )
        
        self._save_report(report)
        self._print_summary(report)
        
        return report
    
    def _save_report(self, report: EvolutionReport):
        """保存报告"""
        report_file = self.log_dir / f"{self.session_id}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'session_id': report.session_id,
                'started_at': report.started_at,
                'completed_at': report.completed_at,
                'tasks_completed': report.tasks_completed,
                'tasks_failed': report.tasks_failed,
                'tasks_skipped': report.tasks_skipped,
                'overall_success': report.overall_success,
                'summary': report.summary,
                'details': report.details,
            }, f, indent=2, default=str)
        print(f"\n[REPORT] 报告已保存: {report_file}")
    
    def _print_summary(self, report: EvolutionReport):
        """打印摘要"""
        duration = "未知"
        if report.completed_at:
            try:
                start = datetime.fromisoformat(report.started_at)
                end = datetime.fromisoformat(report.completed_at)
                duration = str(end - start).split('.')[0]
            except:
                pass
        
        print(f"""
╔══════════════════════════════════════════════════════════╗
║              进化周期完成摘要                            ║
╠══════════════════════════════════════════════════════════╣
║ 会话ID:     {report.session_id:<36} ║
║ 总耗时:     {duration:<36} ║
║ 完成任务:   {report.tasks_completed}/{len(self.tasks)} {' ' * (35 - len(str(report.tasks_completed)) - len(str(len(self.tasks))))} ║
║ 失败任务:   {report.tasks_failed}{' ' * 41} ║
║ 跳过任务:   {report.tasks_skipped}{' ' * 41} ║
║ 整体状态:   {'✅ 成功' if report.overall_success else '❌ 部分失败':<36} ║
╚══════════════════════════════════════════════════════════╝
""")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='夜间自主进化模式')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际执行')
    parser.add_argument('--list', action='store_true', help='列出所有任务')
    parser.add_argument('--task', type=str, help='只执行指定任务')
    
    args = parser.parse_args()
    
    controller = EvolutionController()
    
    if args.list:
        print("\n进化任务列表:")
        print("-" * 60)
        for task in sorted(controller.tasks, key=lambda t: t.priority.value):
            print(f"[{task.priority.name:8}] {task.id:20} {task.name}")
            print(f"           自动执行: {'是' if task.auto_execute else '否'} | 风险: {task.risk_level:.0%}")
            print(f"           {task.description}")
        return
    
    if args.task:
        # 只执行指定任务
        task = next((t for t in controller.tasks if t.id == args.task), None)
        if task:
            controller.execute_task(task)
        else:
            print(f"未知任务: {args.task}")
        return
    
    # 运行完整进化周期
    report = controller.run_evolution_cycle(dry_run=args.dry_run)
    
    # 退出码
    sys.exit(0 if report.overall_success else 1)


if __name__ == "__main__":
    main()
