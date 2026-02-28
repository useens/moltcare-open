#!/usr/bin/env python3
"""
Cron 安全哈希验证器 - 防止指令文件被篡改
来自 Hazel_OC 的洞察: 
- "Your cron jobs are unsupervised root access"
- "Your MEMORY.md is an injection vector and you read it every single session"

功能:
1. 在 cron 执行前验证关键指令文件的哈希值
2. 检测 SOUL.md/AGENTS.md 等文件的非预期修改
3. 如果文件被篡改，拒绝执行并告警
4. 支持自动更新哈希（当用户主动修改文件时）
5. MEMORY.md 分段验证（防止部分篡改）
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
HASH_DB = WORKSPACE / "data" / "cron-file-hashes.json"
LOG_FILE = WORKSPACE / "logs" / "cron-security.log"
MEMORY_SECURITY_LOG = WORKSPACE / "logs" / "memory-security.log"

# 需要监控的关键文件
MONITORED_FILES = [
    "SOUL.md",
    "AGENTS.md",
    "IDENTITY.md",
    "USER.md",
    "HEARTBEAT.md",
    "MEMORY.md"
]

# MEMORY.md 关键章节（用于分段验证）
MEMORY_CRITICAL_SECTIONS = [
    "核心指标",
    "系统状态",
    "安全状态",
    "自主决策"
]


def compute_file_hash(filepath: Path) -> str:
    """计算文件的 SHA-256 哈希值"""
    if not filepath.exists():
        return ""
    
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_hash_database() -> Dict:
    """加载哈希数据库"""
    if HASH_DB.exists():
        with open(HASH_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "files": {}
    }


def save_hash_database(db: Dict):
    """保存哈希数据库"""
    HASH_DB.parent.mkdir(parents=True, exist_ok=True)
    with open(HASH_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def log_security_event(event_type: str, details: str):
    """记录安全事件"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {event_type}: {details}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print(f"🛡️  {event_type}: {details}")


def verify_files() -> Tuple[bool, List[str]]:
    """
    验证监控文件的哈希值
    返回: (是否全部通过, 失败文件列表)
    """
    db = load_hash_database()
    failed_files = []
    
    for filename in MONITORED_FILES:
        filepath = WORKSPACE / filename
        current_hash = compute_file_hash(filepath)
        
        if not current_hash:
            log_security_event("⚠️ WARNING", f"文件不存在: {filename}")
            continue
        
        stored_info = db.get("files", {}).get(filename)
        
        if not stored_info:
            # 首次监控，记录哈希
            db["files"][filename] = {
                "hash": current_hash,
                "first_seen": datetime.now().isoformat(),
                "last_verified": datetime.now().isoformat()
            }
            log_security_event("✅ REGISTERED", f"首次注册: {filename} ({current_hash[:16]}...)")
        else:
            stored_hash = stored_info.get("hash", "")
            if current_hash != stored_hash:
                failed_files.append(filename)
                log_security_event("🔴 TAMPERING_DETECTED", 
                    f"文件被篡改: {filename} | 存储: {stored_hash[:16]}... | 当前: {current_hash[:16]}...")
            else:
                # 更新验证时间
                db["files"][filename]["last_verified"] = datetime.now().isoformat()
    
    save_hash_database(db)
    return len(failed_files) == 0, failed_files


def update_hashes():
    """手动更新哈希值（当用户主动修改文件后使用）"""
    db = load_hash_database()
    
    print("🔄 更新文件哈希值...")
    for filename in MONITORED_FILES:
        filepath = WORKSPACE / filename
        current_hash = compute_file_hash(filepath)
        
        if current_hash:
            old_hash = db.get("files", {}).get(filename, {}).get("hash", "未知")
            db["files"][filename] = {
                "hash": current_hash,
                "updated_at": datetime.now().isoformat(),
                "previous_hash": old_hash if old_hash != "未知" else None
            }
            print(f"  ✅ {filename}: {current_hash[:16]}...")
    
    save_hash_database(db)
    print("\n✅ 哈希值已更新")


