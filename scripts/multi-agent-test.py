#!/usr/bin/env python3
"""
多代理并行深度学习测试 v1.0
测试场景：三平台情报并行收集 + VM协作
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


async def agent_moltbook():
    """子代理1: Moltbook热门扫描 (本地)"""
    log("🤖 Agent-1 [本地] 启动: Moltbook扫描")
    
    try:
        from deep_learning_extractor import DeepLearningExtractor
        extractor = DeepLearningExtractor("scripts/web-extractor/configs/moltbook.json")
        items = await extractor.collect_with_deep_learning(
            url="https://www.moltbook.com/?sort=hot",
            max_deep_extract=2
        )
        
        high_signal = [i for i in items if i.get('deep_content')]
        log(f"✅ Agent-1 完成: 扫描 {len(items)} 条, 深度提取 {len(high_signal)} 条")
        
        return {'agent': 'moltbook', 'items': items, 'high_signal_count': len(high_signal)}
    except Exception as e:
        log(f"❌ Agent-1 失败: {e}")
        return {'agent': 'moltbook', 'error': str(e)}


async def agent_hackernews():
    """子代理2: HackerNews头条扫描 (本地)"""
    log("🤖 Agent-2 [本地] 启动: HackerNews扫描")
    
    try:
        from deep_learning_extractor import DeepLearningExtractor
        extractor = DeepLearningExtractor("scripts/web-extractor/configs/hackernews.json")
        items = await extractor.collect_with_deep_learning(max_deep_extract=2)
        
        high_signal = [i for i in items if i.get('deep_content')]
        log(f"✅ Agent-2 完成: 扫描 {len(items)} 条, 深度提取 {len(high_signal)} 条")
        
        return {'agent': 'hackernews', 'items': items, 'high_signal_count': len(high_signal)}
    except Exception as e:
        log(f"❌ Agent-2 失败: {e}")
        return {'agent': 'hackernews', 'error': str(e)}


async def agent_github_vm():
    """子代理3: GitHub Trending扫描 (VM协作)"""
    log("🤖 Agent-3 [VM] 启动: GitHub Trending扫描")
    log("   🔄 正在执行VM复活同步...")
    
    # Step 1: VM复活同步
    result = subprocess.run(
        ["/root/.openclaw/workspace/scripts/vm-resurrection-sync.sh"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode != 0:
        log(f"❌ VM复活失败: {result.stderr[:200]}")
        return {'agent': 'github_vm', 'error': 'resurrection_failed'}
    
    log("   ✅ VM复活同步完成")
    
    # Step 2: 在VM上执行GitHub扫描 (修复版)
    log("   📡 在VM上启动GitHub提取...")
    
    # 创建Python脚本文件然后通过scp传输执行
    vm_script = '''import sys
sys.path.insert(0, 'scripts/web-extractor')
from deep_learning_extractor import DeepLearningExtractor
import asyncio
import json

async def main():
    try:
        extractor = DeepLearningExtractor('scripts/web-extractor/configs/github_trending.json')
        items = await extractor.collect_with_deep_learning(max_deep_extract=2)
        high_signal = [i for i in items if i.get('deep_content')]
        result = {'scanned': len(items), 'deep': len(high_signal), 'status': 'ok'}
        print(json.dumps(result))
        return items
    except Exception as e:
        print(json.dumps({'error': str(e), 'status': 'failed'}))
        return []

asyncio.run(main())
'''
    
    # 写入临时文件
    with open('/tmp/vm_github_task.py', 'w') as f:
        f.write(vm_script)
    
    # 复制到VM
    subprocess.run(['scp', '-P', '4444', '-o', 'StrictHostKeyChecking=no', 
                   '/tmp/vm_github_task.py', 'root@localhost:/tmp/vm_github_task.py'],
                  check=False, capture_output=True)
    
    vm_result = subprocess.run(
        ['ssh', '-p', '4444', '-o', 'StrictHostKeyChecking=no', 'root@localhost',
         'cd ~/.openclaw/workspace && python3 /tmp/vm_github_task.py'],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if vm_result.returncode == 0:
        output = vm_result.stdout
        log(f"✅ Agent-3 完成: {output[-200:]}")  # 显示最后200字符
        return {'agent': 'github_vm', 'output': output, 'status': 'success'}
    else:
        log(f"❌ Agent-3 VM执行失败: {vm_result.stderr[:200]}")
        return {'agent': 'github_vm', 'error': 'vm_execution_failed'}


async def main():
    """主协调器: 并行调度三个子代理"""
    log("=" * 60)
    log("🚀 多代理并行深度学习测试 v1.0")
    log("=" * 60)
    log("")
    log("任务分配:")
    log("  - Agent-1 [本地]: Moltbook热门")
    log("  - Agent-2 [本地]: HackerNews头条")
    log("  - Agent-3 [VM]:   GitHub Trending (需复活同步)")
    log("")
    
    start_time = datetime.now()
    
    # 并行启动三个子代理
    tasks = [
        agent_moltbook(),
        agent_hackernews(),
        agent_github_vm()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # 汇总结果
    log("")
    log("=" * 60)
    log("📊 测试结果汇总")
    log("=" * 60)
    
    success_count = 0
    for result in results:
        if isinstance(result, Exception):
            log(f"❌ 异常: {result}")
        elif 'error' in result:
            log(f"❌ {result['agent']}: {result['error']}")
        else:
            log(f"✅ {result['agent']}: 成功")
            success_count += 1
    
    log("")
    log(f"⏱️  总耗时: {elapsed:.1f}秒")
    log(f"📈 成功率: {success_count}/3")
    log(f"🎯 多代理并行: {'✅ 正常' if success_count >= 2 else '❌ 异常'}")
    log(f"🔄 VM协作: {'✅ 正常' if any('github_vm' in str(r) and 'success' in str(r) for r in results) else '❌ 异常'}")
    
    # 保存测试报告
    report = {
        'test_time': datetime.now().isoformat(),
        'elapsed_seconds': elapsed,
        'success_count': success_count,
        'results': [str(r) for r in results]
    }
    
    report_file = Path("memory/reports/multi-agent-test-$(date +%Y%m%d-%H%M%S).json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    log(f"")
    log(f"💾 测试报告: {report_file}")
    log("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
