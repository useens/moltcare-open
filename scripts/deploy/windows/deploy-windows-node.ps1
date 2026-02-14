# Windows节点部署脚本
# 森森分布式计算节点 - Windows版
# 功能: 建立与主节点/备用节点的稳定通信通道

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🌲 森森分布式计算节点 - Windows部署程序" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 配置
$PRIMARY_IP = "129.154.251.13"
$PRIMARY_WS_PORT = "2347"
$PRIMARY_API_PORT = "2346"
$TOKEN = "sensen-shared-2024"
$INSTALL_DIR = "$env:USERPROFILE\.sensen"
$PYTHON_URL = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe"

Write-Host "📋 部署配置:" -ForegroundColor Yellow
Write-Host "  主节点IP: $PRIMARY_IP"
Write-Host "  WebSocket端口: $PRIMARY_WS_PORT"
Write-Host "  API端口: $PRIMARY_API_PORT"
Write-Host "  安装目录: $INSTALL_DIR"
Write-Host ""

# 1. 检查并安装Python
Write-Host "🔍 检查Python..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Host "⚠️  Python未安装，正在下载..." -ForegroundColor Red
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $PYTHON_URL -OutFile $pythonInstaller -UseBasicParsing
        Write-Host "📥 正在安装Python..." -ForegroundColor Yellow
        Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1" -Wait
        Remove-Item $pythonInstaller
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        $python = Get-Command python -ErrorAction SilentlyContinue
    } catch {
        Write-Host "❌ Python安装失败，请手动安装Python 3.11+" -ForegroundColor Red
        Write-Host "   下载地址: https://python.org/downloads" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Python已就绪: $($python.Source)" -ForegroundColor Green

# 2. 创建安装目录
Write-Host ""
Write-Host "📁 创建安装目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
Set-Location $INSTALL_DIR

# 3. 安装Python依赖
Write-Host ""
Write-Host "📦 安装Python依赖..." -ForegroundColor Yellow
&amp; $python.Source -m pip install -q websockets requests psutil --user
Write-Host "✅ 依赖安装完成" -ForegroundColor Green

# 4. 生成节点客户端脚本
Write-Host ""
Write-Host "📝 生成节点客户端..." -ForegroundColor Yellow

$clientScript = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
森森分布式计算节点 - Windows客户端
连接到主节点/备用节点，提供计算能力
"""

import asyncio
import websockets
import json
import time
import sys
import os
import platform
import psutil
from datetime import datetime

# 配置
PRIMARY_IP = "129.154.251.13"
PRIMARY_WS_PORT = "2347"
PRIMARY_API_PORT = "2346"
TOKEN = "sensen-shared-2024"
NODE_ID = f"windows-node-{platform.node()}-{int(time.time()) % 10000}"

class WindowsNodeClient:
    def __init__(self):
        self.uri = f"ws://{PRIMARY_IP}:{PRIMARY_WS_PORT}"
        self.ws = None
        self.connected = False
        self.reconnect_delay = 5
        
    def get_system_info(self):
        """获取Windows系统信息"""
        cpu_count = psutil.cpu_count(logical=True)
        cpu_physical = psutil.cpu_count(logical=False)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "node_id": NODE_ID,
            "hostname": platform.node(),
            "platform": platform.system(),
            "version": platform.version(),
            "cpu_cores": cpu_count,
            "cpu_physical": cpu_physical,
            "memory_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_gb": round(disk.total / (1024**3), 2),
            "python_version": platform.python_version(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def connect(self):
        """连接到主节点"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌲 正在连接森森网络...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]    URI: {self.uri}")
        
        try:
            self.ws = await websockets.connect(self.uri)
            
            # 发送认证
            auth_msg = {
                "type": "auth",
                "token": TOKEN,
                "node_id": NODE_ID,
                "role": "windows_worker"
            }
            await self.ws.send(json.dumps(auth_msg))
            
            # 等待认证响应
            response = await self.ws.recv()
            auth_data = json.loads(response)
            
            if auth_data.get("type") == "auth_success":
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 认证成功!")
                self.connected = True
                self.reconnect_delay = 5  # 重置重连延迟
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 认证失败: {auth_data}")
                return False
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 连接失败: {e}")
            return False
    
    async def send_introduction(self):
        """发送节点介绍"""
        intro = {
            "type": "node_introduction",
            "from": NODE_ID,
            "content": f"🖥️ Windows节点上线! {self.get_system_info()}",
            "system_info": self.get_system_info(),
            "capabilities": [
                "windows_computation",
                "local_processing",
                "file_operations",
                "powershell_execution"
            ],
            "status": "ready"
        }
        await self.ws.send(json.dumps(intro))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📤 节点介绍已发送")
    
    async def handle_task(self, task_data):
        """处理任务"""
        task_type = task_data.get('type')
        task_id = task_data.get('task_id')
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📝 收到任务: {task_id} ({task_type})")
        
        # 根据任务类型执行
        if task_type == 'computation':
            result = await self.run_computation(task_data)
        elif task_type == 'powershell':
            result = await self.run_powershell(task_data)
        elif task_type == 'file_operation':
            result = await self.file_operation(task_data)
        else:
            result = {"status": "error", "message": f"未知任务类型: {task_type}"}
        
        # 发送结果
        result_msg = {
            "type": "task_result",
            "task_id": task_id,
            "from": NODE_ID,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        await self.ws.send(json.dumps(result_msg))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 任务完成: {task_id}")
    
    async def run_computation(self, task_data):
        """执行计算任务"""
        payload = task_data.get('payload', {})
        # 这里可以执行实际的计算
        import random
        time.sleep(random.uniform(1, 3))  # 模拟计算
        return {
            "status": "success",
            "computed": True,
            "cores_used": psutil.cpu_count(),
            "result": "computation_done"
        }
    
    async def run_powershell(self, task_data):
        """执行PowerShell命令"""
        import subprocess
        command = task_data.get('payload', {}).get('command', '')
        
        if not command:
            return {"status": "error", "message": "No command provided"}
        
        try:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=task_data.get('timeout', 60)
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "exit_code": result.returncode,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:1000]
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def file_operation(self, task_data):
        """文件操作"""
        # 实现文件读写等操作
        return {"status": "success", "message": "File operation placeholder"}
    
    async def run(self):
        """主运行循环"""
        while True:
            try:
                if await self.connect():
                    await self.send_introduction()
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ 等待任务...")
                    
                    # 持续接收消息
                    while True:
                        try:
                            message = await self.ws.recv()
                            data = json.loads(message)
                            
                            msg_type = data.get('type')
                            
                            if msg_type == 'task':
                                await self.handle_task(data)
                            elif msg_type == 'ping':
                                await self.ws.send(json.dumps({"type": "pong", "timestamp": time.time()}))
                            elif msg_type == 'message':
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📨 消息: {data.get('content', '')}")
                            
                        except websockets.exceptions.ConnectionClosed:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ 连接关闭")
                            break
                            
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 错误: {e}")
            
            # 重连
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 {self.reconnect_delay}秒后重连...")
            await asyncio.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, 60)  # 指数退避，最大60秒

