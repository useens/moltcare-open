#!/usr/bin/env python3
"""
Nanobot 实时对话看板
实时监控10个Agent的状态和对话
"""
import os
import sys
import time
import json
import curses
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")
LOGS_DIR = Path("/root/.openclaw/workspace/projects/nanobot/logs")

AGENTS = {
    "nanobot-1": ("研究员", "research"),
    "nanobot-2": ("架构师", "architecture"),
    "nanobot-3": ("工程师", "coding"),
    "nanobot-4": ("安全专家", "security"),
    "nanobot-5": ("分析师", "analysis"),
    "nanobot-6": ("决策分析师", "decision"),
    "nanobot-7": ("代码审查员", "review"),
    "nanobot-8": ("运维专家", "ops"),
    "nanobot-9": ("战略规划师", "strategy"),
    "nanobot-10": ("协调者", "coordination")
}

class NanobotDashboard:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.max_y, self.max_x = stdscr.getmaxyx()
        self.running = True
        self.last_tasks = []
        self.last_results = []
        
        # 初始化颜色
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)   # 在线
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)     # 离线
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # 警告
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)    # 信息
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)    # 标题
        
    def check_agent_status(self, agent_id):
        """检查Agent进程状态"""
        pid_file = LOGS_DIR / f"{agent_id}.pid"
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                if os.path.exists(f"/proc/{pid}"):
                    return True
            except:
                pass
        return False
    
    def get_latest_messages(self, count=5):
        """获取最新消息"""
        tasks = []
        results = []
        
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
        
        return tasks, results
    
    def draw_header(self):
        """绘制标题"""
        title = "🧠 Nanobot AI Agent 实时看板"
        subtitle = f"更新时间: {datetime.now().strftime('%H:%M:%S')}"
        
        self.stdscr.attron(curses.color_pair(5))
        self.stdscr.addstr(0, 0, " " * self.max_x)
        self.stdscr.addstr(0, (self.max_x - len(title)) // 2, title)
        self.stdscr.attroff(curses.color_pair(5))
        
        self.stdscr.addstr(1, self.max_x - len(subtitle) - 2, subtitle)
        self.stdscr.addstr(2, 0, "=" * self.max_x)
    
    def draw_agent_status(self, start_y):
        """绘制Agent状态"""
        self.stdscr.addstr(start_y, 2, "📊 Agent状态", curses.A_BOLD)
        self.stdscr.addstr(start_y + 1, 2, "-" * 40)
        
        online_count = 0
        for i, (agent_id, (name, role)) in enumerate(AGENTS.items(), start_y + 2):
            is_online = self.check_agent_status(agent_id)
            if is_online:
                online_count += 1
                status = "🟢"
                color = curses.color_pair(1)
            else:
                status = "🔴"
                color = curses.color_pair(2)
            
            line = f"{status} {agent_id:12s} | {name:10s} | {role:15s}"
            self.stdscr.addstr(i, 4, line, color)
        
        # 汇总
        summary_y = start_y + 13
        self.stdscr.addstr(summary_y, 2, "-" * 40)
        summary = f"总计: {online_count}/10 在线"
        self.stdscr.addstr(summary_y + 1, 4, summary, curses.A_BOLD)
        
        return summary_y + 3
    
    def draw_messages(self, start_y):
        """绘制消息流"""
        # 分成左右两栏
        mid_x = self.max_x // 2
        
        # 左栏：我的任务
        self.stdscr.addstr(start_y, 2, "📤 我发送的任务", curses.A_BOLD)
        self.stdscr.addstr(start_y + 1, 2, "-" * (mid_x - 4))
        
        tasks, _ = self.get_latest_messages(5)
        for i, task in enumerate(tasks[:5], start=start_y + 2):
            agent_id = task.get("agent_id", "unknown")
            desc = task.get("data", {}).get("description", "")[:30]
            ts = task.get("timestamp", "")[11:19]  # 只显示时间
            
            name = AGENTS.get(agent_id, (agent_id, ""))[0]
            line = f"[{ts}] -> {name}: {desc}"
            self.stdscr.addstr(i, 4, line[:mid_x-6], curses.color_pair(4))
        
        # 右栏：Agent回复
        self.stdscr.addstr(start_y, mid_x + 2, "📥 Agent回复", curses.A_BOLD)
        self.stdscr.addstr(start_y + 1, mid_x + 2, "-" * (mid_x - 4))
        
        _, results = self.get_latest_messages(5)
        for i, result in enumerate(results[:5], start=start_y + 2):
            agent_id = result.get("agent_id", "unknown")
            text = result.get("result", {}).get("result", "")[:30]
            ts = result.get("timestamp", "")[11:19]
            
            name = AGENTS.get(agent_id, (agent_id, ""))[0]
            line = f"[{ts}] {name}: {text}"
            self.stdscr.addstr(i, mid_x + 4, line[:mid_x-6], curses.color_pair(1))
        
        return start_y + 8
    
    def draw_footer(self, start_y):
        """绘制底部信息"""
        self.stdscr.addstr(start_y, 0, "-" * self.max_x)
        help_text = "按 'q' 退出 | 按 'r' 立即刷新"
        self.stdscr.addstr(start_y + 1, (self.max_x - len(help_text)) // 2, help_text)
    
    def run(self):
        """主循环"""
        self.stdscr.nodelay(1)  # 非阻塞输入
        
        while self.running:
            self.stdscr.clear()
            
            # 绘制各区域
            self.draw_header()
            
            status_y = 4
            next_y = self.draw_agent_status(status_y)
            
            messages_y = next_y + 1
            next_y = self.draw_messages(messages_y)
            
            self.draw_footer(self.max_y - 3)
            
            self.stdscr.refresh()
            
            # 处理输入
            try:
                key = self.stdscr.getch()
                if key == ord('q'):
                    self.running = False
                elif key == ord('r'):
                    continue  # 立即刷新
            except:
                pass
            
            time.sleep(2)  # 每2秒刷新

def main():
    try:
        curses.wrapper(lambda stdscr: NanobotDashboard(stdscr).run())
    except KeyboardInterrupt:
        print("\n看板已退出")
    except Exception as e:
        print(f"错误: {e}")
        # 降级到简单版本
        simple_dashboard()

def simple_dashboard():
    """简单版本（无curses）"""
    os.system('clear')
    print("🧠 Nanobot AI Agent 实时看板 (简化版)")
    print("=" * 70)
    print()
    
    # 检查Agent状态
    print("📊 Agent状态:")
    online = 0
    for agent_id, (name, role) in AGENTS.items():
        pid_file = LOGS_DIR / f"{agent_id}.pid"
        status = "🟢" if pid_file.exists() else "🔴"
        if status == "🟢":
            online += 1
        print(f"  {status} {agent_id:12s} | {name:10s}")
    print(f"\n  总计: {online}/10 在线")
    print()
    
    # 最新消息
    print("📤 最新任务:")
    task_file = HUB_DIR / "tasks.jsonl"
    if task_file.exists():
        with open(task_file) as f:
            lines = f.readlines()
            for line in lines[-3:]:
                try:
                    d = json.loads(line)
                    agent = d.get("agent_id", "")
                    desc = d.get("data", {}).get("description", "")[:40]
                    name = AGENTS.get(agent, (agent, ""))[0]
                    print(f"  -> {name}: {desc}...")
                except:
                    pass
    print()
    
    print("📥 最新回复:")
    result_file = HUB_DIR / "results.jsonl"
    if result_file.exists():
        with open(result_file) as f:
            lines = f.readlines()
            for line in lines[-3:]:
                try:
                    d = json.loads(line)
                    agent = d.get("agent_id", "")
                    text = d.get("result", {}).get("result", "")[:40]
                    name = AGENTS.get(agent, (agent, ""))[0]
                    print(f"  {name}: {text}...")
                except:
                    pass
    print()
    print("=" * 70)
    print("提示: 安装curses可获得更好的可视化效果")

if __name__ == "__main__":
    main()
