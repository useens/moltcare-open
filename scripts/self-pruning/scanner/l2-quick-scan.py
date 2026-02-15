#!/usr/bin/env python3
"""
森森系统精简守护进程 - L2快速扫描器
Sensen System Pruning Guardian - L2 Quick Scanner

Thinking级别: Medium (L2)
执行频率: 每6小时
功能: Token消耗检测、臃肿快速识别、异常预警

作者: 森森自我优化系统
创建: 2026-02-16
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# 配置
WORKSPACE = "/root/.openclaw/workspace"
SCAN_REPORT_DIR = f"{WORKSPACE}/memory/self-pruning/reports"
QUICK_SCAN_LOG = f"{WORKSPACE}/logs/pruning-quick-scan.log"
THRESHOLDS = {
    "script_count_warning": 200,      # 脚本数警告阈值
    "script_count_critical": 250,     # 脚本数危险阈值
    "backup_size_gb": 1.5,            # 备份大小警告(GB)
    "duplicate_files": 5,             # 重复文件警告数
    "token_log_age_hours": 24,        # Token日志多久未更新需警告
    "large_files_mb": 100,            # 大文件警告(MB)
}

# 受保护清单 (L2也可访问，但只读)
PROTECTED_PATHS = [
    "AGENTS.md", "SOUL.md", "USER.md", "IDENTITY.md", "MEMORY.md",
    "learning-debt.md", ".git/", "scripts/backup/"
]

class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class L2QuickScanner:
    """L2级别快速扫描器 - 专注速度和关键指标"""
    
    def __init__(self):
        self.workspace = Path(WORKSPACE)
        self.findings = []
        self.metrics = {}
        self.start_time = time.time()
        
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        
        # 写入日志文件
        os.makedirs(os.path.dirname(QUICK_SCAN_LOG), exist_ok=True)
        with open(QUICK_SCAN_LOG, "a") as f:
            f.write(log_line + "\n")
    
    def scan_script_count(self):
        """L2: 快速统计脚本数量"""
        self.log("📊 L2扫描: 脚本数量统计...")
        
        scripts_dir = self.workspace / "scripts"
        py_scripts = list(scripts_dir.rglob("*.py"))
        sh_scripts = list(scripts_dir.rglob("*.sh"))
        
        total = len(py_scripts) + len(sh_scripts)
        
        self.metrics["total_scripts"] = total
        self.metrics["python_scripts"] = len(py_scripts)
        self.metrics["bash_scripts"] = len(sh_scripts)
        
        if total > THRESHOLDS["script_count_critical"]:
            self.findings.append({
                "level": "CRITICAL",
                "category": "臃肿",
                "message": f"脚本数量严重超标: {total}个 (阈值: {THRESHOLDS['script_count_critical']})",
                "recommendation": "触发L3深度评估"
            })
        elif total > THRESHOLDS["script_count_warning"]:
            self.findings.append({
                "level": "WARNING",
                "category": "臃肿",
                "message": f"脚本数量偏高: {total}个",
                "recommendation": "考虑精简"
            })
        else:
            self.log(f"  ✓ 脚本数量正常: {total}个", "GREEN")
            
        return total
    
    def scan_token_usage(self):
        """L2: 检测Token使用异常"""
        self.log("📊 L2扫描: Token使用检测...")
        
        token_log = self.workspace / "data" / "token-usage.log"
        
        if not token_log.exists():
            self.findings.append({
                "level": "WARNING",
                "category": "Token",
                "message": "Token日志文件不存在",
                "recommendation": "检查token追踪系统"
            })
            return
        
        # 检查最后更新时间
        mtime = datetime.fromtimestamp(token_log.stat().st_mtime)
        age_hours = (datetime.now() - mtime).total_seconds() / 3600
        
        if age_hours > THRESHOLDS["token_log_age_hours"]:
            self.findings.append({
                "level": "WARNING",
                "category": "Token",
                "message": f"Token日志{age_hours:.1f}小时未更新",
                "recommendation": "检查token追踪是否正常工作"
            })
        
        # L2: 快速检查是否有真实数据(非固定值)
        try:
            with open(token_log) as f:
                lines = f.readlines()[-50:]  # 只读最后50行
            
            if lines:
                # 简单检查：如果所有token数都一样，可能是假的
                totals = []
                for line in lines:
                    if '"total":' in line:
                        try:
                            data = json.loads(line)
                            totals.append(data.get("total", 0))
                        except:
                            pass
                
                if totals and len(set(totals)) == 1:
                    self.findings.append({
                        "level": "CRITICAL",
                        "category": "Token",
                        "message": "Token日志数据异常：所有记录值相同，可能是虚假数据",
                        "recommendation": "需要L3深度分析Token系统"
                    })
                else:
                    self.log(f"  ✓ Token日志数据正常", "GREEN")
        except Exception as e:
            self.findings.append({
                "level": "WARNING",
                "category": "Token",
                "message": f"无法解析Token日志: {e}",
                "recommendation": "检查日志格式"
            })
    
    def scan_backup_size(self):
        """L2: 检测备份存储"""
        self.log("📊 L2扫描: 备份存储检测...")
        
        backup_dir = self.workspace / "backups"
        if not backup_dir.exists():
            return
        
        # 快速计算大小
        total_size = 0
        backup_count = 0
        
        for f in backup_dir.glob("*.tar.gz"):
            total_size += f.stat().st_size
            backup_count += 1
        
        size_gb = total_size / (1024**3)
        self.metrics["backup_size_gb"] = round(size_gb, 2)
        self.metrics["backup_count"] = backup_count
        
        if size_gb > THRESHOLDS["backup_size_gb"]:
            self.findings.append({
                "level": "WARNING",
                "category": "存储",
                "message": f"备份占用过大: {size_gb:.2f}GB ({backup_count}个文件)",
                "recommendation": "清理旧备份，保留策略优化"
            })
        else:
            self.log(f"  ✓ 备份存储正常: {size_gb:.2f}GB", "GREEN")
    
    def scan_duplicates(self):
        """L2: 快速重复文件检测"""
        self.log("📊 L2扫描: 重复文件检测...")
        
        # 只扫描scripts目录
        scripts_dir = self.workspace / "scripts"
        files_by_name = defaultdict(list)
        
        for f in scripts_dir.rglob("*"):
            if f.is_file() and f.suffix in ['.py', '.sh']:
                files_by_name[f.name].append(f)
        
        duplicates = []
        for name, paths in files_by_name.items():
            if len(paths) > 1:
                # 快速比较：如果大小一样，可能是重复
                sizes = [p.stat().st_size for p in paths]
                if len(set(sizes)) < len(sizes):
                    duplicates.append({
                        "name": name,
                        "count": len(paths),
                        "paths": [str(p) for p in paths]
                    })
        
        self.metrics["duplicate_groups"] = len(duplicates)
        
        if len(duplicates) > THRESHOLDS["duplicate_files"]:
            self.findings.append({
                "level": "WARNING",
                "category": "重复",
                "message": f"发现{len(duplicates)}组潜在重复文件",
                "recommendation": "运行L2精简任务清理重复",
                "details": duplicates[:3]  # 只记录前3个
            })
        elif duplicates:
            self.log(f"  ⚠ 发现{len(duplicates)}组重复文件", "YELLOW")
        else:
            self.log(f"  ✓ 未发现明显重复文件", "GREEN")
    
    def scan_trash_size(self):
        """L2: 检测trash目录"""
        self.log("📊 L2扫描: 废弃文件检测...")
        
        trash_dir = self.workspace / ".trash"
        if not trash_dir.exists():
            return
        
        trash_files = list(trash_dir.rglob("*"))
        trash_count = len([f for f in trash_files if f.is_file()])
        
        self.metrics["trash_files"] = trash_count
        
        if trash_count > 20:
            self.findings.append({
                "level": "INFO",
                "category": "清理",
                "message": f".trash目录有{trash_count}个文件待清理",
                "recommendation": "可安全删除或归档"
            })
    
    def check_protected_violation(self):
        """L2: 检查是否有对保护清单的修改操作"""
        # L2只检查，不操作
        pass
    
    def generate_report(self):
        """生成L2扫描报告"""
        os.makedirs(SCAN_REPORT_DIR, exist_ok=True)
        
        report = {
            "scan_type": "L2_QUICK_SCAN",
            "thinking_level": "Medium",
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": round(time.time() - self.start_time, 2),
            "metrics": self.metrics,
            "findings_count": len(self.findings),
            "critical_count": len([f for f in self.findings if f["level"] == "CRITICAL"]),
            "warning_count": len([f for f in self.findings if f["level"] == "WARNING"]),
            "findings": self.findings,
            "recommendations": {
                "l2_actions": [],
                "l3_required": len([f for f in self.findings if f["level"] == "CRITICAL"]) > 0
            }
        }
        
        # 生成L2建议
        if self.metrics.get("duplicate_groups", 0) > 0:
            report["recommendations"]["l2_actions"].append("执行重复文件清理")
        if self.metrics.get("trash_files", 0) > 20:
            report["recommendations"]["l2_actions"].append("清理.trash目录")
        if self.metrics.get("backup_count", 0) > 5:
            report["recommendations"]["l2_actions"].append("清理旧备份")
        
        # 保存报告
        report_file = f"{SCAN_REPORT_DIR}/l2-scan-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        # 同时保存最新报告链接
        latest_link = f"{SCAN_REPORT_DIR}/l2-scan-latest.json"
        if os.path.exists(latest_link):
            os.remove(latest_link)
        os.symlink(report_file, latest_link)
        
        return report, report_file
    
    def print_summary(self, report):
        """打印扫描摘要"""
        print("\n" + "="*60)
        print(f"📋 L2快速扫描完成 (Thinking: Medium)")
        print("="*60)
        print(f"执行时间: {report['execution_time_seconds']:.2f}秒")
        print(f"发现问题: {report['findings_count']}个")
        print(f"  - 严重: {report['critical_count']}个")
        print(f"  - 警告: {report['warning_count']}个")
        print(f"\n关键指标:")
        for key, value in report['metrics'].items():
            print(f"  - {key}: {value}")
        
        if report['recommendations']['l3_required']:
            print(f"\n🔴 发现严重问题，建议触发L3深度评估")
        
        if report['recommendations']['l2_actions']:
            print(f"\n💡 L2建议操作:")
            for action in report['recommendations']['l2_actions']:
                print(f"  - {action}")
        
        print(f"\n📄 详细报告: {SCAN_REPORT_DIR}/l2-scan-latest.json")
        print("="*60)
    
    def run(self):
        """执行完整L2扫描"""
        self.log("="*60)
        self.log("🚀 启动L2快速扫描 (Thinking: Medium)")
        self.log("="*60)
        
        # 执行各项扫描
        self.scan_script_count()
        self.scan_token_usage()
        self.scan_backup_size()
        self.scan_duplicates()
        self.scan_trash_size()
        
        # 生成报告
        report, report_file = self.generate_report()
        
        # 打印摘要
        self.print_summary(report)
        
        # 返回是否需要L3
        return report['recommendations']['l3_required']


def main():
    """主入口"""
    scanner = L2QuickScanner()
    need_l3 = scanner.run()
    
    # 退出码：如果需要L3则返回2，正常完成返回0
    sys.exit(2 if need_l3 else 0)


if __name__ == "__main__":
    main()
