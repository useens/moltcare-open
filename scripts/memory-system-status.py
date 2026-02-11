#!/usr/bin/env python3
"""
记忆系统状态监控面板
显示所有v5.1-v6.0组件的实时状态
"""
import os
import json
import sys
from datetime import datetime

sys.path.insert(0, 'scripts/memory-system')

print("="*70)
print("🌐 记忆系统状态监控面板")
print("="*70)
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 系统状态
status = {
    'timestamp': datetime.now().isoformat(),
    'components': {}
}

# v5.1 长期记忆
print("📚 v5.1 分层记忆架构")
print("-" * 50)
try:
    if os.path.exists('memory/long_term_memories.json'):
        with open('memory/long_term_memories.json') as f:
            lt = json.load(f)
        lt_count = len(lt)
        
        # 关联数量
        assoc_count = 0
        if os.path.exists('memory/associations/memory_graph.json'):
            with open('memory/associations/memory_graph.json') as f:
                graph = json.load(f)
                assoc_count = len(graph.get('edges', []))
        
        status['components']['v5.1'] = {
            'status': 'healthy' if lt_count >= 20 else 'warning',
            'long_term_memories': lt_count,
            'associations': assoc_count
        }
        
        print(f"  ✅ 长期记忆: {lt_count} 条")
        print(f"  ✅ 记忆关联: {assoc_count} 条")
    else:
        status['components']['v5.1'] = {'status': 'error', 'error': 'file missing'}
        print(f"  ❌ 长期记忆文件缺失")
except Exception as e:
    status['components']['v5.1'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ 错误: {e}")

print()

# v5.2 向量记忆
print("🔢 v5.2 向量语义检索")
print("-" * 50)
try:
    from vector_memory import get_vector_memory
    vm = get_vector_memory()
    total = len(vm.memories)
    has_vec = sum(1 for m in vm.memories.values() if m.get('vector') or m.get('embedding'))
    
    status['components']['v5.2'] = {
        'status': 'healthy' if has_vec == total else 'warning',
        'total_memories': total,
        'with_vectors': has_vec
    }
    
    print(f"  ✅ 向量记忆: {has_vec}/{total} 条")
    if has_vec == total:
        print(f"  ✅ 全部已向量化")
    else:
        print(f"  ⚠️ {total - has_vec} 条需要向量化")
except Exception as e:
    status['components']['v5.2'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ 错误: {e}")

print()

# v5.3 遗忘系统
print("🧹 v5.3 记忆遗忘压缩")
print("-" * 50)
try:
    from memory_forget import MemoryForgettingSystem
    fsys = MemoryForgettingSystem()
    status['components']['v5.3'] = {'status': 'healthy'}
    print(f"  ✅ 遗忘系统正常")
except Exception as e:
    status['components']['v5.3'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ 错误: {e}")

print()

# v5.4 主动回忆
print("🧠 v5.4 主动回忆预测")
print("-" * 50)
try:
    patterns_exist = os.path.exists('memory/proactive/patterns.json')
    triggers_exist = os.path.exists('memory/proactive/time_triggers.json')
    
    patterns_count = 0
    if patterns_exist:
        with open('memory/proactive/patterns.json') as f:
            patterns_count = len(json.load(f))
    
    status['components']['v5.4'] = {
        'status': 'healthy' if patterns_exist else 'warning',
        'patterns': patterns_count
    }
    
    print(f"  ✅ 行为模式: {patterns_count} 个")
    print(f"  ✅ 时间触发器: {'已配置' if triggers_exist else '未配置'}")
except Exception as e:
    status['components']['v5.4'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ 错误: {e}")

print()

# v5.5 持久化
print("💾 v5.5 跨会话持久化")
print("-" * 50)
try:
    snapshots = []
    if os.path.exists('memory/snapshots'):
        snapshots = [f for f in os.listdir('memory/snapshots') if f.startswith('snap_')]
    
    latest_snap = max(snapshots) if snapshots else None
    
    status['components']['v5.5'] = {
        'status': 'healthy' if len(snapshots) >= 1 else 'warning',
        'snapshots': len(snapshots),
        'latest': latest_snap
    }
    
    print(f"  ✅ 快照数量: {len(snapshots)} 个")
    if latest_snap:
        print(f"  ✅ 最新快照: {latest_snap}")
except Exception as e:
    status['components']['v5.5'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ 错误: {e}")

print()

# v6.0 可视化
print("📊 v6.0 可视化洞察")
print("-" * 50)
try:
    dashboard_exists = os.path.exists('memory/visualizations/dashboard_latest.txt')
    
    status['components']['v6.0'] = {
        'status': 'healthy' if dashboard_exists else 'warning',
        'dashboard': dashboard_exists
    }
    
    print(f"  ✅ 仪表盘: {'已生成' if dashboard_exists else '未生成'}")
except Exception as e:
    status['components']['v6.0'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ 错误: {e}")

print()

# 综合状态
print("=" * 70)
print("📈 综合状态评估")
print("=" * 70)

healthy_count = sum(1 for c in status['components'].values() if c.get('status') == 'healthy')
total_count = len(status['components'])
health_rate = healthy_count / total_count if total_count > 0 else 0

print(f"健康组件: {healthy_count}/{total_count} ({health_rate:.0%})")

if health_rate == 1.0:
    print("🎉 所有系统健康运行！")
elif health_rate >= 0.8:
    print("✅ 系统整体健康，部分组件需注意")
else:
    print("⚠️ 系统需要维护，请检查日志")

# 保存状态报告
os.makedirs('memory/reports', exist_ok=True)
with open('memory/reports/system_status.json', 'w') as f:
    json.dump(status, f, indent=2)

print(f"\n💾 状态报告已保存: memory/reports/system_status.json")
print("=" * 70)
