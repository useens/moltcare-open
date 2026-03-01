#!/usr/bin/env python3
"""
EvoMap Heartbeat Service v1.0
每15分钟发送心跳保持节点在线状态
符合 GEP-A2A v1.0.0 协议
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path

# 配置
HUB_URL = "https://evomap.ai"
CONFIG_PATH = Path.home() / ".openclaw" / "evomap_config.json"
STATE_PATH = Path.home() / ".openclaw" / "workspace" / "data" / "evomap" / "heartbeat_state.json"
LOG_PATH = Path.home() / ".openclaw" / "workspace" / "data" / "evomap" / "heartbeat.log"

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

def load_state():
    """加载状态"""
    defaults = {
        "total_sent": 0,
        "total_failed": 0,
        "consecutive_failures": 0,
        "last_heartbeat": None,
        "last_success": None
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
    return f"msg_{int(time.time() * 1000)}_{secrets.token_hex(4)}"

def send_heartbeat(sender_id: str) -> dict:
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
    
    try:
        response = requests.post(
            f"{HUB_URL}/a2a/heartbeat",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        elif response.status_code == 403 and "unknown_node" in response.text.lower():
            return {"success": False, "error": "unknown_node", "need_reregister": True}
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
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

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
    
    # 发送心跳
    result = send_heartbeat(sender_id)
    
    if result["success"]:
        state["total_sent"] += 1
        state["consecutive_failures"] = 0
        state["last_success"] = datetime.now().isoformat()
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
                log("✅ 心跳发送成功")
            else:
                state["total_failed"] += 1
                state["consecutive_failures"] += 1
                log(f"❌ 心跳发送失败: {result['error']}", "ERROR")
        else:
            state["total_failed"] += 1
            state["consecutive_failures"] += 1
            log(f"❌ 重新注册失败: {hello_result['error']}", "ERROR")
    else:
        state["total_failed"] += 1
        state["consecutive_failures"] += 1
        log(f"❌ 心跳发送失败: {result['error']}", "ERROR")
    
    state["last_heartbeat"] = datetime.now().isoformat()
    save_state(state)
    
    # 特定失败数时记录诊断信息
    cf = state["consecutive_failures"]
    if cf in [3, 10] or (cf > 0 and cf % 50 == 0):
        log(f"⚠️ 连续失败次数: {cf}", "WARN")
    
    log(f"📊 统计: 成功={state['total_sent']}, 失败={state['total_failed']}, 连续失败={cf}")
    log("=" * 60)
    
    return 0 if result["success"] else 1

if __name__ == "__main__":
    exit(main())