if __name__ == '__main__':
    print("=" * 60)
    print("🌲 森森分布式计算节点 - Windows客户端")
    print("=" * 60)
    print(f"节点ID: {NODE_ID}")
    print(f"目标: ws://{PRIMARY_IP}:{PRIMARY_WS_PORT}")
    print("=" * 60)
    print()
    
    client = WindowsNodeClient()
    
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n👋 再见!")
        sys.exit(0)
'@

$clientScript | Out-File -FilePath "$INSTALL_DIR\sensen_windows_node.py" -Encoding UTF8
Write-Host "✅ 客户端脚本已生成: $INSTALL_DIR\sensen_windows_node.py" -ForegroundColor Green

# 5. 创建启动脚本
$startScript = @'
@echo off
echo Starting Sensen Windows Node...
cd /d %USERPROFILE%\.sensen
python sensen_windows_node.py
pause
'@

$startScript | Out-File -FilePath "$INSTALL_DIR\start.bat" -Encoding ASCII
Write-Host "✅ 启动脚本已生成: $INSTALL_DIR\start.bat" -ForegroundColor Green

# 6. 创建后台服务脚本（使用WMI或计划任务）
$serviceScript = @'
# 后台服务模式 - 使用PowerShell Job
$Action = New-ScheduledTaskAction -Execute "python" -Argument "$env:USERPROFILE\.sensen\sensen_windows_node.py"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -Description "Sensen Windows Distributed Computing Node"
Register-ScheduledTask -TaskName "SensenNode" -InputObject $Task -Force
Write-Host "✅ 已创建开机启动任务: SensenNode"
'@

$serviceScript | Out-File -FilePath "$INSTALL_DIR\install_service.ps1" -Encoding UTF8
Write-Host "✅ 服务安装脚本已生成: $INSTALL_DIR\install_service.ps1" -ForegroundColor Green

# 7. 显示信息
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ 部署完成!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📂 安装目录: $INSTALL_DIR"
Write-Host ""
Write-Host "🚀 启动方式:"
Write-Host "  1. 手动启动: $INSTALL_DIR\start.bat"
Write-Host "  2. 后台启动: cd $INSTALL_DIR; python sensen_windows_node.py"
Write-Host "  3. 开机自启: 以管理员运行 install_service.ps1"
Write-Host ""
Write-Host "📊 节点功能:"
Write-Host "  • 计算任务执行"
Write-Host "  • PowerShell命令执行"
Write-Host "  • 文件操作"
Write-Host "  • 实时通信"
Write-Host ""
Write-Host "🔗 连接目标: ws://$PRIMARY_IP`:$PRIMARY_WS_PORT"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

# 8. 询问是否立即启动
$startNow = Read-Host "是否立即启动节点? (y/n)"
if ($startNow -eq 'y' -or $startNow -eq 'Y') {
    Write-Host ""
    Write-Host "🚀 启动节点..." -ForegroundColor Green
    Set-Location $INSTALL_DIR
    &amp; $python.Source sensen_windows_node.py
}
