"""
Polymarket 飞书通知模块
集成飞书消息API，发送预警通知
"""

import requests
import json
import logging
from typing import List
from polymarket_monitor import MarketEvent

logger = logging.getLogger(__name__)


class FeishuNotifier:
    """飞书消息通知器"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        # 从配置文件加载或使用传入的URL
        self.webhook_url = webhook_url or self._load_webhook()
        self.user_id = "ou_dc4db246fa540096f42caefbd2112ed3"  # 默认用户ID
    
    def _load_webhook(self) -> str:
        """从配置文件加载webhook"""
        try:
            with open("config/feishu_webhook.json") as f:
                config = json.load(f)
                return config.get("webhook_url", "")
        except:
            return ""
    
    def send_alert_card(self, events: List[MarketEvent]):
        """发送富文本卡片预警"""
        if not events:
            return
        
        # 构建卡片内容
        elements = []
        
        for i, event in enumerate(events[:5], 1):  # 最多显示5个
            direction = "📈" if event.probability > event.previous_probability else "📉"
            change = f"+{event.change_percent:.1f}%" if event.probability > event.previous_probability else f"-{event.change_percent:.1f}%"
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{i}. {direction} {change}**  {event.title[:40]}...\n"
                              f"概率: {event.previous_probability:.1f}% → **{event.probability:.1f}%**\n"
                              f"类别: {event.category} | 交易量: ${event.volume/1000:.0f}K"
                }
            })
            elements.append({"tag": "hr"})
        
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🚨 Polymarket 概率飙升预警 ({len(events)}个事件)"
                    },
                    "template": "red"
                },
                "elements": elements
            }
        }
        
        self._send(card)
    
    def send_text_message(self, message: str):
        """发送纯文本消息"""
        payload = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        self._send(payload)
    
    def send_accuracy_report(self, stats: dict):
        """发送准确率报告"""
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "📊 Polymarket 预测准确率统计"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**累计准确率: {stats['accuracy_rate']:.1f}%**\n\n"
                                      f"• 总预警次数: {stats['total_alerts']}\n"
                                      f"• 已解决预测: {stats['resolved_predictions']}\n"
                                      f"• 正确预测: {stats['correct_predictions']}\n"
                                      f"• 最后更新: {stats['updated_at'][:19]}"
                        }
                    }
                ]
            }
        }
        self._send(card)
    
    def _send(self, payload: dict):
        """发送请求"""
        if not self.webhook_url:
            logger.warning("飞书webhook未配置")
            return
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            logger.info("飞书消息发送成功")
        except Exception as e:
            logger.error(f"飞书消息发送失败: {e}")


# 全局通知器实例
_notifier: Optional[FeishuNotifier] = None


def init_notifier(webhook_url: Optional[str] = None):
    """初始化通知器"""
    global _notifier
    _notifier = FeishuNotifier(webhook_url)
    return _notifier


def send_alerts(events: List[MarketEvent]):
    """发送预警（便捷函数）"""
    if _notifier:
        _notifier.send_alert_card(events)


def send_accuracy(stats: dict):
    """发送准确率（便捷函数）"""
    if _notifier:
        _notifier.send_accuracy_report(stats)
