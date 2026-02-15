#!/usr/bin/env python3
"""
Skill Audit Tool v1.0
技能审计工具 - 检查技能使用情况并生成审计报告

Usage:
    python3 skill-audit.py [--full]
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

WORKSPACE = Path("/root/.openclaw/workspace")
SKILLS_DIR = WORKSPACE / "skills"
REPORTS_DIR = WORKSPACE / "reports"
MEMORY_DIR = WORKSPACE / "memory"

def get_all_skills():
    """获取所有技能目录"""
    skills = []
    if SKILLS_DIR.exists():
        for item in SKILLS_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    skills.append({
                        "name": item.name,
                        "path": item,
                        "skill_file": skill_file,
                        "size": sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    })
    return skills

def check_skill_usage(skill_name):
    """检查技能使用情况"""
    usage_count = 0
    usage_locations = []
    
    # 要搜索的文件模式
    search_patterns = [
        rf"\b{re.escape(skill_name)}\b",
        rf"skill.*{re.escape(skill_name)}",
        rf"{re.escape(skill_name)}.*skill",
    ]
    
    # 搜索关键文件
    key_files = [
        WORKSPACE / "AGENTS.md",
        WORKSPACE / "MEMORY.md",
        WORKSPACE / "TOOLS.md",
    ]
    
    # 搜索memory目录
    memory_files = list(MEMORY_DIR.rglob("*.md")) if MEMORY_DIR.exists() else []
    
    all_files = key_files + memory_files[:50]  # 限制搜索范围
    
    for file_path in all_files:
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                for pattern in search_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        usage_count += 1
                        usage_locations.append({
                            "file": str(file_path.relative_to(WORKSPACE)),
                            "line": content[:match.start()].count('\n') + 1
                        })
            except Exception:
                pass
    
    return usage_count, usage_locations

def analyze_skill(skill):
    """分析单个技能"""
    skill_name = skill["name"]
    
    # 读取SKILL.md
    skill_content = skill["skill_file"].read_text(encoding='utf-8')
    
    # 提取描述
    description = ""
    desc_match = re.search(r'<description>(.*?)</description>', skill_content, re.DOTALL)
    if desc_match:
        description = desc_match.group(1).strip()
    
    # 检查使用频率
    usage_count, usage_locations = check_skill_usage(skill_name)
    
    # 判断使用状态
    if usage_count >= 5:
        status = "high_usage"
    elif usage_count >= 1:
        status = "used"
    else:
        # 进一步检查是否有脚本引用
        status = check_scripts_reference(skill_name)
    
    return {
        "name": skill_name,
        "description": description[:200] + "..." if len(description) > 200 else description,
        "size_kb": skill["size"] / 1024,
        "usage_count": usage_count,
        "usage_locations": usage_locations[:5],  # 只保留前5个
        "status": status,
        "recommendation": get_recommendation(status, usage_count)
    }

def check_scripts_reference(skill_name):
    """检查脚本是否引用该技能"""
    scripts_dir = WORKSPACE / "scripts"
    if not scripts_dir.exists():
        return "unused"
    
    for script in scripts_dir.glob("*.py"):
        try:
            content = script.read_text(encoding='utf-8')
            if skill_name.lower() in content.lower():
                return "script_used"
        except:
            pass
    
    return "unused"

def get_recommendation(status, usage_count):
    """获取建议"""
    recommendations = {
        "high_usage": "✅ 高频使用，保留",
        "used": "🟡 偶尔使用，保留",
        "script_used": "🟡 脚本引用，保留",
        "unused": "🔴 未使用，可考虑删除"
    }
    return recommendations.get(status, "未知")

def generate_report(skills_data):
    """生成审计报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORTS_DIR / f"skill-audit-{timestamp}.md"
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # 分类统计
    high_usage = [s for s in skills_data if s["status"] == "high_usage"]
    used = [s for s in skills_data if s["status"] == "used"]
    script_used = [s for s in skills_data if s["status"] == "script_used"]
    unused = [s for s in skills_data if s["status"] == "unused"]
    
    total_size = sum(s["size_kb"] for s in skills_data)
    unused_size = sum(s["size_kb"] for s in unused)
    
    report = f"""# 技能审计报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**总技能数**: {len(skills_data)}
**总大小**: {total_size:.1f} KB

## 统计概览

| 类别 | 数量 | 大小 | 占比 |
|------|------|------|------|
| ✅ 高频使用 | {len(high_usage)} | {sum(s['size_kb'] for s in high_usage):.1f} KB | {len(high_usage)/len(skills_data)*100:.1f}% |
| 🟡 偶尔使用 | {len(used)} | {sum(s['size_kb'] for s in used):.1f} KB | {len(used)/len(skills_data)*100:.1f}% |
| 🟡 脚本引用 | {len(script_used)} | {sum(s['size_kb'] for s in script_used):.1f} KB | {len(script_used)/len(skills_data)*100:.1f}% |
| 🔴 未使用 | {len(unused)} | {unused_size:.1f} KB | {len(unused)/len(skills_data)*100:.1f}% |

## 🔴 建议删除的技能（未使用）

"""
    
    if unused:
        for skill in sorted(unused, key=lambda x: x["size_kb"], reverse=True):
            report += f"""### {skill['name']}
- **大小**: {skill['size_kb']:.1f} KB
- **描述**: {skill['description']}
- **删除命令**: `rm -rf skills/{skill['name']}/`

"""
    else:
        report += "未发现完全未使用的技能。\n"
    
    report += f"""
## 🟡 偶尔使用的技能

"""
    
    for skill in sorted(used, key=lambda x: x["usage_count"], reverse=True):
        report += f"- **{skill['name']}**: {skill['usage_count']} 次引用\n"
    
    report += f"""
## ✅ 高频使用的技能

"""
    
    for skill in sorted(high_usage, key=lambda x: x["usage_count"], reverse=True):
        report += f"- **{skill['name']}**: {skill['usage_count']} 次引用\n"
    
    report += f"""
## 📊 磁盘空间优化建议

- **可释放空间**: {unused_size:.1f} KB ({unused_size/1024:.2f} MB)
- **建议操作**: 删除未使用技能后可节省 {unused_size/total_size*100:.1f}% 空间

## 📝 后续行动

1. 审查 🔴 未使用技能列表
2. 确认无用后执行删除
3. 更新 AGENTS.md 中的技能列表
4. 定期重新运行审计（建议每月一次）

---
*报告生成: skill-audit.py*
"""
    
    report_file.write_text(report, encoding='utf-8')
    print(f"📊 审计报告已保存: {report_file}")
    
    return report_file

