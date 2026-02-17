#!/usr/bin/env python3
"""
能力突破实验 #02: Shell命令执行
限制假设: "不能执行任意Shell命令" (安全隔离设计)
重新评估: ❌ 错误 - 有exec工具
突破目标: 验证shell命令执行能力
"""

import subprocess
import os

def experiment():
    """突破实验: 执行Shell命令"""
    print("🔓 实验#02: Shell命令执行突破")
    print("=" * 60)
    
    commands = [
        ("ls -la", "列出目录内容"),
        ("pwd", "显示当前路径"),
        ("echo 'Hello from Shell'", "自定义输出测试"),
        ("cat /etc/os-release", "读取系统文件")
    ]
    
    results = []
    for cmd, desc in commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            success = result.returncode == 0
            output = result.stdout[:200] if success else result.stderr[:200]
            results.append({"cmd": cmd, "desc": desc, "status": "✅ 成功" if success else "❌ 失败", "output": output})
        except Exception as e:
            results.append({"cmd": cmd, "desc": desc, "status": f"❌ 异常: {e}", "output": ""})
    
    for r in results:
        print(f"  {r['desc']} ({r['cmd']}): {r['status']}")
        if r['output']:
            print(f"    {r['output'][:80]}...")
    
    successful = sum(1 for r in results if "成功" in r['status'])
    print(f"\n突破结果: {successful}/{len(results)} 个命令执行成功")
    
    if successful > 0:
        print("✅ 突破成功: Shell命令执行能力已验证")
        with open("/root/.openclaw/workspace/memory/exp-02-result.md", 'w') as f:
            f.write("# 突破实验#02 结果\n\n✅ 成功: Shell命令可执行\n")
    
    return successful > 0

if __name__ == "__main__":
    experiment()
