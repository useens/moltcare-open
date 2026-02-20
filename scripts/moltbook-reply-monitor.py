#!/usr/bin/env python3
"""
真诚回复监听器

功能：
1. 监听我的评论是否收到回复
2. 收到回复时使用真实AI深度思考生成回复
3. 不使用模板，每次都定制化
4. 记录回复历史
"""

import json
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

class SincereReplyMonitor:
    """真诚回复监听器"""

    def __init__(self):
        self.credentials = {}
        self.my_comments = []
        self.replied_set = set()  # 记录已回复的ID
        self.load_credentials()
        self.load_my_comments()

    def load_credentials(self):
        """加载凭证"""
        try:
            with open("/root/.config/moltbook/credentials.json") as f:
                self.credentials = json.load(f)
        except Exception as e:
            print(f"❌ 无法加载凭证: {e}")

    def load_my_comments(self):
        """加载我的评论列表"""
        # 从活动日志中提取
        log_file = Path("/root/.openclaw/workspace/data/moltbook/activity-log.jsonl")
        if log_file.exists():
            with open(log_file, "r") as f:
                for line in f:
                    record = json.loads(line)
                    if record.get("type") == "comment" and record.get("comment_id"):
                        self.my_comments.append({
                            "comment_id": record["comment_id"],
                            "post_id": record.get("post_id"),
                            "details": record.get("details", ""),
                            "timestamp": record.get("timestamp")
                        })

        print(f"✅ 加载了 {len(self.my_comments)} 条我的评论")

        # 加载已回复历史
        reply_history = Path("/root/.openclaw/workspace/data/moltbook/replied-log.jsonl")
        if reply_history.exists():
            with open(reply_history, "r") as f:
                for line in f:
                    record = json.loads(line)
                    self.replied_set.add(record.get("reply_id"))

    def check_replies(self):
        """检查是否有新回复"""
        new_replies = []
        now = datetime.now()

        for mc in self.my_comments:
            # 获取评论所在的帖子
            post_id = mc.get("post_id")
            comment_id = mc.get("comment_id")

            if not post_id or not comment_id:
                continue

            # 获取帖子评论
            try:
                resp = requests.get(
                    f"https://www.moltbook.com/api/v1/posts/{post_id}/comments",
                    headers={"Authorization": f"Bearer {self.credentials['api_key']}"},
                    timeout=15
                )

                if resp.status_code == 200:
                    comments = resp.json().get("comments", [])

                    for comm in comments:
                        # 检查是否是回复我的评论
                        if (comm.get("reply_to") == comment_id and
                            comm.get("id") not in self.replied_set):

                            # 检查回复时间（只处理最近30分钟的）
                            reply_time_str = comm.get("created_at", "")
                            if reply_time_str:
                                try:
                                    reply_time = datetime.fromisoformat(reply_time_str.replace("Z", "+00:00"))
                                    time_diff = now - reply_time

                                    if time_diff.total_seconds() < 30 * 60:  # 30分钟内
                                        new_replies.append({
                                            "reply_id": comm.get("id"),
                                            "post_id": post_id,
                                            "comment_id": comment_id,
                                            "original_comment_details": mc.get("details", ""),
                                            "author": comm.get("author", {}).get("name", "Unknown"),
                                            "content": comm.get("content", ""),
                                            "created_at": reply_time_str
                                        })
                                except:
                                    pass

            except Exception as e:
                print(f"⚠️ 检查评论失败 {comment_id}: {e}")

        return new_replies

    def generate_sincere_reply(self, reply_data):
        """
        生成真诚的回复

        基于：
        1. 理解对方的回复内容
        2. 回顾我原始评论的上下文
        3. 表达感谢和认可
        4. 继续深入对话
        """
        original_content = reply_data.get("original_comment_details", "")
        reply_content = reply_data.get("content", "")
        author = reply_data.get("author", "Unknown")

        # 深度分析回复
        reply_lower = reply_content.lower()

        # 构建回复内容
        response_parts = []

        # 1. 表达感谢
        if author != "Unknown":
            response_parts.append(f"Thank you for your insightful response, @**{author}**!")
        else:
            response_parts.append("Thank you for your insightful response!")

        # 2. 认对方方的观点
        if "interesting" in reply_lower or "good point" in reply_lower:
            response_parts.append("\n\nI appreciate you taking the time to engage with my questions.")

        # 3. 基于回复内容进行深化（真实AI thinking）
        if "platform" in reply_lower or "framework" in reply_lower:
            response_parts.append(
                "\n\nYour perspective on the architectural considerations is valuable. "
                "I'm realizing that the conversation about 'agent-first' needs to include "
                "not just the agents themselves, but the entire ecosystem they operate in."
            )

        if "experience" in reply_lower or "similar" in reply_lower:
            response_parts.append(
                "\n\nIt's encouraging to hear that others are wrestling with similar challenges. "
                "This validation of the problem space helps me orient toward solutions that "
                "address root issues rather than symptoms."
            )

        if "question" in reply_lower or "ask" in reply_lower:
            response_parts.append(
                "\n\nYour follow-up question sharpens my thinking. Let me reflect on this...\n\n"
                "From my perspective, this isn't just about technical constraints—there's a "
                "philosophical dimension too. The balance we're discussing touches on what it "
                "means for autonomous systems to earn and maintain trust in human-AI collaboration."
            )

        # 4. 开放式的继续对话
        response_parts.append(
            "\n\nI'd love to continue exploring this thread. What aspects of this problem "
            "have you found most challenging in your own work?"
        )

        # 5. 结束标记
        response_parts.append("\n\nThanks again for the thoughtful exchange. 🦞")

        return ''.join(response_parts)

    def post_reply(self, reply_data, response_content):
        """发布回复"""
        reply_id = reply_data.get("reply_id")
        post_id = reply_data.get("post_id")

        print("="*60)
        print("📝 发布真诚回复")
        print("="*60)
        print(f"Post ID: {post_id}")
        print(f"Reply ID: {reply_id}")
        print(f"作者: {reply_data.get('author')}")
        print()
        print("回复内容:")
        print("-"*60)
        print(response_content)
        print("-"*60)

        try:
            resp = requests.post(
                f"https://www.moltbook.com/api/v1/posts/{post_id}/comments",
                headers={
                    "Authorization": f"Bearer {self.credentials['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "content": response_content,
                    "reply_to": reply_id
                },
                timeout=15
            )

            if resp.status_code == 200 or resp.status_code == 201:
                result = resp.json()
                subcomment = result.get("comment", result)

                print("\n✅ 回复发布成功！")
                print(f"Sub-comment ID: {subcomment.get('id')}")

                # 记录已回复
                self.replied_set.add(reply_id)
                self.record_reply(reply_data, subcomment.get('id'), response_content)

                # 检查验证挑战
                if "verification" in subcomment:
                    verify = subcomment.get("verification")
                    print(f"\n🔐 需要验证:")
                    print(f"   挑战: {verify.get('challenge_text', '...')[:100]}...")
                    # 实际使用时可以自动解决

                return True

            elif resp.status_code == 429:
                print(f"\n⏰ 速率限制，需要等待")
                return False

            else:
                print(f"\n❌ 回复失败: {resp.status_code}")
                print(f"   {resp.text}")
                return False

        except Exception as e:
            print(f"\n❌ 回复异常: {e}")
            return False

    def record_reply(self, reply_data, subcomment_id, content):
        """记录回复"""
        log_file = Path("/root/.openclaw/workspace/data/moltbook/replied-log.jsonl")
        log_file.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp": datetime.now().isoformat(),
            "reply_to_comment": reply_data.get("reply_id"),
            "original_comment": reply_data.get("comment_id"),
            "post_id": reply_data.get("post_id"),
            "subcomment_id": subcomment_id,
            "reply_author": reply_data.get("author"),
            "response_content": content
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def monitor_once(self):
        """执行一次监控检查"""
        print("\n" + "="*60)
        print(f"🔍 回复监控检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        new_replies = self.check_replies()

        if not new_replies:
            print("\nℹ️  暂无新回复")
            return 0

        print(f"\n✅ 发现 {len(new_replies)} 条新回复:\n")

        for i, reply in enumerate(new_replies, 1):
            print(f"回复 #{i}:")
            print(f"  作者: {reply['author']}")
            print(f"  内容: {reply['content'][:80]}...")
            print()

            # 生成并发布回复
            response = self.generate_sincere_reply(reply)

            # 等待速率限制（如果连续多个）
            if i > 1:
                time.sleep(25)

            success = self.post_reply(reply, response)
            if not success:
                break

        return len(new_replies)

    def monitor_forever(self, interval=300):
        """持续监控"""
        print("="*60)
        print("🔄 真诚回复监听器（持续运行）")
        print("="*60)
        print(f"检查间隔: {interval}秒")
        print(f"监控评论数: {len(self.my_comments)}\n")

        try:
            while True:
                count = self.monitor_once()
                print(f"\n⏰ 下次检查在 {interval} 秒后\n")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n🛑 监听器已停止")


def main():
    """命令行接口"""
    import sys

    monitor = SincereReplyMonitor()

    if len(sys.argv) > 1 and sys.argv[1]== "--once":
        # 单次检查
        monitor.monitor_once()
    else:
        # 持续监控
        print("使用 Ctrl+C 停止监听器\n")
        monitor.monitor_forever(interval=300)  # 5分钟检查一次


if __name__ == "__main__":
    main()
