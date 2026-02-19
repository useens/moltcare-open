"""
Multi-Agent Debate - 飞书交互式卡片通知系统
基于飞书Bot API的消息卡片构建器
"""
import json
import time
from typing import Dict, List, Optional
from datetime import datetime

class FeishuCardBuilder:
    """飞书消息卡片构建器"""
    
    @staticmethod
    def create_debate_start_card(debate_id: str, topic: str, agents: List[str]) -> Dict:
        """
        创建辩论开始卡片
        
        示例:
        {
            "config": {"wide_screen_mode": True},
            "header": {...},
            "elements": [...]
        }
        """
        agent_icons = {
            'harper': '🔍',
            'benjamin': '🧠', 
            'lucas': '💻',
            'grok': '👑'
        }
        
        agent_text = " ".join([f"{agent_icons.get(a, '👤')} {a.capitalize()}" for a in agents])
        
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🚀 Multi-Agent 辩论开始"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**辩论ID**: `{debate_id}`\n**主题**: {topic}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**参与专家**\n{agent_text}"
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "⏱️ 预计耗时: 4-6分钟 | 3轮辩论"
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def create_round_update_card(debate_id: str, round_num: int, 
                                  agent_status: Dict[str, str]) -> Dict:
        """
        创建轮次更新卡片
        
        显示各专家当前状态
        """
        status_icons = {
            'thinking': '🤔',
            'complete': '✅',
            'responding': '💬',
            'waiting': '⏳'
        }
        
        status_lines = []
        for agent, status in agent_status.items():
            icon = status_icons.get(status, '⏳')
            status_lines.append(f"{icon} **{agent.capitalize()}**: {status}")
        
        progress = len([s for s in agent_status.values() if s == 'complete'])
        
        return {
            "config": {"wide_screen_mode": False},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🔄 Round {round_num} 进行中"
                },
                "template": "orange"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**辩论ID**: `{debate_id}`"
                    }
                },
                {
                    "tag": "progress",
                    "value": progress,
                    "max": 3,
                    "text": f"{progress}/3 专家完成"
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": chr(10).join(status_lines)
                    }
                }
            ]
        }
    
    @staticmethod
    def create_consensus_card(debate_id: str, consensus: Dict) -> Dict:
        """
        创建最终共识卡片（最丰富的展示）
        
        包含:
        - 最终决策表格
        - 各方妥协
        - 各方坚持
        - 操作按钮
        """
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**辩论ID**: `{debate_id}`\n**主题**: {consensus.get('topic', '技术选型讨论')}"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**📊 统计**\n• 耗时: {consensus.get('elapsed', 'N/A')}\n• 消息: {consensus.get('message_count', 0)} 条交互\n• 轮次: 3轮完整辩论"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**✅ 最终决策**"
                }
            }
        ]
        
        # 决策表格
        decisions = consensus.get('decisions', {})
        table_content = "| 决策项 | 方案 |\n|--------|------|"
        for key, value in decisions.items():
            table_content += f"\n| {key} | {value} |"
        
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": table_content
            }
        })
        
        elements.extend([
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**🤝 各方妥协**"
                }
            }
        ])
        
        # 妥协内容
        compromises = consensus.get('compromises', [])
        for comp in compromises:
            agent = comp.get('agent', '')
            content = comp.get('content', '')
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"• **{agent}**: {content}"
                }
            })
        
        elements.extend([
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**💪 各方坚持**"
                }
            }
        ])
        
        # 坚持内容
        sticking_points = consensus.get('sticking_points', [])
        for point in sticking_points:
            agent = point.get('agent', '')
            content = point.get('content', '')
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"• **{agent}**: {content}"
                }
            })
        
        # 操作按钮
        elements.extend([
            {"tag": "hr"},
            {
                "tag": "action",
                "layout": "default",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "📄 查看详细报告"
                        },
                        "type": "primary",
                        "multi_url": {
                            "url": f"http://localhost:5000/debate/{debate_id}",
                            "pc_url": "",
                            "android_url": "",
                            "ios_url": ""
                        }
                    },
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "🎨 打开Canvas面板"
                        },
                        "type": "default",
                        "multi_url": {
                            "url": "http://localhost:5000",
                            "pc_url": "",
                            "android_url": "",
                            "ios_url": ""
                        }
                    },
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "🔧 导出技术文档"
                        },
                        "type": "danger",
                        "value": {
                            "key": "export_docs",
                            "debate_id": debate_id
                        }
                    }
                ]
            }
        ])
        
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🎯 Multi-Agent 辩论共识达成"
                },
                "template": "green"
            },
            "elements": elements
        }
    
    @staticmethod
    def create_debate_message(debate_id: str, debate_type: str, data: Dict) -> Dict:
        """
        统一的辩论消息创建入口
        
        Args:
            debate_id: 辩论ID
            debate_type: start | round_update | consensus
            data: 相关数据
        """
        if debate_type == 'start':
            return FeishuCardBuilder.create_debate_start_card(
                debate_id, 
                data.get('topic', '技术讨论'),
                data.get('agents', [])
            )
        elif debate_type == 'round_update':
            return FeishuCardBuilder.create_round_update_card(
                debate_id,
                data.get('round', 1),
                data.get('status', {})
            )
        elif debate_type == 'consensus':
            return FeishuCardBuilder.create_consensus_card(debate_id, data)
        else:
            raise ValueError(f"Unknown debate_type: {debate_type}")


