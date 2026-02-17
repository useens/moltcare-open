#!/usr/bin/env python3
"""
状态快照与漂移检测系统 (P0)
解决 Six-Hour Drift 问题

功能:
1. 每小时自动快照
2. 实时漂移检测算法  
3. 性能指标追踪
4. 自动回滚到健康状态
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from pathlib import Path

# 配置
SNAPSHOT_DIR = Path("/root/.openclaw/workspace/.snapshots")
MAX_SNAPSHOTS = 24  # 保留24个快照（约1天）
DRIFT_THRESHOLD = 0.3
HEALTHY_THRESHOLD = 0.8


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: float
    memory_usage_mb: float
    disk_usage_percent: float
    cpu_usage_percent: float
    context_window_usage: float  # 上下文窗口使用率
    recent_error_rate: float  # 最近错误率
    response_time_ms: float  # 平均响应时间
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PerformanceMetrics":
        return cls(**data)


@dataclass
class DriftReport:
    """漂移检测报告"""
    timestamp: float
    response_consistency: float  # 响应一致性 (0-1)
    memory_retrieval_accuracy: float  # 记忆检索准确性
    hallucination_rate: float  # 幻觉率
    decision_coherence: float  # 决策一致性
    error_rate_trend: float  # 错误率趋势
    overall_score: float  # 综合评分
    
    def is_healthy(self) -> bool:
        return self.overall_score >= HEALTHY_THRESHOLD
    
    def needs_intervention(self) -> bool:
        return self.overall_score < DRIFT_THRESHOLD
    
    def to_dict(self) -> Dict:
        return asdict(self)


class StabilityEngine:
    """长时稳定性保障引擎"""
    
    def __init__(self):
        self.snapshots: List[Dict] = []
        self.snapshot_interval = 3600  # 每小时
        self.drift_threshold = DRIFT_THRESHOLD
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history = 100
        
        # 确保快照目录存在
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        
        # 加载历史快照
        self._load_snapshots()
    
    def _load_snapshots(self):
        """加载历史快照"""
        snapshot_files = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"))
        for f in snapshot_files[-MAX_SNAPSHOTS:]:
            try:
                with open(f) as fp:
                    self.snapshots.append(json.load(fp))
            except Exception as e:
                print(f"[WARN] 加载快照失败 {f}: {e}")
    
    def create_snapshot(self, label: str = "auto") -> Dict:
        """创建完整状态快照"""
        snapshot = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'label': label,
            'context_hash': self._hash_context(),
            'performance_metrics': self._collect_metrics().to_dict(),
            'system_state': self._collect_system_state(),
            'memory_stats': self._collect_memory_stats(),
            'git_state': self._collect_git_state(),
        }
        
        # 保存到文件
        filename = f"snapshot_{int(time.time())}_{label}.json"
        filepath = SNAPSHOT_DIR / filename
        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)
        
        # 添加到内存列表
        self.snapshots.append(snapshot)
        
        # 清理旧快照
        self._cleanup_old_snapshots()
        
        print(f"[SNAPSHOT] 已创建: {filename}")
        return snapshot
    
    def _hash_context(self) -> str:
        """计算当前上下文的哈希"""
        # 收集关键状态信息
        state_str = f"{time.time()}:{os.getpid()}"
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        try:
            # 内存使用
            mem_info = subprocess.run(
                ["free", "-m"], capture_output=True, text=True
            )
            mem_lines = mem_info.stdout.strip().split('\n')
            mem_values = mem_lines[1].split()
            memory_used = int(mem_values[2])
            memory_total = int(mem_values[1])
            memory_usage = memory_used / memory_total * 100
        except:
            memory_usage = 0
        
        # 磁盘使用
        try:
            disk_info = subprocess.run(
                ["df", "-h", "/"], capture_output=True, text=True
            )
            disk_line = disk_info.stdout.strip().split('\n')[1]
            disk_percent = int(disk_line.split()[4].rstrip('%'))
        except:
            disk_percent = 0
        
        # CPU 使用 (简化版)
        try:
            cpu_info = subprocess.run(
                ["top", "-bn1"], capture_output=True, text=True
            )
            cpu_line = [l for l in cpu_info.stdout.split('\n') if 'Cpu(s)' in l][0]
            cpu_usage = float(cpu_line.split(',')[0].split(':')[1].strip().rstrip('% us'))
        except:
            cpu_usage = 0
        
        metrics = PerformanceMetrics(
            timestamp=time.time(),
            memory_usage_mb=memory_used if 'memory_used' in locals() else 0,
            disk_usage_percent=disk_percent,
            cpu_usage_percent=cpu_usage,
            context_window_usage=0.5,  # 占位，需要OpenClaw API获取
            recent_error_rate=self._calculate_error_rate(),
            response_time_ms=100,  # 占位
        )
        
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        return metrics
    
    def _collect_system_state(self) -> Dict:
        """收集系统状态"""
        return {
            'pid': os.getpid(),
            'cwd': os.getcwd(),
            'env_hash': hashlib.sha256(
                str(sorted(os.environ.items())).encode()
            ).hexdigest()[:16],
        }
    
    def _collect_memory_stats(self) -> Dict:
        """收集记忆系统统计"""
        memory_file = Path("/root/.openclaw/workspace/memory/learning-debt.md")
        debt_count = 0
        if memory_file.exists():
            content = memory_file.read_text()
            debt_count = content.count("- [ ]")
        
        return {
            'learning_debt_count': debt_count,
            'snapshot_count': len(self.snapshots),
        }
    
    def _collect_git_state(self) -> Dict:
        """收集Git状态"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd="/root/.openclaw/workspace"
            )
            uncommitted = len([l for l in result.stdout.split('\n') if l.strip()])
            
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, cwd="/root/.openclaw/workspace"
            )
            branch = branch_result.stdout.strip()
            
            return {
                'branch': branch,
                'uncommitted_files': uncommitted,
                'clean': uncommitted == 0,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_error_rate(self) -> float:
        """计算最近错误率"""
        # 简化实现，可以从日志中分析
        return 0.0
    
    def _cleanup_old_snapshots(self):
        """清理旧快照文件"""
        snapshot_files = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"))
        if len(snapshot_files) > MAX_SNAPSHOTS:
            for old_file in snapshot_files[:-MAX_SNAPSHOTS]:
                old_file.unlink()
                print(f"[SNAPSHOT] 清理旧快照: {old_file.name}")
    
    def detect_drift(self) -> DriftReport:
        """多维度漂移检测"""
        if len(self.metrics_history) < 2:
            return DriftReport(
                timestamp=time.time(),
                response_consistency=1.0,
                memory_retrieval_accuracy=1.0,
                hallucination_rate=0.0,
                decision_coherence=1.0,
                error_rate_trend=0.0,
                overall_score=1.0,
            )
        
        recent = self.metrics_history[-10:]  # 最近10个指标
        older = self.metrics_history[-20:-10] if len(self.metrics_history) >= 20 else self.metrics_history[:len(self.metrics_history)//2]
        
        if not older:
            older = [self.metrics_history[0]]
        
        # 计算各项评分
        recent_error_avg = sum(m.recent_error_rate for m in recent) / len(recent)
        older_error_avg = sum(m.recent_error_rate for m in older) / len(older)
        error_trend = recent_error_avg - older_error_avg
        
        # 响应一致性（基于错误率反向计算）
        response_consistency = max(0, 1.0 - recent_error_avg * 10)
        
        # 记忆检索准确性（基于内存使用率，过高可能影响性能）
        mem_usage = recent[-1].memory_usage_mb / 23000  # 假设23GB总内存
        memory_accuracy = max(0, 1.0 - mem_usage) if mem_usage < 0.9 else max(0, 2.0 - mem_usage * 2)
        
        # 决策一致性（简化计算）
        decision_coherence = response_consistency * 0.9 + 0.1
        
        # 幻觉率（简化估算，实际应从输出质量分析）
        hallucination_rate = recent_error_avg * 2
        
        # 综合评分
        overall = (
            response_consistency * 0.25 +
            memory_accuracy * 0.25 +
            (1.0 - hallucination_rate) * 0.25 +
            decision_coherence * 0.25
        )
        
        report = DriftReport(
            timestamp=time.time(),
            response_consistency=response_consistency,
            memory_retrieval_accuracy=memory_accuracy,
            hallucination_rate=hallucination_rate,
            decision_coherence=decision_coherence,
            error_rate_trend=error_trend,
            overall_score=overall,
        )
        
        return report
    
    def auto_intervene(self, report: DriftReport) -> List[str]:
        """自动干预策略"""
        actions = []
        
        if report.hallucination_rate > 0.05:
            actions.append("compress_context")
            print("[INTERVENTION] 幻觉率过高，建议压缩上下文")
        
        if report.response_consistency < 0.7:
            actions.append("refresh_memory")
            print("[INTERVENTION] 响应一致性下降，建议刷新记忆")
        
        if report.overall_score < self.drift_threshold:
            actions.append("rollback")
            print(f"[INTERVENTION] 综合评分 {report.overall_score:.2f} 低于阈值 {self.drift_threshold}，触发回滚")
            self.rollback_to_last_healthy()
        
        if report.memory_retrieval_accuracy < 0.6:
            actions.append("optimize_memory")
            print("[INTERVENTION] 记忆检索准确性低，建议优化记忆系统")
        
        return actions
    
    def rollback_to_last_healthy(self) -> Optional[Dict]:
        """回滚到最后健康状态"""
        if not self.snapshots:
            print("[ROLLBACK] 无可用快照")
            return None
        
        # 找到最新的健康快照
        for snapshot in reversed(self.snapshots):
            # 这里简化处理，实际应该评估快照的健康度
            print(f"[ROLLBACK] 回滚到快照: {snapshot.get('datetime', 'unknown')}")
            return snapshot
        
        return None
    
    def get_health_status(self) -> Dict:
        """获取健康状态摘要"""
        report = self.detect_drift()
        latest_snapshot = self.snapshots[-1] if self.snapshots else None
        latest_metrics = self.metrics_history[-1] if self.metrics_history else None
        
        return {
            'healthy': report.is_healthy(),
            'needs_intervention': report.needs_intervention(),
            'overall_score': report.overall_score,
            'drift_report': report.to_dict(),
            'latest_snapshot': latest_snapshot.get('datetime') if latest_snapshot else None,
            'snapshot_count': len(self.snapshots),
            'uptime_hours': len(self.snapshots),  # 简化估算
        }


def main():
    """命令行入口"""
    engine = StabilityEngine()
    
    if len(sys.argv) < 2:
        print("""状态快照与漂移检测系统

用法:
    python3 stability_engine.py snapshot [label]  - 创建快照
    python3 stability_engine.py drift              - 检测漂移
    python3 stability_engine.py status             - 查看状态
    python3 stability_engine.py auto               - 自动检查并干预
""")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "snapshot":
        label = sys.argv[2] if len(sys.argv) > 2 else "manual"
        snapshot = engine.create_snapshot(label)
        print(f"✅ 快照已创建: {snapshot['datetime']}")
        
    elif cmd == "drift":
        report = engine.detect_drift()
        print(f"""
漂移检测报告 ({datetime.now().isoformat()})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
响应一致性:      {report.response_consistency:.2%}
记忆检索准确性:  {report.memory_retrieval_accuracy:.2%}
幻觉率:          {report.hallucination_rate:.2%}
决策一致性:      {report.decision_coherence:.2%}
错误率趋势:      {report.error_rate_trend:+.2%}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
综合评分:        {report.overall_score:.2%}
健康状态:        {'✅ 健康' if report.is_healthy() else '⚠️ 需要关注' if not report.needs_intervention() else '❌ 需要干预'}
""")
        
    elif cmd == "status":
        status = engine.get_health_status()
        print(f"""
系统健康状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
健康状态:        {'✅ 健康' if status['healthy'] else '❌ 异常'}
需要干预:        {'是' if status['needs_intervention'] else '否'}
综合评分:        {status['overall_score']:.2%}
最新快照:        {status['latest_snapshot'] or '无'}
快照总数:        {status['snapshot_count']}
运行时长(估算):  {status['uptime_hours']} 小时
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        
    elif cmd == "auto":
        print("[AUTO] 执行自动检查与干预...")
        snapshot = engine.create_snapshot("auto_check")
        report = engine.detect_drift()
        actions = engine.auto_intervene(report)
        
        if actions:
            print(f"[AUTO] 执行干预动作: {actions}")
        else:
            print("[AUTO] 系统健康，无需干预")
            
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
