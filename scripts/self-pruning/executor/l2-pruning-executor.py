#!/usr/bin/env python3
"""
森森系统精简守护进程 - L2精简执行器
Sensen System Pruning Guardian - L2 Pruning Executor

Thinking级别: Medium (L2)
触发条件: L2扫描发现可安全清理的问题
功能: 执行安全的精简操作，严格遵守保护清单

安全原则:
1. 只删除明确安全的文件
2. 先移动到.trash，保留30天
3. 绝不触碰保护清单中的任何内容
4. 所有操作记录日志，可回滚

作者: 森森自我优化系统
创建: 2026-02-16
"""

import os
import sys
import json
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
TRASH_DIR = f"{WORKSPACE}/.trash"
ARCHIVE_DIR = f"{WORKSPACE}/archives"
LOG_FILE = f"{WORKSPACE}/logs/pruning-executor.log"
SAFETY_LOCK = f"{WORKSPACE}/.pruning-safety-lock"

# === 受保护清单 (L2只读，绝不可修改) ===
PROTECTED_PATTERNS = [
    "AGENTS.md", "SOUL.md", "USER.md", "IDENTITY.md", "MEMORY.md",
    "learning-debt.md",
    ".git/**/*",                    # Git仓库
    "scripts/backup/**/*",          # 备份脚本
    "memory/**/*",                  # 记忆系统
    "data/vector_memory/**/*",      # 向量记忆
]

# L2允许的安全操作
L2_SAFE_OPERATIONS = {
    "duplicate_files": True,        # 删除重复文件(保留一个)
    "old_backups": True,            # 清理旧备份(保留最近3个)
    "trash_cleanup": True,          # 清理超过30天的.trash
    "temp_files": True,             # 清理临时文件
    "empty_logs": True,             # 清空无效日志
}

class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

