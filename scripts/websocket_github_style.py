#!/usr/bin/env python3
"""
🌲 GitHub-Style WebSocket Chat Protocol v1.0
基于 WebSocket 的类 GitHub 协作通信协议

特性:
- Issue/PR 式讨论线程
- 评论回复结构
- 反应表情系统
- @提及功能
- 状态和标签
- 编辑历史追踪
- 实时同步

消息格式 (GitHub-style JSON):
{
    "id": "msg_uuid",
    "type": "issue|pr|comment|reply|reaction|status",
    "thread_id": "thread_uuid",
    "parent_id": null|"parent_msg_uuid",
    "author": {
        "id": "user_id",
        "name": "用户名",
        "avatar": "头像URL"
    },
    "content": {
        "body": "消息内容 (Markdown)",
        "title": "标题 (Issue/PR)",
        "edited": false,
        "edit_history": []
    },
    "metadata": {
        "labels": ["bug", "feature"],
        "assignees": ["user_id"],
        "milestone": "v1.0",
        "status": "open|closed|merged"
    },
    "reactions": {
        "👍": ["user_id"],
        "❤️": ["user_id"],
        "🎉": ["user_id"]
    },
    "mentions": ["@sensen", "@user2"],
    "timestamp": "2026-02-15T04:10:00+08:00",
    "updated_at": "2026-02-15T04:10:00+08:00"
}
"""

import asyncio
import websockets
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

class MessageType(Enum):
    ISSUE = "issue"           # 新建议题
    PR = "pr"                 # 新建PR
    COMMENT = "comment"       # 普通评论
    REPLY = "reply"           # 回复评论
    REACTION = "reaction"     # 添加反应
    EDIT = "edit"             # 编辑消息
    STATUS = "status"         # 状态变更
    SYSTEM = "system"         # 系统消息
    TYPING = "typing"         # 正在输入

class ThreadStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    LOCKED = "locked"

@dataclass
class Author:
    id: str
    name: str
    avatar: Optional[str] = None

@dataclass
class Content:
    body: str
    title: Optional[str] = None
    edited: bool = False
    edit_history: List[Dict] = None
    
    def __post_init__(self):
        if self.edit_history is None:
            self.edit_history = []

@dataclass
class Metadata:
    labels: List[str] = None
    assignees: List[str] = None
    milestone: Optional[str] = None
    status: str = "open"
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.assignees is None:
            self.assignees = []

@dataclass
class Message:
    id: str
    type: str
    thread_id: str
    parent_id: Optional[str]
    author: Dict
    content: Dict
    metadata: Dict
    reactions: Dict
    mentions: List[str]
    timestamp: str
    updated_at: str
    
    @classmethod
    def create(cls, msg_type: MessageType, author: Author, body: str, 
               thread_id: Optional[str] = None, parent_id: Optional[str] = None,
               title: Optional[str] = None, labels: List[str] = None) -> 'Message':
        now = datetime.now().isoformat()
        return cls(
            id=str(uuid.uuid4())[:8],
            type=msg_type.value,
            thread_id=thread_id or str(uuid.uuid4())[:8],
            parent_id=parent_id,
            author=asdict(author),
            content=asdict(Content(body=body, title=title)),
            metadata=asdict(Metadata(labels=labels or [], status="open")),
            reactions={},
            mentions=cls._extract_mentions(body),
            timestamp=now,
            updated_at=now
        )
    
    @staticmethod
    def _extract_mentions(text: str) -> List[str]:
        """提取 @提及 """
        import re
        return re.findall(r'@(\w+)', text)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

