#!/usr/bin/env python3
"""
MCP Client - 最小可行版本 (MVP)
目标: 证明可以连接和使用外部MCP Server
"""

import json
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")

class MCPClientMVP:
    """MCP客户端最小实现"""
    
    def __init__(self):
        self.connected = False
        self.tools = []
        self.server_process = None
    
    def connect_stdio(self, command: list[str]) -> bool:
        """通过stdio连接MCP Server"""
        try:
            self.server_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 发送initialize请求
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "sensen-mcp-client", "version": "0.1.0"}
                }
            }
            
            self._send(init_request)
            response = self._receive()
            
            if response and "result" in response:
                self.connected = True
                print(f"✅ MCP Server连接成功: {command[0]}")
                return True
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
        
        return False
    
    def _send(self, message: dict):
        """发送JSON-RPC消息"""
        if self.server_process:
            data = json.dumps(message) + "\n"
            self.server_process.stdin.write(data)
            self.server_process.stdin.flush()
    
    def _receive(self) -> dict | None:
        """接收JSON-RPC响应"""
        if self.server_process:
            line = self.server_process.stdout.readline()
            if line:
                return json.loads(line)
        return None
    
    def list_tools(self) -> list:
        """获取可用工具列表"""
        if not self.connected:
            return []
        
        self._send({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        })
        
        response = self._receive()
        if response and "result" in response:
            self.tools = response["result"].get("tools", [])
            return self.tools
        
        return []
    
    def call_tool(self, name: str, arguments: dict) -> dict:
        """调用工具"""
        if not self.connected:
            return {"error": "未连接"}
        
        self._send({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments}
        })
        
        return self._receive() or {"error": "无响应"}
    
    def close(self):
        """关闭连接"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.connected = False


def test_with_filesystem():
    """测试与filesystem MCP server的连接"""
    print("=" * 50)
    print("MCP Client MVP 测试")
    print("=" * 50)
    
    client = MCPClientMVP()
    
    # 尝试连接filesystem server (如果已安装)
    # npx -y @modelcontextprotocol/server-filesystem /tmp
    try:
        if client.connect_stdio(["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"]):
            tools = client.list_tools()
            print(f"📦 可用工具: {len(tools)}个")
            for tool in tools[:3]:  # 只显示前3个
                print(f"  - {tool.get('name')}: {tool.get('description', 'N/A')[:50]}...")
            
            client.close()
            return True
    except FileNotFoundError:
        print("⚠️ npx未安装，跳过filesystem测试")
    
    return False


def test_echo_server():
    """使用简单的echo server测试协议"""
    print("\n🧪 协议测试 (使用echo模拟)")
    
    # 创建一个简单的测试server
    echo_script = '''
import json
import sys

while True:
    try:
        line = sys.stdin.readline()
        if not line:
            break
        msg = json.loads(line)
        
        # Echo back
        response = {
            "jsonrpc": "2.0",
            "id": msg.get("id"),
            "result": {"status": "ok", "echo": msg}
        }
        print(json.dumps(response), flush=True)
    except:
        break
'''
    
    client = MCPClientMVP()
    
    # 使用python -c 启动echo server
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(echo_script)
        script_path = f.name
    
    try:
        if client.connect_stdio(["python3", script_path]):
            print("✅ 协议层测试通过")
            client.close()
            return True
    finally:
        Path(script_path).unlink()
    
    return False


if __name__ == "__main__":
    # 运行测试
    test_echo_server()
    test_with_filesystem()
    
    print("\n" + "=" * 50)
    print("MCP Client MVP 状态: 框架就绪，待连接真实Server")
    print("=" * 50)
