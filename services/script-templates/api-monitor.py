#!/usr/bin/env python3
"""
API监控告警系统 - 24/7服务健康检查
"""

import requests
import time
import json
from datetime import datetime
from pathlib import Path

class APIMonitor:
    def __init__(self, config_file: str = "monitor-config.json"):
        self.config_file = Path(config_file)
        self.endpoints = self._load_config()
        self.alerts = []
    
    def _load_config(self) -> list:
        """加载监控配置"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return []
    
    def check_endpoint(self, endpoint: dict) -> dict:
        """检查单个端点"""
        url = endpoint['url']
        expected_status = endpoint.get('expected_status', 200)
        timeout = endpoint.get('timeout', 10)
        
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'response_time': 0,
            'error': None
        }
        
        try:
            start = time.time()
            response = requests.get(url, timeout=timeout)
            result['response_time'] = round(time.time() - start, 3)
            
            if response.status_code == expected_status:
                result['status'] = 'healthy'
            else:
                result['status'] = 'error'
                result['error'] = f"状态码异常: {response.status_code}"
        
        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
            result['error'] = f"请求超时 (> {timeout}s)"
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def run_check(self) -> list:
        """运行全部检查"""
        results = []
        for endpoint in self.endpoints:
            result = self.check_endpoint(endpoint)
            results.append(result)
            
            if result['status'] != 'healthy':
                self._send_alert(result)
        
        return results
    
    def _send_alert(self, result: dict):
        """发送告警"""
        alert = f"""
🚨 API监控告警

URL: {result['url']}
状态: {result['status']}
时间: {result['timestamp']}
错误: {result.get('error', 'N/A')}
        """
        self.alerts.append(alert)
        print(alert)
    
    def continuous_monitor(self, interval: int = 300):
        """持续监控"""
        print(f"🔍 开始持续监控 (间隔 {interval} 秒)")
        try:
            while True:
                self.run_check()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 监控已停止")

if __name__ == "__main__":
    monitor = APIMonitor()
    
    # 示例配置
    sample_config = [
        {"url": "https://api.example.com/health", "expected_status": 200},
        {"url": "https://api.example.com/status", "expected_status": 200, "timeout": 5}
    ]
    
    print("请将以下配置保存为 monitor-config.json:")
    print(json.dumps(sample_config, indent=2))
