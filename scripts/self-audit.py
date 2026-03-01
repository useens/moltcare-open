#!/usr/bin/env python3
"""
森森自我审计系统 v1.0
每周全面检测: 假优化、无效内容、空转任务、冗余代码、错误数据、架构混乱
"""

import os
import sys
import json
import subprocess
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Set
import logging

WORKSPACE = Path("/root/.openclaw/workspace")
REPORTS_DIR = WORKSPACE / "reports" / "self-audit"

def setup_logging():
    """设置日志"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = REPORTS_DIR / f"audit-{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__), timestamp


class AuditCheck:
    """审计检查基类"""
    def __init__(self, name: str):
        self.name = name
        self.issues = []
        self.warnings = []
        self.metrics = {}
    
    def run(self) -> Tuple[List[str], List[str], Dict]:
        """返回 (问题列表, 警告列表, 指标字典)"""
        raise NotImplementedError


class FalseOptimizationAudit(AuditCheck):
    """检测假优化: 声称已做但实际未生效的内容"""
    
    def __init__(self):
        super().__init__("假优化检测")
    
    def run(self) -> Tuple[List[str], List[str], Dict]:
        issues = []
        warnings = []
        metrics = {"checked_items": 0, "false_optimizations": 0}
        
        # 检查1: 文档声称的脚本是否存在
        claimed_replacements = {
            "scripts/unified-monitor.py": [
                "scripts/health-monitor-v5.py",
                "scripts/auto-health-check.py",
                "scripts/memory-guardian.py",
                "scripts/auto_fix_system.py",
                "scripts/self-diagnosis.py",
                "scripts/advanced_diagnosis.py",
                "scripts/comprehensive-check.py",
                "scripts/diagnosis_service.py",
                "scripts/auto-heal.py"
            ]
        }
        
        for main_script, replacements in claimed_replacements.items():
            main_path = WORKSPACE / main_script
            if main_path.exists():
                content = main_path.read_text()
                for replacement in replacements:
                    metrics["checked_items"] += 1
                    if replacement in content and "已删除" in content:
                        # 检查实际是否已删除
                        rep_path = WORKSPACE / replacement
                        if rep_path.exists():
                            issues.append(f"假优化: {main_script} 声称已替代 {replacement}，但该文件仍存在")
                            metrics["false_optimizations"] += 1
        
        # 检查2: MEMORY.md中的数据是否与实际一致
        memory_md = WORKSPACE / "MEMORY.md"
        if memory_md.exists():
            content = memory_md.read_text()
            
            # 检查记忆数量
            long_term = WORKSPACE / "memory" / "vector" / "long_term_memories.json"
            if long_term.exists():
                try:
                    data = json.loads(long_term.read_text())
                    actual_count = len(data) if isinstance(data, dict) else len(data)
                    # 查找MEMORY.md中声称的数量
                    import re
                    memory_matches = re.findall(r'\*\*长期记忆\*\*\s*\|\s*\*\*(\d+)条\*\*', content)
                    if memory_matches:
                        claimed_count = int(memory_matches[0])
                        if claimed_count != actual_count:
                            issues.append(f"假数据: MEMORY.md 声称 {claimed_count}条记忆，实际 {actual_count}条")
                except:
                    pass
        
        return issues, warnings, metrics


class IneffectiveContentAudit(AuditCheck):
    """检测无效内容: 空文件、占位符、过期数据"""
    
    def __init__(self):
        super().__init__("无效内容检测")
    
    def run(self) -> Tuple[List[str], List[str], Dict]:
        issues = []
        warnings = []
        metrics = {"empty_files": 0, "placeholder_files": 0, "stale_files": 0}
        
        # 检查空文件 (排除venv目录)
        for pattern in ["*.py", "*.sh", "*.md", "*.json"]:
            for file_path in WORKSPACE.rglob(pattern):
                if file_path.is_file() and "venv" not in str(file_path) and ".git" not in str(file_path):
                    if file_path.stat().st_size == 0:
                        issues.append(f"空文件: {file_path.relative_to(WORKSPACE)}")
                        metrics["empty_files"] += 1
        
        # 检查过期的学习债务
        debt_file = WORKSPACE / "memory" / "learning-debt.md"
        if debt_file.exists():
            content = debt_file.read_text()
            # 查找过期的任务 (2月的任务)
            import re
            dates = re.findall(r'2026-02-(\d{2})', content)
            if dates:
                metrics["stale_files"] = len(dates)
                warnings.append(f"过期债务: learning-debt.md 有 {len(dates)} 条2月的待处理项")
        
        return issues, warnings, metrics


class IdleTasksAudit(AuditCheck):
    """检测空转任务"""
    
    def __init__(self):
        super().__init__("空转任务检测")
    
    def run(self) -> Tuple[List[str], List[str], Dict]:
        issues = []
        warnings = []
        metrics = {"idle_scripts": 0}
        
        # 检查日志文件的最后更新时间
        logs_dir = WORKSPACE / "logs"
        if logs_dir.exists():
            week_ago = datetime.now() - timedelta(days=7)
            for log_file in logs_dir.glob("*.log"):
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < week_ago:
                    warnings.append(f"过期日志: {log_file.name} 超过7天未更新")
                    metrics["idle_scripts"] += 1
        
        return issues, warnings, metrics


class RedundancyAudit(AuditCheck):
    """检测冗余代码和配置"""
    
    def __init__(self):
        super().__init__("冗余检测")
    
    def run(self) -> Tuple[List[str], List[str], Dict]:
        issues = []
        warnings = []
        metrics = {"duplicate_functions": 0, "config_files": 0}
        
        # 检查配置文件数量
        config_files = list((WORKSPACE / "config").glob("*.json")) + list((WORKSPACE / "config").glob("*.txt"))
        metrics["config_files"] = len(config_files)
        if len(config_files) > 20:
            warnings.append(f"配置冗余: config目录有 {len(config_files)} 个配置文件")
        
        return issues, warnings, metrics


class DataIntegrityAudit(AuditCheck):
    """检测数据完整性问题"""
    
    def __init__(self):
        super().__init__("数据完整性检测")
    
    def run(self) -> Tuple[List[str], List[str], Dict]:
        issues = []
        warnings = []
        metrics = {"invalid_json": 0, "broken_links": 0}
        
        # 检查JSON文件完整性 (排除venv)
        for json_file in WORKSPACE.rglob("*.json"):
            if "venv" not in str(json_file) and ".git" not in str(json_file):
                if json_file.is_file() and json_file.stat().st_size < 1024 * 1024:  # <1MB
                    try:
                        json.loads(json_file.read_text())
                    except json.JSONDecodeError as e:
                        issues.append(f"损坏JSON: {json_file.relative_to(WORKSPACE)} - {e}")
                        metrics["invalid_json"] += 1
                    except:
                        pass
        
        # 检查broken符号链接
        for item in WORKSPACE.rglob("*"):
            if "venv" not in str(item) and ".git" not in str(item):
                if item.is_symlink():
                    if not item.exists():
                        issues.append(f"断链: {item.relative_to(WORKSPACE)} 指向不存在的目标")
                        metrics["broken_links"] += 1
        
        return issues, warnings, metrics


class ArchitectureAudit(AuditCheck):
    """检测架构混乱"""
    
    def __init__(self):
        super().__init__("架构混乱检测")
    
    def run(self) -> Tuple[List[str], List[str], Dict]:
        issues = []
        warnings = []
        metrics = {"root_py_files": 0, "duplicate_modules": 0}
        
        # 检查根目录的Python文件
        for py_file in WORKSPACE.glob("*.py"):
            if py_file.is_file():
                issues.append(f"根目录Python文件: {py_file.name}")
                metrics["root_py_files"] += 1
        
        # 检查重复的模块
        core_modules = list((WORKSPACE / "core").rglob("*.py"))
        scripts_modules = list((WORKSPACE / "scripts").rglob("*.py"))
        
        core_names = {f.stem for f in core_modules}
        script_names = {f.stem for f in scripts_modules}
        
        duplicates = core_names & script_names
        if duplicates:
            warnings.append(f"模块重复: core/和scripts/有同名模块: {', '.join(duplicates)}")
            metrics["duplicate_modules"] = len(duplicates)
        
        return issues, warnings, metrics


def generate_report(timestamp: str, results: List[Tuple[str, List[str], List[str], Dict]]) -> str:
    """生成审计报告"""
    report_lines = [
        f"# 森森自我审计报告 - {timestamp}",
        f"",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"审计项目: 假优化、无效内容、空转任务、冗余代码、数据完整性、架构混乱",
        f"",
        "---"
    ]
    
    total_issues = 0
    total_warnings = 0
    
    for name, issues, warnings, metrics in results:
        report_lines.append(f"")
        report_lines.append(f"## {name}")
        report_lines.append(f"")
        
        if issues:
            report_lines.append("### 严重问题")
            report_lines.append(f"")
            for issue in issues:
                report_lines.append(f"- {issue}")
            total_issues += len(issues)
        else:
            report_lines.append("### 无严重问题")
            report_lines.append(f"")
        
        if warnings:
            report_lines.append(f"")
            report_lines.append("### 警告")
            report_lines.append(f"")
            for warning in warnings:
                report_lines.append(f"- {warning}")
            total_warnings += len(warnings)
        
        if metrics:
            report_lines.append(f"")
            report_lines.append("### 指标")
            report_lines.append(f"")
            for key, value in metrics.items():
                report_lines.append(f"- {key}: {value}")
        
        report_lines.append(f"")
        report_lines.append("---")
    
    # 总结
    report_lines.append(f"")
    report_lines.append(f"## 总结")
    report_lines.append(f"")
    report_lines.append(f"- 严重问题: {total_issues}个")
    report_lines.append(f"- 警告: {total_warnings}个")
    
    if total_issues == 0 and total_warnings == 0:
        report_lines.append(f"")
        report_lines.append(f"审计通过！系统状态良好。")
    elif total_issues == 0:
        report_lines.append(f"")
        report_lines.append(f"系统基本健康，但有一些需要关注的事项。")
    else:
        report_lines.append(f"")
        report_lines.append(f"发现严重问题，建议立即修复。")
    
    return "\n".join(report_lines)


def main():
    """主入口"""
    logger, timestamp = setup_logging()
    
    logger.info("="*60)
    logger.info("森森自我审计系统启动")
    logger.info("="*60)
    
    # 运行所有审计
    audits = [
        FalseOptimizationAudit(),
        IneffectiveContentAudit(),
        IdleTasksAudit(),
        RedundancyAudit(),
        DataIntegrityAudit(),
        ArchitectureAudit(),
    ]
    
    results = []
    for audit in audits:
        logger.info(f"")
        logger.info(f"运行: {audit.name}...")
        try:
            issues, warnings, metrics = audit.run()
            results.append((audit.name, issues, warnings, metrics))
            logger.info(f"  完成: {len(issues)}个问题, {len(warnings)}个警告")
        except Exception as e:
            logger.error(f"  审计失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((audit.name, [f"审计执行失败: {e}"], [], {}))
    
    # 生成报告
    report_content = generate_report(timestamp, results)
    report_file = REPORTS_DIR / f"audit-report-{timestamp}.md"
    report_file.write_text(report_content, encoding='utf-8')
    
    logger.info(f"")
    logger.info(f"{'='*60}")
    logger.info(f"审计完成，报告已保存: {report_file}")
    logger.info(f"{'='*60}")
    
    # 输出摘要
    total_issues = sum(len(r[1]) for r in results)
    total_warnings = sum(len(r[2]) for r in results)
    
    if total_issues > 0:
        logger.warning(f"发现 {total_issues} 个严重问题")
        sys.exit(1)
    elif total_warnings > 0:
        logger.warning(f"发现 {total_warnings} 个警告")
        sys.exit(0)
    else:
        logger.info("审计通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
