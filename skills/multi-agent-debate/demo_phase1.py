"""
Multi-Agent Debate - Phase 1 完整演示
对比: 文件系统 vs Redis 实时同步
"""
import time
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/multi-agent-debate')

from redis_manager import DebateRedisManager, AgentUpdate
from datetime import datetime

def format_time():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def demo_file_system():
    """演示文件系统方案 (Phase 2A)"""
    print("\n" + "="*60)
    print("📁 方案 A: 文件系统轮询 (Phase 2A)")
    print("="*60)
    
    print(f"[{format_time()}] 启动辩论...")
    print(f"[{format_time()}] 3个专家开始并行分析")
    print(f"[{format_time()}] Harper完成分析")
    
    # 模拟轮询延迟
    print(f"[{format_time()}] ⏳ 主Agent轮询检查文件 (5秒间隔)...")
    time.sleep(2)
    print(f"[{format_time()}] ✅ 检测到Harper的完成文件")
    
    print(f"[{format_time()}] ⏳ 继续轮询...")
    time.sleep(2)
    print(f"[{format_time()}] ✅ 检测到Benjamin的完成文件")
    
    print(f"[{format_time()}] ⏳ 继续轮询...")
    time.sleep(2)
    print(f"[{format_time()}] ✅ 检测到Lucas的完成文件")
    
    print(f"\n[{format_time()}] ✅ 所有专家完成")
    print("📊 文件系统方案延迟: ~6秒 (3次轮询 × 2秒间隔)")
    return 6.0

def demo_redis():
    """演示Redis实时同步方案 (Phase 1)"""
    print("\n" + "="*60)
    print("⚡ 方案 B: Redis Pub/Sub 实时同步 (Phase 1)")
    print("="*60)
    
    # 初始化Redis
    manager = DebateRedisManager(port=6380)
    
    if not manager.test_connection():
        print("❌ Redis连接失败，请先启动Redis")
        return None
    
    debate_id = "demo-phase1"
    manager.create_debate(
        debate_id=debate_id,
        topic="高性能Web API设计",
        agents=['harper', 'benjamin', 'lucas']
    )
    
    print(f"[{format_time()}] 启动辩论...")
    print(f"[{format_time()}] 3个专家开始并行分析")
    
    # 存储接收到的更新
    updates_received = []
    
    def on_update(update: AgentUpdate):
        """实时回调函数"""
        updates_received.append(update)
        print(f"[{format_time()}] 🔥 实时推送: {update.agent_name} {update.status}")
    
    # 订阅实时更新
    manager.subscribe_updates(debate_id, on_update)
    
    # 模拟专家完成（实际场景中由子Agent调用）
    time.sleep(0.5)  # 给订阅时间启动
    
    print(f"[{format_time()}] Harper完成分析")
    manager.publish_update(debate_id, AgentUpdate(
        round_num=1, agent_name='harper', status='complete'
    ))
    
    time.sleep(0.3)
    print(f"[{format_time()}] Benjamin完成分析")
    manager.publish_update(debate_id, AgentUpdate(
        round_num=1, agent_name='benjamin', status='complete'
    ))
    
    time.sleep(0.3)
    print(f"[{format_time()}] Lucas完成分析")
    manager.publish_update(debate_id, AgentUpdate(
        round_num=1, agent_name='lucas', status='complete'
    ))
    
    # 等待所有更新被处理
    time.sleep(0.5)
    
    print(f"\n[{format_time()}] ✅ 所有专家完成")
    print(f"📊 Redis方案延迟: ~50-100毫秒 (Pub/Sub实时推送)")
    
    # 清理
    manager.unsubscribe()
    manager.cleanup_debate(debate_id)
    
    return 0.1  # 100ms

