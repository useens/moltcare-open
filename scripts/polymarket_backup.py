#!/usr/bin/env python3
"""
Polymarket 数据库备份脚本
每天自动备份SQLite数据库
"""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DB_PATH = WORKSPACE / "polymarket_monitor.db"
BACKUP_DIR = WORKSPACE / "backups" / "polymarket"


def backup_database():
    """备份数据库"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"polymarket_monitor_{timestamp}.db"
    
    try:
        # 使用SQLite的backup API确保一致性
        source = sqlite3.connect(DB_PATH)
        backup = sqlite3.connect(backup_file)
        source.backup(backup)
        backup.close()
        source.close()
        
        print(f"✅ 数据库已备份: {backup_file}")
        
        # 清理旧备份（保留最近7天）
        cleanup_old_backups()
        
        return True
        
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False


def cleanup_old_backups():
    """清理7天前的备份"""
    cutoff = datetime.now() - timedelta(days=7)
    
    for backup_file in BACKUP_DIR.glob("polymarket_monitor_*.db"):
        try:
            # 从文件名提取日期
            date_str = backup_file.stem.split('_')[2]
            file_date = datetime.strptime(date_str, "%Y%m%d")
            
            if file_date < cutoff:
                backup_file.unlink()
                print(f"🗑️  删除旧备份: {backup_file.name}")
        except:
            pass


def verify_backup():
    """验证备份完整性"""
    if not DB_PATH.exists():
        print("❌ 数据库文件不存在")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表完整性
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == "ok":
            print("✅ 数据库完整性检查通过")
            return True
        else:
            print(f"⚠️ 数据库完整性问题: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def main():
    print("="*60)
    print("📦 Polymarket 数据库备份")
    print("="*60)
    
    if not DB_PATH.exists():
        print(f"❌ 数据库不存在: {DB_PATH}")
        return 1
    
    # 先验证
    if not verify_backup():
        print("⚠️ 数据库完整性检查失败，但仍尝试备份...")
    
    # 执行备份
    if backup_database():
        print("\n✅ 备份完成")
        return 0
    else:
        print("\n❌ 备份失败")
        return 1


if __name__ == "__main__":
    exit(main())
