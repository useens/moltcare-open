#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保护清单检查机制
硬编码保护项，执行前强制检查
"""

import os
import sys
from pathlib import Path

# 工作目录
WORKSPACE = Path("/root/.openclaw/workspace")

# 🛡️ 绝对保护清单 - 不可精简
PROTECTED_ITEMS = {
    # 核心功能
    "github-backup-sync": [
        "scripts/github-backup-sync.py",
        "scripts/conditional-git-sync.sh",
        ".git/config",
        ".git/hooks",
    ],
    # 核心记忆系统
    "memory-core": [
        "memory/",
        "MEMORY.md",
    ],
    # 核心配置文件
    "core-config": [
        "AGENTS.md",
        "SOUL.md", 
        "USER.md",
        "IDENTITY.md",
        "TOOLS.md",
    ],
    # 学习债务处理
    "learning-debt": [
        "learning-debt.md",
        "knowledge-graph.md",
    ],
    # 心跳检查
    "heartbeat": [
        "scripts/unified-monitor.py",
    ],
    # 向量记忆
    "vector-memory": [
        "memory/vector/",
    ],
    # 自身服务
    "self-pruning": [
        "scripts/self-pruning/",
        "/etc/systemd/system/sensen-system-pruning.service",
    ],
}

def check_protection(target_path: str) -> tuple[bool, str]:
    """
    检查目标路径是否在保护清单中
    返回: (是否受保护, 保护原因)
    """
    target = Path(target_path).resolve()
    
    for category, items in PROTECTED_ITEMS.items():
        for item in items:
            protected = WORKSPACE / item if not item.startswith("/") else Path(item)
            protected = protected.resolve()
            
            # 检查是否是保护项本身或其子路径
            try:
                if target == protected or protected in target.parents or target in protected.rglob("*"):
                    return True, f"受保护类别: {category} ({item})"
            except:
                pass
                
            # 字符串匹配检查
            if str(target).startswith(str(protected)) or str(protected) in str(target):
                return True, f"受保护类别: {category} ({item})"
    
    return False, ""

def validate_pruning_list(pruning_list: list[str]) -> tuple[list[str], list[dict]]:
    """
    验证精简清单，分离安全项和受保护项
    返回: (安全项列表, 受保护项详情列表)
    """
    safe_items = []
    protected_found = []
    
    for item in pruning_list:
        is_protected, reason = check_protection(item)
        if is_protected:
            protected_found.append({
                "path": item,
                "reason": reason
            })
        else:
            safe_items.append(item)
    
    return safe_items, protected_found

def pre_execution_check() -> bool:
    """
    执行前全面检查
    返回: 是否通过检查
    """
    print("🔍 执行保护清单预检查...")
    
    all_protected_exist = True
    for category, items in PROTECTED_ITEMS.items():
        for item in items:
            path = WORKSPACE / item if not item.startswith("/") else Path(item)
            exists = path.exists()
            status = "✅" if exists else "❌"
            print(f"  {status} [{category}] {item}")
            if not exists and category != "vector-memory":  # vector-memory可能不存在
                all_protected_exist = False
    
    if not all_protected_exist:
        print("⚠️ 警告: 部分保护项不存在，请检查系统完整性")
    
    print("✅ 保护清单检查完成")
    return True

def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: protected-check.py [check|validate <file>]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        if pre_execution_check():
            print("✅ 保护检查通过，可以执行精简")
            sys.exit(0)
        else:
            print("❌ 保护检查失败")
            sys.exit(1)
    
    elif command == "validate" and len(sys.argv) > 2:
        # 从文件读取精简清单
        list_file = sys.argv[2]
        with open(list_file, 'r') as f:
            pruning_list = [line.strip() for line in f if line.strip()]
        
        safe, protected = validate_pruning_list(pruning_list)
        
        print(f"精简清单验证结果:")
        print(f"  安全项: {len(safe)}")
        print(f"  受保护项: {len(protected)}")
        
        if protected:
            print("\n🛡️ 以下项目受保护，将被跳过:")
            for p in protected:
                print(f"  - {p['path']} ({p['reason']})")
        
        # 输出安全清单
        safe_file = list_file + ".safe"
        with open(safe_file, 'w') as f:
            for item in safe:
                f.write(item + "\n")
        print(f"\n安全清单已保存: {safe_file}")
        
    else:
        print("未知命令")
        sys.exit(1)

if __name__ == "__main__":
    main()
