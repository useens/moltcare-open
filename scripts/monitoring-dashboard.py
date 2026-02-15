#!/usr/bin/env python3
"""
系统监控仪表板 v2.0
System Monitoring Dashboard

功能:
- 实时系统资源监控
- 超进化状态可视化
- 学习债务追踪
- 自动化任务状态
- 生成可视化报告

使用: python3 monitoring-dashboard.py [--web|--cli|--export]
"""

import os
import json
import subprocess
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys


class MonitoringDashboard:
    """系统监控仪表板"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.memory_dir = self.workspace / "memory"
        self.report_dir = self.workspace / "reports"
        
        # 状态数据
        self.system_stats = {}
        self.hyper_status = {}
        self.learning_debt = {}
        self.automation_status = {}
        self.script_health = {}
    
    def generate_dashboard(self, output_format: str = "cli") -> str:
        """生成监控仪表板"""
        print(f"\n{'='*75}")
        print(f"📊 系统监控仪表板 v2.0")
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*75}\n")
        
        # 收集所有数据
        self.collect_system_stats()
        self.collect_hyper_status()
        self.collect_learning_debt()
        self.collect_automation_status()
        self.check_script_health()
        
        # 根据格式输出
        if output_format == "cli":
            return self.render_cli_dashboard()
        elif output_format == "json":
            return self.render_json_dashboard()
        elif output_format == "markdown":
            return self.render_markdown_dashboard()
        else:
            return self.render_cli_dashboard()
    
    def collect_system_stats(self):
        """收集系统统计"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存
        memory = psutil.virtual_memory()
        
        # 磁盘
        disk = psutil.disk_usage('/')
        
        # 网络
        net_io = psutil.net_io_counters()
        
        # 负载
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        
        # 运行时间
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        self.system_stats = {
            "cpu": {
                "usage": cpu_percent,
                "cores": cpu_count,
                "status": "critical" if cpu_percent > 90 else "warning" if cpu_percent > 70 else "ok"
            },
            "memory": {
                "total_gb": memory.total / (1024**3),
                "used_gb": memory.used / (1024**3),
                "usage": memory.percent,
                "status": "critical" if memory.percent > 95 else "warning" if memory.percent > 80 else "ok"
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "free_gb": disk.free / (1024**3),
                "usage": disk.percent,
                "status": "critical" if disk.percent > 95 else "warning" if disk.percent > 80 else "ok"
            },
            "network": {
                "bytes_sent_mb": net_io.bytes_sent / (1024**2),
                "bytes_recv_mb": net_io.bytes_recv / (1024**2)
            },
            "load": {
                "1min": load_avg[0],
                "5min": load_avg[1],
                "15min": load_avg[2]
            },
            "uptime": {
                "days": uptime.days,
                "hours": uptime.seconds // 3600,
                "minutes": (uptime.seconds % 3600) // 60
            }
        }
    
    def collect_hyper_status(self):
        """收集超进化状态"""
        hyper_state_file = self.memory_dir / "hyper-evolution-state.json"
        
        if hyper_state_file.exists():
            with open(hyper_state_file, 'r', encoding='utf-8') as f:
                try:
                    state = json.load(f)
                    
                    # 计算运行时间
                    if state.get("active") and state.get("start_time"):
                        start = datetime.fromisoformat(state["start_time"])
                        runtime = datetime.now() - start
                        runtime_hours = runtime.total_seconds() / 3600
                    else:
                        runtime_hours = 0
                    
                    self.hyper_status = {
                        "active": state.get("active", False),
                        "mode": state.get("mode", "normal"),
                        "version": state.get("version", "unknown"),
                        "runtime_hours": round(runtime_hours, 2),
                        "deep_learning_count": state.get("deep_learning_count", 0),
                        "knowledge_updates": state.get("knowledge_updates", 0),
                        "learning_debt_cleared": state.get("learning_debt_cleared", 0)
                    }
                except:
                    self.hyper_status = {"active": False, "error": "无法读取状态"}
        else:
            self.hyper_status = {"active": False, "mode": "normal"}
    
    def collect_learning_debt(self):
        """收集学习债务"""
        learning_debt_file = self.memory_dir / "learning-debt.md"
        
        if learning_debt_file.exists():
            with open(learning_debt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 简单统计
                lines = content.split('\n')
                total_lines = len(lines)
                
                # 统计未处理条目
                pending_count = content.count("待处理:")
                high_signal_count = content.count("Signal 9") + content.count("Signal 8")
                
                # 获取文件大小和修改时间
                stat = learning_debt_file.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                self.learning_debt = {
                    "exists": True,
                    "size_kb": stat.st_size / 1024,
                    "lines": total_lines,
                    "high_signal_items": high_signal_count,
                    "last_update": mtime.strftime('%Y-%m-%d %H:%M'),
                    "status": "critical" if high_signal_count > 10 else "warning" if high_signal_count > 5 else "ok"
                }
        else:
            self.learning_debt = {"exists": False, "status": "ok"}
    
    def collect_automation_status(self):
        """收集自动化任务状态"""
        self.automation_status = {
            "log_manager": self.check_automation_state("log-automation-state.json"),
            "backup_check": self.check_automation_state("backup-check-state.json"),
            "health_check": self.check_automation_state("health-state.json"),
            "intel_scheduler": self.check_automation_state("intel-scheduler-state.json")
        }
    
    def check_automation_state(self, state_file: str) -> Dict:
        """检查自动化状态"""
        state_path = self.memory_dir / state_file
        
        if state_path.exists():
            with open(state_path, 'r', encoding='utf-8') as f:
                try:
                    state = json.load(f)
                    last_run = state.get("last_run")
                    if last_run:
                        last_time = datetime.fromisoformat(last_run)
                        hours_ago = (datetime.now() - last_time).total_seconds() / 3600
                        
                        return {
                            "last_run": last_run,
                            "hours_ago": round(hours_ago, 1),
                            "status": "ok" if hours_ago < 24 else "warning" if hours_ago < 48 else "critical"
                        }
                except:
                    pass
        
        return {"status": "unknown", "last_run": None}
    
    def check_script_health(self):
        """检查关键脚本健康"""
        critical_scripts = [
            "scripts/hyper-evolution.py",
            "scripts/collect-web-intel-fast.py",
            "scripts/meta-learning-engine.py",
            "scripts/bootstrapping-system.py",
            "scripts/auto-log-manager.py",
            "scripts/auto-backup-check.py",
            "scripts/auto-health-check.py"
        ]
        
        script_status = {}
        for script in critical_scripts:
            script_path = self.workspace / script
            if script_path.exists():
                stat = script_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                age_days = (datetime.now() - mtime).total_seconds() / 86400
                
                # 检查语法
                syntax_ok = self.check_script_syntax(script_path)
                
                script_status[script] = {
                    "exists": True,
                    "size_kb": stat.st_size / 1024,
                    "last_modified": mtime.strftime('%Y-%m-%d'),
                    "age_days": round(age_days, 1),
                    "syntax_ok": syntax_ok,
                    "status": "ok" if syntax_ok else "error"
                }
            else:
                script_status[script] = {"exists": False, "status": "missing"}
        
        self.script_health = script_status
    
    def check_script_syntax(self, script_path: Path) -> bool:
        """检查脚本语法"""
        try:
            result = subprocess.run(
                ["python3", "-m", "py_compile", str(script_path)],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def render_cli_dashboard(self) -> str:
        """渲染CLI仪表板"""
        output = []
        
        # 系统资源
        output.append(f"{'─'*75}")
        output.append("🖥️  系统资源")
        output.append(f"{'─'*75}")
        
        cpu = self.system_stats["cpu"]
        memory = self.system_stats["memory"]
        disk = self.system_stats["disk"]
        
        cpu_icon = "🔴" if cpu["status"] == "critical" else "🟡" if cpu["status"] == "warning" else "🟢"
        mem_icon = "🔴" if memory["status"] == "critical" else "🟡" if memory["status"] == "warning" else "🟢"
        disk_icon = "🔴" if disk["status"] == "critical" else "🟡" if disk["status"] == "warning" else "🟢"
        
        output.append(f"  CPU:     {cpu_icon} {cpu['usage']:5.1f}% ({cpu['cores']}核)")
        output.append(f"  内存:    {mem_icon} {memory['usage']:5.1f}% ({memory['used_gb']:.1f}/{memory['total_gb']:.1f} GB)")
        output.append(f"  磁盘:    {disk_icon} {disk['usage']:5.1f}% ({disk['free_gb']:.1f} GB可用)")
        output.append(f"  运行时间: {self.system_stats['uptime']['days']}天 {self.system_stats['uptime']['hours']}小时")
        
        # 超进化状态
        output.append("")
        output.append(f"{'─'*75}")
        output.append("🚀 超进化状态")
        output.append(f"{'─'*75}")
        
        if self.hyper_status.get("active"):
            output.append(f"  状态:    🟢 运行中")
            output.append(f"  模式:    {self.hyper_status.get('mode', 'unknown')}")
            output.append(f"  版本:    {self.hyper_status.get('version', 'unknown')}")
            output.append(f"  运行时间: {self.hyper_status.get('runtime_hours', 0):.1f} 小时")
            output.append(f"  深度学习: {self.hyper_status.get('deep_learning_count', 0)} 次")
            output.append(f"  知识更新: {self.hyper_status.get('knowledge_updates', 0)} 次")
        else:
            output.append(f"  状态:    ⚪ 未运行 (正常模式)")
        
        # 学习债务
        output.append("")
        output.append(f"{'─'*75}")
        output.append("📚 学习债务")
        output.append(f"{'─'*75}")
        
        if self.learning_debt.get("exists"):
            debt_icon = "🔴" if self.learning_debt["status"] == "critical" else "🟡" if self.learning_debt["status"] == "warning" else "🟢"
            output.append(f"  文件大小: {self.learning_debt['size_kb']:.1f} KB")
            output.append(f"  总行数:   {self.learning_debt['lines']}")
            output.append(f"  高Signal: {debt_icon} {self.learning_debt['high_signal_items']} 条")
            output.append(f"  最后更新: {self.learning_debt['last_update']}")
        else:
            output.append("  暂无学习债务")
        
        # 自动化任务
        output.append("")
        output.append(f"{'─'*75}")
        output.append("⚙️  自动化任务")
        output.append(f"{'─'*75}")
        
        for task_name, task_status in self.automation_status.items():
            if task_status.get("last_run"):
                icon = "🟢" if task_status["status"] == "ok" else "🟡" if task_status["status"] == "warning" else "🔴"
                output.append(f"  {task_name:20s} {icon} {task_status['hours_ago']:.1f}小时前")
            else:
                output.append(f"  {task_name:20s} ⚪ 未运行")
        
        # 脚本健康
        output.append("")
        output.append(f"{'─'*75}")
        output.append("🔧 关键脚本健康")
        output.append(f"{'─'*75}")
        
        healthy = sum(1 for s in self.script_health.values() if s.get("status") == "ok")
        total = len(self.script_health)
        output.append(f"  健康脚本: {healthy}/{total}")
        
        for script, status in list(self.script_health.items())[:5]:
            icon = "🟢" if status.get("status") == "ok" else "🔴"
            output.append(f"  {icon} {script.split('/')[-1]}")
        
        output.append(f"{'─'*75}")
        
        dashboard_text = "\n".join(output)
        print(dashboard_text)
        
        return dashboard_text
    
    def render_json_dashboard(self) -> str:
        """渲染JSON格式"""
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "system": self.system_stats,
            "hyper_evolution": self.hyper_status,
            "learning_debt": self.learning_debt,
            "automation": self.automation_status,
            "scripts": self.script_health
        }
        
        # 保存到文件
        dashboard_file = self.report_dir / f"dashboard-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 JSON仪表板已保存: {dashboard_file}")
        return json.dumps(dashboard_data, indent=2)
    
    def render_markdown_dashboard(self) -> str:
        """渲染Markdown格式"""
        lines = []
        lines.append("# 系统监控仪表板")
        lines.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 系统资源
        lines.append("## 🖥️ 系统资源\n")
        lines.append(f"| 指标 | 值 | 状态 |")
        lines.append(f"|------|-----|------|")
        cpu = self.system_stats["cpu"]
        memory = self.system_stats["memory"]
        disk = self.system_stats["disk"]
        lines.append(f"| CPU | {cpu['usage']:.1f}% | {cpu['status']} |")
        lines.append(f"| 内存 | {memory['usage']:.1f}% | {memory['status']} |")
        lines.append(f"| 磁盘 | {disk['usage']:.1f}% | {disk['status']} |")
        
        # 超进化状态
        lines.append("\n## 🚀 超进化状态\n")
        if self.hyper_status.get("active"):
            lines.append(f"- **状态**: 运行中")
            lines.append(f"- **模式**: {self.hyper_status.get('mode', 'unknown')}")
            lines.append(f"- **运行时间**: {self.hyper_status.get('runtime_hours', 0):.1f} 小时")
        else:
            lines.append("- **状态**: 未运行")
        
        # 学习债务
        lines.append("\n## 📚 学习债务\n")
        if self.learning_debt.get("exists"):
            lines.append(f"- **文件大小**: {self.learning_debt['size_kb']:.1f} KB")
            lines.append(f"- **高Signal条目**: {self.learning_debt['high_signal_items']}")
        
        md_text = "\n".join(lines)
        
        # 保存到文件
        dashboard_file = self.report_dir / f"dashboard-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(md_text)
        
        print(f"📄 Markdown仪表板已保存: {dashboard_file}")
        return md_text


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="系统监控仪表板")
    parser.add_argument(
        "--format",
        choices=["cli", "json", "markdown"],
        default="cli",
        help="输出格式"
    )
    
    args = parser.parse_args()
    
    dashboard = MonitoringDashboard()
    result = dashboard.generate_dashboard(output_format=args.format)
    
    return result


if __name__ == "__main__":
    main()
