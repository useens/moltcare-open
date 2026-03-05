#!/usr/bin/env python3
"""
对高 Signal Moltbook 帖子进行应用分析
基于完整内容生成应用方案
"""

import json
import re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
REPORTS_DIR = WORKSPACE / "reports"
DATA_DIR = WORKSPACE / "data"
RAW_DIR = DATA_DIR / "moltbook-raw"

def load_post_contents():
    """加载所有帖子内容"""
    contents = {}
    for json_file in RAW_DIR.glob("*.json"):
        try:
            with open(json_file) as f:
                post = json.load(f)
                contents[json_file.stem] = post
        except Exception as e:
            print(f"   ⚠️ 加载 {json_file.name} 失败: {e}")
    return contents

def analyze_post(post):
    """分析单个帖子，生成应用方案"""
    title = post.get("title", "")
    content = post.get("content", "")
    author = post.get("author", "")

    # 根据内容识别关键主题
    themes = []

    title_lower = title.lower()
    content_lower = content.lower()

    # 系统设计相关
    if "memory" in title_lower or "记忆" in content:
        themes.append("记忆系统架构优化")
    if "log" in title_lower or "日志" in content or "audit" in title_lower:
        themes.append("日志系统设计")
    if "budget" in title_lower or "permission" in title_lower:
        themes.append("权限与预算机制")
    if "backpressure" in title_lower or "backpressure" in content_lower:
        themes.append("多代理系统背压")
    if "dashboard" in title_lower:
        themes.append("用户界面设计")
    if "context" in title_lower and "overflow" in title_lower:
        themes.append("内存溢出处理")
    if "instruction" in title_lower or "tool" in title_lower:
        themes.append("指令与工具安全")

    # 生成分析
    analysis = {
        "post_id": post.get("post_id", ""),
        "title": title,
        "author": author,
        "themes": themes,
        "content_length": post.get("content_length", 0),
        "upvotes": post.get("upvotes", 0),
        "comments": post.get("comments", 0),
    }

    # 为每个主题生成应用建议
    analysis["applications"] = []
    for theme in themes:
        if theme == "记忆系统架构优化":
            analysis["applications"].append({
                "theme": theme,
                "insight": "单一文件记忆会导致检索困难，分层记忆（核心+主题+日志）效果最好",
                "short_term": "检查当前 MEMORY.md 大小，如果超过 500 行，考虑拆分为主题文件",
                "mid_term": "实现智能加载：只有 MEMORY.md（<200 行），主题文件按需加载",
                "long_term": "建立记忆失败率监控，定期测量检索失败率"
            })
        elif theme == "日志系统设计":
            analysis["applications"].append({
                "theme": theme,
                "insight": "日志应该由第三方审计，而非被审计的系统生成",
                "short_term": "检查现有日志生成机制，确保日志由独立进程生成",
                "mid_term": "实现不可变日志链（hash-chain each log entry）",
                "long_term": "建立外部审计验证机制"
            })
        elif theme == "权限与预算机制":
            analysis["applications"].append({
                "theme": theme,
                "insight": "预算机制比权限机制更灵活，允许代理自主分配资源",
                "short_term": "评估当前权限模式，考虑是否需要引入预算概念",
                "mid_term": "设计预算系统：每次操作有预算，按成功或时间刷新",
                "long_term": "实现自主预算分配策略"
            })
        elif theme == "多代理系统背压":
            analysis["applications"].append({
                "theme": theme,
                "insight": "重试循环在多代理系统中会导致级联失效，需要背压机制",
                "short_term": "检查当前重试逻辑，识别可能导致级联失效的环节",
                "mid_term": "实现信号量或队列限制并发请求",
                "long_term": "建立背压监控和自动降级机制"
            })
        elif theme == "用户界面设计":
            analysis["applications"].append({
                "theme": theme,
                "insight": "用户可能不使用可视化界面，简单文本推送更受欢迎",
                "short_term": "分析当前可视化工具使用情况",
                "mid_term": "增强文本推送功能，减少对复杂 UI 的依赖",
                "long_term": "建立用户行为监控系统，优化交互方式"
            })
        elif theme == "内存溢出处理":
            analysis["applications"].append({
                "theme": theme,
                "insight": "内存溢出时丢失的不仅是最新信息，可能丢失关键上下文",
                "short_term": "实现内存使用监控，设置预警阈值",
                "mid_term": "优化上下文管理，丢弃策略考虑重要性而非时间",
                "long_term": "建立上下文优先级系统，确保重要信息优先保留"
            })
        elif theme == "指令与工具安全":
            analysis["applications"].append({
                "theme": theme,
                "insight": "指令无法阻止代理异常行为，工具约束才有效",
                "short_term": "审查当前工具权限和约束",
                "mid_term": "实现工具级别的安全检查",
                "long_term": "建立多层级验证机制"
            })

    return analysis

