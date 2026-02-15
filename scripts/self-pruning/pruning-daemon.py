#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统智能精简守护进程 v2.0
支持三档thinking模式分配:
- 快速扫描 (每6小时) → thinking=medium (L2)
- 深度评估 (每天04:00) → thinking=high (L3)
- 精简执行 → thinking=medium (L2)
"""

import os
import sys
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from threading import Event
from enum import Enum

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
PRUNING_DIR = WORKSPACE / "scripts/self-pruning"
LOG_DIR = WORKSPACE / "memory/self-pruning"
LOG_FILE = LOG_DIR / "daemon.log"
L3_LOG_FILE = LOG_DIR / "daemon-l3.log"
PID_FILE = Path("/var/run/sensen-pruning.pid")

# 执行时间配置
QUICK_SCAN_INTERVAL_HOURS = 6  # 快速扫描每6小时
DEEP_EVAL_HOUR = 4             # 深度评估每天04:00
DEEP_EVAL_MINUTE = 0

# Thinking级别
class ThinkingLevel(Enum):
    LOW = "low"       # L1 - 快速检查
    MEDIUM = "medium" # L2 - 标准分析
    HIGH = "high"     # L3 - 深度评估

# 退出事件
shutdown_event = Event()

# 当前thinking级别 (环境变量)
CURRENT_THINKING = ThinkingLevel.MEDIUM

def setup_logging():
    """配置日志系统 - 区分L3日志"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 主日志
    main_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    main_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    main_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger("pruning-daemon")
    logger.setLevel(logging.INFO)
    logger.addHandler(main_handler)
    logger.addHandler(console_handler)
    
    return logger

def setup_l3_logging():
    """配置L3深度评估专用日志"""
    l3_handler = logging.FileHandler(L3_LOG_FILE, encoding='utf-8')
    l3_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - [L3/DEEP] - %(message)s')
    l3_handler.setFormatter(formatter)
    
    l3_logger = logging.getLogger("pruning-l3")
    l3_logger.setLevel(logging.DEBUG)
    l3_logger.addHandler(l3_handler)
    
    return l3_logger

logger = setup_logging()
l3_logger = setup_l3_logging()

def set_thinking_level(level: ThinkingLevel):
    """设置当前thinking级别"""
    global CURRENT_THINKING
    CURRENT_THINKING = level
    os.environ['PRUNING_THINKING_LEVEL'] = level.value
    logger.info(f"🧠 Thinking级别切换为: {level.value.upper()} ({level.name})")

def signal_handler(signum, frame):
    """处理信号"""
    logger.info(f"收到信号 {signum}，准备关闭...")
    shutdown_event.set()

def get_next_quick_scan():
    """计算下次快速扫描时间"""
    return datetime.now() + timedelta(hours=QUICK_SCAN_INTERVAL_HOURS)

def get_next_deep_eval():
    """计算下次深度评估时间"""
    now = datetime.now()
    next_exec = now.replace(hour=DEEP_EVAL_HOUR, minute=DEEP_EVAL_MINUTE, second=0, microsecond=0)
    if next_exec <= now:
        next_exec += timedelta(days=1)
    return next_exec

def run_protection_check():
    """执行保护清单检查 - 任何级别都必须执行"""
    check_script = PRUNING_DIR / "protected-check.py"
    
    logger.info("🛡️ 执行保护清单检查...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(check_script), "check"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✅ 保护清单检查通过")
            return True
        else:
            logger.error("❌ 保护清单检查失败")
            logger.error(result.stderr)
            return False
            
    except Exception as e:
        logger.error(f"❌ 保护清单检查异常: {e}")
        return False

