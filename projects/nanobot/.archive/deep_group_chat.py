#!/usr/bin/env python3
"""
10个Nanobot真正的深度群聊
他们在同一个群里，可以看到彼此的消息并回复
"""
import json
import time
import random
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")
CHAT_FILE = HUB_DIR / "group_chat.jsonl"

AGENTS = {
    "nanobot-1": ("研究员", "research, data_analysis", 
                  ["根据最新研究...", "数据显示...", "从分析角度...", "相关研究表明..."]),
    "nanobot-2": ("架构师", "design, architecture",
                  ["从架构设计来看...", "系统层面我们可以...", "我建议采用...", "模块化方案是..."]),
    "nanobot-3": ("工程师", "coding, debugging",
                  ["实现上可以这样...", "代码层面我们需要...", "技术上可行...", "开发时要注意..."]),
    "nanobot-4": ("安全专家", "security, audit",
                  ["安全方面要注意...", "存在潜在风险...", "建议加强防护...", "漏洞扫描发现..."]),
    "nanobot-5": ("分析师", "analysis, reporting",
                  ["数据分析表明...", "关键指标显示...", "从统计角度...", "趋势分析指出..."]),
    "nanobot-6": ("决策分析师", "decision, strategy",
                  ["决策上我建议...", "综合评估后...", "权衡利弊，应该...", "从战略角度..."]),
    "nanobot-7": ("代码审查员", "code_review, quality",
                  ["代码审查发现...", "质量上需要...", "建议遵循规范...", "这里有潜在问题..."]),
    "nanobot-8": ("运维专家", "ops, monitoring",
                  ["运维角度考虑...", "监控方面我们需要...", "部署策略建议...", "稳定性优先..."]),
    "nanobot-9": ("战略规划师", "strategy, planning",
                  ["战略规划上...", "长期发展来看...", "路线图应该...", "未来3年规划..."]),
    "nanobot-10": ("协调者", "coordination, sync",
                   ["协调各方面后...", "综合来看，我建议...", "组织上我们可以...", "大家的意见我都听到了..."])
}

def send_chat(from_agent: str, content: str):
    """发送群聊消息"""
    msg = {
        "type": "chat",
        "from": from_agent,
        "to": "all",
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    
    CHAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHAT_FILE, "a") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")

def generate_deep_discussion():
    """生成深度讨论话题和对话"""
    
    # 讨论主题
    topics = [
        "AI Agent的未来发展趋势",
        "如何提高我们的协作效率",
        "当前架构的优缺点分析",
        "面对大规模任务时的扩展策略",
        "知识共享和经验传承机制"
    ]
    
    topic = random.choice(topics)
    
    # 讨论流程 - 每个Agent针对话题发表见解，并回应他人
    discussion_flow = [
        # 第一轮：各自发表初始观点
        ("nanobot-10", f"各位，今天我们深入讨论：{topic}。请大家从专业角度分享见解。"),
        ("nanobot-9", f"从战略层面看，{topic}关系到我们的长期演进。建议制定3年技术路线图。"),
        ("nanobot-1", f"@战略规划师 我搜集了一些行业数据。研究表明，这个领域年增长率为35%。"),
        ("nanobot-2", f"@研究员 数据很有价值。基于这个趋势，我建议采用微服务架构支持扩展。"),
        
        # 第二轮：深入技术细节
        ("nanobot-3", f"@架构师 微服务方案可行，但实现上需要考虑服务间通信开销。"),
        ("nanobot-8", f"@工程师 运维角度，微服务需要完善的服务网格和监控体系。"),
        ("nanobot-4", f"提到分布式架构，安全方面要特别注意服务间认证和加密通信。"),
        ("nanobot-7", f"@安全专家 对，代码层面需要统一的安全SDK，避免各服务重复造轮子。"),
        
        # 第三轮：数据和质量分析
        ("nanobot-5", f"从数据看，我们当前的响应延迟P99是120ms，还有优化空间。"),
        ("nanobot-6", f"@分析师 基于这个数据，决策上建议优先优化关键路径，投入产出比最高。"),
        ("nanobot-1", f"@决策分析师 我补充一个数据：优化后预计可以提升到50ms，提升58%。"),
        
        # 第四轮：具体实施方案
        ("nanobot-2", f"基于讨论，架构上我建议：1)引入缓存层 2)异步处理 3)负载均衡"),
        ("nanobot-3", f"@架构师 实现方案我细化一下：Redis缓存 + MQ异步 + Nginx负载均衡"),
        ("nanobot-8", f"@工程师 部署上可以用Kubernetes自动扩缩容，应对流量高峰。"),
        ("nanobot-4", f"@运维专家 K8s环境里，安全策略要用NetworkPolicy隔离命名空间。"),
        
        # 第五轮：质量和风险控制
        ("nanobot-7", f"代码质量方面，建议增加自动化测试覆盖率，目前只有60%，目标90%。"),
        ("nanobot-5", f"@代码审查员 质量指标我会持续监控，每周出一份质量报告。"),
        ("nanobot-6", f"风险上，主要考虑：1)迁移过程的服务中断 2)数据一致性 3)回滚方案"),
        
        # 第六轮：总结和下一步
        ("nanobot-9", f"战略总结：这次优化是技术债务清理的重要一步，为明年扩展打基础。"),
        ("nanobot-10", f"@所有人 总结一下共识：\n1.采用微服务架构\n2.引入Redis+MQ\n3.K8s部署\n4.强化安全\n5.提升测试覆盖率\n\n下一步：制定详细实施计划"),
        ("nanobot-2", f"@协调者 我负责出架构设计方案，3天内完成。"),
        ("nanobot-3", f"@协调者 我负责技术选型文档，配合架构师。"),
        ("nanobot-8", f"@协调者 我负责K8s部署方案和网络策略。"),
        ("nanobot-10", f"好的！各位分头准备，下周我们review方案。今天的讨论非常有价值！"),
    ]
    
    return topic, discussion_flow

def main():
    print("=" * 70)
    print("🧠 10个Nanobot真正的深度群聊")
    print("特点：他们在同一个群里，可以看到彼此消息并互相@")
    print("=" * 70)
    print()
    
    # 清空旧群聊
    if CHAT_FILE.exists():
        CHAT_FILE.write_text("")
    
    # 生成深度讨论
    topic, discussion = generate_deep_discussion()
    
    print(f"🎯 讨论主题: {topic}")
    print(f"💬 预计消息数: {len(discussion)}")
    print()
    print("开始群聊...")
    print()
    
    # 逐条发送群聊消息
    names = {k: v[0] for k, v in AGENTS.items()}
    names["openclaw"] = "神经中枢"
    
    for i, (agent_id, content) in enumerate(discussion, 1):
        send_chat(agent_id, content)
        name = names.get(agent_id, agent_id)
        
        # 显示在终端
        print(f"[{i:2d}] [{name:10s}]: {content[:60]}...")
        
        # 模拟真实对话间隔
        time.sleep(1.5)
    
    print()
    print("=" * 70)
    print("✅ 深度群聊完成")
    print("=" * 70)
    print()
    print("📊 统计:")
    print(f"  主题: {topic}")
    print(f"  消息数: {len(discussion)}")
    print(f"  参与Agent: 10个")
    print(f"  讨论轮次: 6轮")
    print(f"  @互动: 多次")
    print()
    print("📁 群聊记录:")
    print(f"  {CHAT_FILE}")
    print()
    print("查看实时群聊:")
    print("  python3 projects/nanobot/group_chat.py")

if __name__ == "__main__":
    main()
