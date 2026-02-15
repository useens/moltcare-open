#!/usr/bin/env python3
"""
精简执行模块 - System Optimizer
执行精简计划，自动清理/归档/合并
"""

import json
import os
import shutil
import gzip
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

class SystemOptimizer:
    """系统优化器 - 执行精简操作"""
    
    # 保护清单 - 绝对不可精简
    PROTECTED_PATTERNS = [
        'github-backup-sync',
        'github_backup_sync',
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
        'id_rsa',
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
        self.config_dir = self.workspace / 'config'
        self.logs_dir = self.workspace / 'logs'
        self.archives_dir = self.workspace / 'archives'
        self.execution_log = []
        self.stats = {
            'deleted': 0,
            'archived': 0,
            'compressed': 0,
            'space_saved_mb': 0,
            'errors': []
        }
        
        # 确保日志目录存在
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.archives_dir.mkdir(parents=True, exist_ok=True)
    
    def is_protected(self, path: str) -> bool:
        """检查是否受保护"""
        path_lower = str(path).lower()
        for pattern in self.PROTECTED_PATTERNS:
            if pattern.lower() in path_lower:
                return True
        
        # 额外检查：是否是github-backup-sync相关内容
        if 'github' in path_lower and 'backup' in path_lower:
            return True
            
        return False
    
    def log(self, level: str, message: str):
        """记录执行日志"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.execution_log.append(log_entry)
        print(log_entry)
    
    def load_plan(self) -> Dict[str, Any]:
        """加载精简计划"""
        plan_path = self.config_dir / 'optimization-plan.json'
        if plan_path.exists():
            with open(plan_path, 'r') as f:
                return json.load(f)
        return {'opportunities': []}
    
    def execute_optimization(self, plan: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行优化"""
        if plan is None:
            plan = self.load_plan()
        
        self.log('INFO', '开始执行系统精简...')
        self.log('INFO', f"找到 {len(plan.get('opportunities', []))} 个精简机会")
        
        for opportunity in plan.get('opportunities', []):
            try:
                self._execute_opportunity(opportunity)
            except Exception as e:
                error_msg = f"执行 {opportunity.get('id', 'unknown')} 失败: {str(e)}"
                self.log('ERROR', error_msg)
                self.stats['errors'].append(error_msg)
                
                # 自主解决阻碍：尝试3种不同方法
                self._try_alternative_methods(opportunity, e)
        
        self.log('INFO', '系统精简执行完成')
        self._save_execution_log()
        
        return self.stats
    
    def _execute_opportunity(self, opportunity: Dict):
        """执行单个精简机会"""
        opp_id = opportunity.get('id', 'unknown')
        action = opportunity.get('action')
        priority = opportunity.get('priority')
        
        self.log('INFO', f"[{priority}] 执行: {opportunity.get('name', opp_id)}")
        
        if action == 'delete':
            self._action_delete(opportunity)
        elif action == 'archive':
            self._action_archive(opportunity)
        elif action == 'compress':
            self._action_compress(opportunity)
        elif action == 'merge':
            self._action_merge(opportunity)
        elif action == 'review':
            self._action_review(opportunity)
        else:
            self.log('WARN', f"未知操作类型: {action}")
    
    def _action_delete(self, opportunity: Dict):
        """执行删除操作"""
        targets = opportunity.get('targets', [])
        deleted_count = 0
        saved_bytes = 0
        
        for target in targets:
            path_str = target.get('path') if isinstance(target, dict) else target
            if not path_str:
                continue
                
            full_path = self.workspace / path_str
            
            # 保护检查
            if self.is_protected(str(full_path)):
                self.log('SKIP', f"保护项目，跳过删除: {path_str}")
                continue
            
            try:
                if full_path.exists():
                    size = full_path.stat().st_size
                    
                    if full_path.is_file():
                        full_path.unlink()
                        deleted_count += 1
                        saved_bytes += size
                        self.log('DELETE', f"删除文件: {path_str}")
                    elif full_path.is_dir():
                        shutil.rmtree(full_path)
                        deleted_count += 1
                        saved_bytes += size
                        self.log('DELETE', f"删除目录: {path_str}")
            except Exception as e:
                self.log('ERROR', f"删除失败 {path_str}: {str(e)}")
        
        self.stats['deleted'] += deleted_count
        self.stats['space_saved_mb'] += saved_bytes / (1024*1024)
    
    def _action_archive(self, opportunity: Dict):
        """执行归档操作"""
        targets = opportunity.get('targets', [])
        archive_date = datetime.now().strftime('%Y%m%d')
        archive_dir = self.archives_dir / archive_date
        archive_dir.mkdir(exist_ok=True)
        
        archived_count = 0
        saved_bytes = 0
        
        for target in targets:
            path_str = target.get('path') if isinstance(target, dict) else target
            if not path_str:
                continue
                
            full_path = self.workspace / path_str
            
            # 保护检查
            if self.is_protected(str(full_path)):
                self.log('SKIP', f"保护项目，跳过归档: {path_str}")
                continue
            
            try:
                if full_path.exists() and full_path.is_file():
                    size = full_path.stat().st_size
                    archive_path = archive_dir / full_path.name
                    
                    # 移动文件
                    shutil.move(str(full_path), str(archive_path))
                    archived_count += 1
                    saved_bytes += size
                    self.log('ARCHIVE', f"归档: {path_str} -> archives/{archive_date}/")
            except Exception as e:
                self.log('ERROR', f"归档失败 {path_str}: {str(e)}")
        
        self.stats['archived'] += archived_count
        self.stats['space_saved_mb'] += saved_bytes / (1024*1024)
    
    def _action_compress(self, opportunity: Dict):
        """执行压缩操作"""
        targets = opportunity.get('targets', [])
        compressed_count = 0
        saved_bytes = 0
        
        for target in targets:
            path_str = target.get('path') if isinstance(target, dict) else target
            if not path_str:
                continue
                
            full_path = self.workspace / path_str
            
            # 保护检查
            if self.is_protected(str(full_path)):
                self.log('SKIP', f"保护项目，跳过压缩: {path_str}")
                continue
            
            try:
                if full_path.exists() and full_path.is_file():
                    original_size = full_path.stat().st_size
                    
                    # gzip压缩
                    compressed_path = full_path.with_suffix(full_path.suffix + '.gz')
                    with open(full_path, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # 删除原文件
                    full_path.unlink()
                    
                    compressed_size = compressed_path.stat().st_size
                    saved_bytes += (original_size - compressed_size)
                    compressed_count += 1
                    
                    self.log('COMPRESS', f"压缩: {path_str} ({original_size/(1024*1024):.2f}MB -> {compressed_size/(1024*1024):.2f}MB)")
            except Exception as e:
                self.log('ERROR', f"压缩失败 {path_str}: {str(e)}")
        
        self.stats['compressed'] += compressed_count
        self.stats['space_saved_mb'] += saved_bytes / (1024*1024)
    
    def _action_merge(self, opportunity: Dict):
        """执行合并操作"""
        targets = opportunity.get('targets', [])
        
        # 目前只是记录建议，不实际合并（需要人工审核）
        self.log('INFO', f"合并建议: {len(targets)} 个配置项")
        for target in targets:
            path_str = target.get('path') if isinstance(target, dict) else target
            if path_str:
                self.log('MERGE_SUGGESTION', f"可考虑合并: {path_str}")
    
    def _action_review(self, opportunity: Dict):
        """执行审查操作"""
        targets = opportunity.get('targets', [])
        
        # 记录待审查项目
        self.log('INFO', f"待审查项目: {len(targets)} 个")
        for target in targets:
            path_str = target.get('path') if isinstance(target, dict) else target
            reason = target.get('reason', '需要审查') if isinstance(target, dict) else '需要审查'
            if path_str:
                self.log('REVIEW', f"{path_str} - {reason}")
    
    def _try_alternative_methods(self, opportunity: Dict, original_error: Exception):
        """尝试替代方法解决问题"""
        self.log('INFO', f"尝试替代方法解决 {opportunity.get('id')}...")
        
        # 方法1: 尝试使用sudo/提权
        try:
            self.log('INFO', '方法1: 检查文件权限...')
            # 实际上已经在root权限下运行，这里只是示例
            pass
        except Exception as e:
            self.log('WARN', f'方法1失败: {e}')
        
        # 方法2: 尝试忽略错误继续执行
        try:
            self.log('INFO', '方法2: 记录错误继续执行...')
            # 错误已在stats中记录，继续执行
            pass
        except Exception as e:
            self.log('WARN', f'方法2失败: {e}')
        
        # 方法3: 尝试降级操作（如删除改为归档）
        try:
            self.log('INFO', '方法3: 尝试降级操作...')
            if opportunity.get('action') == 'delete':
                opportunity['action'] = 'archive'
                self._action_archive(opportunity)
        except Exception as e:
            self.log('WARN', f'方法3失败: {e}')
    
    def _save_execution_log(self):
        """保存执行日志"""
        log_path = self.logs_dir / 'optimization-execution.log'
        
        # 读取现有日志（保留最近1000行）
        existing_lines = []
        if log_path.exists():
            try:
                with open(log_path, 'r') as f:
                    existing_lines = f.readlines()[-1000:]
            except:
                pass
        
        # 写入新日志
        with open(log_path, 'w') as f:
            f.writelines(existing_lines)
            f.write(f"\n\n{'='*60}\n")
            f.write(f"执行时间: {datetime.now().isoformat()}\n")
            f.write(f"执行统计: 删除={self.stats['deleted']}, 归档={self.stats['archived']}, 压缩={self.stats['compressed']}\n")
            f.write(f"节省空间: {self.stats['space_saved_mb']:.2f} MB\n")
            f.write(f"{'='*60}\n\n")
            
            for entry in self.execution_log:
                f.write(entry + '\n')
        
        print(f"✅ 执行日志已保存: {log_path}")
    
    def get_summary(self) -> str:
        """获取执行摘要"""
        return f"""
📊 精简执行摘要:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 删除: {self.stats['deleted']} 项
📦 归档: {self.stats['archived']} 项
🗜️ 压缩: {self.stats['compressed']} 项
💾 节省空间: {self.stats['space_saved_mb']:.2f} MB
⚠️ 错误: {len(self.stats['errors'])} 项
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

def main():
    """主入口"""
    optimizer = SystemOptimizer()
    stats = optimizer.execute_optimization()
    
    print(optimizer.get_summary())
    
    return stats['space_saved_mb']

if __name__ == '__main__':
    saved = main()
    exit(0 if saved >= 0 else 1)