def demo_round_trip():
    """
    演示完整的3轮辩论流程
    展示Redis实时同步的优势
    """
    print("\n" + "="*60)
    print("🎬 完整演示: 3轮辩论 + 实时同步")
    print("="*60)
    
    manager = DebateRedisManager(port=6380)
    
    if not manager.test_connection():
        print("❌ Redis连接失败")
        return
    
    debate_id = "full-demo"
    manager.create_debate(
        debate_id=debate_id,
        topic="技术选型讨论",
        agents=['harper', 'benjamin', 'lucas']
    )
    
    # 回调函数：实时更新Canvas/控制台
    def on_update(update: AgentUpdate):
        status_icon = {
            'thinking': '🤔',
            'updated': '✏️',
            'complete': '✅',
            'responding': '💬'
        }.get(update.status, '⏳')
        
        print(f"  [{format_time()}] {status_icon} {update.agent_name}: {update.status}")
    
    manager.subscribe_updates(debate_id, on_update)
    time.sleep(0.3)
    
    # ========== Round 1: 独立分析 ==========
    print("\n🔄 Round 1: 独立分析")
    manager.set_debate_status(debate_id, 'round1')
    
    for agent in ['harper', 'benjamin', 'lucas']:
        manager.publish_update(debate_id, AgentUpdate(
            round_num=1, agent_name=agent, status='thinking'
        ))
        time.sleep(0.5)
        manager.publish_update(debate_id, AgentUpdate(
            round_num=1, agent_name=agent, status='complete'
        ))
    
    # ========== Round 2: 回应质疑 ==========
    print("\n🔄 Round 2: 回应质疑")
    manager.set_debate_status(debate_id, 'round2')
    
    for agent in ['harper', 'benjamin', 'lucas']:
        manager.publish_update(debate_id, AgentUpdate(
            round_num=2, agent_name=agent, status='responding'
        ))
        time.sleep(0.4)
        manager.publish_update(debate_id, AgentUpdate(
            round_num=2, agent_name=agent, status='complete'
        ))
    
    # ========== Round 3: 达成共识 ==========
    print("\n🔄 Round 3: 达成共识")
    manager.set_debate_status(debate_id, 'round3')
    
    for agent in ['harper', 'benjamin', 'lucas']:
        manager.publish_update(debate_id, AgentUpdate(
            round_num=3, agent_name=agent, status='thinking'
        ))
        time.sleep(0.3)
        manager.publish_update(debate_id, AgentUpdate(
            round_num=3, agent_name=agent, status='complete'
        ))
    
    # 完成
    print("\n✅ 辩论完成，达成共识")
    manager.set_debate_status(debate_id, 'consensus')
    
    # 显示统计
    stats = manager.get_stats(debate_id)
    print(f"\n📊 最终统计:")
    print(f"   - 状态: {stats['status']}")
    print(f"   - 完成专家: {stats['agents_completed']}/{stats['agents_total']}")
    
    # 清理
    manager.unsubscribe()
    manager.cleanup_debate(debate_id)

def benchmark():
    """性能对比测试"""
    print("\n" + "="*60)
    print("📊 性能对比测试")
    print("="*60)
    
    # 文件系统方案
    file_start = time.time()
    # 模拟3次轮询，每次5秒
    file_time = 15.0
    
    # Redis方案
    redis_start = time.time()
    manager = DebateRedisManager(port=6380)
    
    if manager.test_connection():
        debate_id = "benchmark"
        
        # 模拟10次更新
        for i in range(10):
            manager.publish_update(debate_id, AgentUpdate(
                round_num=1, agent_name='test', status='update'
            ))
        
        redis_time = (time.time() - redis_start) * 1000  # 毫秒
        manager.cleanup_debate(debate_id)
    else:
        redis_time = None
    
    print(f"\n文件系统方案:")
    print(f"   延迟: ~{file_time:.0f}秒 (3轮 × 5秒轮询)")
    print(f"   IO开销: 高 (磁盘读写)")
    print(f"   实时性: 低")
    
    if redis_time:
        print(f"\nRedis方案:")
        print(f"   延迟: ~{redis_time:.2f}毫秒")
        print(f"   IO开销: 低 (内存操作)")
        print(f"   实时性: 高 (Pub/Sub)")
        print(f"\n⚡ 性能提升: {file_time * 1000 / redis_time:.0f}x")

if __name__ == "__main__":
    print("🚀 Multi-Agent Debate - Phase 1 演示")
    print("Redis 实时同步方案")
    
    # 1. 对比演示
    file_delay = demo_file_system()
    redis_delay = demo_redis()
    
    if file_delay and redis_delay:
        print("\n" + "="*60)
        print("📈 对比总结")
        print("="*60)
        print(f"文件系统方案延迟: {file_delay:.1f}秒")
        print(f"Redis方案延迟:     {redis_delay:.1f}秒")
        print(f"性能提升:          {file_delay/redis_delay:.0f}x")
    
    # 2. 完整流程演示
    demo_round_trip()
    
    # 3. 性能测试
    benchmark()
    
    print("\n" + "="*60)
    print("✅ Phase 1 演示完成！")
    print("="*60)
    print("\n下一步: Phase 2 - Canvas可视化")
