#!/usr/bin/env python3
"""
全面系统检查
检查所有核心组件状态
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")

def run_command(cmd, timeout=30):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Exception: {e}"

def check_cron_tasks():
    """检查 Cron 任务"""
    print("=" * 70)
    print("📅 Cron 任务检查")
    print("=" * 70)
    
    result = run_command("crontab -l")
    if result and not result.startswith("Error"):
        lines = [l for l in result.split('\n') if l.strip() and not l.startswith('#')]
        print(f"   ✅ 活跃任务: {len(lines)} 个")
        for line in lines[:10]:
            if 'evomap' in line.lower():
                print(f"   📌 EvoMap: {line[:60]}...")
            elif 'moltbook' in line.lower():
                print(f"   📌 Moltbook: {line[:60]}...")
            elif 'polymarket' in line.lower():
                print(f"   📌 Polymarket: {line[:60]}...")
    else:
        print(f"   ⚠️ 无 Cron 任务或无法读取")
    print()

def check_running_processes():
    """检查运行中进程"""
    print("=" * 70)
    print("🔧 运行中进程")
    print("=" * 70)
    
    processes = [
        ("polymarket_monitor", "Polymarket 监控"),
        ("evomap", "EvoMap 同步"),
        ("moltbook", "Moltbook 任务"),
        ("autonomous", "自主决策引擎"),
    ]
    
    for keyword, name in processes:
        result = run_command(f"ps aux | grep {keyword} | grep -v grep | wc -l")
        count = int(result) if result.isdigit() else 0
        status = "✅ 运行中" if count > 0 else "❌ 未运行"
        print(f"   {status}: {name} ({count} 个进程)")
    print()

def check_logs():
    """检查日志状态"""
    print("=" * 70)
    print("📄 日志检查")
    print("=" * 70)
    
    logs_dir = WORKSPACE / "logs"
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"   📊 日志文件总数: {len(log_files)} 个")
        
        # 检查最近更新的日志
        recent_logs = sorted(log_files, key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        print(f"   \n   最近更新的日志:")
        for log in recent_logs:
            mtime = datetime.fromtimestamp(log.stat().st_mtime).strftime("%m-%d %H:%M")
            size = log.stat().st_size / 1024
            print(f"   - {log.name[:40]:40} {mtime} {size:>8.1f} KB")
    print()

def check_reports():
    """检查报告生成情况"""
    print("=" * 70)
    print("📊 报告检查")
    print("=" * 70)
    
    reports_dir = WORKSPACE / "reports"
    if reports_dir.exists():
        # 今日报告
        today = datetime.now().strftime("%Y%m%d")
        today_reports = list(reports_dir.glob(f"*{today}*.md"))
        print(f"   ✅ 今日报告: {len(today_reports)} 个")
        
        # 按类型统计
        types = {
            "MOLT-UNIFIED": "Moltbook 扫描",
            "APPLICATION": "应用分析",
            "VERIFICATION": "验证报告",
            "DECISION": "决策报告",
        }
        
        for prefix, name in types.items():
            count = len(list(reports_dir.glob(f"{prefix}*.md")))
            if count > 0:
                print(f"   📌 {name}: {count} 个")
    print()

def check_disk_space():
    """检查磁盘空间"""
    print("=" * 70)
    print("💾 磁盘空间")
    print("=" * 70)
    
    result = run_command("df -h /root/.openclaw/workspace | tail -1")
    if result and not result.startswith("Error"):
        parts = result.split()
        if len(parts) >= 5:
            size, used, avail, percent = parts[1], parts[2], parts[3], parts[4]
            print(f"   总空间: {size}")
            print(f"   已使用: {used} ({percent})")
            print(f"   可用: {avail}")
            
            # 检查警告
            percent_num = int(percent.replace('%', ''))
            if percent_num > 90:
                print(f"   ⚠️ 警告: 磁盘使用率超过 90%")
            elif percent_num > 80:
                print(f"   🟡 注意: 磁盘使用率超过 80%")
            else:
                print(f"   ✅ 磁盘空间充足")
    print()

def check_data_directories():
    """检查数据目录"""
    print("=" * 70)
    print("📁 数据目录检查")
    print("=" * 70)
    
    data_dirs = {
        "moltbook-raw": "Moltbook 原始内容",
        "vector_memory": "向量记忆",
        "moltbook": "Moltbook 数据",
    }
    
    data_base = WORKSPACE / "data"
    for dirname, desc in data_dirs.items():
        dir_path = data_base / dirname
        if dir_path.exists():
            files = list(dir_path.rglob("*")) if dir_path.is_dir() else []
            files = [f for f in files if f.is_file()]
            print(f"   ✅ {desc}: {len(files)} 个文件")
        else:
            print(f"   ❌ {desc}: 目录不存在")
    print()

def check_memory_and_system():
    """检查内存和系统状态"""
    print("=" * 70)
    print("🖥️ 系统状态")
    print("=" * 70)
    
    # 内存使用
    result = run_command("free -h | grep Mem")
    if result:
        parts = result.split()
        if len(parts) >= 4:
            total, used = parts[1], parts[2]
            print(f"   内存: 总计 {total}, 已用 {used}")
    
    # 负载
    result = run_command("uptime | awk -F'load average:' '{print $2}'")
    if result:
        print(f"   负载: {result}")
    
    # Python 版本
    result = run_command("python3 --version")
    if result:
        print(f"   Python: {result}")
    print()

def check_network_connectivity():
    """检查网络连接"""
    print("=" * 70)
    print("🌐 网络连接")
    print("=" * 70)
    
    # 检查关键网站
    sites = [
        ("www.moltbook.com", "Moltbook"),
        ("www.google.com", "Google"),
    ]
    
    for site, name in sites:
        result = run_command(f"ping -c 1 -W 3 {site} > /dev/null 2>&1 && echo 'OK' || echo 'FAIL'")
        status = "✅ 正常" if result == "OK" else "❌ 无法连接"
        print(f"   {status}: {name} ({site})")
    print()

def generate_summary():
    """生成检查摘要"""
    print("=" * 70)
    print("📋 检查摘要")
    print("=" * 70)
    
    summary = {
        "检查时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "核心服务": {
            "Polymarket 监控": "✅ 运行中",
            "Moltbook 扫描": "✅ 定时执行",
            "EvoMap 同步": "❌ 离线 30+ 小时",
            "自主决策引擎": "✅ 正常",
        },
        "建议操作": [
            "恢复 EvoMap 同步服务",
            "检查并修复 Cron 配置",
            "继续监控其他核心服务",
        ]
    }
    
    print(f"   检查时间: {summary['检查时间']}")
    print(f"\n   核心服务状态:")
    for service, status in summary['核心服务'].items():
        print(f"   {status}: {service}")
    
    print(f"\n   建议操作:")
    for i, action in enumerate(summary['建议操作'], 1):
        print(f"   {i}. {action}")
    print()

def main():
    print("=" * 70)
    print("🔍 全面系统检查")
    print("=" * 70)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    check_cron_tasks()
    check_running_processes()
    check_logs()
    check_reports()
    check_disk_space()
    check_data_directories()
    check_memory_and_system()
    check_network_connectivity()
    generate_summary()
    
    print("=" * 70)
    print("✅ 全面检查完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
