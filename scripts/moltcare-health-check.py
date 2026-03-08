#!/usr/bin/env python3
"""
MoltCare 系统健康检查
每小时检查所有服务状态
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MoltCare-Health - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/moltcare-health.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_service_health():
    """检查所有服务健康状态"""
    checks = {}
    
    # 1. 检查备份目录
    backup_dir = Path("data/moltcare/backups")
    if backup_dir.exists():
        backup_count = sum(1 for _ in backup_dir.rglob("*.tar.gz.enc"))
        checks["backups"] = f"✅ {backup_count} backups"
    else:
        checks["backups"] = "❌ Backup directory missing"
    
    # 2. 检查扫描报告
    scan_dir = Path("data/moltcare/scans")
    if scan_dir.exists():
        scan_count = len(list(scan_dir.glob("*.json")))
        checks["scans"] = f"✅ {scan_count} scan reports"
    else:
        checks["scans"] = "❌ Scan directory missing"
    
    # 3. 检查订阅者
    subs_file = Path("data/moltcare/subscribers.json")
    if subs_file.exists():
        with open(subs_file) as f:
            subs = json.load(f)
        checks["subscribers"] = f"✅ {len(subs)} subscribers"
    else:
        checks["subscribers"] = "⚠️ No subscribers yet"
    
    # 4. 检查日志
    log_files = [
        "logs/moltcare-memory.log",
        "logs/moltcare-payment.log",
        "logs/moltcare-shield.log",
        "logs/moltcare-automation.log"
    ]
    log_status = []
    for log_file in log_files:
        if Path(log_file).exists():
            size = Path(log_file).stat().st_size
            log_status.append(f"{Path(log_file).name}: {size/1024:.1f}KB")
    checks["logs"] = f"✅ {len(log_status)} logs active"
    
    # 5. 检查Cron任务
    import subprocess
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if "moltcare" in result.stdout:
            checks["cron"] = "✅ Cron jobs installed"
        else:
            checks["cron"] = "❌ No MoltCare cron jobs"
    except:
        checks["cron"] = "❌ Cannot check cron"
    
    return checks


def generate_report():
    """生成健康报告"""
    logger.info("🏥 Running health check...")
    
    checks = check_service_health()
    
    # 生成报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "status": "healthy" if all("✅" in v for v in checks.values()) else "issues"
    }
    
    # 保存报告
    report_file = Path("data/moltcare/health-report.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # 输出摘要
    logger.info("Health Check Summary:")
    for check, status in checks.items():
        logger.info(f"  {check}: {status}")
    
    if report["status"] == "healthy":
        logger.info("✅ All systems healthy")
    else:
        logger.warning("⚠️  Some issues detected")
    
    return report


def main():
    generate_report()


if __name__ == "__main__":
    main()
