#!/usr/bin/env python3
"""
日志轮转脚本 - 防止决策引擎日志无限增长
"""

import os
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
LOG_DIR = WORKSPACE / "logs"

# 配置
LOG_FILES = {
    "decision-engine.jsonl": {"max_lines": 10000, "max_size_mb": 10},
    "decision-rejections.jsonl": {"max_lines": 5000, "max_size_mb": 5},
}
ARCHIVE_DIR = DATA_DIR / "archive"
RETENTION_DAYS = 30


def rotate_log_file(filename: str, config: dict):
    """轮转单个日志文件"""
    log_path = DATA_DIR / filename
    
    if not log_path.exists():
        return
    
    # 检查行数
    try:
        with open(log_path, 'r') as f:
            lines = sum(1 for _ in f)
    except:
        return
    
    # 检查大小
    size_mb = log_path.stat().st_size / (1024 * 1024)
    
    need_rotation = lines > config["max_lines"] or size_mb > config["max_size_mb"]
    
    if not need_rotation:
        return
    
    print(f"🔄 轮转 {filename}: {lines}行, {size_mb:.1f}MB")
    
    # 创建归档目录
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成归档文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{filename}.{timestamp}.gz"
    archive_path = ARCHIVE_DIR / archive_name
    
    # 压缩归档
    with open(log_path, 'rb') as f_in:
        with gzip.open(archive_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # 清空原文件
    log_path.write_text('')
    
    print(f"  ✅ 已归档到: {archive_name}")


def cleanup_old_archives():
    """清理过期的归档文件"""
    if not ARCHIVE_DIR.exists():
        return
    
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    deleted = 0
    
    for archive_file in ARCHIVE_DIR.glob("*.gz"):
        mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)
        if mtime < cutoff:
            archive_file.unlink()
            deleted += 1
    
    if deleted > 0:
        print(f"🗑️  清理过期归档: {deleted}个文件")


def main():
    """主入口"""
    print("="*60)
    print("📋 日志轮转任务")
    print("="*60)
    
    for filename, config in LOG_FILES.items():
        rotate_log_file(filename, config)
    
    cleanup_old_archives()
    
    print("✅ 完成")


if __name__ == "__main__":
    main()
