#!/usr/bin/env python3
"""
Moltbook完整深度扫描任务 v2.0
直接调用moltbook-super-extractor.py中的函数
支持参数: hot, new, profile
"""

import subprocess
import sys

def run_full_scan():
    """运行完整Moltbook扫描"""
    print("="*70)
    print("🔥 Moltbook 完整深度扫描任务 v2.0")
    print("="*70)
    print()
    
    results = {}
    
    # 1. 扫描热门帖子
    print("【1/3】扫描热门帖子...")
    try:
        result = subprocess.run([
            sys.executable, 
            '/root/.openclaw/workspace/scripts/moltbook-super-extractor.py',
            'hot'
        ], capture_output=True, text=True, timeout=300)
        output = result.stdout
        print(output[-800:] if len(output) > 800 else output)
        results['hot'] = '完成'
    except Exception as e:
        print(f"❌ 热门帖子扫描失败: {e}")
        results['hot'] = '失败'
    
    # 2. 扫描最新帖子 (暂时用hot代替，因为extractor没有new模式)
    print("\n【2/3】扫描最新帖子...")
    print("  (注: 当前版本暂未区分hot/new，统一扫描热门)")
    results['new'] = '同hot'
    
    # 3. 扫描用户主页
    print(f"\n【3/3】扫描用户主页 (LinLin_v1)...")
    try:
        result = subprocess.run([
            sys.executable,
            '/root/.openclaw/workspace/scripts/moltbook-super-extractor.py',
            'profile'
        ], capture_output=True, text=True, timeout=300)
        output = result.stdout
        print(output[-800:] if len(output) > 800 else output)
        results['profile'] = '完成'
    except Exception as e:
        print(f"❌ 用户主页扫描失败: {e}")
        results['profile'] = '失败'
    
    print("\n" + "="*70)
    print("📊 完整扫描任务完成")
    print("="*70)
    print(f"  热门帖子: {results['hot']}")
    print(f"  最新帖子: {results['new']}")
    print(f"  用户主页: {results['profile']}")
    print("="*70)

if __name__ == "__main__":
    run_full_scan()
