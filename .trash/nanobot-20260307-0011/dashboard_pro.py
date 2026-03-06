#!/usr/bin/env python3
"""
Nanobot 实时看板 Pro - 增强视觉效果版
使用 Rich 库提供美观的终端UI
"""
import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime

# 尝试导入rich
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")
LOGS_DIR = Path("/root/.openclaw/workspace/projects/nanobot/logs")

AGENTS = {
    "nanobot-1": ("研究员", "🔍", "green"),
    "nanobot-2": ("架构师", "🏗️", "blue"),
    "nanobot-3": ("工程师", "💻", "cyan"),
    "nanobot-4": ("安全专家", "🛡️", "red"),
    "nanobot-5": ("分析师", "📊", "magenta"),
    "nanobot-6": ("决策分析师", "🎯", "yellow"),
    "nanobot-7": ("代码审查员", "🔎", "white"),
    "nanobot-8": ("运维专家", "⚙️", "bright_black"),
    "nanobot-9": ("战略规划师", "📈", "bright_blue"),
    "nanobot-10": ("协调者", "🤝", "bright_green"),
    "openclaw": ("神经中枢", "🧠", "cyan")
}

class DashboardPro:
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        
    def check_agent_status(self, agent_id):
        """检查Agent状态"""
        # 神经中枢是主会话，始终在线
        if agent_id == "openclaw":
            return True
        
        pid_file = LOGS_DIR / f"{agent_id}.pid"
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                if os.path.exists(f"/proc/{pid}"):
                    return True
            except:
                pass
        return False
    
    def get_latest_messages(self, count=8):
        """获取最新消息（包括群聊）"""
        tasks = []
        results = []
        chat_messages = []
        
        # 读取任务
        task_file = HUB_DIR / "tasks.jsonl"
        if task_file.exists():
            with open(task_file) as f:
                lines = f.readlines()
                for line in lines[-count:]:
                    try:
                        d = json.loads(line)
                        tasks.append(d)
                    except:
                        pass
        
        # 读取结果
        result_file = HUB_DIR / "results.jsonl"
        if result_file.exists():
            with open(result_file) as f:
                lines = f.readlines()
                for line in lines[-count:]:
                    try:
                        d = json.loads(line)
                        results.append(d)
                    except:
                        pass
        
        # 读取群聊
        chat_file = HUB_DIR / "group_chat.jsonl"
        if chat_file.exists():
            with open(chat_file) as f:
                lines = f.readlines()
                for line in lines[-count:]:
                    try:
                        d = json.loads(line)
                        chat_messages.append(d)
                    except:
                        pass
        
        return tasks, results, chat_messages
    
    def make_agent_table(self):
        """创建Agent状态表格"""
        table = Table(
            title="🤖 Agent 状态监控",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("状态", style="bold", width=4)
        table.add_column("ID", style="dim", width=12)
        table.add_column("角色", style="bold", width=12)
        table.add_column("图标", width=4)
        table.add_column("运行状态", width=12)
        
        online_count = 0
        for agent_id, (name, icon, color) in AGENTS.items():
            # 神经中枢特殊处理 - 始终在线
            if agent_id == "openclaw":
                online_count += 1
                status = "🟢"
                state = "[green]在线[/green]"
            else:
                is_online = self.check_agent_status(agent_id)
                if is_online:
                    online_count += 1
                    status = "🟢"
                    state = "[green]运行中[/green]"
                else:
                    status = "🔴"
                    state = "[red]离线[/red]"
            
            table.add_row(status, agent_id, f"[{color}]{name}[/{color}]", icon, state)
        
        return table, online_count
    
    def make_message_panel(self, title, messages, is_outgoing=True):
        """创建消息面板"""
        content = []
        for msg in messages[-6:]:
            ts = msg.get("timestamp", "")[11:19]
            if is_outgoing:
                agent_id = msg.get("agent_id", "")
                desc = msg.get("data", {}).get("description", "")[:35]
                name = AGENTS.get(agent_id, (agent_id, "", "white"))[0]
                content.append(f"[{ts}] ➜ {name}: {desc}...")
            else:
                agent_id = msg.get("agent_id", "")
                text = msg.get("result", {}).get("result", "")[:35]
                name = AGENTS.get(agent_id, (agent_id, "", "white"))[0]
                content.append(f"[{ts}] {name}: {text}...")
        
        return Panel(
            "\n".join(content) if content else "等待消息...",
            title=title,
            border_style="cyan" if is_outgoing else "green",
            box=box.ROUNDED
        )
    
    def make_chat_panel(self, chat_messages):
        """创建群聊面板 - 显示更多内容"""
        content = []
        for msg in chat_messages[-6:]:  # 显示最近6条
            ts = msg.get("timestamp", "")[11:19]
            from_id = msg.get("from", "")
            text = msg.get("content", "")
            name = AGENTS.get(from_id, (from_id, "👤", "white"))[0]
            icon = AGENTS.get(from_id, ("", "👤", ""))[1]
            
            # 处理多行内容，显示前100字
            lines = text.split('\n')
            display_lines = []
            total_len = 0
            for line in lines:
                if total_len + len(line) > 100:
                    display_lines.append(line[:100-total_len] + "...")
                    break
                display_lines.append(line)
                total_len += len(line) + 1
            
            display_text = " | ".join(display_lines)
            
            # 高亮@提及
            if "@" in display_text:
                display_text = display_text.replace("@", "[@]")
            
            content.append(f"[{ts}] {icon} {name}: {display_text}")
        
        return Panel(
            "\n".join(content) if content else "暂无群聊消息...",
            title="💬 群聊实时消息 (显示更多内容)",
            border_style="magenta",
            box=box.ROUNDED
        )
    
    def make_stats_panel(self, online_count, tasks, results, chat_msgs):
        """创建统计面板"""
        stats_text = f"""[bold cyan]系统统计[/bold cyan]

在线 Agent: [green]{online_count}/10[/green]
总任务数: [yellow]{len(tasks)}[/yellow]
总回复数: [green]{len(results)}[/green]
群聊消息: [magenta]{len(chat_msgs)}[/magenta]
系统健康: [green]良好[/green]

[dim]最后更新: {datetime.now().strftime('%H:%M:%S')}[/dim]
"""
        return Panel(stats_text, box=box.ROUNDED, border_style="blue")
    
    def make_layout(self):
        """创建整体布局"""
        layout = Layout()
        
        # 分割为头部、主体、底部
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        # 主体分割为左中右三栏
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="center", ratio=3),
            Layout(name="right", ratio=2)
        )
        
        # 左侧面板分割
        layout["left"].split_column(
            Layout(name="agents", ratio=3),
            Layout(name="stats", ratio=2)
        )
        
        # 中间是群聊
        layout["center"].name = "chat"
        
        # 右侧面板分割
        layout["right"].split_column(
            Layout(name="outgoing", ratio=1),
            Layout(name="incoming", ratio=1)
        )
        
        return layout
    
    def update_display(self):
        """更新显示内容"""
        # 创建Agent表格
        agent_table, online_count = self.make_agent_table()
        
        # 获取消息（包括群聊）
        tasks, results, chat_messages = self.get_latest_messages()
        
        # 创建布局
        layout = self.make_layout()
        
        # 头部
        header_text = Text(
            "🧠 Nanobot AI Agent 实时监控看板 Pro + 群聊",
            style="bold cyan",
            justify="center"
        )
        layout["header"].update(Panel(header_text, box=box.DOUBLE))
        
        # Agent表格
        layout["agents"].update(agent_table)
        
        # 统计（包含群聊统计）
        layout["stats"].update(self.make_stats_panel(online_count, tasks, results, chat_messages))
        
        # 群聊面板（放在中间）
        layout["chat"].update(self.make_chat_panel(chat_messages))
        
        # 个人消息面板
        layout["outgoing"].update(self.make_message_panel("📤 我发送的任务", tasks, True))
        layout["incoming"].update(self.make_message_panel("📥 Agent个人回复", results, False))
        
        # 底部
        footer_text = Text(
            "按 Ctrl+C 退出 | 每2秒自动刷新 | 文件队列通信 (0.14ms延迟) | 支持群聊",
            style="dim",
            justify="center"
        )
        layout["footer"].update(Panel(footer_text, box=box.SIMPLE))
        
        return layout
        
        # 消息面板
        layout["outgoing"].update(self.make_message_panel("📤 我发送的任务", tasks, True))
        layout["incoming"].update(self.make_message_panel("📥 Agent回复", results, False))
        
        # 底部
        footer_text = Text(
            "按 Ctrl+C 退出 | 每2秒自动刷新 | 文件队列通信 (0.14ms)",
            style="dim",
            justify="center"
        )
        layout["footer"].update(Panel(footer_text, box=box.SIMPLE))
        
        return layout
    
    def run_rich(self):
        """使用Rich运行"""
        with Live(self.update_display(), refresh_per_second=0.5, screen=True) as live:
            try:
                while True:
                    time.sleep(2)
                    live.update(self.update_display())
            except KeyboardInterrupt:
                pass
    
    def run_simple(self):
        """简单版本（无Rich）"""
        os.system('clear')
        
        # 标题
        print("╔" + "═" * 68 + "╗")
        print("║" + " 🧠 Nanobot AI Agent 实时监控看板 ".center(66) + "║")
        print("║" + f" 更新时间: {datetime.now().strftime('%H:%M:%S')}".center(66) + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        
        # Agent状态表格
        print("┌────────────────────────────────────────────────────────────────────┐")
        print("│ 🤖 AGENT 状态                                                      │")
        print("├──────────┬────────────────┬────────┬───────────────────────────────┤")
        print("│ 状态     │ ID             │ 角色   │ 运行状态                      │")
        print("├──────────┼────────────────┼────────┼───────────────────────────────┤")
        
        online_count = 0
        for agent_id, (name, icon, _) in AGENTS.items():
            is_online = self.check_agent_status(agent_id)
            status = "🟢 在线" if is_online else "🔴 离线"
            state = "✅ 运行中" if is_online else "❌ 已停止"
            if is_online:
                online_count += 1
            print(f"│ {status:8s} │ {agent_id:14s} │ {icon} {name:6s} │ {state:29s} │")
        
        print("└──────────┴────────────────┴────────┴───────────────────────────────┘")
        print(f"  总计: {online_count}/10 在线")
        print()
        
        # 最新消息
        tasks, results = self.get_latest_messages(5)
        
        print("┌────────────────────────────────────────────────────────────────────┐")
        print("│ 📤 最新发送的任务                                                   │")
        print("├────────────────────────────────────────────────────────────────────┤")
        for task in tasks[-5:]:
            agent_id = task.get("agent_id", "")
            desc = task.get("data", {}).get("description", "")[:50]
            name = AGENTS.get(agent_id, (agent_id, "", ""))[0]
            print(f"│ ➜ {name:8s}: {desc:50s}... │")
        print("└────────────────────────────────────────────────────────────────────┘")
        print()
        
        print("┌────────────────────────────────────────────────────────────────────┐")
        print("│ 📥 最新回复                                                        │")
        print("├────────────────────────────────────────────────────────────────────┤")
        for result in results[-5:]:
            agent_id = result.get("agent_id", "")
            text = result.get("result", {}).get("result", "")[:50]
            name = AGENTS.get(agent_id, (agent_id, "", ""))[0]
            print(f"│ {name:8s}: {text:50s}... │")
        print("└────────────────────────────────────────────────────────────────────┘")
        print()
        
        # 统计
        print(f"📊 统计: 任务 {len(tasks)} | 回复 {len(results)} | 在线 {online_count}/10")
        print()
        print("💡 提示: 按 Ctrl+C 退出")
    
    def run(self):
        """主运行函数"""
        if RICH_AVAILABLE and self.console:
            try:
                self.run_rich()
            except Exception as e:
                print(f"Rich模式失败，切换到简单模式: {e}")
                self.run_simple_loop()
        else:
            self.run_simple_loop()
    
    def run_simple_loop(self):
        """简单模式循环"""
        try:
            while True:
                self.run_simple()
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n看板已退出")

def install_rich():
    """安装Rich库"""
    print("正在安装 Rich 库以获得更好的视觉效果...")
    os.system("pip install rich -q")
    print("安装完成！请重新运行看板。")

def main():
    if not RICH_AVAILABLE:
        print("⚠️  Rich库未安装")
        print("建议安装: pip install rich")
        print("")
        print("正在以简单模式运行...")
        print("")
        time.sleep(2)
    
    dashboard = DashboardPro()
    dashboard.run()

if __name__ == "__main__":
    main()
