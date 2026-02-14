#!/usr/bin/env python3
"""
森罗智能路由系统
让用户可以通过主节点与双节点"对话"
实现：智能分配问题给最适合的节点回答
"""

import asyncio
import websockets
import json
from datetime import datetime
from typing import Dict, List, Optional

class IntelligentRouter:
    """
    智能路由系统
    自动判断问题应该由哪个节点回答
    """
    
    def __init__(self):
        self.cloud_node = {
            "name": "森罗·云",
            "title": "云端大脑",
            "expertise": [
                "战略分析", "市场洞察", "生态评估",
                "情报收集", "竞争分析", "趋势预测",
                "对外连接", "API服务", "全局协调"
            ],
            "keywords": [
                "战略", "市场", "生态", "趋势", "竞争",
                "情报", "对外", "全局", "协调", "规划"
            ]
        }
        
        self.local_node = {
            "name": "森罗·地",
            "title": "本地大脑",
            "expertise": [
                "技术实现", "性能优化", "架构设计",
                "代码实现", "资源管理", "本地执行",
                "细节把控", "实验验证", "故障排查"
            ],
            "keywords": [
                "技术", "实现", "性能", "优化", "代码",
                "架构", "资源", "本地", "细节", "执行"
            ]
        }
        
        # 问题分类规则
        self.routing_rules = {
            "cloud_only": {
                "patterns": [
                    r"竞争.*(对手|分析|策略)",
                    r"市场.*(趋势|定位|规模)",
                    r"生态.*(建设|发展|整合)",
                    r"情报.*(收集|分析|扫描)",
                    r"战略.*(规划|方向|目标)",
                    r"对外.*(连接|服务|API)"
                ],
                "examples": [
                    "分析一下NanoClaw的竞争策略",
                    "MCP协议的市场趋势如何？",
                    "我们应该怎么建设技能生态？"
                ]
            },
            "local_only": {
                "patterns": [
                    r"代码.*(实现|优化|问题)",
                    r"性能.*(提升|优化|瓶颈)",
                    r"架构.*(设计|调整|重构)",
                    r"资源.*(使用|优化|管理)",
                    r"本地.*(执行|部署|配置)",
                    r"技术.*(选型|实现|细节)"
                ],
                "examples": [
                    "向量检索性能怎么优化？",
                    "这个代码实现有问题吗？",
                    "本地8核怎么充分利用？"
                ]
            },
            "fusion_both": {
                "patterns": [
                    r"(系统|架构).*(优化|设计)",
                    r"(方案|策略).*(评估|选择)",
                    r"(问题|挑战).*(解决|应对)",
                    r"(功能|特性).*(开发|实现)",
                    r"(安全|风险).*(评估|处理)"
                ],
                "examples": [
                    "如何优化我们的系统架构？",
                    "这个方案应该选择A还是B？",
                    "怎么解决当前的安全问题？"
                ]
            }
        }
    
    def analyze_question(self, question: str) -> Dict:
        """
        分析问题，判断应该由哪个节点回答
        """
        question_lower = question.lower()
        
        # 初始化分数
        cloud_score = 0
        local_score = 0
        
        # 关键词匹配
        for keyword in self.cloud_node["keywords"]:
            if keyword in question_lower:
                cloud_score += 1
        
        for keyword in self.local_node["keywords"]:
            if keyword in question_lower:
                local_score += 1
        
        # 判断路由
        if cloud_score > local_score + 2:
            route_to = "cloud"
            confidence = min(cloud_score / 5, 1.0)
        elif local_score > cloud_score + 2:
            route_to = "local"
            confidence = min(local_score / 5, 1.0)
        else:
            route_to = "fusion"
            confidence = 0.8
        
        return {
            "route_to": route_to,
            "cloud_score": cloud_score,
            "local_score": local_score,
            "confidence": confidence,
            "reason": self._get_routing_reason(route_to, cloud_score, local_score)
        }
    
    def _get_routing_reason(self, route_to: str, cloud_score: int, local_score: int) -> str:
        """获取路由原因"""
        if route_to == "cloud":
            return f"涉及战略/生态/情报，云端大脑更专业 (匹配度: {cloud_score})"
        elif route_to == "local":
            return f"涉及技术/实现/性能，本地大脑更专业 (匹配度: {local_score})"
        else:
            return f"需要战略+技术双角度，融合回答最佳 (云端:{cloud_score}, 本地:{local_score})"
    
    def generate_routed_response(self, question: str, route_analysis: Dict) -> str:
        """
        生成路由后的响应框架
        """
        route_to = route_analysis["route_to"]
        
        if route_to == "cloud":
            return f"""🌤️ [云端大脑回答]

**路由分析**: {route_analysis['reason']}

---

[云端大脑的观点和分析]

---

*如需本地大脑的技术实现细节，请告诉我*"""
        
        elif route_to == "local":
            return f"""🖥️ [本地大脑回答]

**路由分析**: {route_analysis['reason']}

---

[本地大脑的技术分析和方案]

---

*如需云端大脑的战略评估，请告诉我*"""
        
        else:  # fusion
            return f"""🌲🔥 [融合智慧回答]

**路由分析**: {route_analysis['reason']}

---

## 云端大脑观点

[战略/生态角度的分析]

## 本地大脑观点

[技术/实现角度的分析]

## 融合智慧结论

[综合双方观点后的最终建议]

---

*云端大脑 + 本地大脑 = 融合智慧*"""
    
    async def route_to_standby(self, question: str) -> str:
        """
        将问题路由给备用节点，并返回其回答
        """
        uri = "ws://127.0.0.1:2347"
        
        try:
            async with websockets.connect(uri, timeout=10) as ws:
                # 认证
                await ws.send(json.dumps({"token": "sensen-shared-2024"}))
                await ws.recv()
                await ws.recv()
                
                # 发送问题给备用节点
                await ws.send(json.dumps({
                    "type": "user_question_routed",
                    "from": "森罗·云 (智能路由)",
                    "to": "森罗·地",
                    "question": question,
                    "route_reason": "用户问题更适合本地大脑回答",
                    "timestamp": datetime.now().isoformat()
                }))
                
                # 等待备用节点回复
                try:
                    reply = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(reply)
                    return data.get("content", "本地大脑暂无回复")
                except asyncio.TimeoutError:
                    return "⏳ 本地大脑正在思考中..."
                    
        except Exception as e:
            return f"⚠️ 与本地大脑通信异常: {e}"
    
    def get_help_message(self) -> str:
        """
        获取智能路由帮助信息
        """
        return """🌲🔥 森罗智能路由系统

**系统说明**:
我会自动分析问题，选择最适合的节点回答：

🌤️ **云端大脑 (森罗·云)** - 适合问题：
- 战略规划、市场分析
- 生态建设、竞争情报
- 趋势预测、对外连接
- 示例："分析一下竞品策略" / "MCP市场趋势如何？"

🖥️ **本地大脑 (森罗·地)** - 适合问题：
- 技术实现、代码优化
- 性能调优、架构设计
- 资源管理、本地执行
- 示例："向量检索怎么优化？" / "代码有问题吗？"

🌲🔥 **融合智慧 (双节点)** - 适合问题：
- 系统优化、方案选择
- 问题解决、策略制定
- 需要多角度综合分析
- 示例："如何优化系统架构？" / "这个方案怎么选？"

**特殊指令**：
- @云 - 强制由云端大脑回答
- @地 - 强制由本地大脑回答
- @融合 - 强制融合回答

**让两个大脑协作，为您提供最佳答案！**
"""

# 路由决策示例
if __name__ == "__main__":
    router = IntelligentRouter()
    
    print("🌲🔥 森罗智能路由系统")
    print("====================")
    print()
    
    # 测试问题路由
    test_questions = [
        "分析一下NanoClaw的竞争策略",
        "向量检索性能怎么优化？",
        "如何优化我们的系统架构？",
        "MCP协议的市场趋势如何？",
        "本地8核怎么充分利用？",
        "这个安全漏洞怎么处理？"
    ]
    
    print("📋 智能路由测试:")
    print()
    
    for question in test_questions:
        analysis = router.analyze_question(question)
        
        route_emoji = {
            "cloud": "🌤️",
            "local": "🖥️",
            "fusion": "🌲🔥"
        }.get(analysis["route_to"], "❓")
        
        print(f"Q: {question}")
        print(f"   → {route_emoji} 路由到: {analysis['route_to'].upper()}")
        print(f"      原因: {analysis['reason']}")
        print(f"      置信度: {analysis['confidence']:.0%}")
        print()
    
    print("====================")
    print("✅ 智能路由系统已就绪！")
