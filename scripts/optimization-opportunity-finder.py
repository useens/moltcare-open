#!/usr/bin/env python3
"""
精简机会识别模块 - Optimization Opportunity Finder
基于评估结果识别可精简项
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

class OpportunityFinder:
    """精简机会识别器"""
    
    # 保护清单 - 绝对不可精简
    PROTECTED_PATTERNS = [
        'github-backup-sync',
        'SOUL.md',
        'IDENTITY.md',
        'AGENTS.md',
        'USER.md',
        'SOUL',
        'IDENTITY',
        'AGENTS',
        'USER',
        '.env',
        '.key',
        '.pem',
        'v5.1',
        'v5.2',
        'v5.3',
        'v5.4',
        'v5.5',
        '.git',
        'core-archive',
        'knowledge-graph'
    ]
    
    def __init__(self, workspace: str = '/root/.openclaw/workspace'):
        self.workspace = Path(workspace)
        self.data_dir = self.workspace / 'data'
        self.config_dir = self.workspace / 'config'
        self.plan = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'opportunities': [],
            'summary': {}
        }
    
    def is_protected(self, path: str) -> bool:
        """检查是否受保护"""
        path_lower = str(path).lower()
        for pattern in self.PROTECTED_PATTERNS:
            if pattern.lower() in path_lower:
                return True
        return False
    
    def load_evaluation(self) -> Dict[str, Any]:
        """加载评估数据"""
        eval_path = self.data_dir / 'last-evaluation.json'
        if eval_path.exists():
            with open(eval_path, 'r') as f:
                return json.load(f)
        return {}
    
    def find_opportunities(self) -> Dict[str, Any]:
        """识别所有精简机会"""
        print("🔍 识别精简机会...")
        
        eval_data = self.load_evaluation()
        if not eval_data:
            print("⚠️ 未找到评估数据，请先运行系统评估")
            return self.plan
        
        # 识别各类精简机会
        self._find_temp_cleanup_opportunities()
        self._find_log_cleanup_opportunities()
        self._find_old_report_opportunities()
        self._find_duplicate_opportunities(eval_data)
        self._find_orphan_opportunities(eval_data)
        self._find_compression_opportunities(eval_data)
        self._find_redundancy_opportunities()
        
        # 生成汇总
        self._generate_summary()
        
        return self.plan
    
    def _find_temp_cleanup_opportunities(self):
        """识别临时文件清理机会"""
        print("  🧹 查找临时文件...")
        
        temp_patterns = ['*.tmp', '*.temp', '*~', '*.swp', '*.pyc', '__pycache__']
        found = []
        
        for pattern in temp_patterns:
            for path in self.workspace.rglob(pattern):
                if not self.is_protected(str(path)):
                    found.append({
                        'path': str(path.relative_to(self.workspace)),
                        'size': path.stat().st_size if path.exists() else 0
                    })
        
        if found:
            self.plan['opportunities'].append({
                'id': 'temp-cleanup',
                'name': '临时文件清理',
                'priority': 'P0',
                'action': 'delete',
                'target_type': 'files',
                'targets': found[:50],  # 限制数量
                'estimated_saving_mb': sum(f['size'] for f in found) / (1024*1024),
                'description': f'清理 {len(found)} 个临时文件',
                'risk_level': 'low'
            })
    
    def _find_log_cleanup_opportunities(self):
        """识别旧日志清理机会"""
        print("  📜 查找旧日志...")
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        old_logs = []
        
        for log_file in self.workspace.rglob('*.log'):
            if self.is_protected(str(log_file)):
                continue
                
            try:
                stat = log_file.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                if mtime < seven_days_ago:
                    old_logs.append({
                        'path': str(log_file.relative_to(self.workspace)),
                        'size': stat.st_size,
                        'age_days': (datetime.now() - mtime).days
                    })
            except:
                pass
        
        if old_logs:
            # 建议归档而非删除
            self.plan['opportunities'].append({
                'id': 'log-archive',
                'name': '旧日志归档',
                'priority': 'P1',
                'action': 'archive',
                'target_type': 'files',
                'targets': old_logs[:30],
                'estimated_saving_mb': sum(f['size'] for f in old_logs) / (1024*1024),
                'description': f'归档 {len(old_logs)} 个超过7天的日志文件',
                'risk_level': 'low'
            })
    
    def _find_old_report_opportunities(self):
        """识别旧报告归档机会"""
        print("  📊 查找旧报告...")
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        old_reports = []
        
        report_dirs = ['reports', 'docs/reports']
        for report_dir in report_dirs:
            dir_path = self.workspace / report_dir
            if dir_path.exists():
                for report in dir_path.glob('*.md'):
                    if self.is_protected(str(report)):
                        continue
                        
                    try:
                        stat = report.stat()
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        
                        if mtime < seven_days_ago:
                            old_reports.append({
                                'path': str(report.relative_to(self.workspace)),
                                'size': stat.st_size,
                                'age_days': (datetime.now() - mtime).days
                            })
                    except:
                        pass
        
        if old_reports:
            self.plan['opportunities'].append({
                'id': 'report-archive',
                'name': '旧报告归档',
                'priority': 'P1',
                'action': 'archive',
                'target_type': 'files',
                'targets': old_reports[:20],
                'estimated_saving_mb': sum(f['size'] for f in old_reports) / (1024*1024),
                'description': f'归档 {len(old_reports)} 个超过7天的报告文件',
                'risk_level': 'low'
            })
    
    def _find_duplicate_opportunities(self, eval_data: Dict):
        """识别重复文件合并机会"""
        print("  🔄 查找重复文件...")
        
        dup_info = eval_data.get('dimensions', {}).get('duplication', {})
        duplicates = dup_info.get('duplicate_details', [])
        
        if duplicates:
            targets = []
            for dup in duplicates[:10]:  # 限制数量
                if not self.is_protected(dup.get('duplicate', '')):
                    targets.append({
                        'path': dup['duplicate'],
                        'reason': f"与 {dup['original']} 重复"
                    })
            
            if targets:
                self.plan['opportunities'].append({
                    'id': 'duplicate-cleanup',
                    'name': '重复文件清理',
                    'priority': 'P0',
                    'action': 'delete',
                    'target_type': 'files',
                    'targets': targets,
                    'estimated_saving_mb': 0,
                    'description': f'删除 {len(targets)} 个重复文件',
                    'risk_level': 'low'
                })
    
    def _find_orphan_opportunities(self, eval_data: Dict):
        """识别孤立文件清理机会"""
        print("  📝 查找孤立文件...")
        
        invalid_info = eval_data.get('dimensions', {}).get('invalidity', {})
        orphans = invalid_info.get('details', {}).get('orphan_file_samples', [])
        
        if orphans:
            targets = []
            for orphan in orphans[:10]:
                if not self.is_protected(orphan):
                    targets.append({
                        'path': orphan,
                        'reason': '未被引用'
                    })
            
            if targets:
                self.plan['opportunities'].append({
                    'id': 'orphan-review',
                    'name': '孤立文件审查',
                    'priority': 'P1',
                    'action': 'review',
                    'target_type': 'files',
                    'targets': targets,
                    'estimated_saving_mb': 0,
                    'description': f'审查 {len(targets)} 个孤立文件',
                    'risk_level': 'medium'
                })
    
    def _find_compression_opportunities(self, eval_data: Dict):
        """识别压缩机会"""
        print("  🗜️ 查找可压缩内容...")
        
        storage_info = eval_data.get('dimensions', {}).get('storage', {})
        compression_potential = storage_info.get('compression_potential_mb', 0)
        
        if compression_potential > 1:  # 超过1MB才值得压缩
            # 查找大日志文件
            large_logs = []
            for log_file in self.workspace.rglob('*.log'):
                if self.is_protected(str(log_file)):
                    continue
                    
                try:
                    size_mb = log_file.stat().st_size / (1024*1024)
                    if size_mb > 0.5:  # 超过0.5MB
                        large_logs.append({
                            'path': str(log_file.relative_to(self.workspace)),
                            'size_mb': size_mb
                        })
                except:
                    pass
            
            if large_logs:
                self.plan['opportunities'].append({
                    'id': 'log-compression',
                    'name': '日志压缩',
                    'priority': 'P2',
                    'action': 'compress',
                    'target_type': 'files',
                    'targets': large_logs[:10],
                    'estimated_saving_mb': compression_potential,
                    'description': f'压缩 {len(large_logs)} 个大日志文件',
                    'risk_level': 'low'
                })
    
    def _find_redundancy_opportunities(self):
        """识别冗余配置/代码"""
        print("  🔍 查找冗余配置...")
        
        # 检查多个cron配置文件
        cron_files = list(self.workspace.rglob('*cron*'))
        cron_files = [f for f in cron_files if f.is_file() and not self.is_protected(str(f))]
        
        if len(cron_files) > 2:
            self.plan['opportunities'].append({
                'id': 'config-merge',
                'name': '配置合并',
                'priority': 'P2',
                'action': 'merge',
                'target_type': 'configs',
                'targets': [{'path': str(f.relative_to(self.workspace))} for f in cron_files[:5]],
                'estimated_saving_mb': 0,
                'description': f'合并 {len(cron_files)} 个分散的cron配置',
                'risk_level': 'medium'
            })
    
    def _generate_summary(self):
        """生成计划摘要"""
        p0_count = sum(1 for o in self.plan['opportunities'] if o['priority'] == 'P0')
        p1_count = sum(1 for o in self.plan['opportunities'] if o['priority'] == 'P1')
        p2_count = sum(1 for o in self.plan['opportunities'] if o['priority'] == 'P2')
        
        total_saving = sum(o['estimated_saving_mb'] for o in self.plan['opportunities'])
        
        self.plan['summary'] = {
            'total_opportunities': len(self.plan['opportunities']),
            'p0_count': p0_count,
            'p1_count': p1_count,
            'p2_count': p2_count,
            'estimated_saving_mb': round(total_saving, 2),
            'estimated_saving_percent': 0  # 将在执行后计算
        }
        
        print(f"\n📋 识别完成:")
        print(f"  - P0 (立即): {p0_count} 项")
        print(f"  - P1 (本周): {p1_count} 项")
        print(f"  - P2 (本月): {p2_count} 项")
        print(f"  - 预计节省: {total_saving:.2f} MB")
    
    def save_plan(self) -> str:
        """保存精简计划"""
        plan_path = self.config_dir / 'optimization-plan.json'
        
        with open(plan_path, 'w') as f:
            json.dump(self.plan, f, indent=2)
        
        print(f"✅ 精简计划已保存: {plan_path}")
        return str(plan_path)
    
    def get_priority_items(self, priority: str = 'P0') -> List[Dict]:
        """获取指定优先级的项目"""
        return [o for o in self.plan['opportunities'] if o['priority'] == priority]

def main():
    """主入口"""
    finder = OpportunityFinder()
    plan = finder.find_opportunities()
    plan_path = finder.save_plan()
    
    p0_items = finder.get_priority_items('P0')
    print(f"\n🎯 可立即执行: {len(p0_items)} 项")
    
    return len(p0_items)

if __name__ == '__main__':
    count = main()
    exit(0)