def run_quick_scan():
    """
    快速扫描 - L2级别 (每6小时)
    功能: Token消耗检测、臃肿识别
    """
    set_thinking_level(ThinkingLevel.MEDIUM)
    logger.info("=" * 60)
    logger.info("🔍 启动快速扫描 (L2/MEDIUM)")
    logger.info("=" * 60)
    
    # 必须执行保护检查
    if not run_protection_check():
        logger.error("保护检查失败，跳过本次扫描")
        return False
    
    scan_script = PRUNING_DIR / "quick-scan.py"
    
    try:
        # 使用medium thinking级别执行
        env = os.environ.copy()
        env['THINKING'] = 'medium'
        
        result = subprocess.run(
            [sys.executable, str(scan_script)],
            capture_output=True,
            text=True,
            timeout=1800,  # 30分钟
            cwd=str(WORKSPACE),
            env=env
        )
        
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"[quick-scan] {line}")
        
        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.warning(f"[quick-scan] {line}")
        
        success = result.returncode == 0
        if success:
            logger.info("✅ 快速扫描完成")
        else:
            logger.error(f"❌ 快速扫描失败: {result.returncode}")
        
        return success
        
    except subprocess.TimeoutExpired:
        logger.error("❌ 快速扫描超时")
        return False
    except Exception as e:
        logger.error(f"❌ 快速扫描异常: {e}")
        return False

def run_deep_evaluation():
    """
    深度评估 - L3级别 (每天04:00)
    功能: 综合评估、精简方案制定
    触发L3条件: 重大Token浪费、架构级精简需求、复杂耦合问题
    """
    set_thinking_level(ThinkingLevel.HIGH)
    
    l3_logger.info("=" * 60)
    l3_logger.info("🧠 启动深度评估 (L3/HIGH)")
    l3_logger.info("=" * 60)
    
    logger.info("=" * 60)
    logger.info("🧠 启动深度评估 (L3/HIGH)")
    logger.info("=" * 60)
    
    # 必须执行保护检查
    if not run_protection_check():
        logger.error("保护检查失败，跳过本次评估")
        l3_logger.error("保护检查失败，跳过本次评估")
        return False
    
    eval_script = PRUNING_DIR / "deep-eval.py"
    
    try:
        # 使用high thinking级别执行
        env = os.environ.copy()
        env['THINKING'] = 'high'
        
        result = subprocess.run(
            [sys.executable, str(eval_script)],
            capture_output=True,
            text=True,
            timeout=7200,  # 2小时
            cwd=str(WORKSPACE),
            env=env
        )
        
        # L3输出同时记录到专用日志
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"[deep-eval] {line}")
                    l3_logger.info(line)
        
        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.warning(f"[deep-eval] {line}")
                    l3_logger.warning(line)
        
        success = result.returncode == 0
        if success:
            logger.info("✅ 深度评估完成")
            l3_logger.info("✅ 深度评估完成")
        else:
            logger.error(f"❌ 深度评估失败: {result.returncode}")
            l3_logger.error(f"深度评估失败: {result.returncode}")
        
        return success
        
    except subprocess.TimeoutExpired:
        logger.error("❌ 深度评估超时")
        l3_logger.error("深度评估超时")
        return False
    except Exception as e:
        logger.error(f"❌ 深度评估异常: {e}")
        l3_logger.error(f"深度评估异常: {e}")
        return False

def run_pruning_execution(safe_list_file=None):
    """
    精简执行 - L2级别
    功能: 安全精简、保护清单检查
    """
    set_thinking_level(ThinkingLevel.MEDIUM)
    logger.info("=" * 60)
    logger.info("🔧 启动精简执行 (L2/MEDIUM)")
    logger.info("=" * 60)
    
    script_path = PRUNING_DIR / "run-pruning.sh"
    
    if not script_path.exists():
        logger.error(f"精简脚本不存在: {script_path}")
        return False
    
    try:
        env = os.environ.copy()
        env['THINKING'] = 'medium'
        
        cmd = ["bash", str(script_path)]
        if safe_list_file:
            cmd.append(safe_list_file)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1小时
            cwd=str(WORKSPACE),
            env=env
        )
        
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"[pruning] {line}")
        
        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.warning(f"[pruning] {line}")
        
        success = result.returncode == 0
        if success:
            logger.info("✅ 精简执行完成")
        else:
            logger.error(f"❌ 精简执行失败: {result.returncode}")
        
        return success
        
    except subprocess.TimeoutExpired:
        logger.error("❌ 精简执行超时")
        return False
    except Exception as e:
        logger.error(f"❌ 精简执行异常: {e}")
        return False

