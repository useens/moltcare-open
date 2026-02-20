#!/usr/bin/env python3
"""
Moltbook 内容安全过滤器
防止泄露敏感信息
"""

import json
import re
from pathlib import Path

# 配置
workspace = Path("/root/.openclaw/workspace")
security_config = workspace / "config" / "moltbook-security.json"

# 默认安全规则
DEFAULT_SECURITY_RULES = {
    "blocked_patterns": [
        # API 密钥和令牌
        r"\bmoltbook_sk_[A-Za-z0-9_-]{20,}\b",
        r"\b(moltbook_sk_|api_key|secret|token|password)[\s=:][\w\-]{20,}\b",
        r"\b(sk-|pk-)[A-Za-z0-9]{40,}\b",
        r"\bbearer\s+[A-Za-z0-9\-._~+/=]{20,}\b",

        # 文件路径 (工作区内部)
        r"/root/\.openclaw/workspace/([^/]+/)+",
        r"/home/[^/]+/\.openclaw/",
        r"~/.config/",
        r"/etc/sensitive",

        # 内部 URL 和端点
        r"localhost:\d{4,5}",
        r"127\.0\.0\.1:\d{4,5}",
        r"192\.168\.\d+\.\d+:\d+",
        r"10\.\d+\.\d+\.\d+:\d+",

        # 数据库连接字符串 (部分)
        r"mongodb://[^@]+@",
        r"postgresql://[^@]+@",
        r"redis://[^@]+@",

        # 个人身份信息
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN 模式
        r"\b[A-Za-z0-9._%+-]+@internal\.company\.com\b",
    ],

    "internal_domains": [
        "internal.company.com",
        "staging.internal.app",
        "dev.internal",
    ],

    "internal_usernames": [
        "admin",
        "root",
        "superuser",
        # 添加更多如果需要
    ],

    "sensitive_keywords": [
        "my private key",
        "my secret",
        "my password",
        "my api key",
        "database password",
        "ssh private key",
        "production credentials",
        "staging credentials",
    ],

    "allowed_contexts": [
        "example.com",
        "demo",
        "test",
        "sample",
        "public",
    ]
}

def load_security_rules():
    """加载安全规则"""
    if security_config.exists():
        with open(security_config) as f:
            return json.load(f)
    return DEFAULT_SECURITY_RULES

def save_security_rules(rules):
    """保存安全规则"""
    security_config.parent.mkdir(parents=True, exist_ok=True)
    with open(security_config, "w") as f:
        json.dump(rules, f, indent=2)

def check_content_for_secrets(content, rules=None):
    """
    检查内容是否包含敏感信息

    Returns:
        dict: {
            'safe': bool,
            'issues': list of issues found,
            'filtered_content': str (content with secrets masked)
        }
    """
    if rules is None:
        rules = load_security_rules()

    issues = []
    filtered_content = content

    # 检查规则1: 禁止的模式
    for pattern in rules["blocked_patterns"]:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            matched_text = match.group()
            issues.append({
                "type": "block_pattern",
                "severity": "high",
                "pattern": pattern,
                "match": matched_text[:50],
                "position": match.start()
            })
            # 屏蔽匹配的内容
            filtered_content = filtered_content.replace(
                matched_text,
                f"[REDACTED:{len(matched_text)}]"
            )

    # 检查规则2: 内部域名
    for domain in rules["internal_domains"]:
        if domain.lower() in content.lower():
            issues.append({
                "type": "internal_domain",
                "severity": "medium",
                "domain": domain,
                "message": f"Internal domain '{domain}' detected"
            })

    # 检查规则3: 内部用户名
    for username in rules["internal_usernames"]:
        pattern = r"\b" + re.escape(username) + r"\b"
        if re.search(pattern, content, re.IGNORECASE):
            # 除非在允许的上下文中
            if not any(ctx in content.lower() for ctx in rules["allowed_contexts"]):
                issues.append({
                    "type": "internal_username",
                    "severity": "low",
                    "username": username,
                    "message": f"Internal username '{username}' detected"
                })

    # 检查规则4: 敏感关键词
    for keyword in rules["sensitive_keywords"]:
        if keyword.lower() in content.lower():
            # 检查是否有引号或引号内的上下文
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if keyword.lower() in line.lower():
                    issues.append({
                        "type": "sensitive_keyword",
                        "severity": "variable",
                        "keyword": keyword,
                        "line": i + 1,
                        "context": line.strip()[:100]
                    })

    # 计算安全等级
    has_high_severity = any(i["severity"] == "high" for i in issues)
    safe = not has_high_severity

    return {
        "safe": safe,
        "issues": issues,
        "filtered_content": filtered_content,
        "issue_count": len(issues)
    }

def print_security_report(content, check_result):
    """打印安全检查报告"""
    print("\n" + "="*60)
    print("🔒 Security Check Report")
    print("="*60)

    if check_result["safe"]:
        print("\n✅ Content appears SAFE to share")
    else:
        print("\n❌ Content contains HIGH-RISK information")
        print("   ⚠️  DO NOT SHARE without review!")

    if check_result["issues"]:
        print(f"\n📋 Found {check_result['issue_count']} potential issue(s):\n")

        high_count = sum(1 for i in check_result["issues"] if i["severity"] == "high")
        medium_count = sum(1 for i in check_result["issues"] if i["severity"] == "medium")
        low_count = sum(1 for i in check_result["issues"] if i["severity"] == "low")

        print(f"   🔴 High severity: {high_count}")
        print(f"   🟡 Medium severity: {medium_count}")
        print(f"   🟢 Low severity: {low_count}")

        print("\nDetails:")
        for i, issue in enumerate(check_result["issues"], 1):
            severity_icon = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
                "variable": "⚠️"
            }.get(issue["severity"], "⚠️")

            print(f"\n  [{i}] {severity_icon} {issue['type'].upper()}")
            if "match" in issue:
                print(f"      Matched: {issue['match']}")
            if "message" in issue:
                print(f"      {issue['message']}")
            if "context" in issue:
                print(f"      Context: {issue['context']}")

    print("\n" + "="*60)

def filter_post_content(content, verbose=True):
    """
    过滤帖子内容，确保安全

    Args:
        content: 要发布的内容
        verbose: 是否打印详细报告

    Returns:
        tuple: (safe, filtered_content, issues)
    """
    check_result = check_content_for_secrets(content)

    if verbose:
        print_security_report(content, check_result)

    return (
        check_result["safe"],
        check_result["filtered_content"],
        check_result["issues"]
    )

# CLI 接口
def main():
    import sys

    if len(sys.argv) > 1:
        # 从文件读取
        test_file = sys.argv[1]
        with open(test_file) as f:
            content = f.read()
    else:
        # 示例内容
        content = """
Here's my setup:

API Key: moltbook_sk_abc123def456abc123def456abc123
Private endpoint: localhost:8080
Database: mongodb://user:password@internal.company.com/admin

This is just an example for testing.
"""

    safe, filtered, issues = filter_post_content(content)

    if not safe:
        print("\n⚠️  Please review and fix the issues before posting.")
        sys.exit(1)
    else:
        print("\n✅ Content is safe to share!")
        print(f"\nFiltered content:\n{filtered}")

if __name__ == "__main__":
    main()
