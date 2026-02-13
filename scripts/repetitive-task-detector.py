#!/usr/bin/env python3
"""
重复任务检测器 v1.0
分析执行历史，发现重复任务模式
"""
import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
EVOLUTION_DIR = MEMORY_DIR / "evolution" / "2026-02"
DAILY_DIR = MEMORY_DIR / "daily"

class RepetitiveTaskDetector:
    """重复任务检测器"""
    
    # 重复任务模式定义
    REPETITIVE_PATTERNS = {
        "backup": {
            "keywords": ["备份", "backup", "git push", "同步", "sync"],
            "category": "备份相关",
            "frequency": "每30分钟",
            "priority": "高"
        },
        "health_check": {
            "keywords": ["健康检查", "health", "检查", "check", "监控", "monitor"],
            "category": "健康检查",
            "frequency": "每2小时",
            "priority": "高"
        },
        "memory_consolidation": {
            "keywords": ["记忆整理", "memory", "consolidation", "归档", "archive", "整理", "compress"],
            "category": "记忆整理",
            "frequency": "每3小时",
            "priority": "中"
        },
        "intel_collection": {
            "keywords": ["情报", "intel", "收集", "collect", "Moltbook", "HackerNews", "GitHub", "扫描", "sca"],
            "category": "情报收集",
            "frequency": "每4小时",
            "priority": "中"
        },
        "evolution": {
            "keywords": ["进化", "evolution", "轻量进化", "全量进化", "夜间进化", "深度学习"],
            "category": "进化任务",
            "frequency": "每4-8小时",
            "priority": "高"
        },
        "log_cleanup": {
            "keywords": ["日志", "log", "清理", "cleanup", "清理", "归档"],
            "category": "日志清理",
            "frequency": "每周",
            "priority": "低"
        },
        "system_maintenance": {
            "keywords": ["维护", "maintenance", "优化", "优化", "清理", "cleanup", "压缩", "compact"],
            "category": "系统维护",
            "frequency": "每天",
            "priority": "中"
        },
        "vector_maintenance": {
            "keywords": ["向量", "vector", "嵌入", "embedding", "语义", "semantic", "v5.2"],
            "category": "向量维护",
            "frequency": "每小时",
            "priority": "高"
        }
    }
    
    def __init__(self):
        self.findings = defaultdict(lambda: {"count": 0, "files": [], "last_occurrence": None})
        
    def analyze_daily_logs(self, days: int = 7) -> Dict:
        """分析最近N天的日志"""
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # 查找当天的日志文件
            for log_file in DAILY_DIR.glob(f"{date_str}*.md"):
                self._analyze_file(log_file, date_str)
        
        return dict(self.findings)
    
    def _analyze_file(self, file_path: Path, date_str: str):
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for pattern_name, pattern_config in self.REPETITIVE_PATTERNS.items():
                for keyword in pattern_config["keywords"]:
                    if keyword.lower() in content.lower():
                        self.findings[pattern_name]["count"] += 1
                        if str(file_path) not in self.findings[pattern_name]["files"]:
                            self.findings[pattern_name]["files"].append(str(file_path.name))
                        self.findings[pattern_name]["last_occurrence"] = date_str
                        break
                        
        except Exception as e:
            print(f"分析文件失败 {file_path}: {e}")
    
    def analyze_evolution_archives(self) -> Dict:
        """分析进化档案"""
        if not EVOLUTION_DIR.exists():
            return {}
            
        for ev_file in EVOLUTION_DIR.glob("EV-*.md"):
            date_match = re.search(r'(\d{4})(\d{2})(\d{2})', ev_file.name)
            if date_match:
                date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                self._analyze_file(ev_file, date_str)
        
        return dict(self.findings)
    
    def get_automation_coverage(self) -> Dict:
        """获取当前自动化覆盖率"""
        coverage = {}
        
        for pattern_name, pattern_config in self.REPETITIVE_PATTERNS.items():
            findings = self.findings.get(pattern_name, {})
            count = findings.get("count", 0)
            
            # 判断自动化程度
            if count == 0:
                automation_level = "未检测到"
            elif count >= 10:
                automation_level = "高度自动化"
            elif count >= 5:
                automation_level = "部分自动化"
            else:
                automation_level = "手动为主"
            
            coverage[pattern_name] = {
                "category": pattern_config["category"],
                "detected_count": count,
                "frequency": pattern_config["frequency"],
                "priority": pattern_config["priority"],
                "automation_level": automation_level,
                "keywords": pattern_config["keywords"]
            }
        
        return coverage
    
    def generate_report(self) -> str:
        """生成检测报告"""
        self.analyze_daily_logs(days=7)
        self.analyze_evolution_archives()
        coverage = self.get_automation_coverage()
        
        report = []
        report.append("# 重复任务模式检测报告")
        report.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**分析周期**: 过去7天")
        report.append(f"**数据来源**: 每日日志 + 进化档案")
        report.append("")
        
        report.append("## 📊 检测到的重复任务模式")
        report.append("")
        
        # 按优先级排序
        priority_order = {"高": 0, "中": 1, "低": 2}
        sorted_coverage = sorted(
            coverage.items(),
            key=lambda x: (priority_order.get(x[1]["priority"], 3), -x[1]["detected_count"])
        )
        
        for pattern_name, info in sorted_coverage:
            if info["detected_count"] > 0:
                report.append(f"### {info['category']} ({info['priority']}优先级)")
                report.append(f"- **检测次数**: {info['detected_count']}")
                report.append(f"- **建议频率**: {info['frequency']}")
                report.append(f"- **自动化程度**: {info['automation_level']}")
                report.append("")
        
        report.append("## 📈 自动化覆盖率统计")
        report.append("")
        
        levels = defaultdict(list)
        for pattern_name, info in coverage.items():
            levels[info["automation_level"]].append(info["category"])
        
        for level, categories in sorted(levels.items()):
            report.append(f"### {level}")
            for cat in categories:
                report.append(f"- {cat}")
            report.append("")
        
        # 计算总体覆盖率
        total = len(coverage)
        highly_automated = len([c for c in coverage.values() if c["automation_level"] == "高度自动化"])
        coverage_rate = (highly_automated / total * 100) if total > 0 else 0
        
        report.append("## 🎯 覆盖率评估")
        report.append("")
        report.append(f"- **总任务类别**: {total}")
        report.append(f"- **高度自动化**: {highly_automated}")
        report.append(f"- **当前覆盖率**: {coverage_rate:.0f}%")
        report.append("")
        
        if coverage_rate >= 80:
            report.append("**评估**: ✅ 自动化水平优秀")
        elif coverage_rate >= 60:
            report.append("**评估**: ⚠️ 自动化水平良好，仍有提升空间")
        else:
            report.append("**评估**: 🔧 需要加强自动化建设")
        
        return "\n".join(report)


def main():
    """主函数"""
    detector = RepetitiveTaskDetector()
    report = detector.generate_report()
    print(report)
    
    # 保存报告
    output_file = WORKSPACE / "memory" / "optimization" / "repetitive-tasks-report.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(report)
    print(f"\n报告已保存: {output_file}")


if __name__ == "__main__":
    main()