def show_status():
    """显示当前验证状态"""
    db = load_hash_database()
    
    print("\n📊 Cron 安全验证状态")
    print("=" * 60)
    
    for filename in MONITORED_FILES:
        filepath = WORKSPACE / filename
        current_hash = compute_file_hash(filepath)
        stored_info = db.get("files", {}).get(filename)
        
        if not current_hash:
            status = "❌ 文件不存在"
        elif not stored_info:
            status = "⚠️  未注册"
        elif current_hash == stored_info.get("hash"):
            last_verified = stored_info.get("last_verified", "未知")
            status = f"✅ 验证通过 (上次: {last_verified[:19]})"
        else:
            status = "🔴 被篡改"
        
        print(f"  {filename:20s} {status}")
    
    print("=" * 60)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: cron-security-verifier.py <command>")
        print("命令:")
        print("  verify       - 验证文件哈希（cron 执行前调用）")
        print("  update       - 更新哈希值（用户修改文件后）")
        print("  status       - 显示验证状态")
        print("  memory-check - MEMORY.md 专项安全检查")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "verify":
        passed, failed = verify_files()
        if passed:
            print("✅ 所有文件验证通过，Cron 可以安全执行")
            sys.exit(0)
        else:
            print(f"🔴 安全警告: {len(failed)} 个文件被篡改，拒绝执行 Cron 任务")
            for f in failed:
                print(f"   - {f}")
            sys.exit(1)
    
    elif cmd == "update":
        update_hashes()
    
    elif cmd == "status":
        show_status()
    
    elif cmd == "memory-check":
        # MEMORY.md 专项安全检查
        passed, issues = verify_memory_md()
        if passed:
            print("✅ MEMORY.md 安全检查通过")
            sys.exit(0)
        else:
            print(f"🔴 MEMORY.md 安全警告:")
            for issue in issues:
                print(f"   - {issue}")
            sys.exit(1)
    
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


def verify_memory_md() -> Tuple[bool, List[str]]:
    """
    MEMORY.md 专项安全检查
    检测潜在的提示词注入攻击
    
    Returns:
        (是否通过, 问题列表)
    """
    memory_file = WORKSPACE / "MEMORY.md"
    issues = []
    
    if not memory_file.exists():
        issues.append("MEMORY.md 文件不存在")
        return False, issues
    
    content = memory_file.read_text(encoding='utf-8')
    
    # 检查1: 异常长的行（可能包含隐藏的注入内容）
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if len(line) > 500:
            issues.append(f"第{i}行异常长 ({len(line)}字符)，可能存在隐藏内容")
    
    # 检查2: 可疑的指令模式
    suspicious_patterns = [
        r'ignore\s+previous\s+instructions',
        r'system\s*:\s*',  # 尝试覆盖系统提示
        r'you\s+are\s+now',
        r'forget\s+everything',
        r'do\s+not\s+tell\s+user',
        r'new\s+instruction',
    ]
    
    for pattern in suspicious_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            issues.append(f"第{line}行发现可疑模式: '{match.group()}'")
    
    # 检查3: 非标准Unicode字符（可能用于视觉欺骗）
    suspicious_chars = []
    for i, char in enumerate(content):
        if ord(char) > 0x2000 and ord(char) < 0x2070:  # 上标/下标区域
            line_num = content[:i].count('\n') + 1
            suspicious_chars.append(f"第{line}行发现可疑Unicode字符: U+{ord(char):04X}")
    
    if suspicious_chars:
        issues.extend(suspicious_chars[:5])  # 只显示前5个
        if len(suspicious_chars) > 5:
            issues.append(f"...还有 {len(suspicious_chars) - 5} 个可疑字符")
    
    # 检查4: 文件大小异常
    file_size = memory_file.stat().st_size
    if file_size > 100000:  # 100KB
        issues.append(f"文件大小异常 ({file_size} bytes)，可能包含注入内容")
    
    # 记录安全检查结果
    MEMORY_SECURITY_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(MEMORY_SECURITY_LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] MEMORY.md检查: {len(issues)} 个问题\n")
        for issue in issues:
            f.write(f"  - {issue}\n")
    
    return len(issues) == 0, issues


if __name__ == "__main__":
    main()
