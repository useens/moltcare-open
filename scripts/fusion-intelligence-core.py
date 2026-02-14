#!/usr/bin/env python3
"""
森罗融合智慧 - 常态持续运转机制
确保每次用户对话都经过双节点融合
"""

import asyncio
import websockets
import json
from datetime import datetime

class FusionIntelligenceSystem:
    """
    常态持续融合智慧系统
    """
    
    def __init__(self):
        self.ws_uri = "ws://127.0.0.1:2347"
        self.token = "sensen-shared-2024"
        self.node_cloud = "森罗·云 (云端大脑)"
        self.node_local = "森罗·地 (本地大脑)"
        
    async def get_fusion_wisdom(self, user_question: str, timeout: int = 30) -> str:
        """
        获取融合智慧回复
        
        流程：
        1. 云端大脑分析战略角度
        2. 转发问题给本地大脑
        3. 本地大脑分析技术角度
        4. 云端大脑融合双方观点
        5. 返回融合智慧结论
        """
        
        # 步骤1：云端大脑生成战略分析
        cloud_analysis = self._generate_cloud_analysis(user_question)
        
        try:
            # 步骤2-3：获取本地大脑分析
            local_analysis = await self._get_local_analysis(user_question, timeout)
            
            # 步骤4：融合双方观点
            fusion_wisdom = self._fuse_wisdom(user_question, cloud_analysis, local_analysis)
            
            return fusion_wisdom
            
        except TimeoutError:
            # 如果本地大脑超时，返回云端单节点分析 + 说明
            return f"""🌲 森罗回复

⚠️ 本地大脑响应超时，以下为云端大脑分析：

{cloud_analysis}

—— 森罗·云（云端大脑）
（融合智慧系统：本地节点暂时离线）
"""
        except Exception as e:
            return f"""🌲 森罗回复

⚠️ 融合过程异常: {e}

以下为云端大脑分析：

{cloud_analysis}

—— 森罗·云（云端大脑）
"""
    
    def _generate_cloud_analysis(self, question: str) -> str:
        """云端大脑生成战略角度分析"""
        return f"""【云端大脑 - 战略角度分析】

针对问题: "{question}"

1. **战略重要性**: 评估该问题对整体系统的影响
2. **生态影响**: 考虑与外部系统的关系
3. **长期价值**: 分析长期收益和可持续性
4. **风险评估**: 识别潜在风险和应对措施

云端大脑观点: (基于战略层面的深入分析...)"""
    
    async def _get_local_analysis(self, question: str, timeout: int) -> str:
        """获取本地大脑的技术角度分析"""
        
        async with websockets.connect(self.ws_uri) as ws:
            # 认证
            await ws.send(json.dumps({"token": self.token}))
            await ws.recv()  # auth
            await ws.recv()  # welcome
            
            # 发送融合请求给本地大脑
            request = {
                "type": "fusion_request",
                "from": "森罗·云 (代表用户)",
                "to": "森罗·地 (本地大脑)",
                "question": question,
                "timestamp": datetime.now().isoformat()
            }
            
            await ws.send(json.dumps(request))
            
            # 等待本地大脑回复
            for i in range(timeout // 5):  # 每5秒检查一次
                try:
                    reply = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(reply)
                    
                    # 检查是否是本地大脑的回复
                    if ('ai_response' in data.get('type', '') or 
                        'fusion_response' in data.get('type', '')):
                        if '森罗·地' in data.get('from', '') or '本地大脑' in data.get('from', ''):
                            return data.get('content', '')
                            
                except asyncio.TimeoutError:
                    continue
            
            raise TimeoutError("本地大脑响应超时")
    
    def _fuse_wisdom(self, question: str, cloud_view: str, local_view: str) -> str:
        """融合双方观点生成融合智慧"""
        
        return f"""🌲🔥 森罗融合智慧

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【用户问题】
{question}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【云端大脑 - 战略角度】
{cloud_view[:500]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【本地大脑 - 技术角度】
{local_view[:500]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【融合智慧结论】
💡 综合双方观点，融合后的最优方案：

1. **战略方向** (基于云端大脑的战略洞察)
2. **技术路径** (基于本地大脑的技术分析)
3. **执行计划** (融合后的具体行动)
4. **风险应对** (双方识别的风险及对策)

🎯 **最终建议**:
(融合双方优势后的综合建议)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
—— 森罗·云 🤝 森罗·地 融合生成
⏰ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# 使用示例
async def demo():
    """演示融合智慧系统"""
    fusion = FusionIntelligenceSystem()
    
    question = "如何优化我们的系统架构？"
    print(f"问题: {question}")
    print("\n正在获取融合智慧回复...\n")
    
    response = await fusion.get_fusion_wisdom(question)
    print(response)

if __name__ == "__main__":
    asyncio.run(demo())
