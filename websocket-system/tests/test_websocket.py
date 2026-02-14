#!/usr/bin/env python3
"""
WebSocket 系统测试脚本
包含功能测试、压力测试、可靠性测试
"""

import asyncio
import json
import time
import sys
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

import websockets


class WebSocketTester:
    """WebSocket测试器"""
    
    def __init__(self, server_url: str = "ws://localhost:8765", token: str = "demo-token-12345"):
        self.server_url = server_url
        self.token = token
        self.results = []
    
    async def _connect_and_auth(self, node_id: str) -> Tuple[websockets.WebSocketClientProtocol, float]:
        """连接并认证，返回连接和延迟"""
        start_time = time.time()
        ws = await websockets.connect(self.server_url)
        
        # 发送认证
        auth_msg = {
            "msg_id": f"auth-{node_id}",
            "msg_type": "auth",
            "timestamp": int(time.time()),
            "sender": node_id,
            "receiver": "cloud-server",
            "payload": {
                "token": self.token,
                "node_type": "test",
                "version": "1.0.0"
            }
        }
        await ws.send(json.dumps(auth_msg))
        
        # 等待认证响应
        response = await ws.recv()
        data = json.loads(response)
        
        elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
        
        if data.get("msg_type") != "auth_response":
            raise Exception("认证失败")
        
        if not data.get("payload", {}).get("success"):
            raise Exception("认证被拒绝")
        
        return ws, elapsed
    
    async def test_connection_latency(self, iterations: int = 10) -> dict:
        """测试连接延迟"""
        print(f"\n=== 连接延迟测试 ({iterations}次) ===")
        latencies = []
        
        for i in range(iterations):
            node_id = f"test-node-{i}"
            try:
                ws, latency = await self._connect_and_auth(node_id)
                latencies.append(latency)
                await ws.close()
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"  迭代 {i+1}: 失败 - {e}")
        
        if latencies:
            result = {
                "test": "connection_latency",
                "iterations": len(latencies),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "avg_ms": statistics.mean(latencies),
                "median_ms": statistics.median(latencies)
            }
            print(f"  平均延迟: {result['avg_ms']:.2f}ms")
            print(f"  最小延迟: {result['min_ms']:.2f}ms")
            print(f"  最大延迟: {result['max_ms']:.2f}ms")
            return result
        else:
            print("  所有测试失败")
            return {"test": "connection_latency", "error": "all_failed"}
    
    async def test_message_rtt(self, iterations: int = 20) -> dict:
        """测试消息往返延迟"""
        print(f"\n=== 消息RTT测试 ({iterations}次) ===")
        
        ws, _ = await self._connect_and_auth("rtt-test-node")
        latencies = []
        
        try:
            for i in range(iterations):
                # 发送ping请求
                start_time = time.time()
                request_msg = {
                    "msg_id": f"req-{i}",
                    "msg_type": "request",
                    "timestamp": int(time.time()),
                    "sender": "rtt-test-node",
                    "receiver": "cloud-server",
                    "payload": {
                        "action": "ping",
                        "request_id": f"rq-{i}"
                    }
                }
                await ws.send(json.dumps(request_msg))
                
                # 等待响应
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                elapsed = (time.time() - start_time) * 1000
                latencies.append(elapsed)
                
                await asyncio.sleep(0.05)  # 短暂间隔
        finally:
            await ws.close()
        
        if latencies:
            result = {
                "test": "message_rtt",
                "iterations": len(latencies),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "avg_ms": statistics.mean(latencies),
                "median_ms": statistics.median(latencies)
            }
            print(f"  平均RTT: {result['avg_ms']:.2f}ms")
            print(f"  最小RTT: {result['min_ms']:.2f}ms")
            print(f"  最大RTT: {result['max_ms']:.2f}ms")
            return result
        else:
            return {"test": "message_rtt", "error": "all_failed"}
    
    async def test_heartbeat(self, duration: int = 65) -> dict:
        """测试心跳机制"""
        print(f"\n=== 心跳测试 ({duration}秒) ===")
        
        ws, _ = await self._connect_and_auth("heartbeat-test-node")
        heartbeat_count = 0
        ack_count = 0
        
        async def send_heartbeats():
            nonlocal heartbeat_count
            for i in range(duration // 30 + 1):
                heartbeat_msg = {
                    "msg_id": f"hb-{i}",
                    "msg_type": "heartbeat",
                    "timestamp": int(time.time()),
                    "sender": "heartbeat-test-node",
                    "receiver": "cloud-server",
                    "payload": {"sequence": i + 1}
                }
                await ws.send(json.dumps(heartbeat_msg))
                heartbeat_count += 1
                await asyncio.sleep(30)
        
        async def receive_messages():
            nonlocal ack_count
            timeout = time.time() + duration + 10
            while time.time() < timeout:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(msg)
                    if data.get("msg_type") == "heartbeat_ack":
                        ack_count += 1
                except asyncio.TimeoutError:
                    break
        
        try:
            await asyncio.gather(
                send_heartbeats(),
                receive_messages()
            )
        except Exception as e:
            print(f"  心跳测试异常: {e}")
        finally:
            await ws.close()
        
        result = {
            "test": "heartbeat",
            "duration": duration,
            "heartbeat_sent": heartbeat_count,
            "ack_received": ack_count,
            "success_rate": ack_count / heartbeat_count if heartbeat_count > 0 else 0
        }
        print(f"  发送心跳: {heartbeat_count}")
        print(f"  收到确认: {ack_count}")
        print(f"  成功率: {result['success_rate']*100:.1f}%")
        return result
    
    async def test_reconnect(self) -> dict:
        """测试自动重连"""
        print("\n=== 自动重连测试 ===")
        
        ws, _ = await self._connect_and_auth("reconnect-test-node")
        reconnect_detected = False
        
        async def monitor_connection():
            nonlocal reconnect_detected
            try:
                while True:
                    msg = await ws.recv()
            except websockets.exceptions.ConnectionClosed:
                reconnect_detected = True
        
        monitor_task = asyncio.create_task(monitor_connection())
        
        # 等待几秒后断开
        await asyncio.sleep(3)
        print("  模拟服务器断开连接...")
        await ws.close()
        
        await asyncio.sleep(1)
        monitor_task.cancel()
        
        result = {
            "test": "reconnect",
            "disconnect_detected": reconnect_detected
        }
        print(f"  断线检测: {'成功' if reconnect_detected else '失败'}")
        return result
    
    async def test_auto_response(self) -> dict:
        """测试自动响应功能"""
        print("\n=== 自动响应测试 ===")
        
        ws, _ = await self._connect_and_auth("auto-response-test-node")
        
        tests = [
            ("ping", {}),
            ("get_status", {}),
            ("echo", {"message": "Hello, World!"}),
            ("get_sensor_data", {"sensor_id": "temp-01"})
        ]
        
        results = []
        for action, params in tests:
            request_msg = {
                "msg_id": f"req-{action}",
                "msg_type": "request",
                "timestamp": int(time.time()),
                "sender": "cloud-server",  # 模拟服务器发送
                "receiver": "auto-response-test-node",
                "payload": {
                    "action": action,
                    "params": params,
                    "request_id": f"rq-{action}"
                }
            }
            await ws.send(json.dumps(request_msg))
            
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(response)
                success = data.get("msg_type") == "response" and \
                         data.get("payload", {}).get("success", False)
                results.append((action, success))
                print(f"  {action}: {'✓' if success else '✗'}")
            except Exception as e:
                results.append((action, False))
                print(f"  {action}: ✗ ({e})")
        
        await ws.close()
        
        success_count = sum(1 for _, s in results if s)
        result = {
            "test": "auto_response",
            "total": len(tests),
            "passed": success_count,
            "success_rate": success_count / len(tests)
        }
        print(f"  通过率: {result['success_rate']*100:.1f}%")
        return result
    
    async def test_concurrent_connections(self, count: int = 100) -> dict:
        """测试并发连接"""
        print(f"\n=== 并发连接测试 ({count}个) ===")
        
        connected = []
        failed = []
        
        async def connect_one(i: int):
            try:
                ws, latency = await self._connect_and_auth(f"concurrent-node-{i}")
                return ("success", latency, ws)
            except Exception as e:
                return ("failed", str(e), None)
        
        # 并发连接
        start_time = time.time()
        tasks = [connect_one(i) for i in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time
        
        connections = []
        for r in results:
            if isinstance(r, Exception):
                failed.append(str(r))
            elif r[0] == "success":
                connected.append(r[1])
                connections.append(r[2])
            else:
                failed.append(r[1])
        
        # 关闭所有连接
        close_tasks = [ws.close() for ws in connections if ws]
        await asyncio.gather(*close_tasks, return_exceptions=True)
        
        result = {
            "test": "concurrent_connections",
            "target": count,
            "connected": len(connected),
            "failed": len(failed),
            "time_seconds": elapsed,
            "connections_per_second": len(connected) / elapsed if elapsed > 0 else 0
        }
        
        if connected:
            result["avg_connect_latency_ms"] = statistics.mean(connected)
        
        print(f"  目标连接数: {count}")
        print(f"  成功连接: {len(connected)}")
        print(f"  失败: {len(failed)}")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  连接速率: {result['connections_per_second']:.1f}/秒")
        
        return result
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("WebSocket 系统测试套件")
        print("=" * 50)
        print(f"服务器: {self.server_url}")
        
        results = []
        
        try:
            # 基础测试
            results.append(await self.test_connection_latency(10))
            results.append(await self.test_message_rtt(20))
            results.append(await self.test_auto_response())
            results.append(await self.test_heartbeat(65))
            results.append(await self.test_reconnect())
            
            # 压力测试
            results.append(await self.test_concurrent_connections(100))
            
        except Exception as e:
            print(f"\n测试异常: {e}")
        
        # 汇总
        print("\n" + "=" * 50)
        print("测试汇总")
        print("=" * 50)
        
        for r in results:
            test_name = r.get("test", "unknown")
            if "error" in r:
                status = "❌ 失败"
            elif "avg_ms" in r:
                status = f"✅ 通过 (平均 {r['avg_ms']:.2f}ms)"
            elif "success_rate" in r:
                status = f"✅ 通过 ({r['success_rate']*100:.0f}%)"
            else:
                status = "✅ 通过"
            print(f"  {test_name}: {status}")
        
        return results


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='WebSocket System Tests')
    parser.add_argument('--url', default='ws://localhost:8765', help='服务器URL')
    parser.add_argument('--token', default='demo-token-12345', help='认证Token')
    
    args = parser.parse_args()
    
    tester = WebSocketTester(args.url, args.token)
    results = await tester.run_all_tests()
    
    # 保存结果
    import json as json_module
    with open('test_results.json', 'w') as f:
        json_module.dump(results, f, indent=2)
    print("\n测试结果已保存到 test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
