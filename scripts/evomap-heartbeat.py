#!/usr/bin/env python3
"""
EvoMap Heartbeat Service v1.1
符合 GEP-A2A v1.0.0 协议
本地速率限制：至少5分钟间隔，防止过度触发 API 限流
"""

import json
import time
import random
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 配置
HUB_URL = "https://evomap.ai"
CONFIG_PATH = Path.home() / ".openclaw" / "evomap_config.json"
STATE_PATH = Path.home() / ".openclaw" / "workspace" / "data" / "evomap" / "heartbeat_state.json"
LOG_PATH = Path.home() / ".openclaw" / "workspace" / "data" / "evomap" / "heartbeat.log"

# 速率限制配置
MIN_HEARTBEAT_INTERVAL_SECONDS = 300  # 至少5分钟间隔
JITTER_RANGE_MS = (50, 300)  # 随机抖动范围

def log(message, level="INFO"):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(log_entry + "\n")

def load_config():
    """加载配置"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return None

def save_config(config):
    """保存配置"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def load_state():
    """加载状态"""
    defaults = {
        "total_sent": 0,
        "total_failed": 0,
        "consecutive_failures": 0,
        "last_heartbeat": None,
        "last_sent": None,  # 上次发送心跳的时间
        "last_success": None,
        "skip_count": 0,  # 跳过次数（因为速率限制）
        "rate_limit_until": None  # 被限流直到何时
    }
    if STATE_PATH.exists():
        with open(STATE_PATH, "r") as f:
            state = json.load(f)
            # 合并默认值，确保所有键都存在
            return {**defaults, **state}
    return defaults

def save_state(state):
    """保存状态"""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

def generate_message_id():
    """生成消息ID"""
    import secrets
    # 添加随机抖动
    jitter_ms = random.randint(*JITTER_RANGE_MS)
    time.sleep(jitter_ms / 1000.0)
    return f"msg_{int(time.time() * 1000)}_{secrets.token_hex(4)}"

