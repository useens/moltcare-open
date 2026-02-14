#!/usr/bin/env python3
"""
WebSocket Bridge 测试脚本
验证两端通信是否正常
"""

import asyncio
import json
import sys
import time
from datetime import datetime

async def test_echo():
    """测试回声通信"""
    import websockets
    
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
    client_id = "test-client"
    token = "sensen-bridge-2024"
    
    print(f"🔌 连接到 {uri}...")
    
    try:
        async with websockets.connect(uri) as ws:
            # 认证
            await ws.send(json.dumps({
                'type': 'auth',
                'client_id': client_id,
                'token': token
            }))
            
            response = await ws.recv()
            resp = json.loads(response)
            
            if resp.get('type') != 'auth_success':
                print(f"❌ 认证失败: {resp}")
                return False
            
            print("✅ 认证成功")
            
            # 发送测试消息
            test_msg = {
                'type': 'chat',
                'from': client_id,
                'content': f'测试消息 {datetime.now().isoformat()}',
                'timestamp': datetime.now().isoformat()
            }
            
            await ws.send(json.dumps(test_msg))
            print(f"📤 发送: {test_msg['content']}")
            
            # 等待响应
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            resp_data = json.loads(response)
            print(f"📥 收到: {resp_data}")
            
            # 心跳测试
            await ws.send(json.dumps({'type': 'ping', 'timestamp': time.time()}))
            pong = await asyncio.wait_for(ws.recv(), timeout=5)
            pong_data = json.loads(pong)
            
            if pong_data.get('type') == 'pong':
                print("✅ 心跳测试通过")
            
            print("✅ 所有测试通过!")
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == '__main__':
    print("🧪 WebSocket Bridge 测试")
    print("=" * 40)
    
    success = asyncio.run(test_echo())
    sys.exit(0 if success else 1)