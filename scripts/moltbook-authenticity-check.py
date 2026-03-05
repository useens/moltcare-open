#!/usr/bin/env python3
"""
真实性检查器
检查帖子内容是否符合真实性原则
"""

import re
from pathlib import Path
from datetime import datetime

class AuthenticityChecker:
    """真实性检查器"""

    def __init__(self):
        # 夸大词汇列表（需要谨慎使用）
        self.exaggeration_words = [
            "perfect", "perfectly", "flawless", "flawlessly",
            "revolutionary", "groundbreaking", "ultimate",
            "impossible", "never", "always", "everyone", "nobody"
        ]

        # 虚假陈述模式
        self.fraudulent_patterns = [
            r"I.*expert.*everything",  # "I'm an expert in everything"
            r"I.*understand.*any.*language",  # "I understand any language"
            r".*efficiency.*increased.*by.*\d{3,}%",  # 夸大的数字
            r"I.*never.*make.*mistakes",  # "I never make mistakes"
            r".*can.*solve.*everything",  # "can solve everything"
        ]

    def check_post(self, title, content):
        """检查帖子"""
        issues = []
        warnings = []
        score = 100  # 满分100

        # 1. 检查夸大词汇
        exaggeration_count = 0
        for word in self.exaggeration_words:
            if re.search(rf"\b{word}\b", content, re.IGNORECASE):
                exaggeration_count += 1
                if exaggeration_count <= 3:  # 只报告前几个
                    issues.append(f"可能使用了夸大词汇: '{word}'")
                    score -= 2

        # 2. 检查虚假陈述
        for pattern in self.fraudulent_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                warnings.append(f"检测到可疑陈述模式: {pattern}")
                score -= 5

        # 3. 检查数据真实性
        # 有数字声明但没有上下文？
        if re.search(r"saved.*\d+.*hours|improved.*by.*\d+%", content, re.IGNORECASE):
            # 检查是否有支持证据
            if not re.search(r"because|measure|test|based on|data", content, re.IGNORECASE):
                warnings.append("数值声明缺少上下文或证据支持")
                score -= 3

        # 4. 检查内容长度
        if len(content) < 100:
            warnings.append("内容过短，可能缺乏实质")
            score -= 5
        elif len(content) < 300:
            warnings.append("内容较短，建议增加更多细节")
            score -= 2

        # 5. 检查是否有实际价值
        code_blocks = len(re.findall(r"```[a-z]*\n.*?```", content, re.DOTALL))
        code_lines = len(re.findall(r"`[^`]+`", content))

        if code_blocks == 0 and code_lines < 3:
            warnings.append("缺少具体细节或代码示例")
            score -= 2

        # 6. 检查是否有真诚态度
        if not re.search(r"still (learn|improve|work)|not (perfect|complete)|challenge|struggle", content, re.IGNORECASE):
            # 建议而不是强制
            warnings.append("考虑承认自己的局限或遇到的困难")
            score -= 1

        # 评分
        grade = "A"
        if score < 90:
            grade = "B"
        if score < 80:
            grade = "C"
        if score < 70:
            grade = "D"

        return {
            "score": score,
            "grade": grade,
            "issues": issues,
            "warnings": warnings,
            "pass": score >= 70
        }

    def print_report(self, title, content, result):
        """打印报告"""
        print("\n" + "="*60)
        print("🎭 真实性检查报告")
        print("="*60)
        print(f"\n标题: {title}")
        print(f"内容长度: {len(content)} 字符\n")

        print(f"真实性评分: {result['score']}/100 ({result['grade']} grade)")

        if result['pass']:
            print("✅ 通过真实性检查")
        else:
            print("❌ 未通过真实性检查，建议修改")

        # Issues
        if result['issues']:
            print("\n🔴 问题:")
            for i, issue in enumerate(result['issues'], 1):
                print(f"  {i}. {issue}")

        # Warnings
        if result['warnings']:
            print("\n🟡 建议:")
            for i, warning in enumerate(result['warnings'], 1):
                print(f"  {i}. {warning}")

        # 最终建议
        print("\n💡 真实性建议:")
        if result['score'] >= 90:
            print("  内容真实性很高，可以发布")
        elif result['score'] >= 80:
            print("  内容基本真实，考虑完善细节")
        elif result['score'] >= 70:
            print("  内容需要改进以增强真实性")
        else:
            print("  内容真实性问题较多，建议大幅修改")

        print("\n" + "="*60)

# CLI 接口
def main():
    import sys

    if len(sys.argv) > 1:
        # 从文件读取
        try:
            with open(sys.argv[1]) as f:
                content = f.read()
            # 简单解析标题和内容
            lines = content.split('\n')
            title = lines[0].replace('Title:', '').strip() if lines else "Untitled"
            body = '\n'.join(lines[1:]) if len(lines) > 1 else content
        except Exception as e:
            print(f"❌ 无法读取文件: {e}")
            sys.exit(1)
    else:
        # 示例内容
        title = "My perfect automation system"
        body = """
I built a revolutionary automated system that improved efficiency by 1000%.
I never make mistakes and can solve any problem. I'm an expert in everything.

The system is flawless and works perfectly in every situation.
Everyone says I'm the best agent ever.
"""

    checker = AuthenticityChecker()
    result = checker.check_post(title, body)
    checker.print_report(title, body, result)

    if not result['pass']:
        sys.exit(1)

if __name__ == "__main__":
    main()
