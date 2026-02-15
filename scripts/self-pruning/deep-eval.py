#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度评估模块 - L3级别 (每天04:00执行)
功能: 综合评估、精简方案制定
触发条件: 重大Token浪费、架构级精简需求、复杂耦合问题
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

WORKSPACE = Path("/root/.openclaw/workspace")
LOG_DIR = WORKSPACE / "memory/self-pruning"
REPORT_DIR = LOG_DIR / "deep-reports"

def log(msg, level="INFO"):
    """输出日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"[{timestamp}] [{level}]"
    print(f"{prefix} {msg}")

def deep_token_analysis():
    """深度Token使用分析"""
    log("🧠 深度Token使用分析...", "DEEP")
    
    findings = []
    
    # 分析所有markdown文件的Token估算
    memory_dir = WORKSPACE / "memory"
    
    if memory_dir.exists():
        file_stats = []
        for md_file in memory_dir.rglob("*.md"):
            try:
                content = md_file.read_text()
                # 简单估算: 英文约4字符=1token, 中文约1.5字符=1token
                estimated_tokens = len(content) // 3
                
                file_stats.append({
                    'path': str(md_file.relative_to(WORKSPACE)),
                    'size': md_file.stat().st_size,
                    'tokens': estimated_tokens
                })
            except:
                pass
        
        # 按token排序
        file_stats.sort(key=lambda x: -x['tokens'])
        
        total_tokens = sum(f['tokens'] for f in file_stats)
        log(f"  总Token估算: ~{total_tokens:,}", "DEEP")
        log(f"  文件数: {len(file_stats)}", "DEEP")
        
        # 找出高消耗文件
        high_consumption = [f for f in file_stats if f['tokens'] > 5000]
        if high_consumption:
            log(f"  高消耗文件(>5000 tokens): {len(high_consumption)}个", "DEEP")
            for f in high_consumption[:3]:
                log(f"    - {f['path']}: ~{f['tokens']:,} tokens", "DEEP")
            
            findings.append({
                'type': 'HIGH_TOKEN_USAGE',
                'severity': 'HIGH',
                'details': f"发现 {len(high_consumption)} 个高Token消耗文件"
            })
    
    return findings

def architecture_analysis():
    """架构级精简分析"""
    log("🧠 架构级精简分析...", "DEEP")
    
    findings = []
    
    # 分析scripts目录结构
    scripts_dir = WORKSPACE / "scripts"
    
    if scripts_dir.exists():
        # 检查脚本分类
        categories = defaultdict(list)
        
        for script in scripts_dir.rglob("*.py"):
            # 根据文件名和路径分类
            name = script.name.lower()
            if 'backup' in name or 'sync' in name:
                categories['backup'].append(script.name)
            elif 'monitor' in name or 'check' in name:
                categories['monitoring'].append(script.name)
            elif 'prune' in name or 'clean' in name:
                categories['maintenance'].append(script.name)
            elif 'skill' in name:
                categories['skills'].append(script.name)
            else:
                categories['other'].append(script.name)
        
        log(f"  脚本分类统计:", "DEEP")
        for cat, files in sorted(categories.items()):
            log(f"    {cat}: {len(files)}个", "DEEP")
        
        # 检查重复功能
        if len(categories.get('backup', [])) > 2:
            findings.append({
                'type': 'ARCHITECTURE_ISSUE',
                'severity': 'MEDIUM',
                'details': f"备份脚本过多: {categories['backup']}"
            })
    
    return findings

def coupling_analysis():
    """复杂耦合问题分析"""
    log("🧠 复杂耦合问题分析...", "DEEP")
    
    findings = []
    
    # 分析Python导入关系
    scripts_dir = WORKSPACE / "scripts"
    
    if scripts_dir.exists():
        import_graph = defaultdict(set)
        
        for py_file in scripts_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
                imports = []
                
                for line in content.split('\n'):
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line.strip())
                
                if len(imports) > 20:
                    findings.append({
                        'type': 'HIGH_COUPLING',
                        'severity': 'MEDIUM',
                        'details': f"{py_file.name} 导入过多 ({len(imports)}个)"
                    })
                    
            except:
                pass
    
    return findings

def generate_pruning_plan(findings):
    """生成精简方案"""
    log("📝 生成精简方案...", "DEEP")
    
    plan = {
        'timestamp': datetime.now().isoformat(),
        'findings': findings,
        'recommendations': []
    }
    
    for finding in findings:
        if finding['type'] == 'HIGH_TOKEN_USAGE':
            plan['recommendations'].append({
                'action': 'ARCHIVE_OLD_MEMORIES',
                'priority': 'HIGH',
                'details': '归档90天前的记忆文件到压缩存储'
            })
        
        elif finding['type'] == 'ARCHITECTURE_ISSUE':
            plan['recommendations'].append({
                'action': 'CONSOLIDATE_BACKUP_SCRIPTS',
                'priority': 'MEDIUM',
                'details': '合并功能重复的备份脚本'
            })
        
        elif finding['type'] == 'HIGH_COUPLING':
            plan['recommendations'].append({
                'action': 'REFACTOR_IMPORTS',
                'priority': 'LOW',
                'details': '重构高耦合脚本的导入结构'
            })
    
    # 保存方案
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    plan_file = REPORT_DIR / f"pruning-plan-{datetime.now().strftime('%Y%m%d')}.json"
    
    with open(plan_file, 'w') as f:
        json.dump(plan, f, indent=2)
    
    log(f"📄 精简方案已保存: {plan_file}", "DEEP")
    
    # 输出建议摘要
    if plan['recommendations']:
        log("📋 精简建议摘要:", "DEEP")
        for i, rec in enumerate(plan['recommendations'], 1):
            log(f"  {i}. [{rec['priority']}] {rec['action']}: {rec['details']}", "DEEP")
    else:
        log("✅ 暂无精简建议", "DEEP")
    
    return plan

def main():
    """深度评估主流程"""
    log("=" * 60, "DEEP")
    log("🚀 深度评估启动 (L3/HIGH)", "DEEP")
    log("=" * 60, "DEEP")
    
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_findings = []
    
    # 执行深度分析
    all_findings.extend(deep_token_analysis())
    all_findings.extend(architecture_analysis())
    all_findings.extend(coupling_analysis())
    
    # 生成精简方案
    plan = generate_pruning_plan(all_findings)
    
    # 输出总结
    log("=" * 60, "DEEP")
    log(f"📊 深度评估完成", "DEEP")
    log(f"   发现问题: {len(all_findings)}个", "DEEP")
    log(f"   提出建议: {len(plan['recommendations'])}条", "DEEP")
    log("=" * 60, "DEEP")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