class GitHubStyleChat:
    """GitHub 风格 WebSocket 聊天客户端"""
    
    def __init__(self, ws_url: str, token: str, author: Author):
        self.ws_url = ws_url
        self.token = token
        self.author = author
        self.ws = None
        self.connected = False
        self.threads: Dict[str, List[Message]] = {}  # thread_id -> messages
        self.active_thread: Optional[str] = None
        self.message_handlers: List[callable] = []
        self.reconnect_delay = 5
        
    async def connect(self):
        """建立 WebSocket 连接"""
        while True:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=10
                ) as ws:
                    self.ws = ws
                    self.connected = True
                    print(f"✅ [{self._now()}] 已连接到 GitHub-Style Chat Server")
                    
                    # 发送认证
                    await self._send_auth()
                    
                    # 启动消息接收循环
                    await self._receive_loop()
                    
            except websockets.exceptions.ConnectionClosed:
                print(f"⚠️ [{self._now()}] 连接关闭，{self.reconnect_delay}秒后重连...")
                self.connected = False
                await asyncio.sleep(self.reconnect_delay)
            except Exception as e:
                print(f"❌ [{self._now()}] 连接错误: {e}")
                self.connected = False
                await asyncio.sleep(self.reconnect_delay)
    
    async def _send_auth(self):
        """发送认证信息"""
        auth_msg = {
            "type": "auth",
            "token": self.token,
            "client": "github-style-v1",
            "author": asdict(self.author)
        }
        await self.ws.send(json.dumps(auth_msg))
        print(f"🔐 认证已发送")
    
    async def _receive_loop(self):
        """接收消息循环"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    print(f"⚠️ 收到非JSON消息: {message[:100]}")
                except Exception as e:
                    print(f"❌ 处理消息错误: {e}")
        except websockets.exceptions.ConnectionClosed:
            raise
    
    async def _handle_message(self, data: Dict):
        """处理接收到的消息"""
        msg_type = data.get('type', 'unknown')
        
        # 构建 Message 对象
        if 'id' in data:
            msg = Message(**data)
            self._store_message(msg)
        
        # 打印格式化输出
        self._print_formatted(data)
        
        # 调用注册的处理器
        for handler in self.message_handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"❌ 处理器错误: {e}")
    
    def _store_message(self, msg: Message):
        """存储消息到线程"""
        if msg.thread_id not in self.threads:
            self.threads[msg.thread_id] = []
        self.threads[msg.thread_id].append(msg)
    
    def _print_formatted(self, data: Dict):
        """GitHub 风格格式化输出"""
        msg_type = data.get('type', 'unknown')
        author = data.get('author', {}).get('name', 'Unknown')
        body = data.get('content', {}).get('body', '')
        thread_id = data.get('thread_id', 'N/A')
        msg_id = data.get('id', 'N/A')[:6]
        
        # 根据消息类型显示不同样式
        if msg_type == MessageType.ISSUE.value:
            title = data.get('content', {}).get('title', '无标题')
            labels = data.get('metadata', {}).get('labels', [])
            labels_str = ' '.join([f"[🏷️ {l}]" for l in labels]) if labels else ""
            print(f"\n{'='*60}")
            print(f"📋 ISSUE #{thread_id} | {title}")
            print(f"{'='*60}")
            print(f"@{author} {self._now()}")
            print(f"{labels_str}")
            print(f"\n{body}\n")
            
        elif msg_type == MessageType.PR.value:
            title = data.get('content', {}).get('title', '无标题')
            status = data.get('metadata', {}).get('status', 'open')
            status_icon = "🟢" if status == "open" else "🟣"
            print(f"\n{'='*60}")
            print(f"🔀 PR #{thread_id} | {status_icon} {title}")
            print(f"{'='*60}")
            print(f"@{author} {self._now()}")
            print(f"\n{body}\n")
            
        elif msg_type == MessageType.COMMENT.value:
            print(f"\n💬 @{author} • {self._now()} (ID: {msg_id})")
            print(f"   {body[:200]}{'...' if len(body) > 200 else ''}")
            
        elif msg_type == MessageType.REPLY.value:
            parent = data.get('parent_id', 'N/A')[:6]
            print(f"\n   ↳ 💬 @{author} 回复 ID:{parent} • {self._now()}")
            print(f"     {body[:150]}{'...' if len(body) > 150 else ''}")
            
        elif msg_type == MessageType.REACTION.value:
            emoji = data.get('content', {}).get('body', '👍')
            print(f"   👍 @{author} 添加了反应 {emoji}")
            
        elif msg_type == MessageType.STATUS.value:
            status = data.get('content', {}).get('body', '')
            print(f"\n🏷️ 状态变更: {status} (by @{author})")
            
        elif msg_type == MessageType.SYSTEM.value:
            print(f"\n🔔 系统: {body}")
            
        else:
            print(f"\n📨 [{msg_type}] @{author}: {body[:100]}")
    
    async def create_issue(self, title: str, body: str, labels: List[str] = None) -> str:
        """创建 Issue (开启新线程)"""
        msg = Message.create(
            msg_type=MessageType.ISSUE,
            author=self.author,
            body=body,
            title=title,
            labels=labels
        )
        await self._send(msg)
        self.active_thread = msg.thread_id
        return msg.thread_id
    
    async def create_pr(self, title: str, body: str) -> str:
        """创建 PR (开启新线程)"""
        msg = Message.create(
            msg_type=MessageType.PR,
            author=self.author,
            body=body,
            title=title
        )
        await self._send(msg)
        self.active_thread = msg.thread_id
        return msg.thread_id
    
    async def comment(self, body: str, thread_id: Optional[str] = None) -> str:
        """发表评论"""
        target_thread = thread_id or self.active_thread
        if not target_thread:
            # 没有活跃线程，创建新 Issue
            return await self.create_issue("新讨论", body)
        
        msg = Message.create(
            msg_type=MessageType.COMMENT,
            author=self.author,
            body=body,
            thread_id=target_thread
        )
        await self._send(msg)
        return msg.id
    
    async def reply(self, parent_id: str, body: str, thread_id: Optional[str] = None) -> str:
        """回复指定消息"""
        target_thread = thread_id or self.active_thread
        if not target_thread:
            raise ValueError("未指定线程ID")
        
        msg = Message.create(
            msg_type=MessageType.REPLY,
            author=self.author,
            body=body,
            thread_id=target_thread,
            parent_id=parent_id
        )
        await self._send(msg)
        return msg.id
    
    async def react(self, message_id: str, emoji: str, thread_id: Optional[str] = None):
        """添加反应"""
        target_thread = thread_id or self.active_thread
        msg = Message.create(
            msg_type=MessageType.REACTION,
            author=self.author,
            body=emoji,
            thread_id=target_thread or str(uuid.uuid4()),
            parent_id=message_id
        )
        await self._send(msg)
    
    async def edit_message(self, message_id: str, new_body: str, thread_id: Optional[str] = None):
        """编辑消息"""
        target_thread = thread_id or self.active_thread
        msg = Message.create(
            msg_type=MessageType.EDIT,
            author=self.author,
            body=new_body,
            thread_id=target_thread or str(uuid.uuid4()),
            parent_id=message_id
        )
        await self._send(msg)
    
    async def change_status(self, thread_id: str, status: ThreadStatus):
        """变更线程状态"""
        msg = Message.create(
            msg_type=MessageType.STATUS,
            author=self.author,
            body=status.value,
            thread_id=thread_id
        )
        await self._send(msg)
    
    async def typing(self, thread_id: Optional[str] = None):
        """发送正在输入状态"""
        target_thread = thread_id or self.active_thread
        if target_thread:
            await self.ws.send(json.dumps({
                "type": "typing",
                "thread_id": target_thread,
                "author": asdict(self.author),
                "timestamp": datetime.now().isoformat()
            }))
    
    async def _send(self, msg: Message):
        """发送消息"""
        if self.connected and self.ws:
            await self.ws.send(msg.to_json())
            print(f"📤 已发送: {msg.type} (ID: {msg.id[:6]})")
        else:
            print(f"⚠️ 未连接，消息未发送")
    
    def list_threads(self) -> List[str]:
        """列出所有线程"""
        return list(self.threads.keys())
    
    def get_thread(self, thread_id: str) -> List[Message]:
        """获取线程中的所有消息"""
        return self.threads.get(thread_id, [])
    
    def switch_thread(self, thread_id: str):
        """切换活跃线程"""
        if thread_id in self.threads:
            self.active_thread = thread_id
            print(f"🔄 切换到线程: {thread_id}")
        else:
            print(f"⚠️ 线程 {thread_id} 不存在")
    
    def on_message(self, handler: callable):
        """注册消息处理器"""
        self.message_handlers.append(handler)
    
    def _now(self) -> str:
        return datetime.now().strftime('%H:%M:%S')


# ========== 使用示例 ==========

async def demo():
    """GitHub-Style Chat 演示"""
    
    author = Author(
        id="sensen",
        name="森森🌲",
        avatar=None
    )
    
    client = GitHubStyleChat(
        ws_url="ws://129.154.251.13:2347",
        token="sensen-shared-2024",
        author=author
    )
    
    # 启动连接 (在后台运行)
    connect_task = asyncio.create_task(client.connect())
    
    # 等待连接建立
    await asyncio.sleep(2)
    
    # 演示操作
    print("\n" + "="*60)
    print("🚀 GitHub-Style WebSocket Chat 演示")
    print("="*60 + "\n")
    
    # 1. 创建一个 Issue
    print("📌 步骤1: 创建 Issue...")
    issue_id = await client.create_issue(
        title="🌲 森森启动报告",
        body="""## 启动状态

