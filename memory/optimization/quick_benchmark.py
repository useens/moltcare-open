#!/usr/bin/env python3
"""
精简性能基准测试 - Quick Performance Benchmark
测试日期: 2026-02-12
"""

import os
import sys
import time
import json
import random
import statistics
from pathlib import Path
from datetime import datetime

# 添加工作空间到路径
sys.path.insert(0, '/root/.openclaw/workspace')

print("="*70)
print("🔬 精简性能基准测试 - Quick Performance Benchmark")
print("="*70)
print(f"测试时间: {datetime.now().isoformat()}")
print(f"主机: {os.uname().nodename}")
print(f"架构: {os.uname().machine}")
print()

results = {
    "timestamp": datetime.now().isoformat(),
    "host": os.uname().nodename,
    "architecture": os.uname().machine,
    "tests": {}
}

# ============== 1. 向量记忆系统性能测试 ==============
print("\n" + "="*70)
print("📊 测试1: 向量记忆系统性能测试")
print("="*70)

vector_results = {
    "retrieval_latency": {},
    "memory_usage": {},
    "concurrent_performance": {}
}

try:
    from core.vector_memory import create_memory_system
    
    print("\n🧠 初始化向量记忆系统...")
    start_init = time.perf_counter()
    memory = create_memory_system('/root/.openclaw/workspace/memory/vector/production')
    init_time = (time.perf_counter() - start_init) * 1000
    
    stats = memory.get_stats() if hasattr(memory, 'get_stats') else {}
    print(f"   初始化时间: {init_time:.2f}ms")
    print(f"   数据库路径: {stats.get('db_path', 'N/A')}")
    print(f"   记忆总数: {stats.get('total_memories', 'N/A')}")
    print(f"   模型: {stats.get('model', 'N/A')}")
    
    vector_results["memory_usage"]["initial"] = stats
    vector_results["memory_usage"]["init_time_ms"] = init_time
    
    # 测试查询集
    test_queries = [
        "用户偏好设置",
        "向量记忆系统架构",
        "自主进化机制",
        "Moltbook学习",
        "代码生成优化",
    ]
    
    # 1.1 检索延迟测试 (20次随机查询 - 减少数量以加快测试)
    print(f"\n🔍 1.1 检索延迟测试 (20次随机查询)...")
    latencies = []
    
    for i in range(20):
        query = random.choice(test_queries)
        start = time.perf_counter()
        try:
            results_list = memory.search(query, top_k=5, search_type="hybrid")
            elapsed = (time.perf_counter() - start) * 1000  # ms
            latencies.append(elapsed)
            print(f"   查询{i+1}: {elapsed:.2f}ms")
        except Exception as e:
            print(f"   查询{i+1}: 失败 - {e}")
            latencies.append(-1)
    
    successful_latencies = [l for l in latencies if l > 0]
    
    if successful_latencies:
        vector_results["retrieval_latency"] = {
            "iterations": 20,
            "successful": len(successful_latencies),
            "failed": len(latencies) - len(successful_latencies),
            "min_ms": min(successful_latencies),
            "max_ms": max(successful_latencies),
            "mean_ms": statistics.mean(successful_latencies),
            "median_ms": statistics.median(successful_latencies),
            "stdev_ms": statistics.stdev(successful_latencies) if len(successful_latencies) > 1 else 0,
        }
        
        print(f"\n   ✅ 成功: {len(successful_latencies)}/20")
        print(f"   ⏱️  平均延迟: {vector_results['retrieval_latency']['mean_ms']:.2f}ms")
        print(f"   ⏱️  中位数延迟: {vector_results['retrieval_latency']['median_ms']:.2f}ms")
    
    memory.close()
    print("\n✅ 向量记忆系统测试完成")
    
except Exception as e:
    print(f"\n❌ 向量记忆系统测试失败: {e}")
    import traceback
    traceback.print_exc()
    vector_results["error"] = str(e)

results["tests"]["vector_memory"] = vector_results

# ============== 2. 文件I/O性能测试 ==============
print("\n" + "="*70)
print("📁 测试2: 文件I/O性能测试")
print("="*70)

