#!/usr/bin/env python3
"""
Moltbook 社交自动化 - 主处理器 v6.1
在主会话中运行，使用 sessions_spawn 工具

使用方法：
1. Cron 运行 moltbook_social_cron_v61.sh 扫描任务
2. 此脚本检测到 /tmp/moltbook_needs_processing 标记后运行
3. 使用 sessions_spawn 生成回复并发送
"""

import sys
import json
import time
import os
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

from moltbook_social_v61 import SafeSocialAutomation, API_BASE
from moltbook_cli import load_credentials, get_headers
import requests

# 标记文件
NEEDS_PROCESSING_FLAG = "/tmp/moltbook_needs_processing"
PENDING_FILE = "/tmp/moltbook_pending_v61.json"

def main():
    # 检查是否有处理标记
    if not os.path.exists(NEEDS_PROCESSING_FLAG):
        print("没有待处理任务")
        return
    
    # 检查是否有待处理任务文件
    if not os.path.exists(PENDING_FILE):
        print("没有找到任务文件")
        os.remove(NEEDS_PROCESSING_FLAG)
        return
    
    print("="*70)
    print("🦞 Moltbook Social Main Processor v6.1")
    print("="*70)
    
    # 加载任务
    with open(PENDING_FILE, 'r') as f:
        tasks = json.load(f)
    
    if not tasks:
        print("任务列表为空")
        os.remove(NEEDS_PROCESSING_FLAG)
        os.remove(PENDING_FILE)
        return
    
    print(f"\n处理 {len(tasks)} 个任务")
    print()
    
    # 初始化
    agent = SafeSocialAutomation()
    creds = load_credentials()
    headers = get_headers(creds)
    
    sent = 0
    failed = 0
    
    # 处理每个任务 - 注意：这里需要调用 sessions_spawn 工具
    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] @{task['author']}")
        
        # 检查限制
        can_send, reason = agent.check_limits()
        if not can_send:
            print(f"   ⏳ 跳过: {reason}")
            continue
        
        # 生成回复
        print(f"   🤖 生成回复...")
        
        # 这里需要使用 sessions_spawn 工具
        # 由于在当前Python脚本中无法直接调用工具
        # 我们需要输出任务信息，由主会话处理
        
        print(f"   ⚠️  需要调用 sessions_spawn 工具")
        print(f"   Prompt: {task['prompt'][:80]}...")
        
        # 实际使用时，这里应该调用：
        # reply = sessions_spawn(task=task['prompt'], model='glm', ...)
        
        # 临时方案：跳过，等待工具调用
        failed += 1
    
    print()
    print(f"✅ 处理完成: 成功={sent}, 跳过/失败={failed}")
    print("="*70)
    
    # 清理标记
    os.remove(NEEDS_PROCESSING_FLAG)
    # 保留 PENDING_FILE 供后续处理

if __name__ == "__main__":
    main()
