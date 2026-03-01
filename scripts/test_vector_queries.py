#!/usr/bin/env python3
"""
向量数据库查询测试脚本
执行5个不同查询，记录查询时间和结果相关性
"""

import sys
import time
sys.path.insert(0, '/root/.openclaw/workspace')

from core.vector_memory import create_memory_system

DB_PATH = '/root/.openclaw/workspace/memory/vector/production'

# 5个不同类型的测试查询
test_queries = [
    {
        "query": "用户偏好什么回复风格？",
        "expected_type": "preference",
        "description": "用户偏好查询"
    },
    {
        "query": "向量记忆系统使用什么技术？",
        "expected_type": "architecture",
        "description": "技术架构查询"
    },
    {
        "query": "Moltbook账号出了什么问题？",
        "expected_type": "event",
        "description": "事件记录查询"
    },
    {
        "query": "自主进化系统如何运行？",
        "expected_type": "schedule",
        "description": "系统调度查询"
    },
    {
        "query": "记忆系统的设计原则是什么？",
        "expected_type": "design",
        "description": "设计原则查询"
    }
]

def main():
    print("="*70)
    print("🔍 向量数据库查询测试")
    print("="*70)
    
    # 初始化系统
    print("\n🧠 初始化向量记忆系统...")
    try:
        memory = create_memory_system(DB_PATH)
        print("   ✅ 初始化成功")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        return False
    
    # 执行测试查询
    print("\n📋 执行测试查询...")
    results_summary = []
    
    for i, test in enumerate(test_queries, 1):
        query = test["query"]
        desc = test["description"]
        
        print(f"\n{i}. 【{desc}】")
        print(f"   查询: \"{query}\"")
        
        # 记录查询时间
        start_time = time.time()
        try:
            results = memory.search(query, top_k=3, search_type="hybrid")
            elapsed = time.time() - start_time
            
            print(f"   ⏱️  查询时间: {elapsed*1000:.2f}ms")
            
            if results:
                print(f"   📄 找到 {len(results)} 个结果:")
                for j, r in enumerate(results, 1):
                    content = r.content if hasattr(r, 'content') else str(r)
                    score = r.score if hasattr(r, 'score') else 'N/A'
                    # 截取前80个字符
                    content_preview = content[:80].replace('\n', ' ')
                    print(f"      {j}. [{score:.3f}] {content_preview}...")
                
                results_summary.append({
                    'query': query,
                    'success': True,
                    'time_ms': elapsed * 1000,
                    'results_count': len(results)
                })
            else:
                print(f"   ⚠️  未找到结果")
                results_summary.append({
                    'query': query,
                    'success': False,
                    'time_ms': elapsed * 1000,
                    'results_count': 0
                })
        
        except Exception as e:
            print(f"   ❌ 查询错误: {e}")
            results_summary.append({
                'query': query,
                'success': False,
                'time_ms': 0,
                'results_count': 0,
                'error': str(e)
            })
    
    # 关闭连接
    memory.close()
    
    # 输出汇总
    print("\n" + "="*70)
    print("📊 测试汇总")
    print("="*70)
    
    total_time = sum(r['time_ms'] for r in results_summary)
    avg_time = total_time / len(results_summary) if results_summary else 0
    success_count = sum(1 for r in results_summary if r.get('success'))
    
    print(f"  总查询数: {len(results_summary)}")
    print(f"  成功查询: {success_count}")
    print(f"  失败查询: {len(results_summary) - success_count}")
    print(f"  总耗时: {total_time:.2f}ms")
    print(f"  平均耗时: {avg_time:.2f}ms")
    
    print("\n  各查询详细结果:")
    for r in results_summary:
        status = "✅" if r.get('success') else "❌"
        print(f"    {status} \"{r['query'][:30]}...\" - {r['time_ms']:.2f}ms ({r['results_count']} 结果)")
    
    print("="*70)
    
    return success_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
