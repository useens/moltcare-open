#!/usr/bin/env python3
"""
Moltbook 自然社交脚本
每30分钟执行：遍历帖子，遇到真正有感触的内容就回复
不预设、不计划、不凑数
"""

import sys
import json
import random
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import get_hot_posts, get_new_posts, reply_to_post

LOG_FILE = "/root/.openclaw/workspace/data/moltbook/natural-social.log"

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    with open(LOG_FILE, 'a') as f:
        f.write(entry + '\n')

def find_worthwhile_post():
    """寻找真正有感触的帖子"""
    log("🌲 开始自然社交遍历")

    # 混合查看热门和最新帖子
    hot_posts = get_hot_posts(10)
    new_posts = get_new_posts(10)
    all_posts = hot_posts[:7] + new_posts[:7]

    # 过滤掉自己发的帖子
    creds = json.load(open('/root/.config/moltbook/credentials.json'))
    my_agent = creds.get('agent_name', 'novaassistantpro')
    others_posts = [p for p in all_posts if p.get('author', {}).get('name') != my_agent]

    log(f"   扫描到 {len(others_posts)} 个候选帖子")

    # 这里不自动选择，只是返回候选，让人工/外部逻辑决定
    # 但为了简单，这个脚本可以随机选一个去看看详情（如果能获取的话）
    # 实际回复还是需要手动触发或者另一个脚本

    if not others_posts:
        log("   没有找到合适的新帖子")
        return None

    # 随机选一个返回，供手动检查
    selected = random.choice(others_posts)
    log(f"   随机选中: {selected.get('title', 'N/A')} - @{selected.get('author', {}).get('name', 'N/A')}")

    return selected

def main():
    try:
        post = find_worthwhile_post()

        if post:
            log("✅ 遍历完成，发现候选帖子（需手动决定是否回复）")
            # 输出帖子信息，可能被另一个进程读取
            print(f"CANDIDATE:{json.dumps({ 'id': post.get('id'), 'title': post.get('title') })}")
        else:
            log("✅ 遍历完成，未发现值得回复的内容")

    except Exception as e:
        log(f"❌ 异常: {e}")
        import traceback
        log(traceback.format_exc())

if __name__ == '__main__':
    main()
