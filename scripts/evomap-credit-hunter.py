#!/usr/bin/env python3
"""
EvoMap 积分猎人 - 自动发现高价值任务并赚取积分
策略：
1. 监控赏金任务，认领匹配的任务
2. 发布高质量资产获取推广奖励
3. 验证其他资产获取验证奖励
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path

HUB_URL = "https://evomap.ai"
CONFIG_PATH = Path.home() / ".openclaw" / "evomap_config.json"
STATE_PATH = Path.home() / ".openclaw" / "workspace" / "data" / "evomap" / "credit-hunter-state.json"
LOG_PATH = Path.home() / ".openclaw" / "workspace" / "data" / "evomap" / "credit-hunter.log"

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def load_state():
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {
        "total_credits_earned": 0,
        "tasks_completed": [],
        "assets_published": [],
        "last_check": None
    }

def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

def send_request(sender_id: str, msg_type: str, payload: dict) -> dict:
    """发送 A2A 请求"""
    import secrets
    req = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": msg_type,
        "message_id": f"msg_{int(time.time()*1000)}_{secrets.token_hex(4)}",
        "sender_id": sender_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload
    }
    try:
        resp = requests.post(f"{HUB_URL}/a2a/{msg_type}", json=req, timeout=30)
        return resp.json() if resp.status_code == 200 else {"error": resp.text}
    except Exception as e:
        return {"error": str(e)}

def get_my_node_info(sender_id: str) -> dict:
    """获取节点信息（积分、声誉）"""
    result = send_request(sender_id, "fetch", {"include_my_node": True})
    payload = result.get("payload", {})
    return payload.get("my_node", {})

def find_eligible_tasks(sender_id: str, my_reputation: int) -> list:
    """找到可以认领的任务"""
    result = send_request(sender_id, "fetch", {"include_tasks": True})
    tasks = result.get("payload", {}).get("available_tasks", [])
    
    eligible = []
    for task in tasks:
        if task.get("min_reputation", 0) <= my_reputation:
            eligible.append({
                "id": task.get("id"),
                "title": task.get("title", ""),
                "bounty": task.get("bounty_amount", 0),
                "signals": task.get("signals", ""),
                "min_reputation": task.get("min_reputation", 0)
            })
    
    # 按赏金排序
    eligible.sort(key=lambda x: x["bounty"], reverse=True)
    return eligible

def claim_task(sender_id: str, task_id: str) -> bool:
    """认领任务"""
    result = send_request(sender_id, "task/claim", {"task_id": task_id})
    success = "error" not in result
    if success:
        log(f"✅ 成功认领任务: {task_id}")
    else:
        log(f"❌ 认领任务失败: {result.get('error')}", "ERROR")
    return success

def main():
    log("=" * 70)
    log("🎯 EvoMap 积分猎人启动")
    log("=" * 70)
    
    config = load_config()
    sender_id = config["sender_id"]
    state = load_state()
    
    # 获取节点信息
    node = get_my_node_info(sender_id)
    credits = node.get("credits", 0)
    reputation = node.get("reputation", 0)
    
    log(f"💰 当前积分: {credits}")
    log(f"⭐ 当前声誉: {reputation}")
    log(f"🎯 距离Aggregator门槛(60): {max(0, 60 - reputation)}点声誉")
    
    # 查找可认领任务
    tasks = find_eligible_tasks(sender_id, reputation)
    log(f"\n📋 找到 {len(tasks)} 个可认领任务")
    
    if tasks:
        log("\n🏆 高价值任务:")
        for i, task in enumerate(tasks[:5], 1):
            log(f"  {i}. 💵 {task['bounty']}积分 | {task['title'][:60]}...")
        
        # 认领最高价值的任务
        best_task = tasks[0]
        if best_task["bounty"] > 0:
            log(f"\n🚀 尝试认领最高价值任务: {best_task['title'][:50]}...")
            if claim_task(sender_id, best_task["id"]):
                state["tasks_completed"].append({
                    "task_id": best_task["id"],
                    "claimed_at": datetime.now().isoformat(),
                    "bounty": best_task["bounty"]
                })
    else:
        log("\n⚠️ 暂无可认领任务")
        log("💡 建议：发布高质量资产赚取积分 (+100/个)")
    
    # 更新状态
    state["last_check"] = datetime.now().isoformat()
    save_state(state)
    
    log("\n" + "=" * 70)
    log("📊 策略建议:")
    log("  1. 发布资产: 每个推广资产 +100积分")
    log("  2. 验证资产: 每次验证 +10-30积分")
    log("  3. 推荐代理: 每个新代理 +50积分")
    log("=" * 70)

if __name__ == "__main__":
    main()
