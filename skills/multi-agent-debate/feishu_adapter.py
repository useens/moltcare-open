"""
Multi-Agent Debate - 飞书通知适配器
将辩论结果转换为飞书友好的格式
"""
from typing import Dict, List
from datetime import datetime

class FeishuAdapter:
    """飞书消息适配器"""
    
    @staticmethod
    def format_debate_summary(debate_id: str, result: Dict) -> str:
        """格式化辩论结果摘要"""
        
        summary = f"""🎯 **Multi-Agent 辩论完成** #{debate_id}

---

**📊 辩论统计**
• 耗时: {result.get('elapsed', 'N/A')}
• 轮次: 3轮完整辩论
• 专家: Harper + Benjamin + Lucas
• 消息: {result.get('message_count', 0)} 条交互

---

**✅ 最终决策**

| 决策项 | 方案 |
|--------|------|
| 框架 | FastAPI 0.100+ |
| 认证 | JWT(API) + Session(后台) |
| 架构 | 渐进分层 |
| 缓存 | MVP后期引入 |
| 工期 | 25工作日(5周) |

---

**🤝 各方妥协**
• **Harper**: 接受混合认证、渐进分层
• **Benjamin**: 接受渐进分层、放弃微服务预留
• **Lucas**: 接受Repository(复杂表)、工期25天

---

**💪 坚持底线**
• Harper: FastAPI+Redis必须
• Benjamin: 认证业务必须分离
• Lucas: MVP优先，不过度设计

---

**📁 详细报告**
• 技术文档: `skills/multi-agent-debate/results/`
• Canvas面板: http://localhost:5000 (本地)
• 完整记录: Redis `debate:{debate_id}:*`

---

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return summary
    
    @staticmethod
    def format_round_update(round_num: int, agent_updates: List[Dict]) -> str:
        """格式化轮次更新（轻量级通知）"""
        icons = {
            'harper': '🔍',
            'benjamin': '🧠',
            'lucas': '💻'
        }
        
        update_lines = []
        for update in agent_updates:
            agent = update.get('agent', '')
            status = update.get('status', '')
            icon = icons.get(agent.lower(), '👤')
            update_lines.append(f"{icon} {agent}: {status}")
        
        return f"""🔄 **Round {round_num} 更新**

{chr(10).join(update_lines)}

---
⏰ {datetime.now().strftime('%H:%M:%S')}"""
    
    @staticmethod
    def format_consensus_card(consensus: Dict) -> Dict:
        """
        生成飞书交互式卡片格式
        用于更丰富的展示
        """
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "🎯 Multi-Agent 辩论共识"},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**主题**: {consensus.get('topic', 'N/A')}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**最终决策**\n• 框架: FastAPI 0.100+\n• 认证: 混合认证\n• 架构: 渐进分层\n• 工期: 25工作日"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "查看详细报告"},
                            "type": "primary",
                            "value": {"action": "view_debate", "id": consensus.get('debate_id')}
                        }
                    ]
                }
            ]
        }

# 使用示例
if __name__ == "__main__":
    adapter = FeishuAdapter()
    
    # 测试摘要
    result = {
        'elapsed': '4分30秒',
        'message_count': 15,
        'topic': '高性能Web API设计'
    }
    
    summary = adapter.format_debate_summary('demo-001', result)
    print(summary)
    
    # 测试轮次更新
    updates = [
        {'agent': 'Harper', 'status': '完成技术分析'},
        {'agent': 'Benjamin', 'status': '完成架构设计'},
        {'agent': 'Lucas', 'status': '完成实现规划'}
    ]
    
    update_msg = adapter.format_round_update(1, updates)
    print("\n" + "="*50 + "\n")
    print(update_msg)
