#!/usr/bin/env python3
"""
系统评估模块 - System Evaluation Module
评估系统各维度的精简潜力
"""

import os
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import fnmatch

class SystemEvaluator:
    """系统评估器 - 评估系统精简潜力"""
    
    # 保护清单 - 绝对不可精简
    PROTECTED_ITEMS = [
        'github-backup-sync',
        'SOUL.md',
        'IDENTITY.md', 
        'AGENTS.md',
        'USER.md',
        '.env',
        '*.key',
        '*.pem',
        'v5.1',
        'v5.2',
        'v5.3',
        'v5.4',
        'v5.5',
        '.git',
    ]
    
    def __init__(self, workspace: str = '/root/.openclaw/workspace'):
        self.workspace = Path(workspace)
        self.reports_dir = self.workspace / 'reports'
        self.data_dir = self.workspace / 'data'
        self.evaluation_data = {}
        
    def evaluate_all(self) -> Dict[str, Any]:
        """执行全面系统评估"""
        print("🔍 开始系统全面评估...")
        
        self.evaluation_data = {
            'timestamp': datetime.now().isoformat(),
            'workspace': str(self.workspace),
            'dimensions': {}
        }
        
        # 评估各维度
        self.evaluation_data['dimensions']['token_waste'] = self._evaluate_token_waste()
        self.evaluation_data['dimensions']['bloat'] = self._evaluate_bloat()
        self.evaluation_data['dimensions']['duplication'] = self._evaluate_duplication()
        self.evaluation_data['dimensions']['invalidity'] = self._evaluate_invalidity()
        self.evaluation_data['dimensions']['coupling'] = self._evaluate_coupling()
        self.evaluation_data['dimensions']['storage'] = self._evaluate_storage()
        
        # 计算综合评分
        self.evaluation_data['score'] = self._calculate_score()
        
        return self.evaluation_data
    
    def _evaluate_token_waste(self) -> Dict[str, Any]:
        """评估Token浪费率"""
        print("  📊 评估Token浪费率...")
        
        # 统计各类型文件的Token消耗潜力
        token_stats = {
            'python_files': 0,
            'markdown_files': 0,
            'config_files': 0,
            'log_files': 0,
            'total_lines': 0,
            'empty_lines': 0,
            'comment_lines': 0,
            'code_lines': 0
        }
        
        for root, dirs, files in os.walk(self.workspace):
            # 跳过保护目录
            dirs[:] = [d for d in dirs if not any(p in d for p in ['.git', 'node_modules', '__pycache__', 'archives'])]
            
            for file in files:
                if file.endswith(('.py', '.md', '.json', '.yaml', '.yml', '.sh', '.log')):
                    filepath = Path(root) / file
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            token_stats['total_lines'] += len(lines)
                            
                            for line in lines:
                                stripped = line.strip()
                                if not stripped:
                                    token_stats['empty_lines'] += 1
                                elif stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                                    token_stats['comment_lines'] += 1
                                else:
                                    token_stats['code_lines'] += 1
                    except:
                        pass
        
        # 计算浪费率
        total = token_stats['total_lines']
        if total > 0:
            waste_rate = (token_stats['empty_lines'] + token_stats['comment_lines'] * 0.5) / total
        else:
            waste_rate = 0
            
        return {
            'waste_rate': round(waste_rate * 100, 2),
            'total_lines': token_stats['total_lines'],
            'empty_lines': token_stats['empty_lines'],
            'comment_lines': token_stats['comment_lines'],
            'code_lines': token_stats['code_lines'],
            'efficiency': round((1 - waste_rate) * 100, 2)
        }
    
    def _evaluate_bloat(self) -> Dict[str, Any]:
        """评估系统臃肿度"""
        print("  📦 评估系统臃肿度...")
        
        file_stats = {
            'total_files': 0,
            'total_size': 0,
            'scripts': 0,
            'configs': 0,
            'docs': 0,
            'logs': 0,
            'temp_files': 0,
            'old_files': 0  # >30天未修改
        }
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        for root, dirs, files in os.walk(self.workspace):
            # 跳过保护目录
            dirs[:] = [d for d in dirs if not any(p in d for p in ['.git', 'node_modules', '__pycache__'])]
            
            for file in files:
                # 跳过保护文件
                if any(p in file for p in self.PROTECTED_ITEMS):
                    continue
                    
                filepath = Path(root) / file
                try:
                    stat = filepath.stat()
                    file_stats['total_files'] += 1
                    file_stats['total_size'] += stat.st_size
                    
                    # 分类统计
                    if file.endswith('.py'):
                        file_stats['scripts'] += 1
                    elif file.endswith(('.json', '.yaml', '.yml', '.conf')):
                        file_stats['configs'] += 1
                    elif file.endswith('.md'):
                        file_stats['docs'] += 1
                    elif file.endswith('.log'):
                        file_stats['logs'] += 1
                    elif 'temp' in file.lower() or 'tmp' in file.lower():
                        file_stats['temp_files'] += 1
                    
                    # 检查旧文件
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    if mtime < thirty_days_ago:
                        file_stats['old_files'] += 1
                        
                except:
                    pass
        
        # 计算臃肿度 (基于文件数量和平均大小)
        avg_size = file_stats['total_size'] / file_stats['total_files'] if file_stats['total_files'] > 0 else 0
        bloat_score = min(100, (file_stats['total_files'] / 100) * 10 + (avg_size / 10000))
        
        return {
            'bloat_score': round(bloat_score, 2),
            'total_files': file_stats['total_files'],
            'total_size_mb': round(file_stats['total_size'] / (1024*1024), 2),
            'scripts': file_stats['scripts'],
            'configs': file_stats['configs'],
            'docs': file_stats['docs'],
            'logs': file_stats['logs'],
            'temp_files': file_stats['temp_files'],
            'old_files': file_stats['old_files']
        }
    
    def _evaluate_duplication(self) -> Dict[str, Any]:
        """评估重复率"""
        print("  🔄 评估重复率...")
        
        # 查找重复内容
        file_hashes = {}
        duplicates = []
        similar_scripts = []
        
        # 获取所有Python脚本
        scripts = list(self.workspace.rglob('*.py'))
        
        # 检测完全相同的文件
        for script in scripts:
            if any(p in str(script) for p in self.PROTECTED_ITEMS):
                continue
                
            try:
                with open(script, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    
                if file_hash in file_hashes:
                    duplicates.append({
                        'original': str(file_hashes[file_hash]),
                        'duplicate': str(script)
                    })
                else:
                    file_hashes[file_hash] = script
            except:
                pass
        
        # 检测相似功能（基于函数名和导入）
        script_signatures = {}
        for script in scripts[:50]:  # 限制检查数量
            if any(p in str(script) for p in self.PROTECTED_ITEMS):
                continue
                
            try:
                with open(script, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # 提取特征签名
                imports = [line for line in content.split('\n') if line.startswith('import') or line.startswith('from')]
                functions = [line for line in content.split('\n') if line.startswith('def ')]
                
                signature = hashlib.md5(''.join(sorted(imports[:5])).encode()).hexdigest()[:8]
                
                if signature in script_signatures:
                    similar_scripts.append({
                        'script1': str(script_signatures[signature]),
                        'script2': str(script),
                        'signature': signature
                    })
                else:
                    script_signatures[signature] = script
            except:
                pass
        
        total_scripts = len(scripts)
        duplicate_rate = (len(duplicates) * 2 + len(similar_scripts)) / max(total_scripts, 1) * 100
        
        return {
            'duplicate_rate': round(duplicate_rate, 2),
            'exact_duplicates': len(duplicates),
            'similar_scripts': len(similar_scripts),
            'duplicate_details': duplicates[:10],  # 只保留前10个
            'similar_details': similar_scripts[:10]
        }
    
    def _evaluate_invalidity(self) -> Dict[str, Any]:
        """评估失效率"""
        print("  ⚠️ 评估失效率...")
        
        invalid_items = {
            'zombie_tasks': [],
            'expired_debts': [],
            'orphan_files': [],
            'broken_symlinks': []
        }
        
        # 检查学习债务文件
        debt_file = self.workspace / 'memory' / 'learning-debt.md'
        if debt_file.exists():
            try:
                content = debt_file.read_text()
                # 查找超过30天的债务
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '[ ]' in line or '[x]' in line:
                        # 检查是否有日期标记
                        if '2026-01' in line or '2025-' in line:
                            invalid_items['expired_debts'].append({
                                'line': i + 1,
                                'content': line[:100]
                            })
            except:
                pass
        
        # 检查孤立文件（未被引用的脚本）
        for script in self.workspace.rglob('*.py'):
            if any(p in str(script) for p in self.PROTECTED_ITEMS):
                continue
                
            script_name = script.name
            referenced = False
            
            # 检查是否被其他文件引用
            for other_file in self.workspace.rglob('*'):
                if other_file.is_file() and other_file != script:
                    try:
                        content = other_file.read_text(errors='ignore')
                        if script_name.replace('.py', '') in content:
                            referenced = True
                            break
                    except:
                        pass
            
            if not referenced and 'test' not in script_name and '__init__' not in script_name:
                invalid_items['orphan_files'].append(str(script))
        
        # 检查损坏的符号链接
        for item in self.workspace.rglob('*'):
            if item.is_symlink() and not item.exists():
                invalid_items['broken_symlinks'].append(str(item))
        
        # 计算失效率
        total_issues = sum(len(v) for v in invalid_items.values())
        invalidity_rate = min(100, total_issues * 2)
        
        return {
            'invalidity_rate': round(invalidity_rate, 2),
            'zombie_tasks': len(invalid_items['zombie_tasks']),
            'expired_debts': len(invalid_items['expired_debts']),
            'orphan_files': len(invalid_items['orphan_files']),
            'broken_symlinks': len(invalid_items['broken_symlinks']),
            'details': {
                'expired_debt_samples': invalid_items['expired_debts'][:5],
                'orphan_file_samples': invalid_items['orphan_files'][:5]
            }
        }
    
    def _evaluate_coupling(self) -> Dict[str, Any]:
        """评估耦合度"""
        print("  🔗 评估耦合度...")
        
        # 分析脚本间的依赖关系
        dependencies = {}
        all_scripts = list(self.workspace.rglob('*.py'))
        
        for script in all_scripts:
            if any(p in str(script) for p in self.PROTECTED_ITEMS):
                continue
                
            script_deps = set()
            try:
                with open(script, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 检测导入
                for line in content.split('\n'):
                    if line.startswith('import ') or line.startswith('from '):
                        # 提取本地导入
                        for other_script in all_scripts:
                            other_name = other_script.stem
                            if other_name in line and other_script != script:
                                script_deps.add(str(other_script.relative_to(self.workspace)))
            except:
                pass
            
            dependencies[str(script.relative_to(self.workspace))] = list(script_deps)
        
        # 计算平均依赖数
        total_deps = sum(len(deps) for deps in dependencies.values())
        avg_deps = total_deps / len(dependencies) if dependencies else 0
        
        # 高耦合度 = 高依赖数
        coupling_score = min(100, avg_deps * 20)
        
        return {
            'coupling_score': round(coupling_score, 2),
            'avg_dependencies': round(avg_deps, 2),
            'total_dependencies': total_deps,
            'high_coupling_scripts': [
                script for script, deps in dependencies.items() 
                if len(deps) > 5
            ][:10]
        }
    
    def _evaluate_storage(self) -> Dict[str, Any]:
        """评估存储效率"""
        print("  💾 评估存储效率...")
        
        storage_stats = {
            'total_size': 0,
            'redundant_size': 0,
            'log_size': 0,
            'temp_size': 0,
            'archive_size': 0,
            'compression_potential': 0
        }
        
        for root, dirs, files in os.walk(self.workspace):
            # 跳过保护目录
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]
            
            for file in files:
                # 跳过保护文件
                if any(p in file for p in self.PROTECTED_ITEMS):
                    continue
                    
                filepath = Path(root) / file
                try:
                    size = filepath.stat().st_size
                    storage_stats['total_size'] += size
                    
                    # 分类统计
                    if file.endswith('.log'):
                        storage_stats['log_size'] += size
                        storage_stats['compression_potential'] += size * 0.7  # 日志可压缩70%
                    elif 'temp' in file.lower() or 'tmp' in file.lower():
                        storage_stats['temp_size'] += size
                        storage_stats['redundant_size'] += size
                    elif file.endswith('.old') or file.endswith('.bak'):
                        storage_stats['redundant_size'] += size
                    elif 'archive' in str(filepath):
                        storage_stats['archive_size'] += size
                        
                except:
                    pass
        
        total_mb = storage_stats['total_size'] / (1024*1024)
        redundant_mb = storage_stats['redundant_size'] / (1024*1024)
        
        storage_efficiency = 100 - (redundant_mb / max(total_mb, 1) * 100)
        
        return {
            'storage_efficiency': round(storage_efficiency, 2),
            'total_size_mb': round(total_mb, 2),
            'redundant_size_mb': round(redundant_mb, 2),
            'log_size_mb': round(storage_stats['log_size'] / (1024*1024), 2),
            'temp_size_mb': round(storage_stats['temp_size'] / (1024*1024), 2),
            'compression_potential_mb': round(storage_stats['compression_potential'] / (1024*1024), 2)
        }
    
    def _calculate_score(self) -> Dict[str, float]:
        """计算综合精简评分"""
        dimensions = self.evaluation_data['dimensions']
        
        # 各维度权重
        weights = {
            'token_waste': 0.20,
            'bloat': 0.15,
            'duplication': 0.20,
            'invalidity': 0.15,
            'coupling': 0.15,
            'storage': 0.15
        }
        
        # 计算各维度得分（越高越好）
        scores = {
            'token_waste': dimensions['token_waste']['efficiency'],
            'bloat': max(0, 100 - dimensions['bloat']['bloat_score']),
            'duplication': max(0, 100 - dimensions['duplication']['duplicate_rate']),
            'invalidity': max(0, 100 - dimensions['invalidity']['invalidity_rate']),
            'coupling': max(0, 100 - dimensions['coupling']['coupling_score']),
            'storage': dimensions['storage']['storage_efficiency']
        }
        
        # 加权总分
        total_score = sum(scores[k] * weights[k] for k in scores)
        
        return {
            'total': round(total_score, 2),
            'breakdown': scores
        }
    
    def generate_report(self) -> str:
        """生成评估报告"""
        if not self.evaluation_data:
            self.evaluate_all()
        
        date_str = datetime.now().strftime('%Y%m%d')
        report_path = self.reports_dir / f'system-evaluation-{date_str}.md'
        
        report = f"""# 系统精简评估报告

**评估时间**: {self.evaluation_data['timestamp']}
**工作目录**: {self.evaluation_data['workspace']}
**综合评分**: {self.evaluation_data['score']['total']}/100

## 📊 评分详情

| 维度 | 得分 | 说明 |
|------|------|------|
| Token效率 | {self.evaluation_data['score']['breakdown']['token_waste']:.1f} | 有效代码占比 |
| 臃肿度 | {self.evaluation_data['score']['breakdown']['bloat']:.1f} | 反臃肿评分 |
| 重复率 | {self.evaluation_data['score']['breakdown']['duplication']:.1f} | 反重复评分 |
| 失效率 | {self.evaluation_data['score']['breakdown']['invalidity']:.1f} | 反失效评分 |
| 耦合度 | {self.evaluation_data['score']['breakdown']['coupling']:.1f} | 低耦合评分 |
| 存储效率 | {self.evaluation_data['score']['breakdown']['storage']:.1f} | 存储利用率 |

## 🔍 详细分析

### 1. Token浪费率
- **浪费率**: {self.evaluation_data['dimensions']['token_waste']['waste_rate']}%
- **总行数**: {self.evaluation_data['dimensions']['token_waste']['total_lines']:,}
- **空行**: {self.evaluation_data['dimensions']['token_waste']['empty_lines']:,}
- **注释行**: {self.evaluation_data['dimensions']['token_waste']['comment_lines']:,}
- **代码行**: {self.evaluation_data['dimensions']['token_waste']['code_lines']:,}

### 2. 臃肿度
- **臃肿评分**: {self.evaluation_data['dimensions']['bloat']['bloat_score']:.2f}
- **总文件数**: {self.evaluation_data['dimensions']['bloat']['total_files']:,}
- **总大小**: {self.evaluation_data['dimensions']['bloat']['total_size_mb']:.2f} MB
- **脚本**: {self.evaluation_data['dimensions']['bloat']['scripts']}
- **配置**: {self.evaluation_data['dimensions']['bloat']['configs']}
- **文档**: {self.evaluation_data['dimensions']['bloat']['docs']}
- **日志**: {self.evaluation_data['dimensions']['bloat']['logs']}
- **临时文件**: {self.evaluation_data['dimensions']['bloat']['temp_files']}
- **旧文件(>30天)**: {self.evaluation_data['dimensions']['bloat']['old_files']}

### 3. 重复率
- **重复率**: {self.evaluation_data['dimensions']['duplication']['duplicate_rate']:.2f}%
- **完全重复**: {self.evaluation_data['dimensions']['duplication']['exact_duplicates']}
- **相似脚本**: {self.evaluation_data['dimensions']['duplication']['similar_scripts']}

### 4. 失效率
- **失效率**: {self.evaluation_data['dimensions']['invalidity']['invalidity_rate']:.2f}%
- **僵尸任务**: {self.evaluation_data['dimensions']['invalidity']['zombie_tasks']}
- **过期债务**: {self.evaluation_data['dimensions']['invalidity']['expired_debts']}
- **孤立文件**: {self.evaluation_data['dimensions']['invalidity']['orphan_files']}
- **损坏链接**: {self.evaluation_data['dimensions']['invalidity']['broken_symlinks']}

### 5. 耦合度
- **耦合评分**: {self.evaluation_data['dimensions']['coupling']['coupling_score']:.2f}
- **平均依赖**: {self.evaluation_data['dimensions']['coupling']['avg_dependencies']}
- **总依赖数**: {self.evaluation_data['dimensions']['coupling']['total_dependencies']}

### 6. 存储效率
- **存储效率**: {self.evaluation_data['dimensions']['storage']['storage_efficiency']:.2f}%
- **总大小**: {self.evaluation_data['dimensions']['storage']['total_size_mb']:.2f} MB
- **冗余大小**: {self.evaluation_data['dimensions']['storage']['redundant_size_mb']:.2f} MB
- **日志大小**: {self.evaluation_data['dimensions']['storage']['log_size_mb']:.2f} MB
- **临时文件**: {self.evaluation_data['dimensions']['storage']['temp_size_mb']:.2f} MB
- **压缩潜力**: {self.evaluation_data['dimensions']['storage']['compression_potential_mb']:.2f} MB

## 💡 精简建议

1. **高优先级**: 清理临时文件和过期日志
2. **中优先级**: 合并重复脚本，删除孤立文件
3. **低优先级**: 优化代码注释，减少空行

---
*Generated by SystemEvaluator v1.0*
"""
        
        report_path.write_text(report)
        print(f"✅ 评估报告已生成: {report_path}")
        
        return str(report_path)
    
    def save_data(self) -> str:
        """保存评估数据"""
        data_path = self.data_dir / 'last-evaluation.json'
        with open(data_path, 'w') as f:
            json.dump(self.evaluation_data, f, indent=2)
        return str(data_path)

def main():
    """主入口"""
    evaluator = SystemEvaluator()
    
    # 执行评估
    data = evaluator.evaluate_all()
    
    # 生成报告
    report_path = evaluator.generate_report()
    
    # 保存数据
    data_path = evaluator.save_data()
    
    print(f"\n📊 综合评分: {data['score']['total']}/100")
    print(f"📄 报告: {report_path}")
    print(f"💾 数据: {data_path}")
    
    return data['score']['total']

if __name__ == '__main__':
    score = main()
    exit(0 if score >= 60 else 1)
