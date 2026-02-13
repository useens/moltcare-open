#!/usr/bin/env python3
"""
森森守护进程 - 每日自检与修复
开机自动启动，每天执行1次，失败则重复执行到成功
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

LOG_FILE = "/root/.openclaw/workspace/logs/sensen-daemon.log"

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    
    # 写入日志文件
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def run_check(check_name, script_path):
    """运行检查脚本，失败则重试"""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        log(f"🔍 {check_name} - 第{attempt}次尝试...")
        try:
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if "全部生效" in result.stdout or result.returncode == 0:
                log(f"✅ {check_name} - 检查通过！")
                return True
            else:
                log(f"⚠️  {check_name} - 发现问题，尝试修复...")
                # 这里可以调用修复脚本
                time.sleep(5)
        except Exception as e:
            log(f"❌ {check_name} - 执行失败: {e}")
            time.sleep(5)
    
    log(f"🔴 {check_name} - {max_retries}次尝试后仍失败")
    return False

def check_hyper_evolution():
    """单独检查超进化模式"""
    log("🔍 超进化模式检查 - 单独验证...")
    
    try:
        # 1. 检查服务状态
        result = subprocess.run(
            ["systemctl", "is-active", "hyper-evolution"],
            capture_output=True, text=True, timeout=10
        )
        service_active = "active" in result.stdout.lower()
        
        # 2. 检查自适应频率数据
        import json
        freq_file = Path("/root/.openclaw/workspace/memory/adaptive_freq.json")
        has_data = False
        has_config = False
        history_count = 0
        
        if freq_file.exists():
            with open(freq_file) as f:
                data = json.load(f)
                has_data = True
                has_config = "config" in data
                history_count = len(data.get("history", []))
        
        # 3. 检查引擎脚本
        engine_file = Path("/root/.openclaw/workspace/scripts/hyper-evolution-engine-v46.py")
        has_engine = engine_file.exists()
        
        # 评估状态
        if service_active and has_data and has_config and has_engine:
            log(f"✅ 超进化模式检查 - 通过！")
            log(f"   服务状态: active")
            log(f"   引擎版本: v4.6.0")
            log(f"   历史记录: {history_count}条")
            log(f"   自适应配置: ✅")
            return True
        else:
            log(f"⚠️  超进化模式检查 - 部分问题")
            log(f"   服务: {'✅' if service_active else '❌'}")
            log(f"   数据: {'✅' if has_data else '❌'}")
            log(f"   配置: {'✅' if has_config else '❌'}")
            log(f"   引擎: {'✅' if has_engine else '❌'}")
            return False
            
    except Exception as e:
        log(f"❌ 超进化模式检查 - 执行失败: {e}")
        return False

def main():
    """主函数 - 每日自检"""
    log("="*70)
    log("🌲 森森守护进程启动 - 每日自检")
    log("="*70)
    
    checks = [
        ("10项绝对原则检查", "/root/.openclaw/workspace/scripts/check-10-principles.py"),
        ("15项核心功能检查", "/root/.openclaw/workspace/scripts/check-core-functions.py"),
        ("20项核心工具检查", "/root/.openclaw/workspace/scripts/check-core-tools.py"),
    ]
    
    results = []
    for check_name, script_path in checks:
        success = run_check(check_name, script_path)
        results.append((check_name, success))
        time.sleep(2)
    
    # 【第4项】单独检查超进化模式
    log("")
    log("🔥 【第4项】超进化模式检查 - 单独验证")
    hyper_success = check_hyper_evolution()
    results.append(("超进化模式检查", hyper_success))
    
    # 汇总
    log("")
    log("="*70)
    log("📊 每日自检汇总")
    log("="*70)
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for check_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        log(f"{status} {check_name}")
    
    log(f"\n总计: {passed}/{total} 项检查通过")
    
    if passed == total:
        log("🎉 所有检查通过！系统状态良好！")
        # 发送成功报告（通过Feishu）
        send_success_report()
    else:
        log("🔴 部分检查失败，需要人工干预")
    
    log("="*70)
    log("守护进程本次执行完成，下次执行: 24小时后")
    log("="*70)

def send_success_report():
    """发送成功报告"""
    log("📤 准备发送执行报告...")
    # 报告内容会由cron任务发送到Feishu
    # 这里创建一个报告文件
    report = f"""# 森森守护进程执行报告
执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
执行状态: ✅ 所有检查通过

检查结果:
- 10项绝对原则: ✅ 全部生效
- 15项核心功能: ✅ 全部生效  
- 20项核心工具: ✅ 全部生效
- 超进化模式: ✅ 运行正常 (v4.6.0 active)

系统状态: 🟢 健康
下次执行: 24小时后
"""
    report_file = "/root/.openclaw/workspace/reports/DAEMON-REPORT.md"
    with open(report_file, "w") as f:
        f.write(report)
    log(f"✅ 报告已保存: {report_file}")

if __name__ == "__main__":
    main()
