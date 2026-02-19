#!/usr/bin/env python3
"""
Multi-Agent Debate - 快速启动脚本
一键运行辩论
"""
import sys
import argparse
from pathlib import Path

# 添加到路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.multi_agent_debate import MultiAgentDebate, Agent, AgentRole, quick_debate

def main():
    parser = argparse.ArgumentParser(
        description='Multi-Agent Debate System - 多智能体辩论系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认专家运行辩论
  python quickstart.py "选择数据库：PostgreSQL vs MySQL"
  
  # 自定义专家
  python quickstart.py "技术选型" --agents "架构师,工程师,产品经理"
  
  # 指定辩论ID
  python quickstart.py "框架选择" --id "framework-debate-001"
  
  # 快速模式（简化输出）
  python quickstart.py "缓存策略" --quick
        """
    )
    
    parser.add_argument('topic', help='辩论主题')
    parser.add_argument('--id', '-i', help='辩论ID（可选，自动生成）')
    parser.add_argument('--agents', '-a', help='自定义专家，逗号分隔（如：架构师,工程师,产品经理）')
    parser.add_argument('--quick', '-q', action='store_true', help='快速模式，只输出最终结果')
    parser.add_argument('--rounds', '-r', type=int, default=3, help='辩论轮次（默认3）')
    parser.add_argument('--timeout', '-t', type=int, default=120, help='每轮超时时间（秒，默认120）')
    
    args = parser.parse_args()
    
    print("🚀 Multi-Agent Debate System")
    print("=" * 60)
    print(f"主题: {args.topic}")
    print(f"轮次: {args.rounds}")
    print("=" * 60)
    
    # 配置专家
    if args.agents:
        agent_names = [name.strip() for name in args.agents.split(',')]
        agents = [
            Agent(name, AgentRole.CUSTOM, f"{name}专家")
            for name in agent_names
        ]
        print(f"自定义专家: {', '.join(agent_names)}")
    else:
        agents = None  # 使用默认专家
        print("使用默认专家: Harper, Benjamin, Lucas")
    
    print("-" * 60)
    print("辩论进行中...\n")
    
    # 运行辩论
    try:
        if args.quick:
            # 快速模式
            result = quick_debate(
                topic=args.topic,
                debate_id=args.id,
                agents=agents,
                rounds=args.rounds,
                timeout_per_round=args.timeout
            )
        else:
            # 完整模式
            debate = MultiAgentDebate(
                topic=args.topic,
                debate_id=args.id,
                agents=agents,
                rounds=args.rounds,
                timeout_per_round=args.timeout
            )
            
            # 注册回调显示进度
            def on_round_complete(round_num, data):
                print(f"✅ Round {round_num} 完成")
            
            debate.register_callback('round_complete', on_round_complete)
            result = debate.start()
            debate.cleanup()
        
        # 输出结果
        print("\n" + "=" * 60)
        print("🎉 辩论完成！")
        print("=" * 60)
        
        print(f"\n📊 统计:")
        print(f"  辩论ID: {result['debate_id']}")
        print(f"  耗时: {result['elapsed']}")
        print(f"  状态: {result['status']}")
        
        consensus = result.get('consensus', {})
        if consensus:
            print(f"\n✅ 最终决策:")
            decisions = consensus.get('decisions', {})
            for key, value in decisions.items():
                print(f"  • {key}: {value}")
            
            print(f"\n🤝 各方妥协:")
            for comp in consensus.get('compromises', []):
                print(f"  • {comp['agent']}: {comp['content']}")
        
        print("\n" + "=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  辩论被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
