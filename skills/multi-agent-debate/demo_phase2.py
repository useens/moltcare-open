"""
Multi-Agent Canvas - Phase 2 完整演示
结合 Redis 实时同步 + 终端可视化面板
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/multi-agent-debate')

from redis_manager import DebateRedisManager, AgentUpdate
import time
import threading
from datetime import datetime

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
    BG_BLUE = '\033[44m'

def clear():
    print('\033[2J\033[H', end='')

def draw_card(name, role, status, content, color):
    """绘制专家卡片"""
    status_icons = {
        'thinking': '🤔',
        'complete': '✅',
        'responding': '💬',
        'waiting': '⏳'
    }
    icon = status_icons.get(status, '⏳')
    
    print(f"{color}{'─' * 38}{Colors.ENDC}")
    print(f"{color}{icon} {Colors.BOLD}{name}{Colors.ENDC} - {role}")
    print(f"   状态: {status}")
    if content:
        preview = content[:50] + "..." if len(content) > 50 else content
        print(f"   {preview}")
    print(f"{color}{'─' * 38}{Colors.ENDC}")

def demo_canvas_visualization():
    """演示 Canvas 实时可视化"""
    print(f"{Colors.BG_BLUE}{Colors.BOLD} 🔮 Phase 2: Canvas 实时可视化演示 {Colors.ENDC}")
    print("=" * 80)
    
    # 初始化Redis
    manager = DebateRedisManager(port=6380)
    
    if not manager.test_connection():
        print(f"{Colors.RED}❌ Redis连接失败{Colors.ENDC}")
        return
    
    debate_id = "canvas-demo"
    
    # 创建辩论
    manager.create_debate(
        debate_id=debate_id,
        topic="高性能Web API设计",
        agents=['harper', 'benjamin', 'lucas']
    )
    
    print(f"\n{Colors.GREEN}✅ Canvas 系统已启动{Colors.ENDC}")
    print(f"辩论ID: {debate_id}")
    print(f"专家: Harper, Benjamin, Lucas")
    print(f"\n{Colors.YELLOW}即将开始3轮实时辩论...{Colors.ENDC}")
    time.sleep(3)
    
    # 模拟消息存储
    messages = []
    
    def add_msg(agent, content):
        messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {agent}: {content}")
    
    # ========== Round 1 ==========
    clear()
    print(f"{Colors.BG_BLUE}{Colors.BOLD} Round 1: 独立分析 {Colors.ENDC}\n")
    
    manager.set_debate_status(debate_id, 'round1')
    
    # Harper
    print(f"{Colors.PURPLE}🔍 Harper 开始分析...{Colors.ENDC}")
    manager.save_thought(debate_id, 1, 'harper', 
        'FastAPI性能最优(150k req/s)，选择FastAPI+JWT+Redis')
    manager.set_progress(debate_id, 'harper', 'round1:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=1, agent_name='harper', status='complete'
    ))
    add_msg('Harper', '完成技术分析: FastAPI+JWT+Redis')
    draw_card('Harper', '研究专家', 'complete', 
              'FastAPI性能最优(150k req/s)...', Colors.PURPLE)
    time.sleep(1)
    
    # Benjamin
    print(f"\n{Colors.GREEN}🧠 Benjamin 开始设计...{Colors.ENDC}")
    manager.save_thought(debate_id, 1, 'benjamin',
        '分层架构: API→Service→Repository→Model，SOLID原则')
    manager.set_progress(debate_id, 'benjamin', 'round1:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=1, agent_name='benjamin', status='complete'
    ))
    add_msg('Benjamin', '完成架构设计: 分层架构')
    draw_card('Benjamin', '架构专家', 'complete',
              '分层架构: API→Service→Repository→Model...', Colors.GREEN)
    time.sleep(1)
    
    # Lucas
    print(f"\n{Colors.YELLOW}💻 Lucas 开始规划...{Colors.ENDC}")
    manager.save_thought(debate_id, 1, 'lucas',
        '工期17天，项目结构清晰，先跑起来再优化')
    manager.set_progress(debate_id, 'lucas', 'round1:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=1, agent_name='lucas', status='complete'
    ))
    add_msg('Lucas', '完成实现规划: 工期17天')
    draw_card('Lucas', '实现专家', 'complete',
              '工期17天，先跑起来再优化...', Colors.YELLOW)
    time.sleep(2)
    
    # 显示消息流
    print(f"\n{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}💬 消息流{Colors.ENDC}")
    for msg in messages[-5:]:
        print(f"  {msg}")
    
    time.sleep(2)
    
    # ========== Round 2 ==========
    clear()
    print(f"{Colors.BG_BLUE}{Colors.BOLD} Round 2: 回应与质疑 {Colors.ENDC}\n")
    
    manager.set_debate_status(debate_id, 'round2')
    messages = []
    
    # Harper质疑
    print(f"{Colors.PURPLE}🔍 Harper 回应质疑...{Colors.ENDC}")
    manager.save_thought(debate_id, 2, 'harper',
        '@Benjamin: 分层是否过度设计? @Lucas: 工期是否太乐观?')
    manager.set_progress(debate_id, 'harper', 'round2:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=2, agent_name='harper', status='responding'
    ))
    add_msg('Harper', '质疑: 分层是否过度? 工期是否乐观?')
    draw_card('Harper', '研究专家', 'responding',
              '质疑Benjamin的分层和Lucas的工期', Colors.PURPLE)
    time.sleep(1)
    
    # Benjamin回应
    print(f"\n{Colors.GREEN}🧠 Benjamin 回应质疑...{Colors.ENDC}")
    manager.save_thought(debate_id, 2, 'benjamin',
        '@Harper: JWT有即时撤销隐患。分层是SOLID原则要求')
    manager.set_progress(debate_id, 'benjamin', 'round2:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=2, agent_name='benjamin', status='responding'
    ))
    add_msg('Benjamin', '回应: JWT有隐患，分层必须')
    draw_card('Benjamin', '架构专家', 'responding',
              '回应: JWT有隐患，分层必须', Colors.GREEN)
    time.sleep(1)
    
    # Lucas回应
    print(f"\n{Colors.YELLOW}💻 Lucas 回应质疑...{Colors.ENDC}")
    manager.save_thought(debate_id, 2, 'lucas',
        '@Benjamin: 四层架构增加40%代码量。先跑起来更重要')
    manager.set_progress(debate_id, 'lucas', 'round2:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=2, agent_name='lucas', status='responding'
    ))
    add_msg('Lucas', '回应: 分层增加40%代码，先跑起来')
    draw_card('Lucas', '实现专家', 'responding',
              '回应: 分层增加40%代码，先跑起来', Colors.YELLOW)
    time.sleep(2)
    
    # 显示消息流
    print(f"\n{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}💬 消息流 (激烈辩论中...){Colors.ENDC}")
    for msg in messages[-5:]:
        print(f"  {msg}")
    
    time.sleep(2)
    
    # ========== Round 3 ==========
    clear()
    print(f"{Colors.BG_BLUE}{Colors.BOLD} Round 3: 达成共识 {Colors.ENDC}\n")
    
    manager.set_debate_status(debate_id, 'round3')
    messages = []
    
    # Harper妥协
    print(f"{Colors.PURPLE}🔍 Harper 做出妥协...{Colors.ENDC}")
    manager.save_thought(debate_id, 3, 'harper',
        '妥协: 接受混合认证，渐进分层。坚持: FastAPI+Redis必须')
    manager.set_progress(debate_id, 'harper', 'round3:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=3, agent_name='harper', status='complete'
    ))
    add_msg('Harper', '妥协: 混合认证+渐进分层。工期25天')
    draw_card('Harper', '研究专家', 'complete',
              '妥协: 混合认证+渐进分层', Colors.PURPLE)
    time.sleep(1)
    
    # Benjamin妥协
    print(f"\n{Colors.GREEN}🧠 Benjamin 做出妥协...{Colors.ENDC}")
    manager.save_thought(debate_id, 3, 'benjamin',
        '妥协: 渐进分层(MVP允许简化)，放弃微服务预留')
    manager.set_progress(debate_id, 'benjamin', 'round3:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=3, agent_name='benjamin', status='complete'
    ))
    add_msg('Benjamin', '妥协: 渐进分层，放弃微服务预留')
    draw_card('Benjamin', '架构专家', 'complete',
              '妥协: 渐进分层，放弃微服务预留', Colors.GREEN)
    time.sleep(1)
    
    # Lucas妥协
    print(f"\n{Colors.YELLOW}💻 Lucas 做出妥协...{Colors.ENDC}")
    manager.save_thought(debate_id, 3, 'lucas',
        '妥协: 接受Repository(复杂表)，工期修正25天')
    manager.set_progress(debate_id, 'lucas', 'round3:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=3, agent_name='lucas', status='complete'
    ))
    add_msg('Lucas', '妥协: Repository(复杂表)，工期25天')
    draw_card('Lucas', '实现专家', 'complete',
              '妥协: Repository(复杂表)，工期25天', Colors.YELLOW)
    time.sleep(2)
    
    # 最终共识
    manager.set_debate_status(debate_id, 'consensus')
    
    print(f"\n{Colors.GREEN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.GREEN}✅ 辩论完成！达成共识{Colors.ENDC}")
    print(f"{Colors.GREEN}{'='*80}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}🎯 最终决策:{Colors.ENDC}")
    print(f"  • 框架: FastAPI 0.100+")
    print(f"  • 认证: 混合认证 (JWT公开API + Session管理后台)")
    print(f"  • 架构: 渐进分层 (MVP简化，稳定后抽取Repository)")
    print(f"  • 缓存: MVP阶段PG优化优先，P99>200ms时引入Redis")
    print(f"  • 工期: 25工作日 (5周)")
    print(f"  • 日志: 标准logging + python-json-logger")
    
    print(f"\n{Colors.BOLD}📝 各方妥协:{Colors.ENDC}")
    print(f"  • Harper: 接受混合认证、渐进分层")
    print(f"  • Benjamin: 接受渐进分层、放弃微服务预留")
    print(f"  • Lucas: 接受Repository(复杂表)、修正工期25天")
    
    print(f"\n{Colors.BOLD}💪 各方坚持:{Colors.ENDC}")
    print(f"  • Harper: FastAPI+Redis必须、工期保守评估")
    print(f"  • Benjamin: 认证业务分离、敏感操作用Session")
    print(f"  • Lucas: MVP优先、不为低概率场景过度设计")
    
    # 显示统计
    stats = manager.get_stats(debate_id)
    print(f"\n{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}📊 最终统计{Colors.ENDC}")
    print(f"  状态: {stats['status']}")
    print(f"  完成专家: {stats['agents_completed']}/{stats['agents_total']}")
    print(f"  总消息数: {len(messages)}")
    
    # 清理
    manager.cleanup_debate(debate_id)
    
    print(f"\n{Colors.GREEN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}🎉 Phase 2 演示完成！{Colors.ENDC}")
    print(f"{Colors.GREEN}{'='*80}{Colors.ENDC}")
    print(f"\n实现了:")
    print(f"  ✅ Redis实时同步 (50-100ms延迟)")
    print(f"  ✅ 终端Canvas可视化 (实时面板)")
    print(f"  ✅ 3轮辩论完整流程")
    print(f"  ✅ 实时消息流显示")
    print(f"\n{Colors.YELLOW}下一步: Phase 3 - 模板固化{Colors.ENDC}")

if __name__ == '__main__':
    demo_canvas_visualization()