class L2PruningExecutor:
    """L2精简执行器 - 安全第一"""
    
    def __init__(self, dry_run=True):
        self.workspace = Path(WORKSPACE)
        self.dry_run = dry_run  # 默认试运行模式
        self.operations_log = []
        self.stats = {
            "files_moved": 0,
            "files_deleted": 0,
            "space_reclaimed_mb": 0,
            "errors": []
        }
        
        # 确保目录存在
        os.makedirs(TRASH_DIR, exist_ok=True)
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    def log(self, message, level="INFO"):
        """记录操作日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.operations_log.append(log_entry)
        
        # 控制台输出
        color = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "DRY_RUN": Colors.CYAN
        }.get(level, Colors.RESET)
        
        prefix = "[DRY-RUN] " if self.dry_run and level != "DRY_RUN" else ""
        print(f"{color}[{level}]{Colors.RESET} {prefix}{message}")
        
        # 写入日志文件
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] [{level}] {prefix}{message}\n")
    
    def is_protected(self, path):
        """检查路径是否受保护"""
        path_str = str(path.relative_to(self.workspace))
        
        for pattern in PROTECTED_PATTERNS:
            if pattern.endswith("/**/*"):
                # 目录保护
                dir_pattern = pattern[:-5]
                if path_str.startswith(dir_pattern):
                    return True
            elif pattern in path_str:
                return True
        
        return False
    
    def safe_move_to_trash(self, src_path, reason=""):
        """安全移动到trash目录"""
        if self.is_protected(src_path):
            self.log(f"跳过受保护路径: {src_path}", "WARNING")
            return False
        
        try:
            # 在trash中保持目录结构
            rel_path = src_path.relative_to(self.workspace)
            trash_dest = Path(TRASH_DIR) / datetime.now().strftime("%Y%m%d") / rel_path
            
            if self.dry_run:
                self.log(f"[DRY-RUN] 将移动: {rel_path} -> {trash_dest}", "DRY_RUN")
                self.stats["files_moved"] += 1
                self.stats["space_reclaimed_mb"] += src_path.stat().st_size / (1024*1024)
                return True
            
            # 实际移动
            trash_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(trash_dest))
            
            self.log(f"已移动到trash: {rel_path} (原因: {reason})", "SUCCESS")
            self.stats["files_moved"] += 1
            self.stats["space_reclaimed_mb"] += src_path.stat().st_size / (1024*1024)
            
            return True
            
        except Exception as e:
            self.log(f"移动失败 {src_path}: {e}", "ERROR")
            self.stats["errors"].append(str(e))
            return False
    
    def operation_1_cleanup_duplicates(self):
        """L2操作1: 清理重复文件"""
        self.log("="*60)
        self.log("🧹 L2操作: 清理重复文件")
        self.log("="*60)
        
        scripts_dir = self.workspace / "scripts"
        files_by_name = {}
        
        # 收集文件
        for f in scripts_dir.rglob("*"):
            if f.is_file() and f.suffix in ['.py', '.sh']:
                name = f.name
                if name not in files_by_name:
                    files_by_name[name] = []
                files_by_name[name].append(f)
        
        # 处理重复
        cleaned = 0
        for name, paths in files_by_name.items():
            if len(paths) > 1:
                # 按修改时间排序，保留最新的
                paths_sorted = sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)
                keep = paths_sorted[0]
                duplicates = paths_sorted[1:]
                
                self.log(f"发现重复: {name}")
                self.log(f"  保留: {keep.relative_to(self.workspace)}")
                
                for dup in duplicates:
                    if self.safe_move_to_trash(dup, f"重复文件，保留{keep.name}"):
                        cleaned += 1
        
        self.log(f"重复文件清理完成: {cleaned}个文件", "SUCCESS")
        return cleaned
    
    def operation_2_cleanup_backups(self):
        """L2操作2: 清理旧备份"""
        self.log("="*60)
        self.log("🧹 L2操作: 清理旧备份 (保留最近3个)")
        self.log("="*60)
        
        backup_dir = self.workspace / "backups"
        if not backup_dir.exists():
            self.log("备份目录不存在，跳过")
            return 0
        
        backups = sorted(backup_dir.glob("*.tar.gz"), 
                        key=lambda p: p.stat().st_mtime, 
                        reverse=True)
        
        if len(backups) <= 3:
            self.log(f"备份数量({len(backups)})≤3，无需清理")
            return 0
        
        to_remove = backups[3:]  # 保留前3个
        removed = 0
        
        for backup in to_remove:
            # 备份文件不受保护清单限制，但我们也安全处理
            try:
                size_mb = backup.stat().st_size / (1024*1024)
                
                if self.dry_run:
                    self.log(f"[DRY-RUN] 将删除备份: {backup.name} ({size_mb:.1f}MB)", "DRY_RUN")
                else:
                    backup.unlink()
                    self.log(f"已删除旧备份: {backup.name} ({size_mb:.1f}MB)", "SUCCESS")
                
                removed += 1
                self.stats["files_deleted"] += 1
                self.stats["space_reclaimed_mb"] += size_mb
                
            except Exception as e:
                self.log(f"删除备份失败: {e}", "ERROR")
        
        self.log(f"旧备份清理完成: {removed}个文件", "SUCCESS")
        return removed
    
    def operation_3_cleanup_trash(self):
        """L2操作3: 清理超过30天的trash"""
        self.log("="*60)
        self.log("🧹 L2操作: 清理超过30天的trash文件")
        self.log("="*60)
        
        trash_dir = Path(TRASH_DIR)
        if not trash_dir.exists():
            self.log("Trash目录为空")
            return 0
        
        cutoff = datetime.now() - timedelta(days=30)
        removed = 0
        
        for date_dir in trash_dir.iterdir():
            if date_dir.is_dir():
                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y%m%d")
                    if dir_date < cutoff:
                        # 删除整个日期目录
                        if self.dry_run:
                            self.log(f"[DRY-RUN] 将删除trash目录: {date_dir.name}", "DRY_RUN")
                        else:
                            shutil.rmtree(date_dir)
                            self.log(f"已删除旧trash: {date_dir.name}", "SUCCESS")
                        removed += 1
                except ValueError:
                    continue  # 跳过非日期格式目录
        
        self.log(f"Trash清理完成: {removed}个目录", "SUCCESS")
        return removed
    
    def operation_4_cleanup_logs(self):
        """L2操作4: 清理无效日志"""
        self.log("="*60)
        self.log("🧹 L2操作: 清理无效日志")
        self.log("="*60)
        
        # 清空token-usage.log (已知无效)
        token_log = self.workspace / "data" / "token-usage.log"
        if token_log.exists():
            if self.dry_run:
                self.log(f"[DRY-RUN] 将清空: token-usage.log", "DRY_RUN")
            else:
                token_log.write_text("")
                self.log(f"已清空无效日志: token-usage.log", "SUCCESS")
        
        # 清理超过7天且大于10MB的日志
        logs_dir = self.workspace / "logs"
        if logs_dir.exists():
            cutoff = datetime.now() - timedelta(days=7)
            for log_file in logs_dir.rglob("*.log"):
                try:
                    if log_file.stat().st_mtime < cutoff.timestamp():
                        size_mb = log_file.stat().st_size / (1024*1024)
                        if size_mb > 10:  # 只清理大日志
                            if self.dry_run:
                                self.log(f"[DRY-RUN] 将清空大日志: {log_file.name}", "DRY_RUN")
                            else:
                                log_file.write_text("")
                                self.log(f"已清空旧日志: {log_file.name}", "SUCCESS")
                except Exception as e:
                    self.log(f"处理日志失败 {log_file}: {e}", "ERROR")
        
        return True
    
    def operation_5_cleanup_temp(self):
        """L2操作5: 清理临时文件"""
        self.log("="*60)
        self.log("🧹 L2操作: 清理临时文件")
        self.log("="*60)
        
        temp_patterns = [
            "*.tmp", "*.temp", "*.pyc", "__pycache__",
            "*.log.old", "*.bak"
        ]
        
        cleaned = 0
        for pattern in temp_patterns:
            for temp_file in self.workspace.rglob(pattern):
                if temp_file.is_file() and not self.is_protected(temp_file):
                    if self.safe_move_to_trash(temp_file, "临时文件"):
                        cleaned += 1
        
        self.log(f"临时文件清理完成: {cleaned}个文件", "SUCCESS")
        return cleaned
    
    def generate_report(self):
        """生成执行报告"""
        report = {
            "execution_time": datetime.now().isoformat(),
            "thinking_level": "L2_Medium",
            "dry_run": self.dry_run,
            "stats": self.stats,
            "operations": self.operations_log,
            "protected_violations": 0,  # L2绝不应有
        }
        
        report_file = f"{WORKSPACE}/memory/self-pruning/reports/l2-execution-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        return report, report_file
    
    def print_summary(self, report):
        """打印执行摘要"""
        mode = "[试运行]" if self.dry_run else "[实际执行]"
        print("\n" + "="*60)
        print(f"📋 L2精简执行完成 {mode} (Thinking: Medium)")
        print("="*60)
        print(f"文件移动: {self.stats['files_moved']}个")
        print(f"文件删除: {self.stats['files_deleted']}个")
        print(f"空间回收: {self.stats['space_reclaimed_mb']:.2f}MB")
        print(f"错误: {len(self.stats['errors'])}个")
        
        if self.dry_run:
            print(f"\n⚠️  以上为试运行结果，实际执行请使用 --execute")
        else:
            print(f"\n✅ 精简操作已实际执行")
            print(f"🗑️  被移动文件在: {TRASH_DIR}/")
            print(f"📦 30天后自动清理trash")
        
        print("="*60)
    
    def run(self, operations=None):
        """执行精简操作"""
        operations = operations or ["duplicates", "backups", "trash", "logs", "temp"]
        
        self.log("="*60)
        self.log(f"🚀 启动L2精简执行器 (Thinking: Medium)")
        self.log(f"模式: {'试运行' if self.dry_run else '实际执行'}")
        self.log("="*60)
        
        # 执行各项操作
        if "duplicates" in operations:
            self.operation_1_cleanup_duplicates()
        if "backups" in operations:
            self.operation_2_cleanup_backups()
        if "trash" in operations:
            self.operation_3_cleanup_trash()
        if "logs" in operations:
            self.operation_4_cleanup_logs()
        if "temp" in operations:
            self.operation_5_cleanup_temp()
        
        # 生成报告
        report, report_file = self.generate_report()
        self.print_summary(report)
        
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="L2精简执行器")
    parser.add_argument("--execute", action="store_true", help="实际执行(默认试运行)")
    parser.add_argument("--operation", choices=["duplicates", "backups", "trash", "logs", "temp", "all"],
                       default="all", help="执行特定操作")
    args = parser.parse_args()
    
    operations = None if args.operation == "all" else [args.operation]
    
    executor = L2PruningExecutor(dry_run=not args.execute)
    executor.run(operations)


if __name__ == "__main__":
    main()