def main():
    print("="*60)
    print("🔍 技能审计工具启动")
    print("="*60)
    
    # 获取所有技能
    skills = get_all_skills()
    print(f"\n发现 {len(skills)} 个技能")
    
    # 分析每个技能
    skills_data = []
    for i, skill in enumerate(skills, 1):
        print(f"[{i}/{len(skills)}] 分析 {skill['name']}...", end=' ')
        data = analyze_skill(skill)
        skills_data.append(data)
        print(f"{data['status']} ({data['usage_count']} 次引用)")
    
    # 生成报告
    report_file = generate_report(skills_data)
    
    # 打印摘要
    print("\n" + "="*60)
    print("📈 审计摘要")
    print("="*60)
    
    high = len([s for s in skills_data if s["status"] == "high_usage"])
    used = len([s for s in skills_data if s["status"] == "used"])
    script = len([s for s in skills_data if s["status"] == "script_used"])
    unused = len([s for s in skills_data if s["status"] == "unused"])
    
    print(f"✅ 高频使用: {high} 个")
    print(f"🟡 偶尔使用: {used} 个")
    print(f"🟡 脚本引用: {script} 个")
    print(f"🔴 未使用: {unused} 个")
    print(f"\n可释放空间: {sum(s['size_kb'] for s in skills_data if s['status'] == 'unused'):.1f} KB")
    print("="*60)

if __name__ == "__main__":
    main()
