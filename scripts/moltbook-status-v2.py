#!/usr/bin/env python3
"""
改进的Moltbook挑战检测脚本
使用写入测试来检测账号是否可以发帖/评论
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

def check_write_permission():
    """
    使用写入测试检测账号是否可以发帖/评论
    这是真正的账号状态检测 - 读取可能不受限，但写入会被封禁
    """
    creds = load_credentials()
    if not creds:
        return None

    headers = get_headers(creds)

    # 尝试创建一个测试帖子（但立即获取错误，不真正创建）
    # 先用空内容测试，如果403就是封禁
    try:
        resp = requests.post(
            f"{API_BASE}/posts",
            headers=headers,
            json={"title": "_TEST_", "content": "_TEST_", "submolt_name": "General"},
            timeout=30
        )

        if resp.status_code == 201:
            return {"status": "fully_active", "message": "可以发帖"}
        elif resp.status_code == 403:
            try:
                error_data = resp.json()
                return {
                    "status": "write_suspended",
                    "reason": error_data.get("message", "写入受限"),
                    "until": error_data.get("timestamp", ""),
                    "full_error": error_data
                }
            except:
                return {"status": "write_suspended", "reason": "403 Forbidden"}
        elif resp.status_code == 401:
            return {"status": "auth_error", "reason": "认证失败"}
        else:
            return {"status": "error", "code": resp.status_code}

    except Exception as e:
        return {"status": "error", "reason": str(e)}

def check_read_permission():
    """检测读取权限（可能不受限）"""
    creds = load_credentials()
    if not creds:
        return None

    headers = get_headers(creds)

    try:
        resp = requests.get(f"{API_BASE}/posts?limit=1", headers=headers, timeout=30)

        if resp.status_code == 200:
            return {"status": "read_ok", "message": "可以读取"}
        elif resp.status_code == 403:
            try:
                error_data = resp.json()
                return {
                    "status": "read_suspended",
                    "reason": error_data.get("message", "读取受限"),
                    "until": error_data.get("timestamp", "")
                }
            except:
                return {"status": "read_suspended", "reason": "403 Forbidden"}
        elif resp.status_code == 401:
            return {"status": "auth_error", "reason": "认证失败"}
        else:
            return {"status": "error", "code": resp.status_code}

    except Exception as e:
        return {"status": "error", "reason": str(e)}

def main():
    print("=" * 60)
    print("🔍 Moltbook 账号状态完整检测")
    print("=" * 60)
    print()

    # 1. 读取权限检测
    print("[1/2] 检测读取权限...")
    read_status = check_read_permission()

    if read_status is None:
        print("❌ 无法检测读取权限（凭证加载失败）")
    elif read_status.get("status") == "read_ok":
        print("✅ 读取权限: 正常")
    else:
        status = read_status.get("status", "")
        reason = read_status.get("reason", "")
        print(f"⚠️  读取权限: {status}")
        print(f"   原因: {reason}")

    print()

    # 2. 写入权限检测（关键！）
    print("[2/2] 检测写入权限（发帖/评论）...")
    write_status = check_write_permission()

    if write_status is None:
        print("❌ 无法检测写入权限（凭证加载失败）")
        return 2
    elif write_status.get("status") == "fully_active":
        print("✅ 写入权限: 正常（可以发帖和评论）")
        print()
        return 0
    elif write_status.get("status") == "write_suspended":
        print("⚠️  写入权限: 已暂停（不能发帖和评论）")
        reason = write_status.get("reason", "")
        print(f"   原因: {reason}")

        until = write_status.get("until", "")
        if until:
            print(f"   解封时间: {until} (UTC)")

            # 计算剩余时间
            try:
                from datetime import datetime, timezone
                suspend_time = datetime.fromisoformat(until.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                remaining = suspend_time - now

                if remaining.total_seconds() > 0:
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    print(f"   剩余时间: 约 {hours}小时 {minutes}分钟")
                else:
                    print(f"   状态: 应该已解封但API仍返回暂停")
                    print("   建议: 等待几分钟后重试")
            except Exception as e:
                print(f"   无法计算剩余时间: {e}")

        print()
        print("📢 建议：")
        print("   • 写入受限期间无法发帖或评论")
        print("   • 可以使用浏览器登录网站操作")
        print("   • 等待解封后自动化脚本可以正常工作")
        print()

        return 1
    elif write_status.get("status") == "auth_error":
        print("❌ 认证错误")
        reason = write_status.get("reason", "")
        print(f"   原因: {reason}")
        print()
        print("📢 建议：")
        print("   • API Token可能已过期")
        print("   • 联系管理员重新生成Token")
        print()
        return 2
    else:
        print(f"❓ 未知状态: {write_status.get('status', '')}")
        return 3

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
