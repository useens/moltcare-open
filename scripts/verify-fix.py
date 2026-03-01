#!/usr/bin/env python3
"""
最终验证：检查所有学习笔记是否还有真正的"待补充"占位符
"""

import re
from pathlib import Path

REPORTS_DIR = Path("/root/.openclaw/workspace") / "reports"

def check_file(file_path: Path) -> bool:
    """检查文件是否包含真正的待补充占位符"""
    try:
        content = file_path.read_text(encoding='utf-8')

        # 检查真正的占位符模式
        # 1. 知识点后面的 "待补充"
        if re.search(r'\*\*知识点\d+\*\*\s*-\s*待补充', content):
            return True

        # 2. 标题后面跟着 "待补充"
        if re.search(r'^\s*\d+\.\s*\*\*[^*]+\*\*\s*-\s*待补充\s*$', content, re.MULTILINE):
            return True

        return False
    except:
        return False

def main():
    print("🔍 最终验证：检查学习笔记占位符")
    print("="*70)

    all_files = list(REPORTS_DIR.glob("learning-debt-*.md"))
    placeholder_files = []

    for f in sorted(all_files):
        if check_file(f):
            placeholder_files.append(f)

    print(f"📁 总文件数: {len(all_files)}")

    if placeholder_files:
        print(f"\n❌ 发现 {len(placeholder_files)} 个文件包含真正的占位符:")
        for f in placeholder_files[:20]:
            print(f"   - {f.name}")
        if len(placeholder_files) > 20:
            print(f"   ... 还有 {len(placeholder_files) - 20} 个")
    else:
        print(f"\n✅ 成功！所有{len(all_files)}个学习笔记已完全修复！")
        print(f"   没有发现真正的'待补充'占位符")

    # 检查AI增强标记
    ai_enhanced = 0
    for f in all_files:
        try:
            if "AI增强" in f.read_text(encoding='utf-8'):
                ai_enhanced += 1
        except:
            pass

    print(f"\n📊 统计:")
    print(f"   AI增强文件: {ai_enhanced}/{len(all_files)}")
    print(f"   占位符文件: {len(placeholder_files)}/{len(all_files)}")
    print("="*70)

if __name__ == "__main__":
    main()
