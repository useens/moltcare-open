#!/usr/bin/env python3
"""
智能健康检查自动化系统 v2.0
Intelligent Health Check Automation System

功能:
- 系统资源监控 (CPU/内存/磁盘/网络)
- 关键进程状态检查
- 自动化故障恢复
- 健康趋势分析
- 智能告警 (避免告警疲劳)

Cron设置: 每10分钟执行一次
"""

import os
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import psutil


class HealthAutomationSystem:
    """健康检查自动化系统"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.memory_dir = self.workspace / "memory"
        self.report_dir = self.workspace / "reports" / "health"
        self.log_file = self.workspace / "logs" / "health-automation.log"
        
        # 告警配置
        self.alert_config = {
            "cpu_warning": 70,
            "cpu_critical": 90,
            "memory_warning": 80,
            "memory_critical": 95,
            "disk_warning": 80,
            "disk_critical": 95,
            "alert_cooldown_minutes": 30,  # 告警冷却时间
        }
        
        # 关键进程
        self.critical_processes = [
            "openclaw",
            "python3",
            "node"
        ]
        
        # 关键文件
        self.critical_files = [
            "SOUL.md",
            "AGENTS.md",
            "scripts/hyper-evolution.py",
            "scripts/collect-web-intel-fast.py"
        ]
        
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # 状态跟踪
        self.current_status = {
            "cpu": {"usage": 0, "status": "ok"},
            "memory": {"usage": 0, "status": "ok"},
            "disk": {"usage": 0, "status": "ok"},
            "processes": {},
            "services": {}
        }
        
        self.alerts = []
        self.recovery_actions = []
        self.stats = {
            "checks_performed": 0,
            "issues_found": 0,
            "auto_recoveries": 0
        }
    
    def run_health_check(self) -> Dict:
        """运行完整健康检查"""
        print(f"\n{'='*70}")
        print(f"🏥 智能健康检查自动化系统 v2.0")
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        # 1. 系统资源检查
        self.check_system_resources()
        
        # 2. 关键进程检查
        self.check_critical_processes()
        
        # 3. 关键文件检查
        self.check_critical_files()
        
        # 4. 磁盘空间详细检查
        self.check_disk_health()
        
        # 5. 网络连通性
        self.check_network_connectivity()
        
        # 6. 执行自动恢复
        self.execute_auto_recovery()
        
        # 7. 趋势分析
        self.analyze_trends()
        
        # 8. 生成报告
        report = self.generate_report()
        
        # 9. 保存状态
        self.save_health_state()
        
        print(f"\n{'='*70}")
        print("✅ 健康检查完成")
        print(f"{'='*70}\n")
        
        return report
    
    def check_system_resources(self):
        """检查系统资源"""
        print("📊 检查系统资源...")
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        self.current_status["cpu"]["usage"] = cpu_percent
        
        if cpu_percent > self.alert_config["cpu_critical"]:
            self.current_status["cpu"]["status"] = "critical"
            self.add_alert("cpu_critical", f"CPU使用率过高: {cpu_percent}%")
        elif cpu_percent > self.alert_config["cpu_warning"]:
            self.current_status["cpu"]["status"] = "warning"
        else:
            self.current_status["cpu"]["status"] = "ok"
        
        print(f"   CPU: {cpu_percent}% ({self.current_status['cpu']['status']})")
        
        # 内存
        memory = psutil.virtual_memory()
        self.current_status["memory"]["usage"] = memory.percent
        
        if memory.percent > self.alert_config["memory_critical"]:
            self.current_status["memory"]["status"] = "critical"
            self.add_alert("memory_critical", f"内存使用率过高: {memory.percent}%")
        elif memory.percent > self.alert_config["memory_warning"]:
            self.current_status["memory"]["status"] = "warning"
        else:
            self.current_status["memory"]["status"] = "ok"
        
        print(f"   内存: {memory.percent}% ({self.current_status['memory']['status']})")
        
        # 磁盘
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        self.current_status["disk"]["usage"] = disk_percent
        
        if disk_percent > self.alert_config["disk_critical"]:
            self.current_status["disk"]["status"] = "critical"
            self.add_alert("disk_critical", f"磁盘使用率过高: {disk_percent}%")
        elif disk_percent > self.alert_config["disk_warning"]:
            self.current_status["disk"]["status"] = "warning"
        else:
            self.current_status["disk"]["status"] = "ok"
        
        print(f"   磁盘: {disk_percent}% ({self.current_status['disk']['status']})")
        
        self.stats["checks_performed"] += 3
    
    def check_critical_processes(self):
        """检查关键进程"""
        print("🔍 检查关键进程...")
        
        for process_name in self.critical_processes:
            found = False
            count = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        found = True
                        count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.current_status["processes"][process_name] = {
                "running": found,
                "count": count
            }
            
            if found:
                print(f"   ✓ {process_name}: {count}个进程运行中")
            else:
                print(f"   ⚠️  {process_name}: 未运行")
                if process_name == "openclaw":
                    self.add_alert("process_missing", f"关键进程 {process_name} 未运行")
    
    def check_critical_files(self):
        """检查关键文件"""
        print("📁 检查关键文件...")
        
        for file_path in self.critical_files:
            full_path = self.workspace / file_path
            
            if full_path.exists():
                stat = full_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                age_hours = (datetime.now() - mtime).total_seconds() / 3600
                
                self.current_status["services"][file_path] = {
                    "exists": True,
                    "size": stat.st_size,
                    "age_hours": age_hours
                }
                
                print(f"   ✓ {file_path}: 存在 ({age_hours:.1f}小时前修改)")
            else:
                self.current_status["services"][file_path] = {
                    "exists": False
                }
                self.add_alert("file_missing", f"关键文件缺失: {file_path}")
                print(f"   ❌ {file_path}: 不存在")
    
    def check_disk_health(self):
        """详细磁盘健康检查"""
        print("💽 检查磁盘健康...")
        
        # 检查logs目录大小
        logs_dir = self.workspace / "logs"
        if logs_dir.exists():
            result = subprocess.run(
                ["du", "-sh", str(logs_dir)],
                capture_output=True,
                text=True
            )
            logs_size = result.stdout.split()[0] if result.stdout else "unknown"
            print(f"   logs目录: {logs_size}")
        
        # 检查memory目录大小
        if self.memory_dir.exists():
            result = subprocess.run(
                ["du", "-sh", str(self.memory_dir)],
                capture_output=True,
                text=True
            )
            memory_size = result.stdout.split()[0] if result.stdout else "unknown"
            print(f"   memory目录: {memory_size}")
        
        # 检查inode使用率
        result = subprocess.run(
            ["df", "-i", "/"],
            capture_output=True,
            text=True
        )
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                inode_usage = lines[1].split()[4].replace('%', '')
                print(f"   Inode使用: {inode_usage}%")
    
    def check_network_connectivity(self):
        """检查网络连通性"""
        print("🌐 检查网络连通性...")
        
        test_hosts = [
            ("github.com", "GitHub"),
            ("www.moltbook.com", "Moltbook"),
            ("8.8.8.8", "Google DNS")
        ]
        
        for host, name in test_hosts:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "5", host],
                capture_output=True
            )
            
            if result.returncode == 0:
                print(f"   ✓ {name}: 可达")
            else:
                print(f"   ⚠️  {name}: 不可达")
                if name == "GitHub":
                    self.add_alert("network_issue", f"无法连接到 {name}")
    
    def add_alert(self, alert_type: str, message: str):
        """添加告警 (带冷却检查)"""
        # 检查冷却时间
        if not self.should_alert(alert_type):
            return
        
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "severity": "critical" if "critical" in alert_type else "warning"
        }
        
        self.alerts.append(alert)
        self.stats["issues_found"] += 1
        
        # 记录到日志
        self.log_alert(alert)
    
    def should_alert(self, alert_type: str) -> bool:
        """检查是否应该发送告警 (冷却时间检查)"""
        state_file = self.memory_dir / "alert-state.json"
        
        if not state_file.exists():
            return True
        
        with open(state_file, 'r') as f:
            try:
                state = json.load(f)
            except:
                return True
        
        last_alert = state.get("last_alerts", {}).get(alert_type)
        if last_alert:
            last_time = datetime.fromisoformat(last_alert)
            cooldown = timedelta(minutes=self.alert_config["alert_cooldown_minutes"])
            if datetime.now() - last_time < cooldown:
                return False
        
        return True
    
    def log_alert(self, alert: Dict):
        """记录告警"""
        state_file = self.memory_dir / "alert-state.json"
        
        state = {"last_alerts": {}}
        if state_file.exists():
            with open(state_file, 'r') as f:
                try:
                    state = json.load(f)
                except:
                    pass
        
        state["last_alerts"][alert["type"]] = alert["timestamp"]
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def execute_auto_recovery(self):
        """执行自动恢复"""
        print("🔧 执行自动恢复...")
        
        # 检查是否需要清理日志
        if self.current_status["disk"]["status"] in ["warning", "critical"]:
            print("   ⚠️  磁盘空间不足，触发自动清理...")
            self.auto_cleanup_logs()
        
        # 检查是否需要清理内存
        if self.current_status["memory"]["status"] == "critical":
            print("   ⚠️  内存不足，触发内存清理...")
            self.auto_cleanup_memory()
    
    def auto_cleanup_logs(self):
        """自动清理日志"""
        try:
            # 调用日志清理脚本
            result = subprocess.run(
                ["python3", str(self.workspace / "scripts" / "auto-log-manager.py")],
                capture_output=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.recovery_actions.append({
                    "type": "auto_log_cleanup",
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                })
                self.stats["auto_recoveries"] += 1
                print("   ✓ 日志自动清理完成")
            else:
                print(f"   ⚠️  日志清理失败: {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ 日志清理异常: {e}")
    
    def auto_cleanup_memory(self):
        """自动清理内存"""
        try:
            # 尝试释放缓存
            subprocess.run(
                ["sync"],
                capture_output=True
            )
            
            # 如果系统支持，清理页面缓存
            if os.path.exists("/proc/sys/vm/drop_caches"):
                # 注意：需要root权限
                pass  # 暂不执行，避免权限问题
            
            self.recovery_actions.append({
                "type": "memory_cleanup_attempt",
                "timestamp": datetime.now().isoformat()
            })
            print("   ✓ 内存清理尝试完成")
            
        except Exception as e:
            print(f"   ❌ 内存清理异常: {e}")
    
    def analyze_trends(self):
        """分析健康趋势"""
        print("📈 分析健康趋势...")
        
        history_file = self.memory_dir / "health-history.json"
        
        # 加载历史数据
        history = []
        if history_file.exists():
            with open(history_file, 'r') as f:
                try:
                    history = json.load(f)
                except:
                    history = []
        
        # 添加当前数据点
        data_point = {
            "timestamp": datetime.now().isoformat(),
            "cpu": self.current_status["cpu"]["usage"],
            "memory": self.current_status["memory"]["usage"],
            "disk": self.current_status["disk"]["usage"]
        }
        
        history.append(data_point)
        
        # 只保留最近100个数据点
        history = history[-100:]
        
        # 保存历史
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        # 简单趋势分析
        if len(history) >= 10:
            recent = history[-10:]
            cpu_trend = sum(d["cpu"] for d in recent) / len(recent)
            memory_trend = sum(d["memory"] for d in recent) / len(recent)
            
            print(f"   CPU趋势(10次平均): {cpu_trend:.1f}%")
            print(f"   内存趋势(10次平均): {memory_trend:.1f}%")
    
    def generate_report(self) -> Dict:
        """生成健康报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": self.current_status,
            "alerts": self.alerts,
            "recovery_actions": self.recovery_actions,
            "statistics": self.stats,
            "overall_health": "critical" if any(a["severity"] == "critical" for a in self.alerts) else
                            "warning" if self.alerts else "healthy"
        }
        
        # 保存JSON报告
        report_file = self.report_dir / f"health-check-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        print(f"\n{'='*70}")
        print("📋 健康检查报告")
        print(f"{'='*70}")
        print(f"整体状态: {report['overall_health'].upper()}")
        print(f"CPU: {self.current_status['cpu']['usage']:.1f}% ({self.current_status['cpu']['status']})")
        print(f"内存: {self.current_status['memory']['usage']:.1f}% ({self.current_status['memory']['status']})")
        print(f"磁盘: {self.current_status['disk']['usage']:.1f}% ({self.current_status['disk']['status']})")
        print(f"告警数量: {len(self.alerts)}")
        print(f"自动恢复: {len(self.recovery_actions)} 次")
        print(f"报告保存: {report_file}")
        print(f"{'='*70}")
        
        return report
    
    def save_health_state(self):
        """保存健康状态"""
        state_file = self.memory_dir / "health-state.json"
        
        state = {
            "last_check": datetime.now().isoformat(),
            "status": self.current_status,
            "overall_health": "critical" if any(a["severity"] == "critical" for a in self.alerts) else
                            "warning" if self.alerts else "healthy"
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    system = HealthAutomationSystem()
    report = system.run_health_check()
    return report


if __name__ == "__main__":
    main()
