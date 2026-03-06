#!/usr/bin/env python3
"""
神经中枢 2.0 启动脚本
"""
import asyncio
import sys
import signal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.neural_hub import NeuralHub

async def main():
    print("=" * 60)
    print("🧠 神经中枢 2.0 启动中...")
    print("=" * 60)
    
    hub = NeuralHub()
    
    # 信号处理
    def signal_handler(sig):
        print(f"\n收到信号 {sig}，正在关闭...")
        asyncio.create_task(hub.stop())
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
    
    try:
        await hub.start()
    except Exception as e:
        print(f"启动错误: {e}")
        await hub.stop()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
