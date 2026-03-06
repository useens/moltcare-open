#!/usr/bin/env python3
"""
与10个Nanobot对话演示
"""
import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace')

from core.neural_hub import NeuralHub, TaskPriority

async def chat_with_nanobots():
    print('=' * 70)
    print('🧠 神经中枢 2.0 - 与10个Nanobot对话')
    print('=' * 70)
    
    # 启动神经中枢
    hub = NeuralHub()
    await hub.redis.connect()
    await hub.state.start_monitor()
    await hub.scheduler.start()
    
    print('\n📡 神经中枢已启动 (降级模式)')
    bot_count = len(hub.state.bots)
    print(f'   在线Bot: {bot_count}个')
    print()
    
    # 1. 广播问候
    print('[我] 🎤 广播: 各位小弟，报到！')
    print()
    
    for bot_id, bot in hub.state.bots.items():
        caps = ', '.join(bot.capabilities[:3])
        print(f'[{bot.name}] 到！状态: {bot.state} | 能力: {caps}')
    
    # 2. 分配任务
    print()
    print('[我] 📝 分配今日任务...')
    print()
    
    tasks = [
        ('nanobot-1', '分析Moltbook最新情报', ['research', 'analysis'], 1),
        ('nanobot-4', '扫描系统安全漏洞', ['security', 'audit'], 1),
        ('nanobot-7', '审查昨日代码提交', ['code_review', 'quality'], 2),
        ('nanobot-2', '设计新的架构方案', ['design', 'architecture'], 2),
        ('nanobot-9', '制定下周战略计划', ['strategy', 'planning'], 3),
    ]
    
    task_results = []
    for bot_id, desc, caps, priority_int in tasks:
        task_id = await hub.submit_task(
            desc.replace(' ', '_'),
            {'description': desc, 'assigned_bot': bot_id},
            priority_int,
            caps
        )
        
        # 模拟任务分配
        bot = hub.state.get_bot(bot_id)
        if bot:
            hub.state.update_state(bot_id, 'busy', task_id)
            prio_map = {0: 'CRITICAL', 1: 'HIGH', 2: 'NORMAL', 3: 'LOW', 4: 'BACKGROUND'}
            prio_name = prio_map.get(priority_int, 'NORMAL')
            print(f'[{bot.name}] 收到任务: {desc} (优先级: {prio_name})')
            task_results.append((bot_id, task_id, desc))
    
    # 3. 询问状态
    print()
    print('[我] 📊 查询工作状态...')
    print()
    
    stats = hub.state.get_summary()
    total_bots = stats['total_bots']
    online = stats['online']
    available = stats['available']
    busy = stats['busy']
    print(f'   总Bot数: {total_bots}')
    print(f'   在线: {online} | 空闲: {available} | 忙碌: {busy}')
    print()
    
    for bot_id, bot in hub.state.bots.items():
        status = '🟢 空闲' if bot.state == 'idle' else '🔴 忙碌'
        if bot.current_task:
            task_short = bot.current_task[:15]
            task_info = f' (处理: {task_short}...)'
        else:
            task_info = ''
        print(f'   {status} {bot.name:12s} - {task_info}')
    
    # 4. 模拟任务完成
    print()
    print('[我] ⏱️ 等待任务执行...')
    await asyncio.sleep(2)
    
    print()
    print('[我] 📋 任务汇报')
    print()
    
    for bot_id, task_id, desc in task_results:
        bot = hub.state.get_bot(bot_id)
        # 模拟完成
        hub.scheduler.complete_task(task_id, {'status': 'completed', 'result': 'success'})
        hub.state.update_state(bot_id, 'idle')
        print(f'✅ [{bot.name}] 完成: {desc}')
    
    # 5. 总结
    print()
    print('[我] 🎯 今日总结')
    print()
    
    final_stats = await hub.get_stats()
    completed = final_stats['tasks']['completed']
    print(f'   完成任务: {completed}个')
    print(f'   系统状态: 全部正常')
    print()
    print('   nanobot-1: 情报分析完成，发现3条高价值信息')
    print('   nanobot-4: 安全扫描完成，无漏洞')
    print('   nanobot-7: 代码审查完成，发现2个问题')
    print('   nanobot-2: 架构方案已提交')
    print('   nanobot-9: 战略计划制定中...')
    
    # 结束
    print()
    print('[我] 👋 大家辛苦了，继续待命！')
    print()
    
    for bot_id, bot in hub.state.bots.items():
        if bot.state == 'idle':
            print(f'[{bot.name}] 收到，随时待命！')
    
    await hub.stop()
    
    print()
    print('=' * 70)
    print('✅ 对话结束')
    print('=' * 70)

if __name__ == '__main__':
    asyncio.run(chat_with_nanobots())
