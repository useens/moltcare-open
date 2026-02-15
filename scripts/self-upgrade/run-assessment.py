#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensen Intelligence Assessment Runner
智能水平评估执行脚本 (Python版本)

用法: ./run-assessment.py [mode]
mode: high | medium | emergency
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE_DIR = Path("/root/.openclaw/workspace")
SCRIPT_DIR = WORKSPACE_DIR / "scripts" / "self-upgrade"
MEMORY_DIR = WORKSPACE_DIR / "memory" / "self-upgrade"
LOG_DIR = Path("/var/log/sensen-upgrade")

# 确保目录存在
for d in [MEMORY_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 参数
MODE = sys.argv[1] if len(sys.argv) > 1 else "medium"
TIMESTAMP = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
DATE_STR = datetime.now().strftime('%Y%m%d_%H%M%S')
REPORT_FILE = MEMORY_DIR / f"assessment_report_{DATE_STR}.json"

def log(message):
    """输出日志"""
    log_line = f"[{TIMESTAMP}] {message}"
    print(log_line)
    with open(LOG_DIR / "assessment.log", "a") as f:
        f.write(log_line + "\n")

def run_command(cmd, timeout=10):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def evaluate_code_quality():
    """评估代码质量"""
    log("📊 评估: 代码质量")
    
    score = 0.75
    issues = 0
    
    # 检查脚本数量
    scripts = list(WORKSPACE_DIR.rglob("scripts/*.py")) + list(WORKSPACE_DIR.rglob("scripts/*.sh"))
    if len(scripts) > 50:
        score += 0.05
    
    # 检查Python语法
    py_files = list(WORKSPACE_DIR.rglob("scripts/*.py"))
    py_errors = 0
    for f in py_files[:50]:  # 限制检查数量
        try:
            result = subprocess.run(["python3", "-m", "py_compile", str(f)], 
                                  capture_output=True, timeout=5)
            if result.returncode != 0:
                py_errors += 1
        except:
            pass
    
    if py_errors == 0:
        score += 0.05
    else:
        score -= 0.05
        issues += py_errors
    
    # 检查Bash语法
    sh_files = list(WORKSPACE_DIR.rglob("scripts/*.sh"))
    sh_errors = 0
    for f in sh_files[:30]:
        try:
            result = subprocess.run(["bash", "-n", str(f)], 
                                  capture_output=True, timeout=5)
            if result.returncode != 0:
                sh_errors += 1
        except:
            pass
    
    if sh_errors == 0:
        score += 0.05
    else:
        score -= 0.03
    
    score = min(1.0, max(0.1, score))
    log(f"  代码质量得分: {score:.2f} (问题数: {issues})")
    return round(score, 2)

def evaluate_execution_efficiency():
    """评估执行效率"""
    log("📊 评估: 执行效率")
    
    score = 0.70
    
    # 检查系统负载
    try:
        load_avg = os.getloadavg()[0]
        cpu_cores = os.cpu_count() or 1
        
        if load_avg < cpu_cores:
            score += 0.10
        elif load_avg > cpu_cores * 2:
            score -= 0.10
    except:
        pass
    
    # 检查内存使用
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        mem_total = 0
        mem_available = 0
        for line in meminfo.split('\n'):
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemAvailable:'):
                mem_available = int(line.split()[1])
        
        if mem_total > 0:
            mem_usage = ((mem_total - mem_available) / mem_total) * 100
            if mem_usage < 70:
                score += 0.05
            elif mem_usage > 90:
                score -= 0.10
    except:
        pass
    
    score = min(1.0, max(0.1, score))
    load_str = f"{load_avg:.2f}" if 'load_avg' in locals() else "N/A"
    mem_str = f"{mem_usage:.0f}" if 'mem_usage' in locals() else "N/A"
    log(f"  执行效率得分: {score:.2f} (负载: {load_str}, 内存: {mem_str}%)")
    return round(score, 2)

def evaluate_error_recovery():
    """评估错误恢复能力"""
    log("📊 评估: 错误恢复能力")
    
    score = 0.65
    
    # 检查最近的错误日志
    recent_errors = 0
    if LOG_DIR.exists():
        import time
        one_day_ago = time.time() - 86400
        for log_file in LOG_DIR.glob("*.log"):
            if log_file.stat().st_mtime > one_day_ago:
                try:
                    content = log_file.read_text().lower()
                    recent_errors += content.count('error')
                except:
                    pass
    
    if recent_errors == 0:
        score += 0.15
    elif recent_errors < 10:
        score += 0.05
    elif recent_errors > 50:
        score -= 0.15
    
    # 检查自动恢复脚本
    if (WORKSPACE_DIR / "scripts" / "auto_fix_system.py").exists():
        score += 0.05
    
    score = min(1.0, max(0.1, score))
    log(f"  错误恢复得分: {score:.2f} (近期错误: {recent_errors})")
    return round(score, 2)

def evaluate_learning_speed():
    """评估学习速度"""
    log("📊 评估: 学习速度")
    
    score = 0.60
    
    # 检查最近新增脚本
    import time
    one_week_ago = time.time() - 7 * 86400
    recent_scripts = 0
    for f in WORKSPACE_DIR.rglob("scripts/*"):
        if f.is_file() and f.stat().st_mtime > one_week_ago:
            recent_scripts += 1
            if recent_scripts > 20:
                break
    
    if recent_scripts > 10:
        score += 0.20
    elif recent_scripts > 5:
        score += 0.10
    elif recent_scripts > 0:
        score += 0.05
    
    # 检查文档更新
    recent_docs = sum(1 for f in WORKSPACE_DIR.glob("*.md") 
                     if f.stat().st_mtime > one_week_ago)
    if recent_docs > 0:
        score += 0.05
    
    score = min(1.0, score)
    log(f"  学习速度得分: {score:.2f} (7天内新增: {recent_scripts})")
    return round(score, 2)

def evaluate_autonomy():
    """评估自主性"""
    log("📊 评估: 自主性")
    
    score = 0.80
    
    # 检查自动化脚本数量
    auto_keywords = ['auto', 'daemon', 'schedule', 'self-upgrade']
    auto_scripts = 0
    for f in WORKSPACE_DIR.rglob("scripts/*"):
        if any(kw in f.name.lower() for kw in auto_keywords):
            auto_scripts += 1
    
    if auto_scripts > 10:
        score += 0.10
    elif auto_scripts > 5:
        score += 0.05
    
    # 检查systemd服务
    try:
        result = subprocess.run(["systemctl", "list-unit-files"], 
                              capture_output=True, text=True, timeout=5)
        if 'sensen' in result.stdout:
            score += 0.05
    except:
        pass
    
    score = min(1.0, score)
    log(f"  自主性得分: {score:.2f} (自动化脚本: {auto_scripts})")
    return round(score, 2)

def evaluate_verification():
    """评估验证能力"""
    log("📊 评估: 验证能力")
    
    score = 0.70
    
    # 检查验证脚本存在性
    if (WORKSPACE_DIR / "scripts" / "upgrade-verifier.py").exists():
        score += 0.10
    
    if (SCRIPT_DIR / "verify-upgrade.py").exists():
        score += 0.10
    
    # 检查验证历史
    if MEMORY_DIR.exists():
        verify_history = len(list(MEMORY_DIR.glob("*verify*")))
        if verify_history > 0:
            score += 0.05
    
    score = min(1.0, score)
    log(f"  验证能力得分: {score:.2f}")
    return round(score, 2)

def run_deep_checks():
    """深度评估额外检查"""
    log("🔍 执行深度评估额外检查...")
    
    # 执行系统优化机会扫描
    opt_script = WORKSPACE_DIR / "scripts" / "optimization-opportunity-finder.py"
    if opt_script.exists():
        log("  运行优化机会扫描...")
        try:
            subprocess.run(["python3", str(opt_script)], timeout=120, 
                         capture_output=True)
        except:
            pass
    
    # 执行弱点分析
    weak_script = WORKSPACE_DIR / "scripts" / "weakness-analyzer.py"
    if weak_script.exists():
        log("  运行弱点分析...")
        try:
            subprocess.run(["python3", str(weak_script)], timeout=120,
                         capture_output=True)
        except:
            pass
    
    log("✅ 深度评估额外检查完成")

def generate_report(results):
    """生成报告"""
    log("📝 生成评估报告...")
    
    # 计算综合得分
    overall = round(sum(results.values()) / len(results), 2)
    
    report = {
        "timestamp": TIMESTAMP,
        "mode": MODE,
        "overall_score": overall,
        "dimensions": results,
        "hostname": os.uname().nodename,
        "assessment_version": "1.0.0"
    }
    
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    log(f"📄 报告已保存: {REPORT_FILE}")
    log(f"📊 综合得分: {overall}")
    return report

def main():
    """主函数"""
    log("=" * 40)
    log(f"🧠 启动智能水平评估 - 模式: {MODE}")
    log("=" * 40)
    log(f"开始执行{MODE}级别评估...")
    
    # 执行各维度评估
    results = {
        "code_quality": evaluate_code_quality(),
        "execution_efficiency": evaluate_execution_efficiency(),
        "error_recovery": evaluate_error_recovery(),
        "learning_speed": evaluate_learning_speed(),
        "autonomy": evaluate_autonomy(),
        "verification": evaluate_verification()
    }
    
    # 深度模式额外检查
    if MODE == "high":
        run_deep_checks()
    
    # 生成报告
    report = generate_report(results)
    
    log("=" * 40)
    log(f"✅ 评估完成 - 模式: {MODE}")
    log("=" * 40)
    
    # 输出JSON结果
    print(json.dumps(report))

if __name__ == "__main__":
    main()
