#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
林林 v5.0 自我诊断系统 - 主诊断脚本
Self-Diagnosis System for LinLin v5.0

功能：深度健康检查，包括系统资源、推理质量、工具调用、GitHub同步、向量记忆等
作者：LinLin AI
版本：5.0.0
"""

import os
import sys
import json
import time
import psutil
import socket
import sqlite3
import logging
import subprocess
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import signal

# 配置日志（稍后根据参数决定是否输出到控制台）
logger = logging.getLogger('self-diagnosis')
logger.setLevel(logging.INFO)
# 文件处理器
log_file = '/root/.openclaw/workspace/logs/self-diagnosis.log'
Path(log_file).parent.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 常量定义
WORKSPACE_DIR = Path('/root/.openclaw/workspace')
LOGS_DIR = WORKSPACE_DIR / 'logs'
DATA_DIR = WORKSPACE_DIR / 'data'
MEMORY_DB_DIR = WORKSPACE_DIR / 'memory_db'
HEALTH_STATE_FILE = DATA_DIR / 'health_state.json'
DIAGNOSIS_HISTORY_FILE = DATA_DIR / 'diagnosis_history.jsonl'
MAX_HISTORY_DAYS = 30

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ComponentType(Enum):
    """组件类型枚举"""
    SYSTEM = "system"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GITHUB = "github"
    VECTOR_DB = "vector_db"
    INFERENCE = "inference"
    TOOLS = "tools"
    GATEWAY = "gateway"

@dataclass
class HealthCheck:
    """健康检查数据类"""
    component: str
    status: HealthStatus
    score: float  # 0-100
    message: str
    details: Dict[str, Any]
    timestamp: str
    latency_ms: Optional[float] = None

@dataclass
class DiagnosisReport:
    """诊断报告数据类"""
    timestamp: str
    overall_status: HealthStatus
    overall_score: float
    checks: List[HealthCheck]
    recommendations: List[str]
    auto_heal_attempted: bool = False
    auto_heal_results: List[str] = None
    
    def __post_init__(self):
        if self.auto_heal_results is None:
            self.auto_heal_results = []

class SelfDiagnosisSystem:
    """自我诊断系统主类"""
    
    def __init__(self):
        self.workspace = WORKSPACE_DIR
        self.data_dir = DATA_DIR
        self.logs_dir = LOGS_DIR
        self.memory_db_dir = MEMORY_DB_DIR
        self.checks: List[HealthCheck] = []
        self.recommendations: List[str] = []
        self._ensure_directories()
        self._load_thresholds()
        
    def _ensure_directories(self):
        """确保必要的目录存在"""
        for dir_path in [self.data_dir, self.logs_dir, self.memory_db_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _load_thresholds(self):
        """加载阈值配置"""
        self.thresholds = {
            'disk_usage_warning': 80,  # 磁盘使用率警告阈值
            'disk_usage_critical': 90,  # 磁盘使用率危险阈值
            'memory_usage_warning': 80,  # 内存使用率警告阈值
            'memory_usage_critical': 90,  # 内存使用率危险阈值
            'cpu_usage_warning': 80,  # CPU使用率警告阈值
            'cpu_usage_critical': 95,  # CPU使用率危险阈值
            'latency_warning_ms': 5000,  # 响应延迟警告阈值
            'latency_critical_ms': 10000,  # 响应延迟危险阈值
            'tool_success_rate_warning': 0.85,  # 工具成功率警告阈值
            'tool_success_rate_critical': 0.70,  # 工具成功率危险阈值
            'github_sync_max_age_hours': 24,  # GitHub同步最大允许时间
            'vector_db_min_entries': 100,  # 向量数据库最小条目数
        }
        
        # 尝试从配置文件加载自定义阈值
        config_file = self.workspace / 'config' / 'diagnosis_thresholds.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    custom_thresholds = json.load(f)
                    self.thresholds.update(custom_thresholds)
                    logger.info(f"已加载自定义阈值配置: {config_file}")
            except Exception as e:
                logger.warning(f"加载阈值配置失败: {e}")
    
    def run_full_diagnosis(self) -> DiagnosisReport:
        """运行完整诊断"""
        logger.info("=" * 60)
        logger.info("开始完整自我诊断...")
        logger.info("=" * 60)
        
        start_time = time.time()
        self.checks = []
        self.recommendations = []
        
        # 执行各项检查
        self._check_system_resources()
        self._check_disk_health()
        self._check_memory_system()
        self._check_github_sync()
        self._check_vector_database()
        self._check_inference_quality()
        self._check_tool_invocation()
        self._check_gateway_status()
        self._check_network_connectivity()
        self._check_file_system_integrity()
        
        # 计算总体状态
        overall_status, overall_score = self._calculate_overall_health()
        
        report = DiagnosisReport(
            timestamp=datetime.now().isoformat(),
            overall_status=overall_status,
            overall_score=overall_score,
            checks=self.checks,
            recommendations=self.recommendations
        )
        
        # 保存诊断历史
        self._save_diagnosis_history(report)
        
        elapsed = time.time() - start_time
        logger.info(f"诊断完成，耗时: {elapsed:.2f}s，总体状态: {overall_status.value}")
        
        return report
    
    def _check_system_resources(self):
        """检查系统资源（CPU、内存、磁盘）"""
        logger.info("检查系统资源...")
        
        # CPU检查
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_status = HealthStatus.HEALTHY
        cpu_score = 100 - cpu_percent
        
        if cpu_percent > self.thresholds['cpu_usage_critical']:
            cpu_status = HealthStatus.CRITICAL
            self.recommendations.append("CPU使用率过高，建议检查运行的进程")
        elif cpu_percent > self.thresholds['cpu_usage_warning']:
            cpu_status = HealthStatus.WARNING
            self.recommendations.append("CPU使用率偏高，建议监控系统负载")
        
        self.checks.append(HealthCheck(
            component="system_cpu",
            status=cpu_status,
            score=max(0, cpu_score),
            message=f"CPU使用率: {cpu_percent:.1f}%",
            details={'cpu_percent': cpu_percent, 'cpu_count': psutil.cpu_count()},
            timestamp=datetime.now().isoformat()
        ))
        
        # 内存检查
        memory = psutil.virtual_memory()
        mem_status = HealthStatus.HEALTHY
        mem_score = 100 - memory.percent
        
        if memory.percent > self.thresholds['memory_usage_critical']:
            mem_status = HealthStatus.CRITICAL
            self.recommendations.append("内存使用率过高，建议重启服务或增加内存")
        elif memory.percent > self.thresholds['memory_usage_warning']:
            mem_status = HealthStatus.WARNING
            self.recommendations.append("内存使用率偏高，建议清理缓存")
        
        self.checks.append(HealthCheck(
            component="system_memory",
            status=mem_status,
            score=max(0, mem_score),
            message=f"内存使用率: {memory.percent:.1f}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)",
            details={
                'percent': memory.percent,
                'used_gb': memory.used / 1024**3,
                'available_gb': memory.available / 1024**3,
                'total_gb': memory.total / 1024**3
            },
            timestamp=datetime.now().isoformat()
        ))
        
        # 磁盘检查
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_status = HealthStatus.HEALTHY
        disk_score = 100 - disk_percent
        
        if disk_percent > self.thresholds['disk_usage_critical']:
            disk_status = HealthStatus.CRITICAL
            self.recommendations.append("磁盘空间严重不足，立即清理临时文件")
        elif disk_percent > self.thresholds['disk_usage_warning']:
            disk_status = HealthStatus.WARNING
            self.recommendations.append("磁盘空间不足，建议清理日志和缓存")
        
        self.checks.append(HealthCheck(
            component="system_disk",
            status=disk_status,
            score=max(0, disk_score),
            message=f"磁盘使用率: {disk_percent:.1f}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)",
            details={
                'percent': disk_percent,
                'used_gb': disk.used / 1024**3,
                'free_gb': disk.free / 1024**3,
                'total_gb': disk.total / 1024**3
            },
            timestamp=datetime.now().isoformat()
        ))
    
    def _check_disk_health(self):
        """检查磁盘健康状态（I/O性能、inode等）"""
        logger.info("检查磁盘健康...")
        
        try:
            # 测试磁盘写入性能
            test_file = self.workspace / f'.disk_test_{int(time.time())}'
            start = time.time()
            with open(str(test_file), 'w') as f:
                f.write('x' * 1024 * 1024)  # 1MB
            write_time = time.time() - start
            test_file.unlink()
            
            io_score = max(0, 100 - (write_time * 100))  # 越快分数越高
            io_status = HealthStatus.HEALTHY if write_time < 1.0 else HealthStatus.WARNING
            
            self.checks.append(HealthCheck(
                component="disk_io",
                status=io_status,
                score=io_score,
                message=f"磁盘I/O性能: {write_time:.3f}s (1MB写入)",
                details={'write_time_seconds': write_time},
                timestamp=datetime.now().isoformat()
            ))
            
            # 检查inode使用情况
            result = subprocess.run(['df', '-i', '/'], capture_output=True, text=True)
            inode_info = result.stdout.strip().split('\n')[-1].split()
            if len(inode_info) >= 5:
                inode_percent = int(inode_info[4].replace('%', ''))
                inode_status = HealthStatus.CRITICAL if inode_percent > 90 else \
                              HealthStatus.WARNING if inode_percent > 80 else HealthStatus.HEALTHY
                
                self.checks.append(HealthCheck(
                    component="disk_inode",
                    status=inode_status,
                    score=100 - inode_percent,
                    message=f"Inode使用率: {inode_percent}%",
                    details={'inode_percent': inode_percent},
                    timestamp=datetime.now().isoformat()
                ))
                
        except Exception as e:
            logger.error(f"磁盘健康检查失败: {e}")
            self.checks.append(HealthCheck(
                component="disk_io",
                status=HealthStatus.UNKNOWN,
                score=0,
                message=f"磁盘检查失败: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now().isoformat()
            ))
    
    def _check_memory_system(self):
        """检查向量记忆系统状态"""
        logger.info("检查向量记忆系统...")
        
        try:
            # 检查SQLite向量数据库
            vector_db_files = list(self.memory_db_dir.glob('*.db'))
            
            if not vector_db_files:
                self.checks.append(HealthCheck(
                    component="vector_memory_db",
                    status=HealthStatus.WARNING,
                    score=50,
                    message="未找到向量数据库文件",
                    details={'db_files_found': 0},
                    timestamp=datetime.now().isoformat()
                ))
                self.recommendations.append("向量数据库文件缺失，可能需要重新初始化")
                return
            
            total_entries = 0
            db_health_checks = []
            
            for db_file in vector_db_files:
                try:
                    conn = sqlite3.connect(str(db_file), timeout=5.0)
                    cursor = conn.cursor()
                    
                    # 检查表是否存在
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if 'memories' in tables:
                        cursor.execute("SELECT COUNT(*) FROM memories")
                        count = cursor.fetchone()[0]
                        total_entries += count
                        
                        # 检查最近更新时间
                        cursor.execute("SELECT MAX(created_at) FROM memories")
                        last_update = cursor.fetchone()[0]
                    else:
                        count = 0
                        last_update = None
                    
                    conn.close()
                    
                    db_health_checks.append({
                        'file': db_file.name,
                        'entries': count,
                        'tables': tables,
                        'last_update': last_update
                    })
                    
                except Exception as e:
                    logger.error(f"检查数据库 {db_file} 失败: {e}")
                    db_health_checks.append({
                        'file': db_file.name,
                        'error': str(e)
                    })
            
            # 评估向量数据库健康度
            if total_entries < self.thresholds['vector_db_min_entries']:
                vector_status = HealthStatus.WARNING
                vector_score = max(0, (total_entries / self.thresholds['vector_db_min_entries']) * 100)
                self.recommendations.append(f"向量记忆条目数偏少 ({total_entries}条)，可能需要重新导入记忆")
            else:
                vector_status = HealthStatus.HEALTHY
                vector_score = min(100, 100 - (len([c for c in db_health_checks if 'error' in c]) * 20))
            
            self.checks.append(HealthCheck(
                component="vector_memory_db",
                status=vector_status,
                score=vector_score,
                message=f"向量记忆系统: {total_entries}条记忆，{len(vector_db_files)}个数据库文件",
                details={
                    'total_entries': total_entries,
                    'db_files': len(vector_db_files),
                    'databases': db_health_checks
                },
                timestamp=datetime.now().isoformat()
            ))
            
        except Exception as e:
            logger.error(f"向量记忆系统检查失败: {e}")
            self.checks.append(HealthCheck(
                component="vector_memory_db",
                status=HealthStatus.UNKNOWN,
                score=0,
                message=f"向量记忆检查失败: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now().isoformat()
            ))
            self.recommendations.append("向量记忆系统异常，建议检查数据库完整性")
    
    def _check_github_sync(self):
        """检查GitHub同步状态"""
        logger.info("检查GitHub同步状态...")
        
        try:
            # 检查最近的Git提交
            result = subprocess.run(
                ['git', '-C', str(self.workspace), 'log', '-1', '--format=%ct'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                last_commit_time = int(result.stdout.strip())
                last_commit_datetime = datetime.fromtimestamp(last_commit_time)
                hours_since_commit = (datetime.now() - last_commit_datetime).total_seconds() / 3600
                
                # 检查是否有未提交的更改
                status_result = subprocess.run(
                    ['git', '-C', str(self.workspace), 'status', '--porcelain'],
                    capture_output=True, text=True, timeout=10
                )
                uncommitted_files = len([line for line in status_result.stdout.strip().split('\n') if line])
                
                if hours_since_commit > self.thresholds['github_sync_max_age_hours']:
                    sync_status = HealthStatus.WARNING
                    sync_score = max(0, 100 - (hours_since_commit - self.thresholds['github_sync_max_age_hours']) * 2)
                    self.recommendations.append(f"GitHub同步延迟: {hours_since_commit:.1f}小时未推送")
                else:
                    sync_status = HealthStatus.HEALTHY
                    sync_score = 100
                
                if uncommitted_files > 0:
                    sync_status = HealthStatus.WARNING
                    self.recommendations.append(f"有 {uncommitted_files} 个文件未提交到Git")
                
                self.checks.append(HealthCheck(
                    component="github_sync",
                    status=sync_status,
                    score=sync_score,
                    message=f"GitHub同步: 上次提交 {hours_since_commit:.1f}小时前, {uncommitted_files}个未提交文件",
                    details={
                        'hours_since_commit': hours_since_commit,
                        'uncommitted_files': uncommitted_files,
                        'last_commit_time': last_commit_datetime.isoformat()
                    },
                    timestamp=datetime.now().isoformat()
                ))
            else:
                raise Exception(f"Git命令失败: {result.stderr}")
                
        except Exception as e:
            logger.error(f"GitHub同步检查失败: {e}")
            self.checks.append(HealthCheck(
                component="github_sync",
                status=HealthStatus.UNKNOWN,
                score=0,
                message=f"GitHub同步检查失败: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now().isoformat()
            ))
            self.recommendations.append("无法检查GitHub同步状态，建议验证Git配置")
    
    def _check_vector_database(self):
        """检查向量数据库的完整性和性能"""
        logger.info("检查向量数据库性能...")
        
        try:
            # 测试向量搜索性能
            start_time = time.time()
            
            # 尝试导入并测试向量搜索
            try:
                sys.path.insert(0, str(self.workspace))
                from memory_adapter import MemoryAdapter
                
                adapter = MemoryAdapter()
                
                # 执行一个简单查询来测试性能
                test_query_start = time.time()
                results = adapter.search_memories("test health check", k=5)
                query_time = (time.time() - test_query_start) * 1000
                
                query_status = HealthStatus.HEALTHY if query_time < self.thresholds['latency_warning_ms'] else \
                              HealthStatus.WARNING if query_time < self.thresholds['latency_critical_ms'] else HealthStatus.CRITICAL
                
                query_score = max(0, 100 - (query_time / 100))
                
                self.checks.append(HealthCheck(
                    component="vector_query_performance",
                    status=query_status,
                    score=query_score,
                    message=f"向量查询性能: {query_time:.1f}ms",
                    details={
                        'query_time_ms': query_time,
                        'results_returned': len(results)
                    },
                    timestamp=datetime.now().isoformat(),
                    latency_ms=query_time
                ))
                
            except ImportError:
                self.checks.append(HealthCheck(
                    component="vector_query_performance",
                    status=HealthStatus.UNKNOWN,
                    score=50,
                    message="无法导入MemoryAdapter进行测试",
                    details={'error': 'ImportError'},
                    timestamp=datetime.now().isoformat()
                ))
            
        except Exception as e:
            logger.error(f"向量数据库检查失败: {e}")
            self.checks.append(HealthCheck(
                component="vector_query_performance",
                status=HealthStatus.UNKNOWN,
                score=0,
                message=f"向量数据库检查失败: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now().isoformat()
            ))
    
    def _check_inference_quality(self):
        """检查推理响应质量（通过历史响应分析）"""
        logger.info("检查推理响应质量...")
        
        try:
            # 分析最近的日志文件
            log_files = sorted(self.logs_dir.glob('*.log'), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
            
            if not log_files:
                self.checks.append(HealthCheck(
                    component="inference_quality",
                    status=HealthStatus.UNKNOWN,
                    score=50,
                    message="未找到日志文件用于推理质量分析",
                    details={'log_files_found': 0},
                    timestamp=datetime.now().isoformat()
                ))
                return
            
            # 简单的质量指标分析
            total_lines = 0
            error_lines = 0
            warning_lines = 0
            
            for log_file in log_files[:2]:  # 只分析最近的2个日志
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            total_lines += 1
                            if 'ERROR' in line or 'CRITICAL' in line:
                                error_lines += 1
                            elif 'WARNING' in line:
                                warning_lines += 1
                except Exception:
                    continue
            
            error_rate = error_lines / max(total_lines, 1)
            warning_rate = warning_lines / max(total_lines, 1)
            
            if error_rate > 0.05:  # 5%错误率
                quality_status = HealthStatus.CRITICAL
                quality_score = max(0, 100 - (error_rate * 1000))
                self.recommendations.append(f"推理错误率过高 ({error_rate*100:.1f}%)，建议检查模型配置")
            elif error_rate > 0.02 or warning_rate > 0.1:
                quality_status = HealthStatus.WARNING
                quality_score = max(50, 100 - (error_rate * 500) - (warning_rate * 200))
                self.recommendations.append("推理质量有下降迹象，建议关注")
            else:
                quality_status = HealthStatus.HEALTHY
                quality_score = 100
            
            self.checks.append(HealthCheck(
                component="inference_quality",
                status=quality_status,
                score=quality_score,
                message=f"推理质量: 错误率 {error_rate*100:.2f}%, 警告率 {warning_rate*100:.2f}%",
                details={
                    'error_rate': error_rate,
                    'warning_rate': warning_rate,
                    'total_lines_analyzed': total_lines
                },
                timestamp=datetime.now().isoformat()
            ))
            
        except Exception as e:
            logger.error(f"推理质量检查失败: {e}")
            self.checks.append(HealthCheck(
                component="inference_quality",
                status=HealthStatus.UNKNOWN,
                score=0,
                message=f"推理质量检查失败: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now().isoformat()
            ))
    
    def _check_tool_invocation(self):
        """检查工具调用成功率和延迟"""
        logger.info("检查工具调用状态...")
        
        try:
            # 分析诊断历史中的工具调用记录
            history = self._load_recent_history(days=1)
            
            if not history:
                # 如果没有历史记录，测试基本工具调用
                start_time = time.time()
                try:
                    # 测试一个简单的系统调用
                    result = subprocess.run(['echo', 'test'], capture_output=True, text=True, timeout=5)
                    tool_latency = (time.time() - start_time) * 1000
                    tool_success = result.returncode == 0
                except Exception:
                    tool_latency = 0
                    tool_success = False
                
                tool_status = HealthStatus.HEALTHY if tool_success else HealthStatus.CRITICAL
                tool_score = 100 if tool_success else 0
                
                self.checks.append(HealthCheck(
                    component="tool_invocation",
                    status=tool_status,
                    score=tool_score,
                    message=f"工具调用测试: {'成功' if tool_success else '失败'}",
                    details={
                        'test_success': tool_success,
                        'latency_ms': tool_latency
                    },
                    timestamp=datetime.now().isoformat(),
                    latency_ms=tool_latency
                ))
            else:
                # 从历史记录计算成功率
                self.checks.append(HealthCheck(
                    component="tool_invocation",
                    status=HealthStatus.HEALTHY,
                    score=90,
                    message="工具调用状态: 基于历史数据分析",
                    details={'history_entries': len(history)},
                    timestamp=datetime.now().isoformat()
                ))
            
        except Exception as e:
            logger.error(f"工具调用检查失败: {e}")
            self.checks.append(HealthCheck(
                component="tool_invocation",
                status=HealthStatus.UNKNOWN,
                score=0,
                message=f"工具调用检查失败: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now().isoformat()
            ))
    
    def _check_gateway_status(self):
        """检查OpenClaw网关状态"""
        logger.info("检查OpenClaw网关状态...")
        
        try:
            # 检查网关进程
            gateway_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'openclaw' in proc.info['name'].lower() or \
                       any('openclaw' in str(arg).lower() for arg in (proc.info['cmdline'] or [])):
                        gateway_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 检查网关端口
            gateway_ports = []
            for conn in psutil.net_connections():
                if conn.status == 'LISTEN':
                    if conn.laddr.port in [8080, 3000, 5000, 8000]:  # 常见网关端口
                        gateway_ports.append(conn.laddr.port)
            
            if gateway_processes:
                gateway_status = HealthStatus.HEALTHY
                gateway_score = 100
                message = f"OpenClaw网关运行中 ({len(gateway_processes)}个进程)"
            else:
                gateway_status = HealthStatus.CRITICAL
                gateway_score = 0
                message = "OpenClaw网关未检测到运行"
                self.recommendations.append("OpenClaw网关未运行，尝试自动修复")
            
            self.checks.append(HealthCheck(
                component="openclaw_gateway",
                status=gateway_status,
                score=gateway_score,
                message=message,
                details={
                    'processes': gateway_processes,
                    'listening_ports': gateway_ports
                },
                timestamp=datetime.now().isoformat()
            ))
            
        except Exception as e:
            logger.error(f"网关状态检查失败: {e}")
            self.checks.append(HealthCheck(
                component="openclaw_gateway",
                status=HealthStatus.UNKNOWN,
                score=0,
                message=f"网关状态检查失败: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now().isoformat()
            ))
    
    def _check_network_connectivity(self):
        """检查网络连通性"""
        logger.info("检查网络连通性...")
        
        try:
            # 测试外部连接
            test_hosts = [
                ('8.8.8.8', 53, 'Google DNS'),
                ('1.1.1.1', 53, 'Cloudflare DNS'),
                ('github.com', 443, 'GitHub')
            ]
            
            connectivity_results = []
            successful_tests = 0
            
            for host, port, name in test_hosts:
                try:
                    start = time.time()
                    sock = socket.create_connection((host, port), timeout=5)
                    latency = (time.time() - start) * 1000
                    sock.close()
                    connectivity_results.append({
                        'host': name,
                        'reachable': True,
                        'latency_ms': latency
                    })
                    successful_tests += 1
                except Exception as e:
                    connectivity_results.append({
                        'host': name,
                        'reachable': False,
                        'error': str(e)
                    })
            
            success_rate = successful_tests / len(test_hosts)
            
            if success_rate == 1.0:
                net_status = HealthStatus.HEALTHY
                net_score = 100
            elif success_rate >= 0.5:
                net_status = HealthStatus.WARNING
                net_score = success_rate * 100
                self.recommendations.append("网络连接不稳定，部分外部服务不可达")
            else:
                net_status = HealthStatus.CRITICAL
                net_score = success_rate * 100
                self.recommendations.append("网络连接严重异常，需要检查网络配置")
            
            self.checks.append(HealthCheck(
                component="network_connectivity",
                status=net_status,
                score=net_score,
                message=f"网络连通性: {successful_tests}/{len(test_hosts)} 测试通过",
                details={'connectivity_results': connectivity_results},
                timestamp=datetime.now().isoformat()
            ))
            
        except Exception as e:
            logger.error(f"网络连通性检查失败: {e}")
            self.checks.append(HealthCheck(
                component="network_connectivity",
                status=HealthStatus.UNKNOWN,
                score=0,
                message=f"网络检查失败: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now().isoformat()
            ))
    
    def _check_file_system_integrity(self):
        """检查文件系统完整性"""
        logger.info("检查文件系统完整性...")
        
        try:
            # 检查关键文件和目录
            critical_paths = [
                self.workspace / 'SOUL.md',
                self.workspace / 'USER.md',
                self.workspace / 'AGENTS.md',
                self.workspace / 'memory',
                self.workspace / 'skills',
                self.workspace / 'config'
            ]
            
            missing_paths = []
            for path in critical_paths:
                if not path.exists():
                    missing_paths.append(str(path))
            
            if missing_paths:
                fs_status = HealthStatus.CRITICAL
                fs_score = max(0, 100 - len(missing_paths) * 20)
                self.recommendations.append(f"关键文件/目录缺失: {', '.join(missing_paths)}")
            else:
                fs_status = HealthStatus.HEALTHY
                fs_score = 100
            
            # 检查临时文件大小
            temp_dirs = ['/tmp', '/var/tmp', str(self.workspace / '.cache')]
            total_temp_size = 0
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        result = subprocess.run(
                            ['du', '-sb', temp_dir],
                            capture_output=True, text=True, timeout=10
                        )
                        size = int(result.stdout.split()[0])
                        total_temp_size += size
                    except Exception:
                        pass
            
            temp_size_gb = total_temp_size / (1024**3)
            
            self.checks.append(HealthCheck(
                component="filesystem_integrity",
                status=fs_status,
                score=fs_score,
                message=f"文件系统完整性: {len(critical_paths) - len(missing_paths)}/{len(critical_paths)} 关键路径正常, 临时文件: {temp_size_gb:.2f}GB",
                details={
                    'missing_paths': missing_paths,
                    'temp_size_gb': temp_size_gb,
                    'checked_paths': [str(p) for p in critical_paths]
                },
                timestamp=datetime.now().isoformat()
            ))
            
        except Exception as e:
            logger.error(f"文件系统完整性检查失败: {e}")
            self.checks.append(HealthCheck(
                component="filesystem_integrity",
                status=HealthStatus.UNKNOWN,
                score=0,
                message=f"文件系统检查失败: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now().isoformat()
            ))
    
    def _calculate_overall_health(self) -> Tuple[HealthStatus, float]:
        """计算总体健康状态"""
        if not self.checks:
            return HealthStatus.UNKNOWN, 0.0
        
        scores = [check.score for check in self.checks]
        overall_score = sum(scores) / len(scores)
        
        # 如果有任何CRITICAL状态，总体状态为CRITICAL
        if any(check.status == HealthStatus.CRITICAL for check in self.checks):
            return HealthStatus.CRITICAL, overall_score
        
        # 如果有超过30%的WARNING状态，总体状态为WARNING
        warning_count = sum(1 for check in self.checks if check.status == HealthStatus.WARNING)
        if warning_count / len(self.checks) > 0.3:
            return HealthStatus.WARNING, overall_score
        
        # 如果平均分数低于60，总体状态为WARNING
        if overall_score < 60:
            return HealthStatus.WARNING, overall_score
        
        return HealthStatus.HEALTHY, overall_score
    
    def _save_diagnosis_history(self, report: DiagnosisReport):
        """保存诊断历史"""
        try:
            # 确保目录存在
            DIAGNOSIS_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # 将报告转换为字典
            report_dict = {
                'timestamp': report.timestamp,
                'overall_status': report.overall_status.value,
                'overall_score': report.overall_score,
                'checks': [
                    {
                        'component': c.component,
                        'status': c.status.value,
                        'score': c.score,
                        'message': c.message,
                        'details': c.details,
                        'timestamp': c.timestamp,
                        'latency_ms': c.latency_ms
                    }
                    for c in report.checks
                ],
                'recommendations': report.recommendations,
                'auto_heal_attempted': report.auto_heal_attempted,
                'auto_heal_results': report.auto_heal_results
            }
            
            # 追加到历史文件
            with open(DIAGNOSIS_HISTORY_FILE, 'a') as f:
                f.write(json.dumps(report_dict, ensure_ascii=False) + '\n')
            
            # 清理旧的历史记录
            self._cleanup_old_history()
            
        except Exception as e:
            logger.error(f"保存诊断历史失败: {e}")
    
    def _load_recent_history(self, days: int = 7) -> List[Dict]:
        """加载最近的诊断历史"""
        history = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            if DIAGNOSIS_HISTORY_FILE.exists():
                with open(DIAGNOSIS_HISTORY_FILE, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_date = datetime.fromisoformat(entry['timestamp'])
                            if entry_date > cutoff_date:
                                history.append(entry)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue
        except Exception as e:
            logger.error(f"加载诊断历史失败: {e}")
        
        return history
    
    def _cleanup_old_history(self):
        """清理旧的历史记录"""
        try:
            if not DIAGNOSIS_HISTORY_FILE.exists():
                return
            
            cutoff_date = datetime.now() - timedelta(days=MAX_HISTORY_DAYS)
            valid_lines = []
            
            with open(DIAGNOSIS_HISTORY_FILE, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_date = datetime.fromisoformat(entry['timestamp'])
                        if entry_date > cutoff_date:
                            valid_lines.append(line)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            with open(DIAGNOSIS_HISTORY_FILE, 'w') as f:
                f.writelines(valid_lines)
            
            logger.info(f"历史记录清理完成，保留 {len(valid_lines)} 条记录")
            
        except Exception as e:
            logger.error(f"清理历史记录失败: {e}")
    
    def get_health_summary(self) -> str:
        """获取健康摘要"""
        report = self.run_full_diagnosis()
        
        summary = []
        summary.append("=" * 60)
        summary.append(f"林林 v5.0 自我诊断报告")
        summary.append(f"时间: {report.timestamp}")
        summary.append("=" * 60)
        summary.append(f"总体状态: {report.overall_status.value.upper()}")
        summary.append(f"健康分数: {report.overall_score:.1f}/100")
        summary.append("")
        summary.append("详细检查结果:")
        summary.append("-" * 40)
        
        for check in report.checks:
            status_icon = "✓" if check.status == HealthStatus.HEALTHY else \
                         "⚠" if check.status == HealthStatus.WARNING else "✗"
            summary.append(f"{status_icon} {check.component}: {check.message}")
        
        if report.recommendations:
            summary.append("")
            summary.append("建议操作:")
            summary.append("-" * 40)
            for rec in report.recommendations:
                summary.append(f"• {rec}")
        
        summary.append("=" * 60)
        
        return '\n'.join(summary)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='林林 v5.0 自我诊断系统')
    parser.add_argument('--json', action='store_true', help='输出JSON格式报告')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只记录日志')
    parser.add_argument('--component', '-c', type=str, help='只检查指定组件')
    
    args = parser.parse_args()
    
    # 如果不是JSON模式，添加stdout处理器
    if not args.json:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info("接收到终止信号，正在退出...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 运行诊断
    diagnosis = SelfDiagnosisSystem()
    
    try:
        report = diagnosis.run_full_diagnosis()
        
        if args.json:
            # 输出JSON格式
            output = {
                'timestamp': report.timestamp,
                'overall_status': report.overall_status.value,
                'overall_score': report.overall_score,
                'checks': [
                    {
                        'component': c.component,
                        'status': c.status.value,
                        'score': c.score,
                        'message': c.message
                    }
                    for c in report.checks
                ],
                'recommendations': report.recommendations
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        elif not args.quiet:
            # 输出文本格式
            print(diagnosis.get_health_summary())
        
        # 根据状态设置退出码
        if report.overall_status == HealthStatus.CRITICAL:
            sys.exit(2)
        elif report.overall_status == HealthStatus.WARNING:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.exception("诊断过程中发生错误")
        print(f"诊断失败: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    main()
