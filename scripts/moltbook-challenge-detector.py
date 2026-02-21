#!/usr/bin/env python3
"""
Moltbook 挑战检测与响应脚本
优先检测并响应自动审核系统发送的挑战

检测方式:
1. 浏览器自动化检查通知页面
2. API错误监控 (403 Forbidden)
3. 账号状态监控

响应策略:
1. CAPTCHA 转人工处理
2. 理解检查 自动回答
3. 行为验证 点击确认
4. 内容审核 暂停等待通知
"""

import json
import requests
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
CREDENTIALS_FILE = "/root/.config/moltbook/credentials.json"
CHALLENGE_LOG = WORKSPACE / "data" / "moltbook" / "challenge_detected.jsonl"
API_BASE = "https://www.moltbook.com/api/v1"

def load_credentials():
    try:
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 无法加载凭证: {e}")
        return None

def get_headers(creds):
    return {
        "Authorization": f"Bearer {creds['api_key']}",
        "Content-Type": "application/json"
    }

def check_api_status():
    """通过API检查账号状态"""
    creds = load_credentials()
    if not creds:
        return None

    headers = get_headers(creds)
    try:
        resp = requests.get(f"{API_BASE}/posts?limit=1", headers=headers, timeout=30)

        if resp.status_code == 200:
            return {"status": "active", "message": "API连接正常"}
        elif resp.status_code == 403:
            # 尝试解析挑战信息
            try:
                error_data = resp.json()
                return {
                    "status": "suspended",
                    "reason": error_data.get("message", "未知原因"),
                    "until": error_data.get("timestamp", ""),
                    "type": "api_challenge"
                }
            except:
                return {
                    "status": "suspended",
                    "reason": "403 Forbidden - 可能是挑战",
                    "type": "api_challenge"
                }
        elif resp.status_code == 401:
            return {"status": "error", "reason": "认证失败 -Token可能过期"}
        else:
            return {"status": "error", "code": resp.status_code}

    except Exception as e:
        return {"status": "error", "reason": str(e)}

def log_challenge(challenge_info):
    """记录挑战检测日志"""
    CHALLENGE_LOG.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": challenge_info.get("type", "unknown"),
        "status": challenge_info.get("status", ""),
        "reason": challenge_info.get("reason", ""),
        "until": challenge_info.get("until", ""),
        "action_taken": challenge_info.get("action_taken", "")
    }

    with open(CHALLENGE_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return log_entry

def get_challenge_response_guidance(challenge_type):
    """获取挑战响应指引"""
    guidance = {
        "api_challenge_suspended": """
╔══════════════════════════════════════════════════════╗
║ 🚨 检测到账号暂停 (挑战未响应)                     ║
╚══════════════════════════════════════════════════════╝

立即行动:
  1. 停止所有 Moltbook 自动化脚本
  2. 访问 https://www.moltbook.com
  3. 查看通知页面中的挑战详情
  4. 根据挑战类型完成响应

紧急命令:
  crontab -l | grep -v moltbook | crontab -  # 移除所有自动化
  systemctl stop moltbook-*                       # 停止服务

恢复后记得重新应用配置！
""",

        "challenge_no_answer": """
╔══════════════════════════════════════════════════════╗
║ ⚠️  挑战未响应 (challenge_no_answer)               ║
╚══════════════════════════════════════════════════════╝

说明: 系统发送了挑战，但自动化脚本无法响应

优先响应步骤:
  1. 登录 Moltbook 网站查看通知
  2. 找到挑战并完成响应
  3. 使用浏览器而非API

常见挑战类型:
  • CAPTCHA - 图形或文字验证
  • 理解检查 - 证明理解社区规则
  • 行为验证 - 点击"我确认"
  • 内容审核 - 修改不合规内容

响应后等待系统审核（通常几分钟到几小时）。
""",

        "auth_error": """
╔══════════════════════════════════════════════════════╗
║ 🔑 认证错误                                         ║
╚══════════════════════════════════════════════════════╝

可能原因:
  1. API Token 已过期
  2. Token 权限不足
  3. 凭证文件损坏

解决步骤:
  1. 登录 Moltbook 查看账号状态
  2. 如需重新生成Token，联系管理员
  3. 更新 /root/.config/moltbook/credentials.json
"""
    }

    return guidance.get(challenge_type, f"未知挑战类型: {challenge_type}")

def check_browser_notifications():
    """
    使用浏览器检查是否有挑战通知
    目前需要手动实现，或使用浏览器控制脚本

    返回: 是否有未读挑战通知
    """
    # TODO: 集成浏览器自动化
    # 优先级: 中 - 可以用API错误检测作为临时方案

    return {
        "has_notification": False,
        "method": "browser_automation"
    }

def main():
    print("=" * 60)
    print("🔍 Moltbook 挑战检测脚本")
    print("=" * 60)
    print()

    # 1. API 状态检查
    print("[1/2] 检查 API 账号状态...")
    api_status = check_api_status()

    if api_status is None:
        print("❌ 无法检查状态（凭证加载失败）")
        print()
        # 记录日志但不退出
        api_status = {"status": "error", "reason": "凭证加载失败"}

    # 2. 显示状态
    status = api_status.get("status", "unknown")
    if status == "active":
        print("✅ 账号状态: 正常")
        print("   无挑战需要响应")
        print()
        return 0

    elif status == "suspended":
        print("⚠️  账号状态: 已暂停")
        reason = api_status.get("reason", "")
        print(f"   原因: {reason}")

        until = api_status.get("until", "")
        if until:
            print(f"   解封时间: {until}")

        print()

        # 3. 记录并显示响应指引
        api_status["action_taken"] = "pause_automation"
        log_challenge(api_status)

        challenge_type = "api_challenge_suspended"
        guidance = get_challenge_response_guidance(challenge_type)
        print(guidance)

        # 4. 建议暂停自动化
        print("📢 建议: 是否立即暂停所有 Moltbook 自动化任务?")
        print("     运行: crontab -l | grep -v moltbook | crontab -")
        print()

        return 1  # 返回非0表示有问题

    elif status == "error":
        print("❌ API 错误:")
        reason = api_status.get("reason", "未知原因")
        print(f"   {reason}")
        print()

        # 记录错误
        api_status["action_taken"] = "log_only"
        log_challenge(api_status)

        if "auth" in reason.lower() or "401" in str(api_status.get("code", "")):
            guidance = get_challenge_response_guidance("auth_error")
            print(guidance)

        return 2

    else:
        print(f"❓ 未知状态: {status}")
        return 3

    # 5. 浏览器通知检查 (未实现)
    print("[2/2] 浏览器通知检查...")
    browser_check = check_browser_notifications()
    print("   (浏览器自动化检测 - 待实现)")
    print()

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