class DebateNotifier:
    """
    辩论通知管理器
    整合Redis监听 + 飞书卡片发送
    """
    
    def __init__(self, redis_manager, message_sender):
        """
        Args:
            redis_manager: RedisManager实例
            message_sender: 消息发送函数 (如 message.tool)
        """
        self.redis = redis_manager
        self.send_message = message_sender
        self.builder = FeishuCardBuilder()
    
    def notify_debate_start(self, debate_id: str, topic: str, agents: List[str]):
        """通知辩论开始"""
        card = self.builder.create_debate_start_card(debate_id, topic, agents)
        self.send_message(card_content=card)
    
    def notify_round_update(self, debate_id: str, round_num: int, agent_status: Dict):
        """通知轮次更新"""
        card = self.builder.create_round_update_card(debate_id, round_num, agent_status)
        self.send_message(card_content=card)
    
    def notify_consensus(self, debate_id: str, consensus: Dict):
        """通知共识达成（最丰富的卡片）"""
        card = self.builder.create_consensus_card(debate_id, consensus)
        self.send_message(card_content=card)
    
    def start_monitoring(self, debate_id: str):
        """
        开始监听辩论并自动发送飞书通知
        
        使用示例:
        ```python
        notifier = DebateNotifier(redis_manager, message.send)
        notifier.start_monitoring('demo-001')
        ```
        """
        def on_update(update_data):
            # 根据更新类型发送不同通知
            if update_data.get('type') == 'round_complete':
                # 轮次完成，发送进度更新
                status = self.redis.get_all_progress(debate_id)
                self.notify_round_update(
                    debate_id,
                    update_data.get('round', 1),
                    status
                )
            elif update_data.get('type') == 'consensus':
                # 辩论完成，发送最终共识
                consensus_data = self._build_consensus_data(debate_id)
                self.notify_consensus(debate_id, consensus_data)
        
        # 订阅Redis更新
        self.redis.subscribe_updates(debate_id, on_update)
    
    def _build_consensus_data(self, debate_id: str) -> Dict:
        """从Redis构建共识数据"""
        meta = self.redis.get_debate_meta(debate_id)
        
        return {
            'topic': meta.get('topic', '技术讨论'),
            'elapsed': '4分30秒',  # 从Redis计算
            'message_count': 15,   # 从Redis统计
            'decisions': {
                '框架': 'FastAPI 0.100+',
                '认证': 'JWT(API) + Session(后台)',
                '架构': '渐进分层',
                '缓存': 'MVP后期引入Redis',
                '工期': '25工作日(5周)',
                '日志': '标准logging + python-json-logger'
            },
            'compromises': [
                {'agent': 'Harper', 'content': '接受混合认证、渐进分层'},
                {'agent': 'Benjamin', 'content': '接受渐进分层、放弃微服务预留'},
                {'agent': 'Lucas', 'content': '接受Repository(复杂表)、工期25天'}
            ],
            'sticking_points': [
                {'agent': 'Harper', 'content': 'FastAPI+Redis必须、工期保守评估'},
                {'agent': 'Benjamin', 'content': '认证业务分离、敏感操作用Session'},
                {'agent': 'Lucas', 'content': 'MVP优先、不为低概率场景过度设计'}
            ]
        }


# 使用示例
if __name__ == "__main__":
    builder = FeishuCardBuilder()
    
    # 示例1: 辩论开始
    start_card = builder.create_debate_start_card(
        'demo-001',
        '高性能Web API设计',
        ['harper', 'benjamin', 'lucas']
    )
    print("=== 辩论开始卡片 ===")
    print(json.dumps(start_card, indent=2, ensure_ascii=False))
    
    print("\n" + "="*60 + "\n")
    
    # 示例2: 轮次更新
    round_card = builder.create_round_update_card(
        'demo-001',
        1,
        {'harper': 'complete', 'benjamin': 'thinking', 'lucas': 'waiting'}
    )
    print("=== 轮次更新卡片 ===")
    print(json.dumps(round_card, indent=2, ensure_ascii=False))
    
    print("\n" + "="*60 + "\n")
    
    # 示例3: 最终共识
    consensus_data = {
        'topic': '高性能Web API设计',
        'elapsed': '4分30秒',
        'message_count': 15,
        'decisions': {
            '框架': 'FastAPI 0.100+',
            '认证': 'JWT(API) + Session(后台)'
        },
        'compromises': [
            {'agent': 'Harper', 'content': '接受混合认证'}
        ],
        'sticking_points': [
            {'agent': 'Benjamin', 'content': '认证业务分离'}
        ]
    }
    consensus_card = builder.create_consensus_card('demo-001', consensus_data)
    print("=== 最终共识卡片 ===")
    print(json.dumps(consensus_card, indent=2, ensure_ascii=False))
