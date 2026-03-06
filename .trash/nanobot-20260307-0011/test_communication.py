#!/usr/bin/env python3
"""
对比测试: 文件队列 vs Redis Pub/Sub
测试两种通信方式的延迟和可靠性
"""
import asyncio
import json
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace')

from core.neural_hub.redis_client import RedisClient

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")

def send_via_file(agent_id: str, message: str) -> float:
    """通过文件队列发送"""
    task = {
        "type": "ping",
        "agent_id": agent_id,
        "data": {"message": message, "ts": time.time()},
        "timestamp": datetime.now().isoformat()
    }
    
    task_file = HUB_DIR / "tasks.jsonl"
    start = time.time()
    
    with open(task_file, "a") as f:
        f.write(json.dumps(task) + "\n")
    
    return time.time() - start

async def send_via_redis(redis: RedisClient, agent_id: str, message: str) -> float:
    """通过Redis发送"""
    start = time.time()
    
    await redis.send_command(agent_id, "ping", {
        "message": message,
        "ts": time.time()
    })
    
    return time.time() - start

async def test_file_queue():
    """测试文件队列"""
    print("[测试1] 📁 文件队列通信测试")
    print("-" * 50)
    
    # 清空任务队列
    task_file = HUB_DIR / "tasks.jsonl"
    if task_file.exists():
        task_file.write_text("")
    
    latencies = []
    
    for i in range(5):
        agent_id = f"nanobot-{i+1}"
        latency = send_via_file(agent_id, f"测试消息{i+1}")
        latencies.append(latency * 1000)  # 转为ms
        print(f"  发送给 {agent_id}: {latency*1000:.2f}ms")
        time.sleep(0.1)
    
    avg_latency = sum(latencies) / len(latencies)
    print(f"\n  📊 平均延迟: {avg_latency:.2f}ms")
    print(f"  📊 写入次数: 5次")
    print()
    
    return avg_latency

async def test_redis():
    """测试Redis"""
    print("[测试2] 🔴 Redis Pub/Sub通信测试")
    print("-" * 50)
    
    redis = RedisClient("redis://localhost:6380")
    
    try:
        await redis.connect()
        print("  ✅ Redis连接成功")
    except Exception as e:
        print(f"  ❌ Redis连接失败: {e}")
        return None
    
    latencies = []
    
    for i in range(5):
        agent_id = f"nanobot-{i+1}"
        latency = await send_via_redis(redis, agent_id, f"测试消息{i+1}")
        latencies.append(latency * 1000)  # 转为ms
        print(f"  发送给 {agent_id}: {latency*1000:.2f}ms")
        await asyncio.sleep(0.1)
    
    await redis.disconnect()
    
    avg_latency = sum(latencies) / len(latencies)
    print(f"\n  📊 平均延迟: {avg_latency:.2f}ms")
    print(f"  📊 网络往返: 5次")
    print()
    
    return avg_latency

def test_file_read():
    """测试文件读取性能"""
    print("[测试3] 📖 文件队列读取性能")
    print("-" * 50)
    
    task_file = HUB_DIR / "tasks.jsonl"
    
    if not task_file.exists():
        print("  无任务文件")
        return None
    
    start = time.time()
    
    with open(task_file) as f:
        lines = f.readlines()
    
    elapsed = time.time() - start
    
    print(f"  读取 {len(lines)} 条记录: {elapsed*1000:.2f}ms")
    print(f"  单条平均: {elapsed*1000/max(len(lines),1):.2f}ms")
    print()
    
    return elapsed * 1000

async def main():
    print("=" * 70)
    print("🧪 通信方式对比测试: 文件队列 vs Redis Pub/Sub")
    print("=" * 70)
    print()
    
    # 测试1: 文件队列
    file_latency = await test_file_queue()
    
    # 测试2: Redis
    redis_latency = await test_redis()
    
    # 测试3: 文件读取
    file_read_time = test_file_read()
    
    # 总结
    print("=" * 70)
    print("📊 测试结果总结")
    print("=" * 70)
    print()
    
    print("| 指标 | 文件队列 | Redis Pub/Sub |")
    print("|------|----------|---------------|")
    
    if file_latency:
        print(f"| 发送延迟 | {file_latency:.2f}ms | - |")
    
    if redis_latency:
        print(f"| 发送延迟 | - | {redis_latency:.2f}ms |")
    
    if file_read_time:
        print(f"| 读取延迟 | {file_read_time:.2f}ms | ~0ms (内存) |")
    
    print()
    
    # 推荐
    print("💡 推荐:")
    
    if redis_latency and file_latency:
        if redis_latency < file_latency:
            speedup = file_latency / redis_latency
            print(f"  Redis更快，提速 {speedup:.1f}x")
            print("  适合: 实时性要求高的场景")
        else:
            print("  文件队列简单可靠")
            print("  适合: 稳定性优先的场景")
    
    print()
    print("  文件队列优点:")
    print("    ✅ 无网络依赖，最稳定")
    print("    ✅ 可持久化，断点续传")
    print("    ✅ 调试方便，直接看文件")
    
    print()
    print("  Redis优点:")
    print("    ✅ 延迟更低 (~10ms)")
    print("    ✅ 支持实时广播")
    print("    ✅ 可跨机器部署")

if __name__ == "__main__":
    asyncio.run(main())
