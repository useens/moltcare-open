#!/usr/bin/env python3
"""漂移检测器 - 基于状态快照对比检测系统漂移"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import argparse


@dataclass
class DriftAlert:
    """漂移警告"""
    category: str
    severity: str
    metric: str
    expected: Any
    actual: Any
    delta: Any
    message: str = ""


class DriftThresholds:
    """漂移阈值配置"""
    
    DEFAULT_THRESHOLDS = {
        'memory_usage_percent': {'warning': 80, 'critical': 90},
        'disk_usage_percent': {'warning': 80, 'critical': 95},
        'load_average_1m': {'warning': 5.0, 'critical': 10.0},
        'disconnected_services': {'warning': 1, 'critical': 3},
        'skill_error_increase': {'warning': 1, 'critical': 5},
    }
    
    def __init__(self, custom: Optional[Dict] = None):
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        if custom:
            self.thresholds.update(custom)
    
    def get(self, metric: str) -> Optional[Dict]:
        return self.thresholds.get(metric)


class DriftDetector:
    """漂移检测器"""
    
    def __init__(self, thresholds: Optional[DriftThresholds] = None):
        self.thresholds = thresholds or DriftThresholds()
        self.alerts: List[DriftAlert] = []
    
    def detect(self, baseline: Dict, current: Dict) -> List[DriftAlert]:
        """对比两个快照，检测漂移"""
        self.alerts = []
        
        self._check_system(baseline.get('system', {}), current.get('system', {}))
        self._check_resources(baseline.get('resources', {}), current.get('resources', {}))
        self._check_cron(baseline.get('cron', {}), current.get('cron', {}))
        self._check_skills(baseline.get('skills', {}), current.get('skills', {}))
        
        # 按严重级别排序
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        self.alerts.sort(key=lambda a: severity_order.get(a.severity, 99))
        
        return self.alerts
    
    def _check_system(self, baseline: Dict, current: Dict):
        """检测系统状态漂移"""
        base_uptime = baseline.get('uptime', 0)
        curr_uptime = current.get('uptime', 0)
        
        # 检测系统重启
        if curr_uptime < base_uptime - 60:
            self._add_alert('system', 'critical', 'system_reboot_detected',
                          base_uptime, curr_uptime, curr_uptime - base_uptime,
                          message="系统意外重启检测")
    
    def _check_resources(self, baseline: Dict, current: Dict):
        """检测资源使用漂移"""
        # 内存使用
        base_mem = baseline.get('memory', {}).get('usage_percent', 0)
        curr_mem = current.get('memory', {}).get('usage_percent', 0)
        self._check_threshold('resources', 'memory_usage_percent', 
                            base_mem, curr_mem, curr_mem - base_mem)
        
        # 磁盘使用
        base_disks = baseline.get('disk', {}).get('partitions', [])
        curr_disks = current.get('disk', {}).get('partitions', [])
        
        for curr in curr_disks:
            base = next((d for d in base_disks if d.get('mount') == curr.get('mount')), None)
            if base:
                base_u = base.get('usage_percent', 0)
                curr_u = curr.get('usage_percent', 0)
                self._check_threshold('resources', f"disk_{curr['mount']}",
                                    base_u, curr_u, curr_u - base_u)
    
    def _check_cron(self, baseline: Dict, current: Dict):
        """检测Cron任务漂移"""
        base_jobs = {j.get('id', ''): j for j in baseline.get('jobs', [])}
        curr_jobs = {j.get('id', ''): j for j in current.get('jobs', [])}
        
        status_changes = sum(
            1 for jid, cj in curr_jobs.items() 
            if jid in base_jobs and base_jobs[jid].get('status') != cj.get('status')
        )
        
        if status_changes > 0:
            self._add_alert('cron', 'warning', 'cron_status_changes',
                          0, status_changes, status_changes,
                          message=f"{status_changes} 个Cron任务状态变化")
    
    def _check_skills(self, baseline: Dict, current: Dict):
        """检测技能服务漂移"""
        base_active = baseline.get('active_count', 0)
        curr_active = current.get('active_count', 0)
        
        if curr_active < base_active:
            self._add_alert('skills', 'warning', 'skill_count_decrease',
                          base_active, curr_active, curr_active - base_active,
                          message=f"活跃技能减少 {base_active - curr_active} 个")
    
    def _check_threshold(self, category: str, metric: str, 
                        expected: float, actual: float, delta: float):
        """检查是否超出阈值"""
        config = self.thresholds.get(metric)
        if not config:
            return
        
        severity = None
        if actual >= config['critical']:
            severity = 'critical'
        elif actual >= config['warning']:
            severity = 'warning'
        
        if severity:
            self._add_alert(category, severity, metric, expected, actual, delta)
    
    def _add_alert(self, category: str, severity: str, metric: str,
                   expected: Any, actual: Any, delta: Any, message: str = ""):
        """添加警报"""
        self.alerts.append(DriftAlert(
            category=category, severity=severity, metric=metric,
            expected=expected, actual=actual, delta=delta, message=message
        ))


def load_snapshot(path: str) -> Dict:
    """加载快照文件"""
    with open(path, 'r') as f:
        return json.load(f)


def format_alert(alert: DriftAlert) -> str:
    """格式化警报输出"""
    emoji = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(alert.severity, '⚪')
    return (f"{emoji} [{alert.severity.upper()}] {alert.category}/{alert.metric}\n"
            f"   预期: {alert.expected} → 实际: {alert.actual} (Δ={alert.delta})\n"
            f"   {alert.message}")


def main():
    parser = argparse.ArgumentParser(description='漂移检测器')
    parser.add_argument('--baseline', '-b', required=True, help='基线快照文件')
    parser.add_argument('--current', '-c', required=True, help='当前快照文件')
    parser.add_argument('--output', '-o', help='输出报告到文件')
    parser.add_argument('--fail-on-critical', action='store_true', 
                       help='发现严重漂移时返回非零退出码')
    args = parser.parse_args()
    
    try:
        baseline = load_snapshot(args.baseline)
        current = load_snapshot(args.current)
    except Exception as e:
        print(f"错误: 无法加载快照文件: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 执行漂移检测
    detector = DriftDetector()
    alerts = detector.detect(baseline, current)
    
    # 输出报告
    lines = [
        "=" * 60,
        "漂移检测报告",
        "=" * 60,
        f"基线: {args.baseline}",
        f"当前: {args.current}",
        f"检测到: {len(alerts)} 个漂移",
        "-" * 60
    ]
    
    critical_count = sum(1 for a in alerts if a.severity == 'critical')
    warning_count = sum(1 for a in alerts if a.severity == 'warning')
    
    if alerts:
        lines.append("")
        for alert in alerts:
            lines.append(format_alert(alert))
            lines.append("")
    else:
        lines.append("✅ 未发现明显漂移")
    
    lines.extend([
        "-" * 60,
        f"总结: {critical_count} 严重, {warning_count} 警告",
        "=" * 60
    ])
    
    report = '\n'.join(lines)
    print(report)
    
    # 保存报告
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\n报告已保存: {args.output}")
    
    # 退出码
    if args.fail_on_critical and critical_count > 0:
        sys.exit(2)
    if warning_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