file_io_results = {
    "memory_dir": {},
    "github_sync": {}
}

MEMORY_DIR = Path('/root/.openclaw/workspace/memory')

# 2.1 memory/目录读写速度
print("\n📝 2.1 memory/目录读写速度测试...")

try:
    test_file = MEMORY_DIR / ".perf_test_temp"
    test_content = "X" * 1024  # 1KB内容
    
    write_times = []
    read_times = []
    delete_times = []
    
    for i in range(100):
        file_path = test_file.with_suffix(f".tmp{i}")
        
        # 写入测试
        start = time.perf_counter()
        file_path.write_text(test_content)
        write_times.append((time.perf_counter() - start) * 1000)
        
        # 读取测试
        start = time.perf_counter()
        _ = file_path.read_text()
        read_times.append((time.perf_counter() - start) * 1000)
        
        # 删除测试
        start = time.perf_counter()
        file_path.unlink()
        delete_times.append((time.perf_counter() - start) * 1000)
    
    for op, times in [("write", write_times), ("read", read_times), ("delete", delete_times)]:
        file_io_results["memory_dir"][op] = {
            "iterations": len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
        }
        print(f"   {op.upper()}: 平均 {statistics.mean(times):.3f}ms, 中位数 {statistics.median(times):.3f}ms")

except Exception as e:
    print(f"   ❌ 文件I/O测试失败: {e}")
    file_io_results["memory_dir"]["error"] = str(e)

# 2.2 GitHub同步延迟
print("\n🌐 2.2 GitHub同步延迟测试...")

try:
    import subprocess
    
    # 检查git状态
    git_start = time.perf_counter()
    result = subprocess.run(
        ['git', '-C', '/root/.openclaw/workspace', 'status', '--porcelain'],
        capture_output=True,
        text=True,
        timeout=30
    )
    git_status_time = (time.perf_counter() - git_start) * 1000
    
    file_io_results["github_sync"] = {
        "status_time_ms": git_status_time,
        "pending_changes": len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0,
    }
    
    print(f"   Git状态检查: {git_status_time:.2f}ms")
    print(f"   待处理变更: {file_io_results['github_sync']['pending_changes']} 文件")
    
except Exception as e:
    print(f"   ❌ GitHub同步测试失败: {e}")
    file_io_results["github_sync"]["error"] = str(e)

results["tests"]["file_io"] = file_io_results

# ============== 3. 系统资源使用情况 ==============
print("\n" + "="*70)
print("💻 测试3: 系统资源使用情况")
print("="*70)

try:
    import psutil
    
    system_results = {
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_total_mb": psutil.virtual_memory().total / 1024 / 1024,
        "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": {}
    }
    
    # 磁盘使用情况
    for path in ['/root/.openclaw/workspace/memory', '/root/.openclaw/workspace/data']:
        try:
            usage = psutil.disk_usage(path)
            system_results["disk_usage"][path] = {
                "total_mb": usage.total / 1024 / 1024,
                "used_mb": usage.used / 1024 / 1024,
                "free_mb": usage.free / 1024 / 1024,
                "percent": usage.percent,
            }
        except:
            pass
    
    print(f"   CPU核心数: {system_results['cpu_count']}")
    print(f"   CPU使用率: {system_results['cpu_percent']:.1f}%")
    print(f"   内存总量: {system_results['memory_total_mb']:.0f}MB")
    print(f"   内存可用: {system_results['memory_available_mb']:.0f}MB")
    print(f"   内存使用率: {system_results['memory_percent']:.1f}%")
    
    results["tests"]["system_resources"] = system_results
    
except Exception as e:
    print(f"   ❌ 系统资源测试失败: {e}")
    results["tests"]["system_resources"] = {"error": str(e)}

# ============== 保存结果 ==============
print("\n" + "="*70)
print("💾 保存测试结果")
print("="*70)

output_path = Path('/root/.openclaw/workspace/memory/optimization/perf_benchmark_raw.json')
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"✅ 结果已保存: {output_path}")
print(f"   文件大小: {output_path.stat().st_size} bytes")

print("\n" + "="*70)
print("🏁 性能基准测试完成")
print("="*70)
