#!/usr/bin/env python3
"""
森森系统精简守护进程主控
Sensen System Pruning Guardian - Main Controller

Thinking模式分配:
- 快速扫描 (每6小时) → thinking=medium (L2)
- 深度评估 (每天04:00) → thinking=high (L3) 
- 精简执行 → thinking=medium (L2)

触发L3的条件:
- 发现重大Token浪费问题
- 架构级精简需求
- 复杂耦合问题需要深度分析

作者: 森森自我优化系统
创建: 2026-02-16
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
CONFIG_FILE = f"{WORKSPACE}/config/pruning-guardian.json"
LOG_FILE = f"{WORKSPACE}/logs/pruning-guardian.log"
PID_FILE = f"{WORKSPACE}/.pruning-guardian.pid"

# L3触发条件配置
L3_TRIGGER_CONDITIONS = {
    "script_count_critical": 250,      # 脚本数超过此值触发L3
    "token_anomaly_detected": True,     # 发现Token异常触发L3
    "architecture_change_needed": True, # 需要架构变更时触发L3
    "complex_coupling_found": True,     # 发现复杂耦合时触发L3
}

class PruningGuardian:
    """系统精简守护进程主控"""
    
    def __init__(self):
        self.workspace = Path(WORKSPACE)
        self.config = self.load_config()
        self.running = True
        
    def load_config(self):
        """加载配置"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                return json.load(f)
        return {
            "l2_scan_interval_hours": 6,
            "l3_scan_time": "04:00",
            "auto_prune": False,  # 默认不自动精简
            "dry_run": True,
            "protected_paths": [
                "AGENTS.md", "SOUL.md", "USER.md", "IDENTITY.md", "MEMORY.md",
                "learning-debt.md", ".git", "scripts/backup"
            ]
        }
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [Guardian] [{level}] {message}"
        print(log_line)
        
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(log_line + "\n")
    
    def run_l2_scan(self):
        """执行L2快速扫描"""
        self.log("🔄 启动L2快速扫描 (thinking=medium)...")
        
        scanner_script = f"{WORKSPACE}/scripts/self-pruning/scanner/l2-quick-scan.py"
        
        try:
            result = subprocess.run(
                [sys.executable, scanner_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            need_l3 = (result.returncode == 2)
            
            if need_l3:
                self.log("🔴 L2扫描发现严重问题，建议触发L3深度评估", "WARNING")
                return "L3_REQUIRED"
            else:
                self.log("✅ L2扫描完成，系统状态正常")
                return "OK"
                
        except Exception as e:
            self.log(f"❌ L2扫描失败: {e}", "ERROR")
            return "ERROR"
    
    def run_l3_assessment(self):
        """执行L3深度评估"""
        self.log("🧠 启动L3深度评估 (thinking=high)...")
        
        # L3评估是深度分析，需要更长时间
        # 这里可以调用更复杂的分析逻辑
        
        # 简单实现：检查是否需要L3
        scripts_count = len(list(Path(f"{WORKSPACE}/scripts").rglob("*.py"))) + \
                       len(list(Path(f"{WORKSPACE}/scripts").rglob("*.sh")))
        
        if scripts_count > L3_TRIGGER_CONDITIONS["script_count_critical"]:
            self.log(f"📊 L3分析: 脚本数量({scripts_count})超过阈值", "WARNING")
        
        # 生成L3报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "thinking_level": "L3_High",
            "script_count": scripts_count,
            "recommendations": [
                "实施系统精简路线图",
                "合并重复功能脚本",
                "建立统一监控框架"
            ]
        }
        
        report_file = f"{WORKSPACE}/memory/self-pruning/reports/l3-scan-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"✅ L3深度评估完成: {report_file}")
        return report
    
    def run_l2_pruning(self, dry_run=True):
        """执行L2精简"""
        self.log(f"🧹 启动L2精简执行 (dry_run={dry_run})...")
        
        executor_script = f"{WORKSPACE}/scripts/self-pruning/executor/l2-pruning-executor.py"
        
        args = [sys.executable, executor_script]
        if not dry_run:
            args.append("--execute")
        
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.log("✅ L2精简执行完成")
                return True
            else:
                self.log(f"⚠️ L2精简执行有警告: {result.stderr}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"❌ L2精简执行失败: {e}", "ERROR")
            return False
    
    def should_run_l3(self):
        """判断是否应该运行L3"""
        now = datetime.now()
        l3_time = datetime.strptime(self.config.get("l3_scan_time", "04:00"), "%H:%M").time()
        
        # 检查是否是L3执行时间(04:00左右)
        if now.hour == l3_time.hour and now.minute < 10:
            return True
        
        # 检查是否需要紧急L3
        # 这里可以添加更多触发条件
        
        return False
    
    def run_single_cycle(self):
        """运行单个周期"""
        self.log("="*60)
        self.log(f"🚀 精简守护进程周期执行 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.log("="*60)
        
        # 1. 执行L2快速扫描
        l2_result = self.run_l2_scan()
        
        # 2. 检查是否需要L3
        if l2_result == "L3_REQUIRED" or self.should_run_l3():
            self.run_l3_assessment()
        
        # 3. 如果配置允许，执行L2精简
        if self.config.get("auto_prune", False):
            self.run_l2_pruning(dry_run=self.config.get("dry_run", True))
        else:
            self.log("ℹ️ 自动精简已禁用，跳过精简执行")
            self.log("   手动执行: python3 scripts/self-pruning/executor/l2-pruning-executor.py --execute")
        
        self.log("="*60)
    
    def run_daemon(self):
        """以守护进程模式运行"""
        self.log("🤖 启动精简守护进程...")
        
        # 写入PID文件
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        
        try:
            while self.running:
                self.run_single_cycle()
                
                # 计算下次运行时间(6小时后)
                interval = self.config.get("l2_scan_interval_hours", 6) * 3600
                next_run = datetime.now() + timedelta(seconds=interval)
                self.log(f"⏰ 下次扫描: {next_run.strftime('%Y-%m-%d %H:%M')}")
                
                # 睡眠，但允许被信号中断
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.log("👋 收到中断信号，守护进程停止")
        finally:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
    
    def run_once(self):
        """单次运行模式"""
        self.run_single_cycle()


def main():
    parser = argparse.ArgumentParser(description="森森系统精简守护进程")
    parser.add_argument("--daemon", action="store_true", help="守护进程模式")
    parser.add_argument("--l2-only", action="store_true", help="只执行L2扫描")
    parser.add_argument("--l3-only", action="store_true", help="只执行L3评估")
    parser.add_argument("--prune", action="store_true", help="执行精简(需配合--execute)")
    parser.add_argument("--execute", action="store_true", help="实际执行(非试运行)")
    args = parser.parse_args()
    
    guardian = PruningGuardian()
    
    if args.l2_only:
        guardian.run_l2_scan()
    elif args.l3_only:
        guardian.run_l3_assessment()
    elif args.prune:
        guardian.run_l2_pruning(dry_run=not args.execute)
    elif args.daemon:
        guardian.run_daemon()
    else:
        guardian.run_once()


if __name__ == "__main__":
    main()
