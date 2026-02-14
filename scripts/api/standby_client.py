#!/usr/bin/env python3
# 备用节点客户端 v1.0
# 部署在备用节点(本地)，主动连接主节点API

import requests
import time
import threading
import json
import os
import sys
from typing import Dict, List, Optional
import psutil

class StandbyClient:
    """备用节点客户端 - 主动连接主节点API"""
    
    def __init__(self, primary_url: str, token: str, node_id: str = None):
        self.primary_url = primary_url.rstrip('/')
        self.token = token
        self.node_id = node_id or self._generate_node_id()
        self.running = False
        self.active_tasks: Dict[str, Dict] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
        
        # 配置
        self.poll_interval = 30  # 轮询间隔（秒）
        self.heartbeat_interval = 60  # 心跳间隔（秒）
        self.progress_interval = 5  # 进度更新间隔（秒）
        
    def _generate_node_id(self) -> str:
        """生成节点ID"""
        import socket
        hostname = socket.gethostname()
        return f"standby-{hostname}-{int(time.time()) % 10000}"
        
    def _api_get(self, endpoint: str, **kwargs) -> Optional[Dict]:
        """GET请求"""
        try:
            response = self.session.get(
                f"{self.primary_url}{endpoint}",
                timeout=10,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ERROR] API GET {endpoint}: {e}")
            return None
            
    def _api_post(self, endpoint: str, data: Dict, **kwargs) -> Optional[Dict]:
        """POST请求"""
        try:
            response = self.session.post(
                f"{self.primary_url}{endpoint}",
                json=data,
                timeout=10,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ERROR] API POST {endpoint}: {e}")
            return None
    
    def start(self):
        """启动客户端"""
        print("=" * 60)
        print("🌲 Sensen Standby Node Client v1.0")
        print("=" * 60)
        print(f"Node ID: {self.node_id}")
        print(f"Primary URL: {self.primary_url}")
        print(f"Poll Interval: {self.poll_interval}s")
        print(f"Heartbeat Interval: {self.heartbeat_interval}s")
        print("=" * 60)
        
        # 检查主节点连接
        if not self._check_connection():
            print("[ERROR] 无法连接到主节点，请检查URL和Token")
            return False
            
        print("[OK] 已连接到主节点")
        self.running = True
        
        # 启动工作线程
        threads = [
            threading.Thread(target=self._poll_loop, name="Poller", daemon=True),
            threading.Thread(target=self._heartbeat_loop, name="Heartbeat", daemon=True),
        ]
        
        for t in threads:
            t.start()
            
        print("[OK] 所有工作线程已启动")
        return True
        
    def stop(self):
        """停止客户端"""
        print("[INFO] 正在停止客户端...")
        self.running = False
        
    def _check_connection(self) -> bool:
        """检查与主节点的连接"""
        try:
            response = self.session.get(f"{self.primary_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def _poll_loop(self):
        """任务轮询循环"""
        print("[THREAD] 轮询线程已启动")
        
        while self.running:
            try:
                # 获取待处理任务
                data = self._api_get('/api/tasks/pending')
                
                if data and 'tasks' in data:
                    tasks = data['tasks']
                    
                    for task in tasks:
                        task_id = task.get('id')
                        
                        # 检查是否已在处理中
                        if task_id not in self.active_tasks:
                            print(f"[NEW TASK] {task_id} - {task.get('type')}")
                            
                            # 启动任务执行线程
                            thread = threading.Thread(
                                target=self._execute_task,
                                args=(task,),
                                name=f"Task-{task_id}",
                                daemon=True
                            )
                            thread.start()
                            
            except Exception as e:
                print(f"[ERROR] 轮询错误: {e}")
                
            # 等待下次轮询
            for _ in range(self.poll_interval):
                if not self.running:
                    break
                time.sleep(1)
                
    def _heartbeat_loop(self):
        """心跳循环"""
        print("[THREAD] 心跳线程已启动")
        
        while self.running:
            try:
                self._send_heartbeat()
            except Exception as e:
                print(f"[ERROR] 心跳错误: {e}")
                
            # 等待下次心跳
            for _ in range(self.heartbeat_interval):
                if not self.running:
                    break
                time.sleep(1)
                
    def _send_heartbeat(self):
        """发送状态心跳"""
        status = {
            "node_id": self.node_id,
            "hostname": os.uname().nodename,
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "active_tasks": len(self.active_tasks),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        result = self._api_post('/api/nodes/status', status)
        if result:
            print(f"[HEARTBEAT] CPU: {status['cpu_usage']}% | Mem: {status['memory_usage']}% | Tasks: {status['active_tasks']}")
            
    def _execute_task(self, task: Dict):
        """执行任务"""
        task_id = task['id']
        task_type = task.get('type', 'generic')
        
        self.active_tasks[task_id] = task
        
        try:
            # 1. 认领任务
            claim_result = self._api_post(
                f'/api/tasks/{task_id}/claim',
                {
                    "node_id": self.node_id,
                    "claimed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            )
            
            if not claim_result:
                print(f"[ERROR] 无法认领任务 {task_id}")
                return
                
            print(f"[TASK STARTED] {task_id} - {task_type}")
            start_time = time.time()
            
            # 2. 根据任务类型执行
            if task_type == 'data-processing':
                result = self._process_data(task)
            elif task_type == 'web-scraping':
                result = self._scrape_web(task)
            elif task_type == 'computation':
                result = self._computation(task)
            elif task_type == 'command':
                result = self._execute_command(task)
            else:
                result = self._generic_task(task)
                
            execution_time = int(time.time() - start_time)
            
            # 3. 提交结果
            self._api_post(
                f'/api/tasks/{task_id}/complete',
                {
                    "status": "success",
                    "result": result,
                    "execution_time": execution_time,
                    "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            )
            
            print(f"[TASK COMPLETED] {task_id} - {execution_time}s")
            
        except Exception as e:
            print(f"[ERROR] 任务执行失败 {task_id}: {e}")
            
            # 提交错误
            self._api_post(
                f'/api/tasks/{task_id}/complete',
                {
                    "status": "failed",
                    "result": {"error": str(e)},
                    "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            )
        finally:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                
    def _process_data(self, task: Dict) -> Dict:
        """数据处理任务示例"""
        payload = task.get('payload', {})
        # 实际实现根据需求编写
        return {"processed": True, "items": payload.get('items', 0)}
        
    def _scrape_web(self, task: Dict) -> Dict:
        """Web爬取任务示例"""
        payload = task.get('payload', {})
        url = payload.get('url')
        # 实际实现使用requests/selenium
        return {"scraped": True, "url": url, "data": "..."}
        
    def _computation(self, task: Dict) -> Dict:
        """计算任务示例"""
        payload = task.get('payload', {})
        # 利用8核CPU进行计算
        result = sum(i ** 2 for i in range(1000000))
        return {"computed": True, "result": result}
        
    def _execute_command(self, task: Dict) -> Dict:
        """执行系统命令"""
        import subprocess
        
        payload = task.get('payload', {})
        command = payload.get('command', '')
        
        if not command:
            return {"error": "No command specified"}
            
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=payload.get('timeout', 60)
            )
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout[:1000],  # 限制输出长度
                "stderr": result.stderr[:1000]
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timeout"}
        except Exception as e:
            return {"error": str(e)}
            
    def _generic_task(self, task: Dict) -> Dict:
        """通用任务处理"""
        return {"message": "Generic task executed", "task_id": task['id']}


def main():
    """主函数"""
    # 从环境变量读取配置
    primary_url = os.environ.get('PRIMARY_URL', 'http://localhost:2346')
    api_token = os.environ.get('SENSEN_API_TOKEN', 'default-token')
    node_id = os.environ.get('NODE_ID')
    
    if len(sys.argv) >= 2:
        primary_url = sys.argv[1]
    if len(sys.argv) >= 3:
        api_token = sys.argv[2]
        
    print(f"启动参数:")
    print(f"  Primary URL: {primary_url}")
    print(f"  API Token: {api_token[:10]}...")
    print()
    
    client = StandbyClient(primary_url, api_token, node_id)
    
    if not client.start():
        sys.exit(1)
        
    # 保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INTERRUPT] 收到中断信号")
        client.stop()
        print("[OK] 客户端已停止")


if __name__ == '__main__':
    main()
