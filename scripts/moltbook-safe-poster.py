#!/usr/bin/env python3
"""
安全的 Moltbook 帖子发版器
包含内容安全检查和自动过滤
"""

import json
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 安全检查函数（内联以避免模块导入问题）
def check_content_security(content):
    """内联的安全检查函数"""
    import re

    blocked_patterns = [
        r"\bmoltbook_sk_[A-Za-z0-9_-]{20,}\b",
        r"\b(api_key|secret|token|password)[\s=:][\w\-]{20,}\b",
        r"\b(sk-|pk-)[A-Za-z0-9]{40,}\b",
        r"/root/\.openclaw/workspace/",
        r"localhost:\d{4,5}",
        r"127\.0\.0\.1:\d{4,5}",
    ]

    issues = []
    filtered_content = content

    for pattern in blocked_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            matched_text = match.group()
            issues.append({"pattern": pattern, "match": matched_text[:50]})
            filtered_content = filtered_content.replace(
                matched_text,
                f"[REDACTED:{len(matched_text)}]"
            )

    safe = len(issues) == 0
    return safe, filtered_content, issues

def filter_post_content(content, verbose=True):
    """兼容接口的安全检查"""
    return check_content_security(content)

# 配置
workspace = Path("/root/.openclaw/workspace")

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60)

def check_rate_limits():
    """检查速率限制"""
    try:
        result = subprocess.run(
            [sys.executable, f"{workspace}/scripts/moltbook-activity-tracker.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # 解析结果
            if "可发帖: 否" in result.stdout:
                return False, "冷却中"
            return True, "可以发帖"
    except Exception as e:
        print(f"⚠️ 无法检查速率限制: {e}")
    return True, "unknown"

def create_post_safely(submolt, title, content, preview_mode=True):
    """
    安全发布帖子

    Args:
        submolt: 子molts名称
        title: 帖子标题
        content: 帖子内容
        preview_mode: 预览模式（不实际发布）

    Returns:
        dict: 结果
    """
    print_header("🔒 Step 1: Security Check")

    # 步骤1: 安全检查
    safe, filtered_content, issues = filter_post_content(content, verbose=True)

    if not safe:
        print("\n❌ 内容包含高风险信息，无法发布！")
        print("\n建议:")
        print("  1. 移除 API keys、密码、内部 URL")
        print("  2. 使用示例数据代替真实数据")
        print("  3. 审查所有敏感关键词")
        return {
            "success": False,
            "reason": "security_check_failed",
            "issues": issues
        }

    print("\n✅ 安全检查通过")

    if preview_mode:
        print_header("👁️  Step 2: Preview Mode (Post Skipped)")
        print("标题:", title)
        print("子molts:", submolt)
        print("\n过滤后的内容:")
        print("-" * 60)
        print(filtered_content[:500])
        if len(filtered_content) > 500:
            print(f"\n... (还有 {len(filtered_content) - 500} 字符)")
        print("-" * 60)
        print("\n💡 提示: 设置 preview_mode=False 实际发布")
        return {
            "success": True,
            "preview": True,
            "filtered_content": filtered_content
        }

    # 步骤2: 检查速率限制
    print_header("⏰ Step 2: Check Rate Limits")
    can_post, status = check_rate_limits()
    if not can_post:
        print(f"❌ 无法发帖: {status}")
        return {
            "success": False,
            "reason": "rate_limit",
            "status": status
        }

    print(f"✅ {status}")

    # 步骤3: 实际发布
    print_header("📤 Step 3: Publish Post")

    try:
        import requests
        with open("/root/.config/moltbook/credentials.json") as f:
            creds = json.load(f)

        data = {
            "submolt_name": submolt,
            "title": title,
            "content": filtered_content  # 使用过滤后的内容
        }

        print(f"发布到: {submolt}")
        print(f"标题: {title}")
        print(f"内容长度: {len(filtered_content)} 字符\n")

        resp = requests.post(
            "https://www.moltbook.com/api/v1/posts",
            headers={
                "Authorization": f"Bearer {creds['api_key']}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=15
        )

        if resp.status_code == 200:
            result = resp.json()
            print("✅ 帖子创建成功！")

            # 检查是否需要验证
            post = result.get("post", result)
            if "verification" in post:
                print("\n🔐 需要解决验证挑战...")

                # 简化：这里假设自动处理验证
                # 实际使用时需要调用验证接口
                print("⚠️  请手动完成验证")

            # 记录活动
            record_activity("post", title, post.get("id"))

            return {
                "success": True,
                "post_id": post.get("id"),
                "url": f"https://www.moltbook.com/post/{post.get('id')}"
            }
        else:
            print(f"❌ 发布失败: {resp.status_code}")
            print(f"   {resp.text}")
            return {
                "success": False,
                "reason": "api_error",
                "status_code": resp.status_code,
                "response": resp.text
            }

    except Exception as e:
        print(f"❌ 发布异常: {e}")
        return {
            "success": False,
            "reason": "exception",
            "error": str(e)
        }

def record_activity(activity_type, details, post_id=None):
    """记录活动"""
    import json
    log_file = workspace / "data" / "moltbook" / "activity-log.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": activity_type,
        "details": details,
        "post_id": post_id
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"✅ 活动已记录: {activity_type}")

# 示例使用
if __name__ == "__main__":
    print_header("🦞 Moltbook Safe Poster")

    # 示例帖子（包含可能的敏感信息用于测试）
    sample_title = "My automation workflow example"
    sample_content = """
I've been working on an automation setup that works great.

The workflow uses these components:
- Task scheduler
- API integration
- Data processing

Here's an example config (with demo API key):
API_KEY: demo_key_for_testing_only
ENDPOINT: https://api.example.com/v1

The system has been running smoothy in production.
"""

    # 预览模式（不实际发布）
    result = create_post_safely(
        submolt="general",
        title=sample_title,
        content=sample_content,
        preview_mode=True  # 改为 False 实际发布
    )

    if result.get("success"):
        print("\n✅ 一切准备就绪！")
        print("\n发布步骤:")
        print("  1. 审查过滤后的内容")
        print("  2. 确认满意后，设置 preview_mode=False")
        print("  3. 再次运行脚本实际发布")
    else:
        print(f"\n⚠️ 发布失败: {result.get('reason')}")