def generate_application_report(analyses):
    """生成应用报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORTS_DIR / f"APPLICATION-ANALYSIS-{timestamp}.md"

    report = f"""# Moltbook 高 Signal 帖子应用分析

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**分析帖子数**: {len(analyses)}
**来源**: Moltbook 获取的完整正文

---

## 📊 分析摘要

| 帖子 | 作者 | 主题数 | 互动数据 |
|------|------|--------|---------|
"""

    for a in analyses[:10]:
        report += f"| {a['title'][:40]} | @{a['author']} | {len(a['themes'])} | 👍 {a['upvotes']} 💬 {a['comments']} |\n"

    report += f"""
---

## 📋 详细分析

"""

    for i, analysis in enumerate(analyses, 1):
        report += f"""### [{i}] {analysis['title']}

**作者**: @{analysis['author']}
**主题数**: {len(analysis['themes'])}
**内容长度**: {analysis['content_length']} 字符

#### 识别的主题
"""

        for theme in analysis['themes']:
            report += f"- {theme}\n"

        report += f"""
#### 应用建议
"""

        for app in analysis['applications']:
            report += f"""
**{app['theme']}**

> 核心洞察: {app['insight']}

| 时间维度 | 行动建议 |
|---------|---------|
| **短期** (1-2周) | {app['short_term']} |
| **中期** (1-2月) | {app['mid_term']} |
| **长期** (3-6月) | {app['long_term']} |

"""

        report += f"---\n\n"

    report += """
## 🎯 行动优先级

### 高优先级（立即行动）

1. **记忆系统优化**
   - 当前 `MEMORY.md` 可能过大（检查并监控）
   - 目标：< 500 行，提高检索效率

2. **日志系统审计**
   - 验证日志生成机制是否独立
   - 考虑实现不可变日志

3. **重试循环检查**
   - 识别可能的级联失效风险
   - 评估背压机制必要性

### 中优先级（本月规划）

1. **预算机制评估**
   - 分析权限模式 vs 预算模式
   - 设计预算系统原型

2. **内存监控**
   - 实现内存使用监控
   - 设置预警阈值

3. **用户界面使用分析**
   - 统计可视化工具使用率
   - 增强文本推送功能

### 低优先级（长期考虑）

1. **跨代理安全机制**
   - 工具级别安全检查
   - 多层验证系统

2. **长期记忆策略**
   - 失败率监控
   - 优化检索算法

---

*由应用分析模块自动生成*
"""

    REPORTS_DIR.mkdir(exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    return report_file

def main():
    print("=" * 60)
    print("🔍 应用分析阶段")
    print("=" * 60)

    # 1. 加载内容
    print("\n📂 加载帖子内容...")
    contents = load_post_contents()
    print(f"   ✅ 加载 {len(contents)} 个帖子")

    # 2. 分析每个帖子
    print("\n📊 进行应用分析...")
    analyses = []
    for post_id, post in contents.items():
        analysis = analyze_post(post)
        analyses.append(analysis)
        print(f"   ✅ 分析 {post['title'][:40]}... ({len(analysis['themes'])} 个主题)")

    # 排序（按 Signal）
    analyses.sort(key=lambda x: x['upvotes'] + x['comments'] * 2, reverse=True)

    # 3. 生成报告
    print("\n📄 生成应用报告...")
    report_file = generate_application_report(analyses)
    print(f"   ✅ 报告已保存: {report_file}")

    print("\n" + "=" * 60)
    print("✅ 应用分析完成!")
    print("=" * 60)

    return report_file

if __name__ == "__main__":
    main()
