#!/usr/bin/env python3
"""
批量修复所有学习笔记的脚本
处理所有日期的学习笔记，消除"待补充"占位符，填充AI智能提取的内容
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# Configuration
WORKSPACE = Path("/root/.openclaw/workspace")
REPORTS_DIR = WORKSPACE / "reports"
MEMORY_DIR = WORKSPACE / "memory"

# 导入AI知识提取器
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# 导入已有的AI增强系统
try:
    from ai_powered_learning_note_fix import (
        AIKnowledgeExtractor,
        extract_topics_by_date_range,
        generate_ai_enhanced_learning_note
    )
    AI_SYSTEM_AVAILABLE = True
except ImportError:
    AI_SYSTEM_AVAILABLE = False


def extract_all_topics_from_debt() -> Dict[str, List[Dict]]:
    """
    从learning-debt.md中提取所有主题，按日期分类
    """
    debt_file = MEMORY_DIR / "learning-debt.md"
    if not debt_file.exists():
        return {}

    content = debt_file.read_text(encoding='utf-8')
    topics_by_date = defaultdict(list)

    # Pattern to extract list format entries
    list_pattern = r'- \[([ x])\]\s*\*\*([^*]+)\*\*\s*- Signal (\d+)/10\s*\n\s*- 来源:\s*(\w+)\s+@(\w+)\s*\n\s*- 链接:\s*(https://[^\n]+)\s*\n\s*- 添加:\s*(\d{4}-\d{2}-\d{2}[^\n]*)'

    for match in re.finditer(list_pattern, content):
        status, title, signal, source, author, url, added_date = match.groups()
        signal = int(signal)

        # 提取日期部分（用于文件匹配）
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', added_date)
        if date_match:
            date_str = date_match.group(1)
        else:
            date_str = added_date[:10]

        topics_by_date[date_str].append({
            "title": title.strip(),
            "signal": signal,
            "source": source.strip(),
            "author": author.strip(),
            "url": url.strip(),
            "added_date": added_date.strip(),
            "status": "completed" if status == 'x' else "pending"
        })

    return dict(topics_by_date)


def get_date_from_filename(filename: str) -> Optional[str]:
    """从文件名提取日期"""
    # Pattern: learning-debt-20260222-001.md
    match = re.search(r'(\d{8})', filename)
    if match:
        date_str = match.group(1)
        # Convert to YYYY-MM-DD
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None


def needs_fixing(file_path: Path) -> bool:
    """检查文件是否需要修复"""
    try:
        content = file_path.read_text(encoding='utf-8')
        # 检查是否包含"待补充"
        if "待补充" in content:
            return True
        # 检查是否不是AI增强版本
        if "AI增强" not in content:
            return True
    except Exception as e:
        return True
    return False


def fix_single_note(file_path: Path, topic_data: Dict, extractor: AIKnowledgeExtractor) -> bool:
    """修复单个学习笔记"""
    try:
        task_id = file_path.stem.replace("learning-debt-", "")
        enhanced_note = generate_ai_enhanced_learning_note(topic_data, task_id, extractor)

        # 写入文件
        file_path.write_text(enhanced_note, encoding='utf-8')

        return True
    except Exception as e:
        print(f"   ❌ 修复失败: {e}")
        return False


def main():
    """主函数：修复所有学习笔记"""
    print("🚀 批量AI增强修复所有学习笔记")
    print("="*70)

    if not AI_SYSTEM_AVAILABLE:
        print("❌ AI系统模块不可用")
        return

    # 提取所有学习债务
    print("📖 正在从learning-debt.md提取所有主题...")
    topics_by_date = extract_all_topics_from_debt()

    total_topics = sum(len(topics) for topics in topics_by_date.values())
    print(f"✅ 提取了 {total_topics} 条学习债务，涵盖 {len(topics_by_date)} 个日期")

    # 查找所有学习笔记文件
    learning_files = list(REPORTS_DIR.glob("learning-debt-*.md"))
    print(f"📁 找到 {len(learning_files)} 个学习笔记文件")

    # 初始化AI知识提取器
    extractor = AIKnowledgeExtractor()

    # 统计结果
    fixed_count = 0
    skipped_count = 0
    failed_count = 0
    no_topic_count = 0

    # 批量处理
    for file_path in sorted(learning_files):
        filename = file_path.name

        # 检查是否需要修复
        if not needs_fixing(file_path):
            print(f"♻️  {filename}: 已是AI增强版本，跳过")
            skipped_count += 1
            continue

        # 提取日期
        date_str = get_date_from_filename(filename)
        if not date_str:
            print(f"⚠️  {filename}: 无法提取日期，跳过")
            skipped_count += 1
            continue

        # 查找对应的学习债务
        if date_str not in topics_by_date or not topics_by_date[date_str]:
            print(f"⚠️  {filename}: 没有找到 {date_str} 的学习债务")
            no_topic_count += 1
            continue

        topics = topics_by_date[date_str]

        print(f"\n🔍 处理 {filename} ({date_str})")

        # 简单匹配：使用文件名中的序号来分配主题
        # 提取序号：learning-debt-20260222-001.md -> 001
        seq_match = re.search(r'-(\d+)\\.md$', filename)
        seq_num = int(seq_match.group(1)) if seq_match else 0

        # 找到对应的主题（按序号匹配）
        topic_index = min(seq_num - 1, len(topics) - 1) if seq_num > 0 else 0
        topic_data = topics[topic_index]

        print(f"   主题: {topic_data['title'][:50]}...")
        print(f"   作者: @{topic_data['author']}, Signal: {topic_data['signal']}")

        # 修复学习笔记
        if fix_single_note(file_path, topic_data, extractor):
            print(f"   ✅ 修复成功")
            fixed_count += 1
        else:
            print(f"   ❌ 修复失败")
            failed_count += 1

    # 输出统计结果
    print(f"\n{'='*70}")
    print("📊 批量修复结果统计:")
    print(f"   ✅ 已修复: {fixed_count}")
    print(f"   ♻️  已跳过: {skipped_count}")
    print(f"   ❌ 修复失败: {failed_count}")
    print(f"   ⚠️  缺失主题: {no_topic_count}")
    print(f"   📄 总文件数: {len(learning_files)}")
    print('='*70)

    if fixed_count > 0:
        print(f"\n🎉 成功修复了 {fixed_count} 个学习笔记！")
        print("   所有'待补充'占位符已被实质性内容替换")

    # 检查是否还有未修复的文件
    remaining = [f for f in learning_files if needs_fixing(f)]
    if remaining:
        print(f"\n⚠️  还有 {len(remaining)} 个文件需要修复:")
        for f in remaining[:5]:  # 只显示前5个
            print(f"   - {f.name}")
        if len(remaining) > 5:
            print(f"   ... 还有 {len(remaining) - 5} 个")
    else:
        print("\n✨ 所有学习笔记已全部完成AI增强！")


if __name__ == "__main__":
    main()
