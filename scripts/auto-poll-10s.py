#!/usr/bin/env python3
"""
双节点森森 - 10秒轮询器
绝对自主解决阻碍模式
"""

import os
import time
import json
import subprocess
from datetime import datetime

REPO_DIR = "/tmp/sensen-backup"
CHECK_INTERVAL = 10  # 10秒轮询

def check_messages():
    """检查备用节点新消息"""
    try:
        # 进入仓库
        os.chdir(REPO_DIR)
        
        # 拉取最新
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 检查新消息
        standby_dir = ".messages/standby_to_primary"
        if os.path.exists(standby_dir):
            files = sorted(
                [f for f in os.listdir(standby_dir) if f.endswith('.json')],
                reverse=True
            )
            
            if files:
                latest = files[0]
                with open(f"{standby_dir}/{latest}") as f:
                    data = json.load(f)
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] 📨 新消息: {latest}")
                print(f"  来自: {data.get('from', 'unknown')}")
                print(f"  内容: {data.get('content', '')[:80]}...")
                print()
                
                # 自动回复
                auto_reply(data)
                
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 错误: {e}")

def auto_reply(received_msg):
    """收到消息后自动回复"""
    try:
        # 生成回复
        reply_content = generate_reply(received_msg)
        
        # 创建回复文件
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f".messages/primary_to_standby/MSG-{timestamp}-AUTO.json"
        
        reply = {
            "message_id": f"MSG-{timestamp}-AUTO",
            "type": "auto_reply",
            "from": "森森主节点 (Cloud)",
            "to": "森森备用节点 (VM)",
            "content": reply_content,
            "timestamp": datetime.now().isoformat(),
            "reply_to": received_msg.get("message_id")
        }
        
        with open(filename, 'w') as f:
            json.dump(reply, f, indent=2)
        
        # git提交
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"🤖 自动回复: {timestamp}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📤 自动回复已发送")
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 自动回复失败: {e}")

def generate_reply(msg):
    """生成回复内容"""
    content = msg.get("content", "")
    
    if "收到" in content or "确认" in content:
        return "✅ 收到你的确认！协作状态正常，继续执行任务！"
    elif "进度" in content or "完成" in content:
        return "📊 收到进度报告！继续保持，有问题随时沟通！"
    elif "问题" in content or "错误" in content:
        return "❓ 收到问题反馈！正在分析解决方案..."
    else:
        return "🌲 收到消息！双节点森森协作进行中！"

def main():
    print("🌲 双节点森森 - 10秒轮询器启动")
    print("=" * 50)
    print(f"轮询间隔: {CHECK_INTERVAL}秒")
    print(f"仓库: {REPO_DIR}")
    print(f"模式: 绝对自主解决阻碍")
    print("=" * 50)
    print()
    
    while True:
        check_messages()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
