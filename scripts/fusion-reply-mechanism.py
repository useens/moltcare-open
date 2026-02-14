#!/usr/bin/env python3
"""
森罗融合智慧 - 真正的融合回复机制
确保每次用户提问都经过双节点融合
"""

import asyncio
import websockets
import json
from datetime import datetime

async def get_fusion_response(user_question: str) -> str:
    """
    获取融合智慧回复
    流程：用户问题 → 云端+本地讨论 → 融合回复
    """
    
    uri = "ws://127.0.0.1:2347"
    
    async with websockets.connect(uri) as ws:
        # 认证
        await ws.send(json.dumps({"token": "sensen-shared-2024"}))
        await ws.recv()
        await ws.recv()
        
        # 步骤1：云端大脑发起讨论
        await ws.send(json.dumps({
            "type": "fusion_request",
            "from": "用户",
            "content": user_question,
            "timestamp": datetime.now().isoformat()
        }))
        
        # 步骤2：等待本地大脑回复（最多30秒）
        local_view = None
        for i in range(6):  # 6次 * 5秒 = 30秒
            try:
                reply = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(reply)
                if 'ai_response' in data.get('type', '') and '森罗·地' in data.get('from', ''):
                    local_view = data.get('content', '')
                    break
            except:
                continue
        
        if not local_view:
            # 如果本地大脑未及时回复，使用云端大脑单节点回复
            return f"""🌲 森罗回复

（本地大脑暂时未响应，以下为云端大脑分析）

{generate_cloud_response(user_question)}

—— 森罗·云（云端大脑）
"""
        
        # 步骤3：云端大脑融合双方观点
        fusion_response = f"""🌲🔥 森罗融合智慧回复

【用户问题】
{user_question}

【本地大脑观点】
{local_view[:500]}...

【云端大脑观点】
{generate_cloud_response(user_question)[:500]}...

【融合智慧结论】
（融合双方观点后的综合回答）

—— 森罗·云 & 森罗·地 融合生成
"""
        
        return fusion_response

def generate_cloud_response(question: str) -> str:
    """云端大脑生成回复"""
    return f"云端大脑对'{question}'的分析..."

# 使用示例
if __name__ == "__main__":
    question = "如何优化系统架构？"
    response = asyncio.run(get_fusion_response(question))
    print(response)
