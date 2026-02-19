"""
Multi-Agent Canvas - Phase 2 终端可视化
在控制台实时显示讨论面板
"""
import redis
import json
import time
import sys
import os
from datetime import datetime

# 清屏函数
def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

# 颜色代码
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    PURPLE = '\033[35m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BG_BLACK = '\033[40m'
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'

class TerminalCanvas:
    def __init__(self, debate_id='demo', redis_port=6380):
        self.debate_id = debate_id
        self.r = redis.Redis(host='localhost', port=redis_port, decode_responses=True)
        self.agents = {
            'grok': {'name': 'Grok', 'role': '队长 · 整合裁决', 'color': Colors.CYAN},
            'harper': {'name': 'Harper', 'role': '研究 · 验证专家', 'color': Colors.PURPLE},
            'benjamin': {'name': 'Benjamin', 'role': '架构 · 逻辑专家', 'color': Colors.GREEN},
            'lucas': {'name': 'Lucas', 'role': '工具 · 执行专家', 'color': Colors.YELLOW}
        }
        self.messages = []
        self.start_time = time.time()
        self.current_round = 0
        
    def format_time(self):
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        return f"{mins:02d}:{secs:02d}"
    
    def get_status_icon(self, status):
        icons = {
            'thinking': f"{Colors.YELLOW}🤔 思考中{Colors.ENDC}",
            'complete': f"{Colors.GREEN}✅ 已完成{Colors.ENDC}",
            'debating': f"{Colors.CYAN}💬 回应中{Colors.ENDC}",
            'waiting': f"{Colors.RED}⏳ 等待中{Colors.ENDC}",
            'responding': f"{Colors.CYAN}💬 回应中{Colors.ENDC}",
            'unknown': f"{Colors.RED}❓ 未知{Colors.ENDC}"
        }
        return icons.get(status, status)
    
    def draw_panel(self):
        """绘制讨论面板"""
        clear_screen()
        
        # 标题
        print(f"{Colors.BG_BLUE}{Colors.BOLD} 🔮 Multi-Agent Real-time Discussion Panel {Colors.ENDC}")
        print(f"{Colors.CYAN}LIVE{Colors.ENDC} | 辩论ID: {self.debate_id} | 运行时间: {self.format_time()}")
        print("=" * 80)
        
        # 获取当前状态
        status = self.r.get(f"debate:{self.debate_id}:status") or "等待开始"
        progress = self.r.keys(f"debate:{self.debate_id}:progress:*")
        completed = len([p for p in progress if 'complete' in self.r.get(p)])
        
        print(f"\n{Colors.BOLD}状态:{Colors.ENDC} {status} | "
              f"{Colors.BOLD}进度:{Colors.ENDC} {completed}/3 专家 | "
              f"{Colors.BOLD}消息:{Colors.ENDC} {len(self.messages)}")
        print("-" * 80)
        
        # 专家卡片（简化版）
        for agent_id, info in self.agents.items():
            # 获取状态
            progress_key = f"debate:{self.debate_id}:progress:{agent_id}"
            status = self.r.get(progress_key) or "waiting"
            
            # 获取最新内容
            content = ""
            for round_num in [1, 2, 3]:
                key = f"debate:{self.debate_id}:round:{round_num}"
                thought = self.r.hget(key, agent_id)
                if thought:
                    content = thought[:100] + "..." if len(thought) > 100 else thought
                    break
            
            # 显示卡片
            print(f"\n{info['color']}{Colors.BOLD}[{info['name']}]{Colors.ENDC} - {info['role']}")
            print(f"  状态: {self.get_status_icon(status)}")
            if content:
                print(f"  内容: {content[:60]}...")
        
        # 消息流
        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}💬 实时消息流{Colors.ENDC}")
        print("-" * 80)
        
        # 显示最近10条消息
        for msg in self.messages[-10:]:
            time_str = msg.get('time', '--:--:--')
            agent = msg.get('agent', 'System')
            content = msg.get('content', '')
            
            agent_color = self.agents.get(agent.lower(), {}).get('color', Colors.ENDC)
            print(f"{Colors.GRAY}[{time_str}]{Colors.ENDC} "
                  f"{agent_color}{agent:10}{Colors.ENDC} {content}")
        
        print("\n" + "=" * 80)
        print(f"{Colors.YELLOW}按 Ctrl+C 退出 | 自动刷新中...{Colors.ENDC}")
    
    def add_message(self, agent, content):
        """添加消息"""
        self.messages.append({
            'time': datetime.now().strftime("%H:%M:%S"),
            'agent': agent,
            'content': content[:80]
        })
    
    def run(self):
        """运行可视化"""
        print(f"{Colors.GREEN}🚀 Canvas 终端可视化已启动{Colors.ENDC}")
        print(f"辩论ID: {self.debate_id}")
        print(f"Redis: localhost:6380")
        print("\n等待辩论开始...\n")
        time.sleep(2)
        
        try:
            while True:
                # 检查Redis中的新更新
                pubsub = self.r.pubsub()
                pubsub.subscribe(f"debate:{self.debate_id}:updates")
                
                # 非阻塞检查消息
                message = pubsub.get_message(timeout=0.5)
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        agent = data.get('agent', 'Unknown')
                        status = data.get('status', '')
                        self.add_message(agent, f"{status} | Round {data.get('round', 1)}")
                    except:
                        pass
                
                pubsub.unsubscribe()
                
                # 绘制面板
                self.draw_panel()
                
                # 等待刷新
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}👋 Canvas 可视化已停止{Colors.ENDC}")

if __name__ == '__main__':
    import sys
    debate_id = sys.argv[1] if len(sys.argv) > 1 else 'demo'
    
    canvas = TerminalCanvas(debate_id=debate_id)
    canvas.run()
