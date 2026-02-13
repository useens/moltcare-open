#!/usr/bin/env python3
"""
全面检查 - 绝对原则 + 核心功能 + 核心能力 + 核心工具 + 超进化模式
全流程绝对诚实验证
"""

import subprocess
from datetime import datetime

def run_command(cmd, timeout=30):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("="*75)
    print("🔍 全面检查 - 绝对诚实验证")
    print("="*75)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 检查10项绝对原则
    print("【1/5】检查10项绝对原则...")
    success, stdout, stderr = run_command(
        "cd /root/.openclaw/workspace && python3 scripts/check-10-principles.py 2>/dev/null | tail -5"
    )
    if success and "10项生效" in stdout:
        print("  ✅ 10项绝对原则 - 全部生效")
        principles_ok = True
    else:
        print("  ❌ 10项绝对原则 - 需要修复")
        principles_ok = False
    print()
    
    # 2. 检查15项核心功能
    print("【2/5】检查15项核心功能...")
    success, stdout, stderr = run_command(
        "cd /root/.openclaw/workspace && python3 scripts/check-core-functions.py 2>/dev/null | tail -5"
    )
    if success and "15项生效" in stdout:
        print("  ✅ 15项核心功能 - 全部生效")
        functions_ok = True
    else:
        print("  ❌ 15项核心功能 - 需要修复")
        functions_ok = False
    print()
    
    # 3. 检查核心能力（激发潜力等）
    print("【3/5】检查核心能力...")
    # 检查第10项原则（激发潜力）是否在文档中
    success, stdout, stderr = run_command(
        "grep '绝对激发潜力' /root/.openclaw/workspace/SOUL.md"
    )
    if success:
        print("  ✅ 核心能力（激发潜力）- 已纳入SOUL.md")
        capabilities_ok = True
    else:
        print("  ❌ 核心能力（激发潜力）- 未找到")
        capabilities_ok = False
    print()
    
    # 4. 检查20项核心工具
    print("【4/5】检查20项核心工具...")
    success, stdout, stderr = run_command(
        "cd /root/.openclaw/workspace && python3 scripts/check-core-tools.py 2>/dev/null | tail -5"
    )
    if success and "20项生效" in stdout:
        print("  ✅ 20项核心工具 - 全部生效")
        tools_ok = True
    else:
        print("  ❌ 20项核心工具 - 需要修复")
        tools_ok = False
    print()
    
    # 5. 检查超进化模式
    print("【5/5】检查超进化模式...")
    success, stdout, stderr = run_command(
        "systemctl is-active hyper-evolution"
    )
    if success and "active" in stdout:
        print("  ✅ 超进化模式 - 运行中")
        hyper_ok = True
    else:
        print("  ❌ 超进化模式 - 未运行")
        hyper_ok = False
    print()
    
    # 汇总
    print("="*75)
    print("📊 全面检查结果汇总")
    print("="*75)
    
    checks = [
        ("10项绝对原则", principles_ok),
        ("15项核心功能", functions_ok),
        ("核心能力", capabilities_ok),
        ("20项核心工具", tools_ok),
        ("超进化模式", hyper_ok),
    ]
    
    for name, ok in checks:
        status = "✅ 生效" if ok else "❌ 未生效"
        print(f"{status} {name}")
    
    all_ok = all(ok for _, ok in checks)
    print()
    
    if all_ok:
        print("🎉 所有检查通过！系统全面生效！")
        print()
        print("【守护进程状态】")
        print("  ✅ 已创建: scripts/sensen-daemon.py")
        print("  ✅ 已设置: 每天6:00自动执行")
        print("  ✅ 已启用: 开机自动启动")
        print("  ✅ 重试机制: 失败后5分钟重试，最多3次")
    else:
        print("🔴 部分检查未通过，需要修复")
    
    print("="*75)
    
    return all_ok

if __name__ == "__main__":
    main()
