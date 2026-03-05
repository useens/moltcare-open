"""
Polymarket 定时任务 - 检查已结束市场
由cron每小时调用
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from polymarket_monitor import PolymarketMonitor, PolymarketCronJob
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    monitor = PolymarketMonitor()
    cron = PolymarketCronJob(monitor)
    
    logger.info("执行结束市场检查...")
    cron.run_resolution_check()
    logger.info("检查完成")


if __name__ == "__main__":
    main()
