#!/usr/bin/env python3
"""
Self-Optimization System v5.0
自优化建议模块

功能：
1. 分析日志找出优化点
2. 自动生成优化建议
3. 低风险优化自动执行
4. 性能分析和调优建议
"""

import json
import re
import os
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from pathlib import Path
import logging
import hashlib
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/self_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SelfOptimization')


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"        # 可自动执行
    MEDIUM = "medium"  # 需要确认
    HIGH = "high"      # 需要详细审查
    CRITICAL = "critical"  # 仅建议，不执行


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    id: str
    timestamp: str
    category: str
    title: str
    description: str
    current_value: Any
    suggested_value: Any
    expected_improvement: str
    risk_level: str
    auto_executable: bool
    command: Optional[str] = None
    executed: bool = False
    execution_result: Optional[str] = None
    execution_time: Optional[str] = None


@dataclass
class LogPattern:
    """日志模式"""
    name: str
    pattern: str
    severity: str
    category: str
    suggestion_template: str


class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self):
        self.patterns = [
            # 性能相关
            LogPattern(
                name='slow_operation',
                pattern=r'(?:took|spent|elapsed)\s+(\d+(?:\.\d+)?)\s*(ms|s|seconds?|minutes?)',
                severity='medium',
                category='performance',
                suggestion_template='检测到慢操作：{value}，建议优化或添加缓存'
            ),
            LogPattern(
                name='high_memory_usage',
                pattern=r'(?:memory|ram)\s*(?:usage|consumption)?\s*(?:is|\:)?\s*(\d+(?:\.\d+)?)\s*%',
                severity='high',
                category='performance',
                suggestion_template='内存使用率较高：{value}%，建议检查内存泄漏'
            ),
            LogPattern(
                name='timeout_error',
                pattern=r'(?:timeout|timed out|connection timeout)',
                severity='high',
                category='reliability',
                suggestion_template='检测到超时错误，建议增加超时时间或优化操作'
            ),
            # 错误相关
            LogPattern(
                name='api_error',
                pattern=r'(?:api|request)\s*(?:error|failed|failure)\s*(?:code)?\s*:?\s*(\d{3})',
                severity='high',
                category='reliability',
                suggestion_template='API错误码：{value}，建议检查API状态和限流'
            ),
            LogPattern(
                name='rate_limit',
                pattern=r'(?:rate limit|too many requests|429)',
                severity='medium',
                category='performance',
                suggestion_template='触发限流，建议降低请求频率或增加缓存'
            ),
            LogPattern(
                name='exception',
                pattern=r'(?:exception|error|traceback|failed)',
                severity='medium',
                category='reliability',
                suggestion_template='检测到异常，建议检查错误日志并修复'
            ),
            # 资源相关
            LogPattern(
                name='disk_full',
                pattern=r'(?:disk full|no space left|insufficient space)',
                severity='critical',
                category='resource',
                suggestion_template='磁盘空间不足，建议立即清理'
            ),
            LogPattern(
                name='connection_error',
                pattern=r'(?:connection refused|network error|unable to connect)',
                severity='high',
                category='network',
                suggestion_template='网络连接错误，建议检查网络配置'
            ),
        ]
        
        self.pattern_counts: Dict[str, int] = defaultdict(int)
        self.pattern_history: deque = deque(maxlen=1000)
    
    def analyze_file(self, log_file: str, lines: int = 1000) -> List[Dict]:
        """分析日志文件"""
        findings = []
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # 读取最后N行
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line_num, line in enumerate(recent_lines, 1):
                    for pattern in self.patterns:
                        matches = re.finditer(pattern.pattern, line, re.IGNORECASE)
                        for match in matches:
                            self.pattern_counts[pattern.name] += 1
                            
                            finding = {
                                'pattern_name': pattern.name,
                                'category': pattern.category,
                                'severity': pattern.severity,
                                'line_number': line_num,
                                'matched_text': match.group(0),
                                'extracted_value': match.group(1) if match.groups() else None,
                                'timestamp': self._extract_timestamp(line),
                                'context': line.strip()[:200]
                            }
                            findings.append(finding)
                            
                            self.pattern_history.append({
                                'timestamp': datetime.now().isoformat(),
                                'pattern': pattern.name,
                                'finding': finding
                            })
        except Exception as e:
            logger.error(f"Failed to analyze log file {log_file}: {e}")
        
        return findings
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """从日志行提取时间戳"""
        patterns = [
            r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
            r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',
            r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None
    
    def get_frequent_issues(self, min_count: int = 3) -> List[Dict]:
        """获取频繁出现的问题"""
        frequent = []
        
        for pattern_name, count in self.pattern_counts.items():
            if count >= min_count:
                pattern_info = next((p for p in self.patterns if p.name == pattern_name), None)
                if pattern_info:
                    frequent.append({
                        'pattern': pattern_name,
                        'count': count,
                        'category': pattern_info.category,
                        'severity': pattern_info.severity,
                        'suggestion': pattern_info.suggestion_template
                    })
        
        return sorted(frequent, key=lambda x: x['count'], reverse=True)
    
    def analyze_performance_trends(self) -> Dict:
        """分析性能趋势"""
        # 分析慢操作的时间分布
        slow_ops = [h for h in self.pattern_history if h['pattern'] == 'slow_operation']
        
        if not slow_ops:
            return {'message': 'No slow operations found'}
        
        # 计算趋势
        recent = list(slow_ops)[-20:]
        older = list(slow_ops)[:-20] if len(slow_ops) > 20 else slow_ops[:len(slow_ops)//2]
        
        return {
            'total_slow_operations': len(slow_ops),
            'recent_count': len(recent),
            'trend': 'increasing' if len(recent) > len(older) else 'stable',
            'suggestion': 'Performance issues detected, consider optimization'
        }


class ConfigAnalyzer:
    """配置分析器"""
    
    def __init__(self):
        self.optimization_rules = {
            'log_retention': {
                'check': self._check_log_retention,
                'optimize': self._optimize_log_retention,
                'risk': RiskLevel.LOW
            },
            'temp_cleanup': {
                'check': self._check_temp_files,
                'optimize': self._cleanup_temp_files,
                'risk': RiskLevel.LOW
            },
            'cache_size': {
                'check': self._check_cache_size,
                'optimize': self._optimize_cache_size,
                'risk': RiskLevel.MEDIUM
            }
        }
    
    def analyze(self) -> List[OptimizationSuggestion]:
        """分析配置并生成建议"""
        suggestions = []
        
        for rule_name, rule in self.optimization_rules.items():
            try:
                result = rule['check']()
                if result['needs_optimization']:
                    suggestion = OptimizationSuggestion(
                        id=hashlib.md5(f"{rule_name}_{datetime.now()}".encode()).hexdigest()[:12],
                        timestamp=datetime.now().isoformat(),
                        category='configuration',
                        title=result['title'],
                        description=result['description'],
                        current_value=result['current_value'],
                        suggested_value=result['suggested_value'],
                        expected_improvement=result['expected_improvement'],
                        risk_level=rule['risk'].value,
                        auto_executable=rule['risk'] == RiskLevel.LOW,
                        command=result.get('command')
                    )
                    suggestions.append(suggestion)
            except Exception as e:
                logger.error(f"Failed to analyze {rule_name}: {e}")
        
        return suggestions
    
    def _check_log_retention(self) -> Dict:
        """检查日志保留策略"""
        log_dir = Path('/root/.openclaw/workspace/logs')
        
        if not log_dir.exists():
            return {'needs_optimization': False}
        
        log_files = list(log_dir.glob('*.log'))
        total_size = sum(f.stat().st_size for f in log_files)
        total_size_mb = total_size / (1024 * 1024)
        
        # 如果日志超过100MB，建议清理
        if total_size_mb > 100:
            old_logs = [f for f in log_files 
                       if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days > 7]
            
            return {
                'needs_optimization': True,
                'title': '日志文件过大',
                'description': f'日志目录大小: {total_size_mb:.1f}MB，建议清理超过7天的日志',
                'current_value': f'{total_size_mb:.1f}MB',
                'suggested_value': '< 50MB',
                'expected_improvement': '释放磁盘空间，提高日志查询效率',
                'command': f'find {log_dir} -name "*.log" -mtime +7 -delete'
            }
        
        return {'needs_optimization': False}
    
    def _optimize_log_retention(self) -> bool:
        """执行日志保留优化"""
        try:
            log_dir = Path('/root/.openclaw/workspace/logs')
            result = subprocess.run(
                ['find', str(log_dir), '-name', '*.log', '-mtime', '+7', '-delete'],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to optimize log retention: {e}")
            return False
    
    def _check_temp_files(self) -> Dict:
        """检查临时文件"""
        temp_dirs = ['/tmp', '/var/tmp', str(Path.home() / '.cache')]
        
        total_temp_size = 0
        for temp_dir in temp_dirs:
            path = Path(temp_dir)
            if path.exists():
                try:
                    total_temp_size += sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                except:
                    pass
        
        total_temp_mb = total_temp_size / (1024 * 1024)
        
        if total_temp_mb > 500:
            return {
                'needs_optimization': True,
                'title': '临时文件过多',
                'description': f'临时文件总大小: {total_temp_mb:.1f}MB',
                'current_value': f'{total_temp_mb:.1f}MB',
                'suggested_value': '< 200MB',
                'expected_improvement': '释放磁盘空间',
                'command': 'find /tmp -type f -atime +3 -delete 2>/dev/null; find ~/.cache -type f -atime +7 -delete 2>/dev/null'
            }
        
        return {'needs_optimization': False}
    
    def _cleanup_temp_files(self) -> bool:
        """清理临时文件"""
        try:
            subprocess.run(['find', '/tmp', '-type', 'f', '-atime', '+3', '-delete'],
                         capture_output=True, timeout=30)
            subprocess.run(['find', str(Path.home() / '.cache'), '-type', 'f', '-atime', '+7', '-delete'],
                         capture_output=True, timeout=30)
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return False
    
    def _check_cache_size(self) -> Dict:
        """检查缓存大小"""
        cache_dir = Path('/root/.openclaw/workspace/data')
        
        if not cache_dir.exists():
            return {'needs_optimization': False}
        
        cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        cache_size_mb = cache_size / (1024 * 1024)
        
        if cache_size_mb > 1000:
            return {
                'needs_optimization': True,
                'title': '缓存数据过大',
                'description': f'缓存目录大小: {cache_size_mb:.1f}MB',
                'current_value': f'{cache_size_mb:.1f}MB',
                'suggested_value': '< 500MB',
                'expected_improvement': '减少磁盘占用，提高访问速度',
                'command': None  # 需要人工确认
            }
        
        return {'needs_optimization': False}
    
    def _optimize_cache_size(self) -> bool:
        """优化缓存大小"""
        # 这个操作风险较高，默认不自动执行
        logger.info("Cache optimization requires manual confirmation")
        return False


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.metrics_history: deque = deque(maxlen=1000)
    
    def collect_metrics(self) -> Dict:
        """收集性能指标"""
        import psutil
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
            'open_files': len(psutil.Process().open_files()),
            'connections': len(psutil.Process().connections())
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def analyze_bottlenecks(self) -> List[OptimizationSuggestion]:
        """分析性能瓶颈"""
        suggestions = []
        
        if len(self.metrics_history) < 10:
            return suggestions
        
        recent = list(self.metrics_history)[-10:]
        
        # 分析CPU
        avg_cpu = sum(m['cpu_percent'] for m in recent) / len(recent)
        if avg_cpu > 80:
            suggestions.append(OptimizationSuggestion(
                id=hashlib.md5(f"cpu_{datetime.now()}".encode()).hexdigest()[:12],
                timestamp=datetime.now().isoformat(),
                category='performance',
                title='CPU使用率过高',
                description=f'平均CPU使用率: {avg_cpu:.1f}%',
                current_value=f'{avg_cpu:.1f}%',
                suggested_value='< 70%',
                expected_improvement='降低系统负载，提高响应速度',
                risk_level='medium',
                auto_executable=False
            ))
        
        # 分析内存
        avg_memory = sum(m['memory_percent'] for m in recent) / len(recent)
        if avg_memory > 80:
            suggestions.append(OptimizationSuggestion(
                id=hashlib.md5(f"memory_{datetime.now()}".encode()).hexdigest()[:12],
                timestamp=datetime.now().isoformat(),
                category='performance',
                title='内存使用率过高',
                description=f'平均内存使用率: {avg_memory:.1f}%',
                current_value=f'{avg_memory:.1f}%',
                suggested_value='< 75%',
                expected_improvement='减少OOM风险，提高系统稳定性',
                risk_level='medium',
                auto_executable=False
            ))
        
        # 分析打开的文件数
        avg_open_files = sum(m['open_files'] for m in recent) / len(recent)
        if avg_open_files > 500:
            suggestions.append(OptimizationSuggestion(
                id=hashlib.md5(f"files_{datetime.now()}".encode()).hexdigest()[:12],
                timestamp=datetime.now().isoformat(),
                category='performance',
                title='打开文件数过多',
                description=f'平均打开文件数: {avg_open_files:.0f}',
                current_value=f'{avg_open_files:.0f}',
                suggested_value='< 300',
                expected_improvement='减少文件描述符消耗',
                risk_level='low',
                auto_executable=True,
                command='echo "Check for file descriptor leaks"'
            ))
        
        return suggestions


class AutoExecutor:
    """自动执行器"""
    
    def __init__(self):
        self.execution_log: deque = deque(maxlen=100)
        self.approved_commands: set = {
            'find.*-delete',
            'rm.*\.log',
            'echo',
        }
    
    def can_auto_execute(self, suggestion: OptimizationSuggestion) -> bool:
        """检查是否可以自动执行"""
        if not suggestion.auto_executable:
            return False
        
        if suggestion.risk_level not in ['low']:
            return False
        
        if not suggestion.command:
            return False
        
        # 检查命令是否在白名单中
        for pattern in self.approved_commands:
            if re.search(pattern, suggestion.command):
                return True
        
        return False
    
    def execute(self, suggestion: OptimizationSuggestion) -> bool:
        """执行优化建议"""
        if not self.can_auto_execute(suggestion):
            logger.warning(f"Cannot auto-execute suggestion {suggestion.id}")
            return False
        
        try:
            logger.info(f"Executing suggestion {suggestion.id}: {suggestion.command}")
            
            result = subprocess.run(
                suggestion.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            
            # 更新建议状态
            suggestion.executed = True
            suggestion.execution_time = datetime.now().isoformat()
            suggestion.execution_result = 'success' if success else f'failed: {result.stderr}'
            
            # 记录执行日志
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'suggestion_id': suggestion.id,
                'command': suggestion.command,
                'success': success,
                'output': result.stdout if success else result.stderr
            })
            
            logger.info(f"Execution {'succeeded' if success else 'failed'} for {suggestion.id}")
            return success
            
        except Exception as e:
            logger.error(f"Execution failed for {suggestion.id}: {e}")
            suggestion.execution_result = f'error: {str(e)}'
            return False


class SelfOptimizer:
    """自优化主类"""
    
    def __init__(self, data_dir: str = '/root/.openclaw/workspace/data/diagnosis'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_analyzer = LogAnalyzer()
        self.config_analyzer = ConfigAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.auto_executor = AutoExecutor()
        
        self.suggestions: List[OptimizationSuggestion] = []
        self.suggestion_file = self.data_dir / 'optimization_suggestions.json'
        
        self.running = False
        self.analyze_interval = 3600  # 1小时
    
    def load_suggestions(self):
        """加载已有的建议"""
        if self.suggestion_file.exists():
            try:
                with open(self.suggestion_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        self.suggestions.append(OptimizationSuggestion(**item))
            except Exception as e:
                logger.error(f"Failed to load suggestions: {e}")
    
    def save_suggestions(self):
        """保存建议"""
        try:
            with open(self.suggestion_file, 'w') as f:
                json.dump([asdict(s) for s in self.suggestions], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save suggestions: {e}")
    
    def analyze_logs(self, log_files: Optional[List[str]] = None) -> List[OptimizationSuggestion]:
        """分析日志"""
        if log_files is None:
            log_dir = Path('/root/.openclaw/workspace/logs')
            log_files = [str(f) for f in log_dir.glob('*.log') if f.is_file()]
        
        all_findings = []
        for log_file in log_files:
            findings = self.log_analyzer.analyze_file(log_file)
            all_findings.extend(findings)
        
        # 基于发现生成建议
        suggestions = []
        frequent_issues = self.log_analyzer.get_frequent_issues(min_count=5)
        
        for issue in frequent_issues:
            suggestion = OptimizationSuggestion(
                id=hashlib.md5(f"{issue['pattern']}_{datetime.now()}".encode()).hexdigest()[:12],
                timestamp=datetime.now().isoformat(),
                category=issue['category'],
                title=f"频繁出现: {issue['pattern']}",
                description=f"在过去24小时内出现 {issue['count']} 次",
                current_value=f"{issue['count']} 次",
                suggested_value="0 次",
                expected_improvement=issue['suggestion'].format(value='N/A'),
                risk_level='medium',
                auto_executable=False
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def analyze_config(self) -> List[OptimizationSuggestion]:
        """分析配置"""
        return self.config_analyzer.analyze()
    
    def analyze_performance(self) -> List[OptimizationSuggestion]:
        """分析性能"""
        self.performance_analyzer.collect_metrics()
        return self.performance_analyzer.analyze_bottlenecks()
    
    def run_full_analysis(self) -> List[OptimizationSuggestion]:
        """运行完整分析"""
        logger.info("Starting full optimization analysis")
        
        all_suggestions = []
        
        # 日志分析
        log_suggestions = self.analyze_logs()
        all_suggestions.extend(log_suggestions)
        logger.info(f"Log analysis: {len(log_suggestions)} suggestions")
        
        # 配置分析
        config_suggestions = self.analyze_config()
        all_suggestions.extend(config_suggestions)
        logger.info(f"Config analysis: {len(config_suggestions)} suggestions")
        
        # 性能分析
        perf_suggestions = self.analyze_performance()
        all_suggestions.extend(perf_suggestions)
        logger.info(f"Performance analysis: {len(perf_suggestions)} suggestions")
        
        # 合并并去重
        existing_ids = {s.id for s in self.suggestions}
        new_suggestions = [s for s in all_suggestions if s.id not in existing_ids]
        
        self.suggestions.extend(new_suggestions)
        self.save_suggestions()
        
        logger.info(f"Analysis complete: {len(new_suggestions)} new suggestions")
        
        return new_suggestions
    
    def execute_auto_optimizations(self) -> List[Dict]:
        """执行自动优化"""
        results = []
        
        for suggestion in self.suggestions:
            if not suggestion.executed and suggestion.auto_executable:
                success = self.auto_executor.execute(suggestion)
                results.append({
                    'suggestion_id': suggestion.id,
                    'success': success,
                    'executed_at': suggestion.execution_time
                })
        
        self.save_suggestions()
        return results
    
    def get_suggestions(self, category: Optional[str] = None,
                       risk_level: Optional[str] = None,
                       pending_only: bool = False) -> List[Dict]:
        """获取建议列表"""
        filtered = self.suggestions
        
        if category:
            filtered = [s for s in filtered if s.category == category]
        
        if risk_level:
            filtered = [s for s in filtered if s.risk_level == risk_level]
        
        if pending_only:
            filtered = [s for s in filtered if not s.executed]
        
        return [asdict(s) for s in sorted(filtered, key=lambda x: x.timestamp, reverse=True)]
    
    def get_summary(self) -> Dict:
        """获取优化摘要"""
        total = len(self.suggestions)
        executed = sum(1 for s in self.suggestions if s.executed)
        pending = total - executed
        
        by_category = defaultdict(int)
        by_risk = defaultdict(int)
        
        for s in self.suggestions:
            by_category[s.category] += 1
            by_risk[s.risk_level] += 1
        
        return {
            'total_suggestions': total,
            'executed': executed,
            'pending': pending,
            'by_category': dict(by_category),
            'by_risk_level': dict(by_risk),
            'last_analysis': self.suggestions[-1].timestamp if self.suggestions else None
        }
    
    async def run(self):
        """主运行循环"""
        self.running = True
        self.load_suggestions()
        
        logger.info("Self-optimization system started")
        
        while self.running:
            try:
                # 运行分析
                self.run_full_analysis()
                
                # 执行自动优化
                self.execute_auto_optimizations()
                
                await asyncio.sleep(self.analyze_interval)
            except Exception as e:
                logger.error(f"Optimization cycle failed: {e}")
                await asyncio.sleep(300)
        
        logger.info("Self-optimization system stopped")
    
    def stop(self):
        """停止系统"""
        self.running = False


# 便捷函数
_optimizer: Optional[SelfOptimizer] = None


def get_optimizer() -> SelfOptimizer:
    """获取全局优化器实例"""
    global _optimizer
    if _optimizer is None:
        _optimizer = SelfOptimizer()
    return _optimizer


def analyze_now() -> List[Dict]:
    """立即运行分析"""
    optimizer = get_optimizer()
    optimizer.load_suggestions()
    new_suggestions = optimizer.run_full_analysis()
    return [asdict(s) for s in new_suggestions]


def get_optimization_summary() -> Dict:
    """获取优化摘要"""
    optimizer = get_optimizer()
    optimizer.load_suggestions()
    return optimizer.get_summary()


# CLI接口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Self-Optimization System')
    parser.add_argument('--run', action='store_true', help='Run continuous optimization')
    parser.add_argument('--analyze', action='store_true', help='Run analysis once')
    parser.add_argument('--auto-execute', action='store_true', help='Execute auto-optimizations')
    parser.add_argument('--summary', action='store_true', help='Show summary')
    parser.add_argument('--list', action='store_true', help='List all suggestions')
    parser.add_argument('--pending', action='store_true', help='List pending suggestions')
    
    args = parser.parse_args()
    
    optimizer = get_optimizer()
    
    if args.run:
        try:
            asyncio.run(optimizer.run())
        except KeyboardInterrupt:
            optimizer.stop()
    elif args.analyze:
        suggestions = analyze_now()
        print(json.dumps(suggestions, indent=2, default=str))
    elif args.auto_execute:
        optimizer.load_suggestions()
        results = optimizer.execute_auto_optimizations()
        print(json.dumps(results, indent=2))
    elif args.summary:
        print(json.dumps(get_optimization_summary(), indent=2))
    elif args.list:
        optimizer.load_suggestions()
        print(json.dumps(optimizer.get_suggestions(), indent=2))
    elif args.pending:
        optimizer.load_suggestions()
        print(json.dumps(optimizer.get_suggestions(pending_only=True), indent=2))
    else:
        print(json.dumps(get_optimization_summary(), indent=2))
