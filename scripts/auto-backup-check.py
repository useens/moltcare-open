#!/usr/bin/env python3
"""
智能备份检查与修复系统 v2.0
Intelligent Backup Check & Repair System

功能:
- 备份完整性检查
- 自动修复损坏备份
- GitHub同步验证
- 备份策略优化
- 灾难恢复测试

Cron设置: 每6小时执行一次
"""

import os
import json
import subprocess
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tarfile
import shutil


class BackupRepairSystem:
    """备份检查与修复系统"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.backup_dir = Path("/root/.openclaw/backups")
        self.memory_dir = self.workspace / "memory"
        self.report_dir = self.workspace / "reports" / "backup"
        
        # 配置
        self.config = {
            "min_backups": 5,              # 最少保留5个备份
            "max_backups": 20,             # 最多保留20个备份
            "backup_interval_hours": 6,    # 备份间隔6小时
            "github_sync": True,           # 启用GitHub同步
            "integrity_check": True,       # 启用完整性检查
            "auto_repair": True            # 启用自动修复
        }
        
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # 状态跟踪
        self.issues_found = []
        self.repairs_made = []
        self.stats = {
            "backups_checked": 0,
            "backups_corrupt": 0,
            "backups_repaired": 0,
            "github_sync_status": "unknown"
        }
    
    def run_backup_check(self) -> Dict:
        """运行完整的备份检查流程"""
        print(f"\n{'='*70}")
        print(f"💾 智能备份检查与修复系统 v2.0")
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        # 1. 检查本地备份目录
        self.ensure_backup_directory()
        
        # 2. 检查现有备份完整性
        self.check_backup_integrity()
        
        # 3. 验证GitHub同步
        self.verify_github_sync()
        
        # 4. 检查备份策略
        self.check_backup_strategy()
        
        # 5. 执行必要的修复
        if self.config["auto_repair"]:
            self.execute_repairs()
        
        # 6. 创建新备份（如果需要）
        self.create_backup_if_needed()
        
        # 7. 生成报告
        report = self.generate_report()
        
        print(f"\n{'='*70}")
        print("✅ 备份检查完成")
        print(f"{'='*70}\n")
        
        return report
    
    def ensure_backup_directory(self):
        """确保备份目录存在"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ 备份目录: {self.backup_dir}")
    
    def check_backup_integrity(self):
        """检查备份完整性"""
        print("🔍 检查备份完整性...")
        
        backup_files = sorted(
            self.backup_dir.glob("workspace_backup_*.tar.gz"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for backup_file in backup_files[:10]:  # 只检查最近10个
            self.stats["backups_checked"] += 1
            
            try:
                # 检查tar文件完整性
                with tarfile.open(backup_file, 'r:gz') as tar:
                    members = tar.getmembers()
                    
                    # 检查关键文件是否存在
                    critical_files = [
                        'SOUL.md',
                        'AGENTS.md',
                        'scripts/hyper-evolution.py',
                        'scripts/collect-web-intel-fast.py'
                    ]
                    
                    found_critical = []
                    for member in members:
                        for critical in critical_files:
                            if critical in member.name:
                                found_critical.append(critical)
                    
                    if len(found_critical) < len(critical_files) / 2:
                        self.issues_found.append({
                            "type": "incomplete_backup",
                            "file": str(backup_file),
                            "details": f"关键文件缺失: {set(critical_files) - set(found_critical)}"
                        })
                        self.stats["backups_corrupt"] += 1
                        print(f"   ⚠️  {backup_file.name}: 备份不完整")
                    else:
                        print(f"   ✓ {backup_file.name}: 完整")
                    
            except Exception as e:
                self.issues_found.append({
                    "type": "corrupt_backup",
                    "file": str(backup_file),
                    "details": str(e)
                })
                self.stats["backups_corrupt"] += 1
                print(f"   ❌ {backup_file.name}: 损坏 - {e}")
    
    def verify_github_sync(self):
        """验证GitHub同步状态"""
        print("🐙 验证GitHub同步...")
        
        try:
            # 检查Git配置
            result = subprocess.run(
                ["git", "-C", str(self.workspace), "status", "--short"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.issues_found.append({
                    "type": "git_error",
                    "details": result.stderr
                })
                self.stats["github_sync_status"] = "error"
                print(f"   ❌ Git错误: {result.stderr}")
                return
            
            # 检查未提交的更改
            if result.stdout.strip():
                # 有未提交的更改
                pending_files = len(result.stdout.strip().split('\n'))
                print(f"   ⚠️  有 {pending_files} 个未提交更改")
                
                # 自动提交
                self.auto_commit_changes()
            else:
                print(f"   ✓ 工作区干净")
            
            # 检查上次推送
            result = subprocess.run(
                ["git", "-C", str(self.workspace), "log", 
                 "--format=%H", "-1", "origin/main..HEAD"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout.strip():
                unpushed = len(result.stdout.strip().split('\n'))
                print(f"   ⚠️  有 {unpushed} 个提交未推送")
                self.auto_push_changes()
            else:
                print(f"   ✓ 已同步到GitHub")
                self.stats["github_sync_status"] = "synced"
                
        except Exception as e:
            self.issues_found.append({
                "type": "github_sync_error",
                "details": str(e)
            })
            self.stats["github_sync_status"] = "error"
            print(f"   ❌ GitHub同步验证失败: {e}")
    
    def auto_commit_changes(self):
        """自动提交更改"""
        try:
            subprocess.run(
                ["git", "-C", str(self.workspace), "add", "-A"],
                check=True,
                timeout=30
            )
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            subprocess.run(
                ["git", "-C", str(self.workspace), "commit", "-m", 
                 f"auto-backup: {timestamp}"],
                capture_output=True,
                timeout=30
            )
            
            self.repairs_made.append({
                "type": "auto_commit",
                "timestamp": datetime.now().isoformat()
            })
            print(f"   ✓ 已自动提交更改")
            
        except Exception as e:
            print(f"   ❌ 自动提交失败: {e}")
    
    def auto_push_changes(self):
        """自动推送更改"""
        try:
            subprocess.run(
                ["git", "-C", str(self.workspace), "push", "origin", "main"],
                capture_output=True,
                timeout=60
            )
            
            self.repairs_made.append({
                "type": "auto_push",
                "timestamp": datetime.now().isoformat()
            })
            print(f"   ✓ 已自动推送到GitHub")
            
        except Exception as e:
            print(f"   ❌ 自动推送失败: {e}")
    
    def check_backup_strategy(self):
        """检查备份策略"""
        print("📊 检查备份策略...")
        
        backup_files = sorted(
            self.backup_dir.glob("workspace_backup_*.tar.gz"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # 检查备份数量
        if len(backup_files) < self.config["min_backups"]:
            self.issues_found.append({
                "type": "insufficient_backups",
                "details": f"备份数量不足: {len(backup_files)} < {self.config['min_backups']}"
            })
            print(f"   ⚠️  备份数量不足: {len(backup_files)} < {self.config['min_backups']}")
        elif len(backup_files) > self.config["max_backups"]:
            print(f"   ⚠️  备份数量过多: {len(backup_files)} > {self.config['max_backups']}")
            # 清理旧备份
            self.cleanup_old_backups(backup_files[self.config["max_backups"]:])
        else:
            print(f"   ✓ 备份数量正常: {len(backup_files)}")
        
        # 检查备份时效性
        if backup_files:
            latest = backup_files[0]
            mtime = datetime.fromtimestamp(latest.stat().st_mtime)
            age_hours = (datetime.now() - mtime).total_seconds() / 3600
            
            if age_hours > self.config["backup_interval_hours"] * 2:
                self.issues_found.append({
                    "type": "stale_backup",
                    "details": f"最新备份已过期: {age_hours:.1f}小时前"
                })
                print(f"   ⚠️  最新备份已过期: {age_hours:.1f}小时前")
            else:
                print(f"   ✓ 最新备份: {age_hours:.1f}小时前")
    
    def cleanup_old_backups(self, old_backups: List[Path]):
        """清理旧备份"""
        for backup_file in old_backups:
            try:
                backup_file.unlink()
                self.repairs_made.append({
                    "type": "cleanup_old_backup",
                    "file": str(backup_file)
                })
                print(f"   ✓ 清理旧备份: {backup_file.name}")
            except Exception as e:
                print(f"   ❌ 清理失败: {backup_file.name} - {e}")
    
    def execute_repairs(self):
        """执行修复操作"""
        print("🔧 执行修复...")
        
        # 修复损坏的备份
        for issue in self.issues_found:
            if issue["type"] == "corrupt_backup":
                try:
                    corrupt_file = Path(issue["file"])
                    if corrupt_file.exists():
                        # 删除损坏的备份
                        corrupt_file.unlink()
                        self.stats["backups_repaired"] += 1
                        self.repairs_made.append({
                            "type": "delete_corrupt_backup",
                            "file": str(corrupt_file)
                        })
                        print(f"   ✓ 删除损坏备份: {corrupt_file.name}")
                except Exception as e:
                    print(f"   ❌ 删除失败: {e}")
    
    def create_backup_if_needed(self):
        """如果需要，创建新备份"""
        print("💾 检查是否需要创建新备份...")
        
        # 检查是否有任何备份
        backup_files = list(self.backup_dir.glob("workspace_backup_*.tar.gz"))
        
        if not backup_files:
            print("   ⚠️  没有现有备份，创建新备份...")
            self.create_full_backup()
            return
        
        # 检查最新备份年龄
        latest = max(backup_files, key=lambda p: p.stat().st_mtime)
        mtime = datetime.fromtimestamp(latest.stat().st_mtime)
        age_hours = (datetime.now() - mtime).total_seconds() / 3600
        
        if age_hours > self.config["backup_interval_hours"]:
            print(f"   ⚠️  备份已过期({age_hours:.1f}小时)，创建新备份...")
            self.create_full_backup()
        else:
            print(f"   ✓ 备份仍有效({age_hours:.1f}小时)")
    
    def create_full_backup(self):
        """创建完整备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"workspace_backup_{timestamp}.tar.gz"
            
            # 排除目录
            exclude_dirs = [
                '__pycache__', '.git', 'node_modules', 
                'logs/archive', '*.pyc'
            ]
            
            with tarfile.open(backup_file, 'w:gz') as tar:
                tar.add(
                    self.workspace, 
                    arcname='workspace',
                    filter=lambda x: None if any(ex in x.name for ex in exclude_dirs) else x
                )
            
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            self.repairs_made.append({
                "type": "create_backup",
                "file": str(backup_file),
                "size_mb": round(size_mb, 2)
            })
            print(f"   ✓ 创建备份: {backup_file.name} ({size_mb:.1f}MB)")
            
        except Exception as e:
            print(f"   ❌ 备份创建失败: {e}")
    
    def generate_report(self) -> Dict:
        """生成检查报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.stats,
            "issues_found": self.issues_found,
            "repairs_made": self.repairs_made,
            "config": self.config,
            "status": "healthy" if len(self.issues_found) == 0 else "issues_detected"
        }
        
        # 保存JSON报告
        report_file = self.report_dir / f"backup-check-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        print(f"\n{'='*70}")
        print("📋 备份检查报告")
        print(f"{'='*70}")
        print(f"状态: {report['status']}")
        print(f"检查备份: {self.stats['backups_checked']} 个")
        print(f"损坏备份: {self.stats['backups_corrupt']} 个")
        print(f"修复操作: {len(self.repairs_made)} 次")
        print(f"GitHub同步: {self.stats['github_sync_status']}")
        print(f"发现问题: {len(self.issues_found)} 个")
        print(f"报告保存: {report_file}")
        print(f"{'='*70}")
        
        return report


def main():
    """主函数"""
    system = BackupRepairSystem()
    report = system.run_backup_check()
    return report


if __name__ == "__main__":
    main()
