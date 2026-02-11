#!/usr/bin/env python3
"""
多代理并行深度学习测试 v2.0 - 方案2
浏览器任务在主节点，VM执行计算任务
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
    """子代理1: Moltbook热门扫描 (主节点浏览器任务)"""
    log("🤖 Agent-1 [主节点/浏览器] 启动: Moltbook扫描")
    
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
    """子代理2: HackerNews头条扫描 (主节点浏览器任务)"""
    log("🤖 Agent-2 [主节点/浏览器] 启动: HackerNews扫描")
    
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


async def agent_github():
    """子代理3: GitHub Trending扫描 (主节点浏览器任务)"""
    log("🤖 Agent-3 [主节点/浏览器] 启动: GitHub Trending扫描")
    
    try:
        from deep_learning_extractor import DeepLearningExtractor
        extractor = DeepLearningExtractor("scripts/web-extractor/configs/github_trending.json")
        items = await extractor.collect_with_deep_learning(max_deep_extract=2)
        
        high_signal = [i for i in items if i.get('deep_content')]
        log(f"✅ Agent-3 完成: 扫描 {len(items)} 条, 深度提取 {len(high_signal)} 条")
        
        return {'agent': 'github', 'items': items, 'high_signal_count': len(high_signal)}
    except Exception as e:
        log(f"❌ Agent-3 失败: {e}")
        return {'agent': 'github', 'error': str(e)}


async def agent_vm_compute():
    """子代理4: VM计算任务 (数据处理/向量计算)"""
    log("🤖 Agent-4 [VM/计算] 启动: 数据处理任务")
    log("   🔄 正在执行VM复活同步...")
    
    # Step 1: VM复活同步
    result = subprocess.run(
        ["/root/.openclaw/workspace/scripts/vm-resurrection-sync.sh"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode != 0:
        log(f"❌ VM复活失败")
        return {'agent': 'vm_compute', 'error': 'resurrection_failed'}
    
    log("   ✅ VM复活同步完成")
    
    # Step 2: 在VM上执行纯Python计算任务（非浏览器）
    log("   📡 在VM上执行计算任务...")
    
    # 示例：数据处理任务（可以替换为实际的向量计算等）
    vm_script = '''
import json
import os
from datetime import datetime

# 模拟计算密集型任务
result = {
    "task": "data_processing",
    "processed_files": 0,
    "start_time": datetime.now().isoformat()
}

# 统计工作区文件数量
workspace_path = "/root/.openclaw/workspace"
if os.path.exists(workspace_path):
    for root, dirs, files in os.walk(workspace_path):
        result["processed_files"] += len(files)
        if result["processed_files"] > 1000:  # 限制遍历
            break

result["end_time"] = datetime.now().isoformat()
result["status"] = "completed"

print(json.dumps(result))
'''
    
    # 写入临时文件并复制到VM
    with open('/tmp/vm_compute_task.py', 'w') as f:
        f.write(vm_script)
    
    subprocess.run(
        ['scp', '-P', '4444', '-o', 'StrictHostKeyChecking=no',
         '/tmp/vm_compute_task.py', 'root@localhost:/tmp/vm_compute_task.py'],
        check=False, capture_output=True
    )
    
    vm_result = subprocess.run(
        ['ssh', '-p', '4444', '-o', 'StrictHostKeyChecking=no', 'root@localhost',
         'python3 /tmp/vm_compute_task.py'],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if vm_result.returncode == 0:
        try:
            output = json.loads(vm_result.stdout.strip().split('\n')[-1])
            log(f"✅ Agent-4 完成: 处理 {output.get('processed_files', 0)} 个文件")
            return {'agent': 'vm_compute', 'output': output, 'status': 'success'}
        except:
            log(f"✅ Agent-4 完成: {vm_result.stdout[-100:]}")
            return {'agent': 'vm_compute', 'output': vm_result.stdout, 'status': 'success'}
    else:
        log(f"❌ Agent-4 VM执行失败: {vm_result.stderr[:100]}")
        return {'agent': 'vm_compute', 'error': 'vm_execution_failed'}


async def main():
    """主协调器: 并行调度四个子代理"""
    log("=" * 60)
    log("🚀 多代理并行深度学习测试 v2.0 (方案2)")
    log("=" * 60)
    log("")
    log("任务分配:")
    log("  - Agent-1 [主节点/浏览器]: Moltbook热门")
    log("  - Agent-2 [主节点/浏览器]: HackerNews头条")
    log("  - Agent-3 [主节点/浏览器]: GitHub Trending")
    log("  - Agent-4 [VM/计算]:      数据处理")
    log("")
    
    start_time = datetime.now()
    
    # 并行启动四个子代理
    tasks = [
        agent_moltbook(),
        agent_hackernews(),
        agent_github(),
        agent_vm_compute()
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
    log(f"📈 成功率: {success_count}/4")
    log(f"🎯 多代理并行: {'✅ 正常' if success_count >= 3 else '❌ 异常'}")
    log(f"🔄 VM协作(计算): {'✅ 正常' if any('vm_compute' in str(r) and 'success' in str(r) for r in results) else '❌ 异常'}")
    
    # 保存测试报告
    report = {
        'test_time': datetime.now().isoformat(),
        'elapsed_seconds': elapsed,
        'success_count': success_count,
        'results': [str(r) for r in results],
        'mode': '方案2-VM非浏览器任务'
    }
    
    report_file = Path(f"memory/reports/multi-agent-test-v2-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    log(f"")
    log(f"💾 测试报告: {report_file}")
    log("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
