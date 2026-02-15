#!/usr/bin/env python3
"""
系统优化守护进程 - System Optimization Daemon
主控制脚本，协调评估→识别→精简→验证流程
"""

import os
import sys
import json
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class OptimizationDaemon:
    """系统优化守护进程"""
    
    def __init__(self, workspace: str = '/root/.openclaw/workspace'):
        self.workspace = Path(workspace)
        self.scripts_dir = self.workspace / 'scripts'
        self.data_dir = self.workspace / 'data'
        self.logs_dir = self.workspace / 'logs'
        self.config_dir = self.workspace / 'config'
        
        # 状态文件
        self.state_file = self.data_dir / 'optimization-state.json'
        
        # 默认执行时间：每天04:00
        self.schedule_hour = 4
        self.schedule_minute = 0
        
        # 运行标志
        self.running = True
        
        # 升级系统锁文件路径
        self.upgrade_lock_file = self.data_dir / 'upgrade-in-progress.lock'
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """处理终止信号"""
        print(f"\n📡 收到信号 {signum}，正在优雅退出...")
        self.running = False
    
    def load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'last_run': None,
            'total_runs': 0,
            'total_saved_mb': 0,
            'status': 'initialized'
        }
    
    def save_state(self, state: Dict[str, Any]):
        """保存状态"""
        state['updated_at'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def is_upgrade_running(self) -> bool:
        """检查升级系统是否正在运行"""
        return self.upgrade_lock_file.exists()
    
    def wait_for_upgrade(self, timeout: int = 300) -> bool:
        """等待升级系统完成"""
        print("⏳ 检查升级系统状态...")
        
        waited = 0
        while self.is_upgrade_running() and waited < timeout:
            print(f"  升级系统运行中，等待... ({waited}s)")
            time.sleep(10)
            waited += 10
        
        return not self.is_upgrade_running()
    
    def run_cycle(self) -> Dict[str, Any]:
        """执行一个完整的优化周期"""
        print(f"\n{'='*60}")
        print(f"🚀 开始系统精简周期 - {datetime.now().isoformat()}")
        print(f"{'='*60}\n")
        
        cycle_result = {
            'timestamp': datetime.now().isoformat(),
            'steps': {}
        }
        
        # 步骤0: 保存基线
        print("\n📊 步骤0: 保存优化前基线...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / 'optimization-verifier.py'), '--save-baseline'],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=60
            )
            cycle_result['steps']['baseline'] = {'status': 'ok'}
        except Exception as e:
            print(f"⚠️ 保存基线警告: {e}")
            cycle_result['steps']['baseline'] = {'status': 'warning', 'error': str(e)}
        
        # 步骤1: 系统评估
        print("\n📋 步骤1: 系统评估...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / 'system-evaluation.py')],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=300
            )
            print(result.stdout)
            if result.returncode == 0:
                cycle_result['steps']['evaluation'] = {'status': 'ok'}
            else:
                cycle_result['steps']['evaluation'] = {'status': 'warning'}
        except Exception as e:
            print(f"❌ 系统评估失败: {e}")
            cycle_result['steps']['evaluation'] = {'status': 'error', 'error': str(e)}
            return cycle_result
        
        # 步骤2: 识别精简机会
        print("\n🔍 步骤2: 识别精简机会...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / 'optimization-opportunity-finder.py')],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=300
            )
            print(result.stdout)
            cycle_result['steps']['opportunity_finding'] = {'status': 'ok'}
        except Exception as e:
            print(f"❌ 识别精简机会失败: {e}")
            cycle_result['steps']['opportunity_finding'] = {'status': 'error', 'error': str(e)}
            return cycle_result
        
        # 步骤3: 执行精简
        print("\n⚡ 步骤3: 执行精简...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / 'system-optimizer.py')],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=300
            )
            print(result.stdout)
            cycle_result['steps']['optimization'] = {'status': 'ok'}
            
            # 尝试解析节省的空间
            for line in result.stdout.split('\n'):
                if '节省空间' in line and 'MB' in line:
                    try:
                        saved = float(line.split(':')[-1].replace('MB', '').strip())
                        cycle_result['space_saved_mb'] = saved
                    except:
                        pass
        except Exception as e:
            print(f"❌ 执行精简失败: {e}")
            cycle_result['steps']['optimization'] = {'status': 'error', 'error': str(e)}
        
        # 步骤4: 效果验证（连续3次）
        print("\n✅ 步骤4: 效果验证（连续3次绝对诚实）...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / 'optimization-verifier.py')],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=600  # 10分钟（包含3次30秒间隔）
            )
            print(result.stdout)
            
            # 检查验证结果
            verification_passed = '精简完成' in result.stdout or '全部通过' in result.stdout
            cycle_result['steps']['verification'] = {
                'status': 'ok' if verification_passed else 'warning',
                'passed': verification_passed
            }
        except Exception as e:
            print(f"❌ 效果验证失败: {e}")
            cycle_result['steps']['verification'] = {'status': 'error', 'error': str(e)}
        
        cycle_result['completed_at'] = datetime.now().isoformat()
        return cycle_result
    
    def should_run_now(self) -> bool:
        """检查是否应该现在运行"""
        now = datetime.now()
        state = self.load_state()
        
        last_run_str = state.get('last_run')
        if not last_run_str:
            return True
        
        last_run = datetime.fromisoformat(last_run_str)
        
        # 检查是否是新的一天且过了执行时间
        if now.date() > last_run.date() and now.hour >= self.schedule_hour:
            return True
        
        # 检查是否超过24小时未运行
        if now - last_run > timedelta(hours=24):
            return True
        
        return False
    
    def calculate_next_run(self) -> datetime:
        """计算下次运行时间"""
        now = datetime.now()
        next_run = now.replace(hour=self.schedule_hour, minute=self.schedule_minute, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def run_once(self):
        """执行单次运行（用于立即执行）"""
        state = self.load_state()
        
        # 检查升级系统
        if self.is_upgrade_running():
            print("⏳ 升级系统正在运行，等待其完成...")
            if not self.wait_for_upgrade():
                print("❌ 等待升级系统超时，跳过本次执行")
                return
        
        # 执行周期
        state['status'] = 'running'
        self.save_state(state)
        
        result = self.run_cycle()
        
        # 更新状态
        state['last_run'] = datetime.now().isoformat()
        state['total_runs'] = state.get('total_runs', 0) + 1
        state['total_saved_mb'] = state.get('total_saved_mb', 0) + result.get('space_saved_mb', 0)
        state['last_result'] = result
        state['status'] = 'completed'
        self.save_state(state)
        
        print(f"\n{'='*60}")
        print(f"✅ 周期完成 - 累计运行: {state['total_runs']} 次")
        print(f"   累计节省: {state['total_saved_mb']:.2f} MB")
        print(f"{'='*60}\n")
    
    def run_daemon(self):
        """以守护进程模式运行"""
        print("🤖 系统优化守护进程已启动")
        print(f"   工作目录: {self.workspace}")
        print(f"   执行时间: 每天 {self.schedule_hour:02d}:{self.schedule_minute:02d}")
        print(f"   按 Ctrl+C 退出\n")
        
        while self.running:
            try:
                if self.should_run_now():
                    self.run_once()
                
                # 计算下次检查时间
                next_run = self.calculate_next_run()
                wait_seconds = (next_run - datetime.now()).total_seconds()
                
                if wait_seconds > 0:
                    print(f"⏰ 下次执行: {next_run.isoformat()}")
                    print(f"   等待 {int(wait_seconds/60)} 分钟...\n")
                    
                    # 分段等待以便响应信号
                    while wait_seconds > 0 and self.running:
                        sleep_time = min(60, wait_seconds)
                        time.sleep(sleep_time)
                        wait_seconds -= sleep_time
                else:
                    time.sleep(60)
                    
            except Exception as e:
                print(f"❌ 守护进程错误: {e}")
                time.sleep(60)
        
        print("👋 守护进程已退出")

def main():
    """主入口"""
    daemon = OptimizationDaemon()
    
    # 检查参数
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # 单次执行模式
        daemon.run_once()
    else:
        # 守护进程模式
        daemon.run_daemon()

if __name__ == '__main__':
    main()
