#!/usr/bin/env python3
"""
自动化日志管理系统 v2.0
Automated Log Management System

功能:
- 智能日志轮转
- 自动压缩归档
- 重复日志去重
- 磁盘空间保护
- 日志分析报告

Cron设置: 每天凌晨2:00执行
"""

import os
import gzip
import json
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

class LogAutomationManager:
    """自动化日志管理器"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.logs_dir = self.workspace / "logs"
        self.archive_dir = self.logs_dir / "archive"
        self.report_dir = self.workspace / "reports" / "log-management"
        
        # 配置参数
        self.config = {
            "max_log_size_mb": 100,        # 单个日志最大100MB
            "max_log_age_days": 30,        # 日志保留30天
            "archive_days": 3,             # 3天前日志归档
            "critical_disk_threshold": 90,  # 磁盘告警阈值
            "warning_disk_threshold": 80,  # 磁盘警告阈值
            "dedup_enabled": True,         # 启用日志去重
            "compression_enabled": True    # 启用压缩
        }
        
        # 确保目录存在
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.stats = {
            "processed": 0,
            "archived": 0,
            "deleted": 0,
            "deduped": 0,
            "space_saved_mb": 0
        }
    
    def run_automation(self) -> Dict:
        """运行完整的日志自动化管理"""
        print(f"\n{'='*70}")
        print(f"🗂️  自动化日志管理系统 v2.0")
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        # 1. 检查磁盘空间
        disk_status = self.check_disk_space()
        if disk_status["usage"] > self.config["critical_disk_threshold"]:
            print(f"⚠️  磁盘空间严重不足: {disk_status['usage']}%")
            self.emergency_cleanup()
        
        # 2. 日志去重
        if self.config["dedup_enabled"]:
            self.deduplicate_logs()
        
        # 3. 处理超大日志
        self.process_oversized_logs()
        
        # 4. 归档旧日志
        self.archive_old_logs()
        
        # 5. 清理过期归档
        self.cleanup_old_archives()
        
        # 6. 生成报告
        report = self.generate_report(disk_status)
        
        # 7. 保存状态
        self.save_automation_state(report)
        
        print(f"\n{'='*70}")
        print("✅ 日志自动化管理完成")
        print(f"{'='*70}\n")
        
        return report
    
    def check_disk_space(self) -> Dict:
        """检查磁盘空间"""
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            usage = int(parts[4].replace('%', ''))
            total = parts[1]
            available = parts[3]
        else:
            usage = 0
            total = "unknown"
            available = "unknown"
        
        return {
            "usage": usage,
            "total": total,
            "available": available,
            "status": "critical" if usage > self.config["critical_disk_threshold"] else 
                     "warning" if usage > self.config["warning_disk_threshold"] else "ok"
        }
    
    def deduplicate_logs(self):
        """日志去重 - 检测并合并重复日志条目"""
        print("🔍 执行日志去重...")
        
        dedup_dir = self.logs_dir / ".dedup_cache"
        dedup_dir.mkdir(exist_ok=True)
        
        for log_file in self.logs_dir.glob("*.log"):
            if not log_file.is_file():
                continue
            
            # 计算文件哈希
            file_hash = self.calculate_file_hash(log_file)
            hash_file = dedup_dir / f"{log_file.stem}.hash"
            
            if hash_file.exists():
                with open(hash_file, 'r') as f:
                    prev_hash = f.read().strip()
                
                if prev_hash == file_hash:
                    # 文件未变化，跳过
                    continue
            
            # 去重处理：保留最后1000行
            lines = []
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 使用集合检测连续重复行
            unique_lines = []
            prev_line = None
            dup_count = 0
            
            for line in lines:
                if line == prev_line:
                    dup_count += 1
                    if dup_count <= 2:  # 最多保留3个重复
                        unique_lines.append(line)
                else:
                    dup_count = 0
                    unique_lines.append(line)
                    prev_line = line
            
            # 写回文件
            if len(unique_lines) < len(lines):
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.writelines(unique_lines)
                self.stats["deduped"] += len(lines) - len(unique_lines)
                print(f"   ✓ {log_file.name}: 去重 {len(lines) - len(unique_lines)} 行")
            
            # 保存哈希
            with open(hash_file, 'w') as f:
                f.write(file_hash)
            
            self.stats["processed"] += 1
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def process_oversized_logs(self):
        """处理超大日志文件"""
        print("📦 处理超大日志...")
        
        max_size = self.config["max_log_size_mb"] * 1024 * 1024
        
        for log_file in self.logs_dir.glob("*.log"):
            if not log_file.is_file():
                continue
            
            size = log_file.stat().st_size
            
            if size > max_size:
                # 保留最后5000行
                result = subprocess.run(
                    ["tail", "-n", "5000", str(log_file)],
                    capture_output=True,
                    text=True
                )
                
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                
                new_size = log_file.stat().st_size
                saved_mb = (size - new_size) / (1024 * 1024)
                self.stats["space_saved_mb"] += saved_mb
                
                print(f"   ✓ {log_file.name}: {size/1024/1024:.1f}MB → {new_size/1024/1024:.1f}MB")
    
    def archive_old_logs(self):
        """归档旧日志"""
        print("📁 归档旧日志...")
        
        cutoff_date = datetime.now() - timedelta(days=self.config["archive_days"])
        
        for log_file in self.logs_dir.glob("*.log"):
            if not log_file.is_file():
                continue
            
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if mtime < cutoff_date:
                # 压缩归档
                archive_name = f"{log_file.stem}_{mtime.strftime('%Y%m%d')}.log.gz"
                archive_path = self.archive_dir / archive_name
                
                with open(log_file, 'rb') as f_in:
                    with gzip.open(archive_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # 删除原文件
                size_mb = log_file.stat().st_size / (1024 * 1024)
                log_file.unlink()
                
                self.stats["archived"] += 1
                self.stats["space_saved_mb"] += size_mb
                
                print(f"   ✓ {log_file.name} → {archive_name}")
    
    def cleanup_old_archives(self):
        """清理过期归档"""
        print("🗑️  清理过期归档...")
        
        cutoff_date = datetime.now() - timedelta(days=self.config["max_log_age_days"])
        
        for archive_file in self.archive_dir.glob("*.gz"):
            mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)
            
            if mtime < cutoff_date:
                size_mb = archive_file.stat().st_size / (1024 * 1024)
                archive_file.unlink()
                self.stats["deleted"] += 1
                self.stats["space_saved_mb"] += size_mb
                print(f"   ✓ 删除: {archive_file.name}")
    
    def emergency_cleanup(self):
        """紧急清理 - 磁盘空间严重不足时"""
        print("🚨 执行紧急清理...")
        
        # 立即清理所有超过7天的日志
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for log_file in self.logs_dir.glob("*.log"):
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff_date:
                size_mb = log_file.stat().st_size / (1024 * 1024)
                log_file.unlink()
                self.stats["deleted"] += 1
                self.stats["space_saved_mb"] += size_mb
                print(f"   紧急删除: {log_file.name}")
        
        # 清理所有超过14天的归档
        cutoff_date = datetime.now() - timedelta(days=14)
        for archive_file in self.archive_dir.glob("*.gz"):
            mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)
            if mtime < cutoff_date:
                size_mb = archive_file.stat().st_size / (1024 * 1024)
                archive_file.unlink()
                self.stats["deleted"] += 1
                self.stats["space_saved_mb"] += size_mb
    
    def generate_report(self, disk_status: Dict) -> Dict:
        """生成管理报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "disk_status": disk_status,
            "statistics": self.stats,
            "config": self.config,
            "logs_directory": {
                "path": str(self.logs_dir),
                "total_files": len(list(self.logs_dir.glob("*.log"))),
                "archive_files": len(list(self.archive_dir.glob("*.gz")))
            }
        }
        
        # 保存JSON报告
        report_file = self.report_dir / f"log-automation-{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        print(f"\n{'='*70}")
        print("📊 日志自动化管理报告")
        print(f"{'='*70}")
        print(f"磁盘使用: {disk_status['usage']}% ({disk_status['status']})")
        print(f"处理日志: {self.stats['processed']} 个")
        print(f"归档日志: {self.stats['archived']} 个")
        print(f"删除归档: {self.stats['deleted']} 个")
        print(f"去重行数: {self.stats['deduped']} 行")
        print(f"节省空间: {self.stats['space_saved_mb']:.1f} MB")
        print(f"报告保存: {report_file}")
        print(f"{'='*70}")
        
        return report
    
    def save_automation_state(self, report: Dict):
        """保存自动化状态"""
        state_file = self.workspace / "memory" / "log-automation-state.json"
        
        state = {
            "last_run": datetime.now().isoformat(),
            "last_report": report,
            "total_runs": 0
        }
        
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                try:
                    old_state = json.load(f)
                    state["total_runs"] = old_state.get("total_runs", 0) + 1
                except:
                    state["total_runs"] = 1
        else:
            state["total_runs"] = 1
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    manager = LogAutomationManager()
    report = manager.run_automation()
    return report


if __name__ == "__main__":
    main()