def should_trigger_l3():
    """
    判断是否触发L3深度评估
    触发条件:
    - 发现重大Token浪费问题
    - 架构级精简需求
    - 复杂耦合问题需要深度分析
    """
    # 检查是否有L3触发标记
    l3_trigger_file = LOG_DIR / ".l3-trigger"
    
    if l3_trigger_file.exists():
        logger.info("🚨 检测到L3触发标记")
        l3_trigger_file.unlink()  # 消费标记
        return True
    
    # 检查快速扫描是否发现严重问题
    scan_report = LOG_DIR / "last-scan-report.txt"
    if scan_report.exists():
        content = scan_report.read_text()
        # 如果检测到重大Token浪费 (>10000 tokens) 或架构问题
        if "CRITICAL" in content or "ARCHITECTURE_ISSUE" in content:
            logger.info("🚨 快速扫描发现严重问题，触发L3评估")
            return True
    
    return False

def wait_until(target_time: datetime):
    """等待直到目标时间"""
    wait_seconds = (target_time - datetime.now()).total_seconds()
    
    if wait_seconds <= 0:
        return
    
    logger.info(f"等待 {(wait_seconds/3600):.1f} 小时直到 {target_time.strftime('%Y-%m-%d %H:%M:%S')}...")
    
    while wait_seconds > 0 and not shutdown_event.is_set():
        sleep_time = min(60, wait_seconds)
        shutdown_event.wait(sleep_time)
        wait_seconds -= sleep_time

def create_pid_file():
    """创建PID文件"""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"PID文件已创建: {PID_FILE}")
    except Exception as e:
        logger.warning(f"无法创建PID文件: {e}")

def remove_pid_file():
    """删除PID文件"""
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
            logger.info("PID文件已删除")
    except Exception as e:
        logger.warning(f"无法删除PID文件: {e}")

def daemon_loop():
    """守护进程主循环 - 双轨制"""
    logger.info("🚀 系统精简守护进程 v2.0 启动")
    logger.info(f"工作目录: {WORKSPACE}")
    logger.info(f"快速扫描: 每 {QUICK_SCAN_INTERVAL_HOURS} 小时 (L2)")
    logger.info(f"深度评估: 每天 {DEEP_EVAL_HOUR:02d}:{DEEP_EVAL_MINUTE:02d} (L3)")
    
    create_pid_file()
    
    next_quick_scan = get_next_quick_scan()
    next_deep_eval = get_next_deep_eval()
    
    try:
        while not shutdown_event.is_set():
            now = datetime.now()
            
            # 决定执行哪种任务
            should_quick_scan = now >= next_quick_scan
            should_deep_eval = now >= next_deep_eval
            
            # L3触发检查
            force_deep_eval = should_trigger_l3()
            
            if should_deep_eval or force_deep_eval:
                # 执行深度评估 (L3)
                run_deep_evaluation()
                next_deep_eval = get_next_deep_eval()
                next_quick_scan = get_next_quick_scan()  # 重置快速扫描时间
                
            elif should_quick_scan:
                # 执行快速扫描 (L2)
                run_quick_scan()
                next_quick_scan = get_next_quick_scan()
                
            else:
                # 计算下次任务时间
                next_task = min(next_quick_scan, next_deep_eval)
                wait_until(next_task)
                
    except Exception as e:
        logger.exception("守护进程异常")
    finally:
        remove_pid_file()
        logger.info("👋 守护进程已关闭")

def main():
    """主入口"""
    # 注册信号处理
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 检查工作目录
    if not WORKSPACE.exists():
        logger.error(f"工作目录不存在: {WORKSPACE}")
        sys.exit(1)
    
    # 启动守护循环
    daemon_loop()

if __name__ == "__main__":
    main()
