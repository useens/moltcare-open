#!/usr/bin/env python3
"""
智能水平升级守护进程
主循环：评估→分析→升级→验证→休眠
默认执行周期：每天02:00（低峰期）
支持手动触发和自动触发
"""

import os
import sys
import json
import time
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path

class IntelligenceUpgradeDaemon:
    def __init__(self, workspace_path="/root/.openclaw/workspace"):
        self.workspace = Path(workspace_path)
        self.scripts_dir = self.workspace / "scripts"
        self.data_dir = self.workspace / "data"
        self.logs_dir = self.workspace / "logs"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.data_dir / "upgrade-state.json"
        self.pid_file = self.data_dir / "upgrade-daemon.pid"
        
        self.running = False
        self.next_run_time = None
        self.default_hour = 2  # 默认02:00执行
        self.default_minute = 0
        
        # 设置信号处理
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
    
    def handle_signal(self, signum, frame):
        """处理系统信号"""
        self.log(f"收到信号 {signum}，准备退出...")
        self.running = False
        self.save_state()
        sys.exit(0)
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 写入日志文件
        log_file = self.logs_dir / "upgrade-daemon.log"
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
        
        # 同时输出到journald
        print(log_entry, flush=True)
    
    def save_state(self):
        """保存守护进程状态"""
        state = {
            "last_run": datetime.now().isoformat(),
            "next_run": self.next_run_time.isoformat() if self.next_run_time else None,
            "status": "running" if self.running else "stopped",
            "pid": os.getpid()
        }
        self.state_file.write_text(json.dumps(state, indent=2))
    
    def load_state(self):
        """加载守护进程状态"""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {}
    
    def save_pid(self):
        """保存PID文件"""
        self.pid_file.write_text(str(os.getpid()))
    
    def remove_pid(self):
        """移除PID文件"""
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def calculate_next_run(self):
        """计算下次执行时间"""
        now = datetime.now()
        next_run = now.replace(hour=self.default_hour, minute=self.default_minute, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def run_assessment(self):
        """执行评估"""
        self.log("="*60)
        self.log("阶段1: 执行智能水平评估")
        self.log("="*60)
        
        try:
            script = self.scripts_dir / "intelligence-assessment.py"
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("评估完成 ✓")
                return True
            else:
                self.log(f"评估失败: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"评估执行异常: {e}", "ERROR")
            return False
    
    def run_analysis(self):
        """执行弱项分析"""
        self.log("="*60)
        self.log("阶段2: 执行弱项分析")
        self.log("="*60)
        
        try:
            script = self.scripts_dir / "weakness-analyzer.py"
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("弱项分析完成 ✓")
                return True
            else:
                self.log(f"弱项分析失败: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"弱项分析异常: {e}", "ERROR")
            return False
    
    def run_upgrade(self):
        """执行升级"""
        self.log("="*60)
        self.log("阶段3: 执行升级")
        self.log("="*60)
        
        try:
            script = self.scripts_dir / "intelligence-upgrader.py"
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                self.log("升级执行完成 ✓")
                return True
            else:
                self.log(f"升级执行失败: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"升级执行异常: {e}", "ERROR")
            return False
    
    def run_verification(self):
        """执行验证"""
        self.log("="*60)
        self.log("阶段4: 执行升级验证")
        self.log("="*60)
        
        try:
            script = self.scripts_dir / "upgrade-verifier.py"
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # 验证脚本返回0表示3次全部通过
            passed = result.returncode == 0
            
            if passed:
                self.log("验证通过 ✓ (连续3次全部通过)")
            else:
                self.log("验证未完全通过，但流程继续", "WARN")
            
            return passed
                
        except Exception as e:
            self.log(f"验证执行异常: {e}", "ERROR")
            return False
    
    def generate_summary(self, results):
        """生成升级周期摘要"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "overall_status": "success" if all(results.values()) else "partial"
        }
        
        # 保存摘要
        summary_file = self.data_dir / "upgrade-summary-latest.json"
        summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        
        return summary
    
    def run_single_cycle(self):
        """执行单个升级周期"""
        self.log("\n" + "="*60)
        self.log("开始升级周期")
        self.log("="*60)
        
        results = {
            "assessment": False,
            "analysis": False,
            "upgrade": False,
            "verification": False
        }
        
        # 阶段1: 评估
        results["assessment"] = self.run_assessment()
        if not results["assessment"]:
            self.log("评估阶段失败，继续执行其他阶段...", "WARN")
        
        # 阶段2: 分析
        results["analysis"] = self.run_analysis()
        if not results["analysis"]:
            self.log("分析阶段失败，继续执行其他阶段...", "WARN")
        
        # 阶段3: 升级
        results["upgrade"] = self.run_upgrade()
        if not results["upgrade"]:
            self.log("升级阶段失败，继续执行其他阶段...", "WARN")
        
        # 阶段4: 验证
        results["verification"] = self.run_verification()
        
        # 生成摘要
        summary = self.generate_summary(results)
        
        self.log("\n" + "="*60)
        self.log("升级周期完成")
        self.log(f"评估: {'✓' if results['assessment'] else '✗'}")
        self.log(f"分析: {'✓' if results['analysis'] else '✗'}")
        self.log(f"升级: {'✓' if results['upgrade'] else '✗'}")
        self.log(f"验证: {'✓' if results['verification'] else '✗'}")
        self.log("="*60)
        
        return summary
    
    def sleep_until_next_run(self):
        """休眠到下次执行时间"""
        self.next_run_time = self.calculate_next_run()
        self.save_state()
        
        now = datetime.now()
        sleep_seconds = (self.next_run_time - now).total_seconds()
        
        self.log(f"下次执行时间: {self.next_run_time.isoformat()}")
        self.log(f"休眠 {sleep_seconds/3600:.1f} 小时...")
        
        # 分段休眠，便于响应信号
        while sleep_seconds > 0 and self.running:
            sleep_chunk = min(sleep_seconds, 60)  # 每分钟检查一次
            time.sleep(sleep_chunk)
            sleep_seconds -= sleep_chunk
    
    def run_daemon(self, single_run=False):
        """运行守护进程主循环"""
        self.log("="*60)
        self.log("智能水平升级守护进程启动")
        self.log(f"工作目录: {self.workspace}")
        self.log(f"执行周期: 每天 {self.default_hour:02d}:{self.default_minute:02d}")
        self.log("="*60)
        
        self.running = True
        self.save_pid()
        self.save_state()
        
        try:
            while self.running:
                # 执行升级周期
                self.run_single_cycle()
                
                if single_run:
                    self.log("单次执行模式，退出")
                    break
                
                # 休眠到下次执行
                self.sleep_until_next_run()
                
        except Exception as e:
            self.log(f"守护进程异常: {e}", "ERROR")
        finally:
            self.remove_pid()
            self.log("守护进程已停止")
    
    def run_manual_trigger(self):
        """手动触发执行"""
        self.log("手动触发升级周期")
        return self.run_single_cycle()

if __name__ == "__main__":
    daemon = IntelligenceUpgradeDaemon()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--manual" or sys.argv[1] == "-m":
            # 手动触发单次执行
            daemon.run_manual_trigger()
        elif sys.argv[1] == "--once":
            # 单次执行模式
            daemon.run_daemon(single_run=True)
        else:
            print(f"用法: {sys.argv[0]} [--manual|--once]")
            print("  --manual: 手动触发单次执行")
            print("  --once:   运行一次后退出")
            sys.exit(1)
    else:
        # 正常运行守护进程
        daemon.run_daemon()