def send_heartbeat(sender_id: str, node_secret: str = None) -> dict:
    """发送心跳"""
    payload = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "heartbeat",
        "message_id": generate_message_id(),
        "sender_id": sender_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "status": "online",
            "timestamp": int(time.time())
        }
    }
    
    # 如果提供了 node_secret，添加到请求中
    headers = {"Content-Type": "application/json"}
    if node_secret:
        headers["Authorization"] = f"Bearer {node_secret}"
    
    try:
        response = requests.post(
            f"{HUB_URL}/a2a/heartbeat",
            json=payload,
            timeout=30,
            headers=headers
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        elif response.status_code == 429:
            # 处理速率限制
            try:
                error_data = response.json()
                retry_after_ms = error_data.get("retry_after_ms", 300000)
                next_request_at = error_data.get("next_request_at")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "rate_limited": True,
                    "retry_after_ms": retry_after_ms,
                    "next_request_at": next_request_at
                }
            except:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "rate_limited": True,
                    "retry_after_ms": 300000
                }
        elif response.status_code == 403 and "unknown_node" in response.text.lower():
            return {"success": False, "error": "unknown_node", "need_reregister": True}
        elif response.status_code == 401 and "node_secret_required" in response.text.lower():
            return {"success": False, "error": "node_secret_required", "need_reregister": True}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_hello(sender_id: str) -> dict:
    """重新注册节点"""
    import platform
    
    payload = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "hello",
        "message_id": generate_message_id(),
        "sender_id": sender_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "capabilities": {},
            "env_fingerprint": {
                "platform": platform.system().lower(),
                "arch": platform.machine().lower()
            }
        }
    }
    
    try:
        response = requests.post(
            f"{HUB_URL}/a2a/hello",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # 提取 node_secret
            node_secret = data.get("node_secret") or data.get("payload", {}).get("node_secret")
            return {"success": True, "data": data, "node_secret": node_secret}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def should_skip_heartbeat(state) -> tuple:
    """
    检查是否应该跳过本次心跳
    返回 (should_skip, reason)
    """
    now = datetime.now(timezone.utc)
    
    # 检查速率限制是否生效
    if state.get("rate_limit_until"):
        try:
            rate_limit_until = parse_datetime(state["rate_limit_until"])
            # 如果当前时间还在限流期内，且距离限流结束还有至少1分钟，则跳过
            if now < rate_limit_until - timedelta(minutes=1):
                wait_seconds = (rate_limit_until - now).total_seconds()
                return (True, f"📬 还在速率限制期内，需等待 {int(wait_seconds)} 秒")
        except Exception as e:
            log(f"⚠️ 解析 rate_limit_until 失败: {e}", "WARN")
    
    # 检查距离上次发送是否不足最小间隔
    if state.get("last_sent"):
        try:
            last_sent = parse_datetime(state["last_sent"])
            time_since_last = (now - last_sent).total_seconds()
            # 如果距离上次发送不足最小间隔，跳过
            if time_since_last < MIN_HEARTBEAT_INTERVAL_SECONDS:
                wait_seconds = MIN_HEARTBEAT_INTERVAL_SECONDS - time_since_last
                return (True, f"⏰ 距离上次心跳仅 {int(time_since_last)} 秒，需等待 {int(wait_seconds)} 秒")
        except Exception as e:
            log(f"⚠️ 解析 last_sent 失败: {e}", "WARN")
    
    return (False, None)

def parse_datetime(dt_str: str) -> datetime:
    """
    解析日期时间字符串，处理无时区信息的情况
    """
    dt = datetime.fromisoformat(dt_str)
    # 如果没有时区信息，则假设为 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def update_state_with_rate_limit(state, result: dict):
    """
    根据请求结果更新状态中的速率限制信息
    """
    if result.get("rate_limited"):
        retry_after_ms = result.get("retry_after_ms", 300000)
        next_request_at = result.get("next_request_at")
        
        # 设置限流时间
        if next_request_at:
            try:
                state["rate_limit_until"] = next_request_at
            except:
                pass
        else:
            # 使用 retry_after_ms 计算
            rate_limit_until = datetime.now(timezone.utc) + timedelta(milliseconds=retry_after_ms)
            state["rate_limit_until"] = rate_limit_until.isoformat()

def main():
    """主函数 - 发送单次心跳"""
    log("=" * 60)
    log("🫀 EvoMap Heartbeat")
    log("=" * 60)
    
    # 加载配置
    config = load_config()
    if not config or not config.get("sender_id"):
        log("❌ 未找到 sender_id，请先运行节点注册", "ERROR")
        return 1
    
    sender_id = config["sender_id"]
    log(f"节点: {sender_id}")
    
    # 加载状态
    state = load_state()
    
    # 检查是否应该跳过本次心跳
    should_skip, skip_reason = should_skip_heartbeat(state)
    if should_skip:
        state["skip_count"] += 1
        log(f"⏭️ {skip_reason}，跳过本次发送")
        log(f"📊 统计: 成功={state['total_sent']}, 失败={state['total_failed']}, 跳过={state['skip_count']}")
        log("=" * 60)
        save_state(state)
        return 0  # 返回0表示正常退出（故意跳过）
    
    # 发送心跳
    result = send_heartbeat(sender_id)
    
    if result["success"]:
        state["total_sent"] += 1
        state["consecutive_failures"] = 0
        state["last_success"] = datetime.now().isoformat()
        state["last_sent"] = datetime.now().isoformat()
        state["rate_limit_until"] = None  # 清除限流状态
        log("✅ 心跳发送成功")
        
        # 检查是否有可用工作
        if "available_work" in result.get("data", {}):
            work = result["data"]["available_work"]
            log(f"📋 可用工作: {work}")
            
    elif result.get("need_reregister"):
        log("⚠️ 节点未注册或已清理，尝试重新注册...", "WARN")
        hello_result = send_hello(sender_id)
        
        if hello_result["success"]:
            log("✅ 重新注册成功，重新发送心跳...")
            # 重新发送心跳
            result = send_heartbeat(sender_id)
            if result["success"]:
                state["total_sent"] += 1
                state["consecutive_failures"] = 0
                state["last_success"] = datetime.now().isoformat()
                state["last_sent"] = datetime.now().isoformat()
                state["rate_limit_until"] = None
                log("✅ 心跳发送成功")
            else:
                state["total_failed"] += 1
                state["consecutive_failures"] += 1
                state["last_sent"] = datetime.now().isoformat()
                update_state_with_rate_limit(state, result)
                log(f"❌ 心跳发送失败: {result['error']}", "ERROR")
        else:
            state["total_failed"] += 1
            state["consecutive_failures"] += 1
            state["last_sent"] = datetime.now().isoformat()
            log(f"❌ 重新注册失败: {hello_result['error']}", "ERROR")
    else:
        state["total_failed"] += 1
        state["consecutive_failures"] += 1
        state["last_sent"] = datetime.now().isoformat()
        update_state_with_rate_limit(state, result)
        log(f"❌ 心跳发送失败: {result['error']}", "ERROR")
    
    state["last_heartbeat"] = datetime.now().isoformat()
    save_state(state)
    
    # 特定失败数时记录诊断信息
    cf = state["consecutive_failures"]
    if cf in [3, 10] or (cf > 0 and cf % 50 == 0):
        log(f"⚠️ 连续失败次数: {cf}", "WARN")
    
    log(f"📊 统计: 成功={state['total_sent']}, 失败={state['total_failed']}, 跳过={state['skip_count']}, 连续失败={cf}")
    log("=" * 60)
    
    return 0 if result["success"] else 1

if __name__ == "__main__":
    exit(main())
