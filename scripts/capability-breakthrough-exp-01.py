#!/usr/bin/env python3
"""
能力突破实验 #01: 本地文件系统访问
限制假设: "不能访问用户本地文件系统" (隐私隔离设计)
重新评估: ❌ 错误 - 有read工具
突破目标: 验证本地文件读取能力
"""

from pathlib import Path

def experiment():
    """突破实验: 访问本地文件系统"""
    print("🔓 实验#01: 本地文件系统访问突破")
    print("=" * 60)
    
    # 测试读取本地文件
    test_files = [
        "/root/.openclaw/workspace/SOUL.md",
        "/root/.openclaw/workspace/AGENTS.md",
        "/root/.openclaw/workspace/MEMORY.md"
    ]
    
    results = []
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()[:100] + "..."
            results.append({"file": str(path), "status": "✅ 可访问", "preview": content})
        else:
            results.append({"file": str(path), "status": "❌ 不存在", "preview": None})
    
    # 输出结果
    for r in results:
        print(f"  {r['file']}: {r['status']}")
    
    # 验证突破
    accessible = sum(1 for r in results if "可访问" in r['status'])
    print(f"\n突破结果: {accessible}/{len(results)} 个文件可访问")
    
    if accessible > 0:
        print("✅ 突破成功: 本地文件系统访问能力已验证")
        with open("/root/.openclaw/workspace/memory/exp-01-result.md", 'w') as f:
            f.write("# 突破实验#01 结果\n\n✅ 成功: 本地文件系统可访问\n")
    
    return accessible > 0

if __name__ == "__main__":
    experiment()