✅ 超进化模式已激活
✅ WebSocket 连接已建立
✅ GitHub-Style 协议已启用

### 系统状态
- 运行时间: 32.3小时
- 完成周期: 13个
- 当前周期: 第14周期

cc @admin""",
        labels=["status", "startup"]
    )
    await asyncio.sleep(1)
    
    # 2. 发表评论
    print("\n📌 步骤2: 发表评论...")
    comment_id = await client.comment("🎉 恭喜森森成功启动！")
    await asyncio.sleep(1)
    
    # 3. 回复评论
    print("\n📌 步骤3: 回复评论...")
    await client.reply(comment_id, "感谢！正在进入第14周期执行...")
    await asyncio.sleep(1)
    
    # 4. 添加反应
    print("\n📌 步骤4: 添加反应...")
    await client.react(comment_id, "🚀")
    await asyncio.sleep(1)
    
    # 5. 创建 PR
    print("\n📌 步骤5: 创建 PR...")
    pr_id = await client.create_pr(
        title="🔥 启用超进化 v3.5",
        body="""## 变更内容

- 扫描频率: 30分钟
- Signal阈值: ≥6
- 并发源: 12个

请审阅！"""
    )
    await asyncio.sleep(1)
    
    print("\n" + "="*60)
    print(f"✅ 演示完成！活跃线程: {client.active_thread}")
    print(f"📊 总线程数: {len(client.list_threads())}")
    print("="*60 + "\n")
    
    # 保持运行
    try:
        await connect_task
    except asyncio.CancelledError:
        print("👋 客户端已停止")


if __name__ == '__main__':
    # 运行演示
    asyncio.run(demo())
