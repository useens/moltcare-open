#!/usr/bin/env python3
"""
evolution-status.py - 自我进化系统状态报告
全自主运行模式下的健康监控和效果评估
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
STAGING = WORKSPACE / "staging"
LOGS = STAGING / "logs"
CRON_JOBS_FILE = Path("/root/.openclaw/cron/jobs.json")

def format_time(ms=None, seconds=None):
    """格式化时间为可读格式"""
    if ms:
        seconds = ms / 1000
    elif seconds is None:
        return "N/A"
    
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def read_cron_jobs():
    """读取cron作业状态"""
    try:
        with open(CRON_JOBS_FILE) as f:
            data = json.load(f)
        return data.get("jobs", [])
    except Exception as e:
        print(f"❌ 无法读取cron作业: {e}")
        return []

def analyze_job_health(job):
    """分析单个作业的健康状态"""
    state = job.get("state", {})
    last_status = state.get("lastStatus", "unknown")
    consecutive_errors = state.get("consecutiveErrors", 0)
    
    if last_status == "error" or consecutive_errors > 0:
        return "🔴", f"错误({consecutive_errors}次连续)"
    elif last_status == "ok":
        return "🟢", "正常"
    else:
        return "🟡", "未知"

def get_evolution_metrics():
    """获取自我进化指标"""
    metrics = {
        "evolution_runs": 0,
        "last_evolution": None,
        "targets_improved": set(),
        "signal_strength_history": [],
        "deploy_success_rate": 0,
        "avg_improvement_time": 0
    }
    
    # 读取进化日志
    log_file = LOGS / "evolution.log"
    if log_file.exists():
        content = log_file.read_text()
        lines = content.split("\n")
        
        for line in lines:
            if "信号充足" in line:
                metrics["evolution_runs"] += 1
            if "选择: " in line and "轮换" in line:
                target = line.split("选择: ")[1].split(" (")[0]
                metrics["targets_improved"].add(target)
            if "信号评分:" in line:
                # 提取评分
                parts = line.split("信号评分: ")
                if len(parts) > 1:
                    score_part = parts[1].split("/")[0]
                    try:
                        score = int(score_part)
                        metrics["signal_strength_history"].append(score)
                    except:
                        pass
        
        # 最后一次进化时间
        for line in reversed(lines):
            if "🌲 自我进化引擎启动" in line:
                metrics["last_evolution"] = line.split("[")[1].split("]")[0]
                break
    
    # 读取部署历史
    backup_dir = STAGING / "backups"
    if backup_dir.exists():
        backups = list(backup_dir.glob("*"))
        if backups:
            latest = max(backups, key=lambda x: x.stat().st_mtime)
            metrics["last_deploy"] = datetime.fromtimestamp(latest.stat().st_mtime).strftime("%m-%d %H:%M")
    
    return metrics

def check_files_health():
    """检查关键文件的健康状况"""
    files_to_check = [
        "AGENTS.md", "SOUL.md", "MEMORY.md", "USER.md", 
        "IDENTITY.md", "TOOLS.md", "CONFIG.md"
    ]
    
    health = {}
    for filename in files_to_check:
        filepath = WORKSPACE / filename
        if filepath.exists():
            stat = filepath.stat()
            age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600
            size = stat.st_size
            
            if age_hours > 48:
                status = "🔴"  # 陈旧
            elif age_hours > 24:
                status = "🟡"  # 需更新
            else:
                status = "🟢"  # 新鲜
                
            health[filename] = {
                "exists": True,
                "status": status,
                "age_hours": age_hours,
                "size_kb": size / 1024,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).strftime("%m-%d %H:%M")
            }
        else:
            health[filename] = {"status": "❌", "exists": False}
    
    return health

def generate_report():
    """生成完整的系统状态报告"""
    print("🧬 全自主运行·自我进化系统状态报告")
    print("=" * 60)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Cron作业健康检查
    print("📋 Cron作业状态监控")
    print("-" * 40)
    jobs = read_cron_jobs()
    
    evolution_jobs = []
    monitoring_jobs = []
    other_jobs = []
    
    for job in jobs:
        job_name = job.get("name", "未命名")
        status_icon, status_text = analyze_job_health(job)
        
        if "evolution" in job_name.lower():
            evolution_jobs.append((job_name, status_icon, status_text))
        elif any(keyword in job_name.lower() for keyword in ["monitor", "snapshot", "backup", "sync"]):
            monitoring_jobs.append((job_name, status_icon, status_text))
        else:
            other_jobs.append((job_name, status_icon, status_text))
    
    print("🎯 进化引擎:")
    for name, icon, text in evolution_jobs:
        print(f"  {icon} {name}: {text}")
    
    print("\n🛡️ 监控维护:")
    for name, icon, text in monitoring_jobs[:5]:  # 只显示前5个
        print(f"  {icon} {name}: {text}")
    
    # 2. 自我进化指标
    print("\n📈 自我进化效果")
    print("-" * 40)
    metrics = get_evolution_metrics()
    
    print(f"总进化次数: {metrics['evolution_runs']}")
    if metrics['last_evolution']:
        print(f"最近一次: {metrics['last_evolution']}")
    if metrics['targets_improved']:
        print(f"改进目标: {', '.join(sorted(metrics['targets_improved']))}")
    if metrics['signal_strength_history']:
        avg_signal = sum(metrics['signal_strength_history']) / len(metrics['signal_strength_history'])
        print(f"平均信号强度: {avg_signal:.1f}/9")
    
    # 3. 文件健康状态
    print("\n📁 核心文件状态")
    print("-" * 40)
    file_health = check_files_health()
    
    critical_files = ["AGENTS.md", "SOUL.md", "MEMORY.md"]
    for filename in critical_files:
        if filename in file_health:
            info = file_health[filename]
            if info.get("exists"):
                print(f"{info['status']} {filename}: {info['age_hours']:.1f}小时未更新")
            else:
                print(f"❌ {filename}: 文件缺失")
        else:
            print(f"❓ {filename}: not in health dict")
    
    print("\n其他文件:")
    for filename, info in file_health.items():
        if filename not in critical_files and info.get("exists"):
            if info['age_hours'] > 24:
                print(f"{info['status']} {filename}: {info['age_hours']:.1f}小时")
    
    # 4. 系统健康总结
    print("\n💡 系统健康总结")
    print("-" * 40)
    
    issues = []
    warnings = []
    
    # 检查问题
    for job in jobs:
        state = job.get("state", {})
        if state.get("lastStatus") == "error" or state.get("consecutiveErrors", 0) > 0:
            issues.append(f"❌ {job.get('name')} 执行失败")
    
    for filename, info in file_health.items():
        if info.get("exists") and info['age_hours'] > 48:
            warnings.append(f"⚠️  {filename} 超过48小时未更新")
    
    if not issues and not warnings:
        print("✅ 系统运行状态良好")
        print("🔄 自我进化机制正常工作")
    else:
        if issues:
            print("发现以下问题:")
            for issue in issues[:5]:
                print(f"  {issue}")
        if warnings:
            print("警告:")
            for warning in warnings[:3]:
                print(f"  {warning}")
    
    # 5. 下一步建议
    print("\n🚀 优化建议")
    print("-" * 40)
    
    if metrics['evolution_runs'] == 0:
        print("📌 自我进化尚未启动，请检查 self-evolution-trigger 任务")
    
    stale_files = [f for f, info in file_health.items() if info.get("exists") and info['age_hours'] > 24]
    if stale_files:
        print(f"📌 需要更新文件: {', '.join(stale_files[:3])}")
    
    print("📌 建议: 运行自我进化手动触发")
    print("  cd /root/.openclaw/workspace && ./staging/scripts/self-evolution.sh")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    generate_report()