#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
林林 v5.0 自动修复系统 - Auto-Heal Script

功能：自动故障隔离和修复尝试
- 自动降级非核心功能
- 重启openclaw网关
- 清理缓存/临时文件
- 切换备用配置
- 重新初始化连接

作者：LinLin AI
版本：5.0.0
"""

import os
import sys
import json
import time
import shutil
import signal
import logging
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import psutil

# 将workspace添加到路径
sys.path.insert(0, '/root/.openclaw/workspace')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/auto-heal.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('auto-heal')

# 常量定义
WORKSPACE_DIR = Path('/root/.openclaw/workspace')
DATA_DIR = WORKSPACE_DIR / 'data'
LOGS_DIR = WORKSPACE_DIR / 'logs'
CACHE_DIR = WORKSPACE_DIR / '.cache'
TEMP_DIR = Path('/tmp/linlin_heal')
HEAL_STATE_FILE = DATA_DIR / 'heal_state.json'
HEAL_HISTORY_FILE = DATA_DIR / 'heal_history.jsonl'
MAX_HEAL_ATTEMPTS = 3  # 同一问题最大修复尝试次数
HEAL_COOLDOWN_MINUTES = 30  # 修复冷却时间

class HealSeverity(Enum):
    """修复严重级别"""
    INFO = "info"           # 信息，无需修复
    LOW = "low"             # 轻微问题，静默修复
    MEDIUM = "medium"       # 中等问题，记录修复
    HIGH = "high"           # 严重问题，通知用户
    CRITICAL = "critical"   # 紧急问题，立即告警

class HealAction(Enum):
    """修复动作类型"""
    CLEANUP_CACHE = "cleanup_cache"
    RESTART_GATEWAY = "restart_gateway"
    REINIT_CONNECTION = "reinit_connection"
    SWITCH_CONFIG = "switch_config"
    DEGRADE_FEATURES = "degrade_features"
    COMPACT_DATABASE = "compact_database"
    CLEAR_LOGS = "clear_logs"
    RESTART_PROCESS = "restart_process"
    GARBAGE_COLLECT = "garbage_collect"

@dataclass
class HealResult:
    """修复结果数据类"""
    action: str
    target: str
    success: bool
    message: str
    timestamp: str
    duration_ms: float
    before_state: Optional[Dict] = None
    after_state: Optional[Dict] = None

@dataclass
class HealReport:
    """修复报告数据类"""
    timestamp: str
    trigger_reason: str
    severity: HealSeverity
    actions_taken: List[HealResult]
    overall_success: bool
    needs_human_attention: bool
    notification_message: Optional[str] = None

class AutoHealSystem:
    """自动修复系统主类"""
    
    def __init__(self):
        self.workspace = WORKSPACE_DIR
        self.data_dir = DATA_DIR
        self.logs_dir = LOGS_DIR
        self.cache_dir = CACHE_DIR
        self.heal_state = self._load_heal_state()
        self.actions_taken: List[HealResult] = []
        self._ensure_directories()
        
    def _ensure_directories(self):
        """确保必要的目录存在"""
        for dir_path in [self.data_dir, self.logs_dir, TEMP_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _load_heal_state(self) -> Dict:
        """加载修复状态"""
        if HEAL_STATE_FILE.exists():
            try:
                with open(HEAL_STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载修复状态失败: {e}")
        return {
            'last_heal_time': None,
            'heal_attempts': {},  # 问题 -> 尝试次数
            'successful_heals': [],
            'failed_heals': []
        }
    
    def _save_heal_state(self):
        """保存修复状态"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(HEAL_STATE_FILE, 'w') as f:
                json.dump(self.heal_state, f, indent=2)
        except Exception as e:
            logger.error(f"保存修复状态失败: {e}")
    
    def _can_attempt_heal(self, issue_key: str) -> bool:
        """检查是否可以尝试修复（避免过度修复）"""
        now = datetime.now()
        
        # 检查冷却时间
        if self.heal_state['last_heal_time']:
            last_time = datetime.fromisoformat(self.heal_state['last_heal_time'])
            if (now - last_time) < timedelta(minutes=HEAL_COOLDOWN_MINUTES):
                logger.info(f"修复冷却中，跳过修复: {issue_key}")
                return False
        
        # 检查尝试次数
        attempts = self.heal_state['heal_attempts'].get(issue_key, 0)
        if attempts >= MAX_HEAL_ATTEMPTS:
            logger.warning(f"问题 {issue_key} 已达到最大修复尝试次数")
            return False
        
        return True
    
    def _record_heal_attempt(self, issue_key: str):
        """记录修复尝试"""
        self.heal_state['last_heal_time'] = datetime.now().isoformat()
        self.heal_state['heal_attempts'][issue_key] = \
            self.heal_state['heal_attempts'].get(issue_key, 0) + 1
        self._save_heal_state()
    
    def run_auto_heal(self, diagnosis_report: Optional[Dict] = None) -> HealReport:
        """运行自动修复流程"""
        logger.info("=" * 60)
        logger.info("启动自动修复系统...")
        logger.info("=" * 60)
        
        start_time = time.time()
        self.actions_taken = []
        
        # 如果没有诊断报告，先运行诊断
        if diagnosis_report is None:
            diagnosis_report = self._run_diagnosis()
        
        # 评估严重程度
        severity = self._assess_severity(diagnosis_report)
        trigger_reason = f"诊断状态: {diagnosis_report.get('overall_status', 'unknown')}"
        
        # 根据严重程度决定修复策略
        if severity == HealSeverity.INFO:
            logger.info("系统健康，无需修复")
            return HealReport(
                timestamp=datetime.now().isoformat(),
                trigger_reason=trigger_reason,
                severity=severity,
                actions_taken=[],
                overall_success=True,
                needs_human_attention=False
            )
        
        # 执行修复动作
        needs_attention = False
        notification_msg = None
        
        # 1. 清理缓存和临时文件（所有级别都执行）
        self._heal_cleanup_cache()
        
        # 2. 根据问题类型执行特定修复
        if severity in [HealSeverity.MEDIUM, HealSeverity.HIGH, HealSeverity.CRITICAL]:
            # 检查网关状态
            self._heal_gateway_restart()
            
            # 检查内存系统
            self._heal_memory_system()
            
            # 检查磁盘空间
            self._heal_disk_space()
        
        if severity in [HealSeverity.HIGH, HealSeverity.CRITICAL]:
            # 执行更激进的修复
            self._heal_compact_databases()
            self._heal_clear_old_logs()
            
            # 尝试重新初始化连接
            self._heal_reinit_connections()
        
        if severity == HealSeverity.CRITICAL:
            # 紧急模式：降级非核心功能
            self._heal_degrade_features()
            needs_attention = True
            notification_msg = self._build_critical_notification()
        
        # 计算总体成功率
        overall_success = all(action.success for action in self.actions_taken) if self.actions_taken else True
        
        # 如果有失败的修复且级别较高，需要人工关注
        if not overall_success and severity in [HealSeverity.HIGH, HealSeverity.CRITICAL]:
            needs_attention = True
            notification_msg = notification_msg or self._build_failure_notification()
        
        # 保存修复历史
        report = HealReport(
            timestamp=datetime.now().isoformat(),
            trigger_reason=trigger_reason,
            severity=severity,
            actions_taken=self.actions_taken,
            overall_success=overall_success,
            needs_human_attention=needs_attention,
            notification_message=notification_msg
        )
        
        self._save_heal_history(report)
        
        elapsed = time.time() - start_time
        logger.info(f"自动修复完成，耗时: {elapsed:.2f}s，总体成功: {overall_success}")
        
        return report
    
    def _run_diagnosis(self) -> Dict:
        """运行诊断"""
        try:
            result = subprocess.run(
                [sys.executable, str(self.workspace / 'scripts' / 'self-diagnosis.py'), '--json'],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode in [0, 1, 2]:  # 0=健康, 1=警告, 2=严重
                return json.loads(result.stdout)
            else:
                logger.error(f"诊断脚本执行失败: {result.stderr}")
                return {'overall_status': 'unknown', 'overall_score': 0}
        except Exception as e:
            logger.error(f"运行诊断失败: {e}")
            return {'overall_status': 'unknown', 'overall_score': 0}
    
    def _assess_severity(self, diagnosis_report: Dict) -> HealSeverity:
        """评估严重程度"""
        status = diagnosis_report.get('overall_status', 'unknown')
        score = diagnosis_report.get('overall_score', 0)
        
        if status == 'healthy' and score >= 80:
            return HealSeverity.INFO
        elif status == 'healthy' and score >= 60:
            return HealSeverity.LOW
        elif status == 'warning' and score >= 50:
            return HealSeverity.MEDIUM
        elif status == 'warning' or (status == 'critical' and score >= 30):
            return HealSeverity.HIGH
        else:
            return HealSeverity.CRITICAL
    
    def _heal_cleanup_cache(self) -> HealResult:
        """修复：清理缓存和临时文件"""
        action_start = time.time()
        action_key = HealAction.CLEANUP_CACHE.value
        
        if not self._can_attempt_heal(action_key):
            return HealResult(
                action=HealAction.CLEANUP_CACHE.value,
                target="cache_cleanup",
                success=False,
                message="修复冷却中，跳过",
                timestamp=datetime.now().isoformat(),
                duration_ms=0
            )
        
        logger.info("执行缓存清理...")
        self._record_heal_attempt(action_key)
        
        try:
            cleaned_size = 0
            cleaned_items = 0
            
            # 清理Python缓存
            pycache_dirs = list(self.workspace.rglob('__pycache__'))
            for pycache in pycache_dirs:
                try:
                    size = sum(f.stat().st_size for f in pycache.rglob('*') if f.is_file())
                    shutil.rmtree(pycache)
                    cleaned_size += size
                    cleaned_items += 1
                except Exception as e:
                    logger.warning(f"清理 {pycache} 失败: {e}")
            
            # 清理.pyc文件
            for pyc_file in self.workspace.rglob('*.pyc'):
                try:
                    size = pyc_file.stat().st_size
                    pyc_file.unlink()
                    cleaned_size += size
                    cleaned_items += 1
                except Exception:
                    pass
            
            # 清理临时文件
            temp_patterns = ['*.tmp', '*.temp', '*.log.old', '.DS_Store']
            for pattern in temp_patterns:
                for temp_file in self.workspace.rglob(pattern):
                    try:
                        if temp_file.is_file():
                            size = temp_file.stat().st_size
                            temp_file.unlink()
                            cleaned_size += size
                            cleaned_items += 1
                    except Exception:
                        pass
            
            # 清理系统临时目录中的LinLin相关文件
            system_temp = Path('/tmp')
            if system_temp.exists():
                for item in system_temp.iterdir():
                    if item.name.startswith('linlin') or item.name.startswith('openclaw'):
                        try:
                            if item.is_file():
                                size = item.stat().st_size
                                item.unlink()
                                cleaned_size += size
                                cleaned_items += 1
                            elif item.is_dir():
                                size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                                shutil.rmtree(item)
                                cleaned_size += size
                                cleaned_items += 1
                        except Exception:
                            pass
            
            duration = (time.time() - action_start) * 1000
            cleaned_mb = cleaned_size / (1024 * 1024)
            
            result = HealResult(
                action=HealAction.CLEANUP_CACHE.value,
                target="cache_cleanup",
                success=True,
                message=f"清理完成: {cleaned_items}项, {cleaned_mb:.2f}MB",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration,
                before_state={'cleaned_items': 0},
                after_state={'cleaned_items': cleaned_items, 'cleaned_mb': cleaned_mb}
            )
            
            self.actions_taken.append(result)
            logger.info(f"缓存清理完成: {cleaned_mb:.2f}MB")
            return result
            
        except Exception as e:
            duration = (time.time() - action_start) * 1000
            result = HealResult(
                action=HealAction.CLEANUP_CACHE.value,
                target="cache_cleanup",
                success=False,
                message=f"清理失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration
            )
            self.actions_taken.append(result)
            logger.error(f"缓存清理失败: {e}")
            return result
    
    def _heal_gateway_restart(self) -> HealResult:
        """修复：重启OpenClaw网关"""
        action_start = time.time()
        action_key = HealAction.RESTART_GATEWAY.value
        
        if not self._can_attempt_heal(action_key):
            return HealResult(
                action=HealAction.RESTART_GATEWAY.value,
                target="openclaw_gateway",
                success=False,
                message="修复冷却中，跳过",
                timestamp=datetime.now().isoformat(),
                duration_ms=0
            )
        
        logger.info("尝试重启OpenClaw网关...")
        self._record_heal_attempt(action_key)
        
        try:
            # 查找并停止现有网关进程
            stopped = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'openclaw' in proc.info['name'].lower():
                        process = psutil.Process(proc.info['pid'])
                        process.terminate()
                        process.wait(timeout=5)
                        stopped = True
                        logger.info(f"已停止网关进程 PID:{proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
            
            # 等待一下
            time.sleep(2)
            
            # 启动网关
            started = False
            gateway_script = self.workspace / 'scripts' / 'start_gateway.sh'
            if gateway_script.exists():
                subprocess.Popen(
                    ['bash', str(gateway_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                started = True
            else:
                # 尝试使用openclaw命令
                try:
                    result = subprocess.run(
                        ['openclaw', 'gateway', 'status'],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode != 0:
                        subprocess.Popen(
                            ['openclaw', 'gateway', 'start'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                        started = True
                except FileNotFoundError:
                    pass
            
            duration = (time.time() - action_start) * 1000
            
            result = HealResult(
                action=HealAction.RESTART_GATEWAY.value,
                target="openclaw_gateway",
                success=started,
                message=f"网关重启{'成功' if started else '失败'} (已停止: {stopped})",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration,
                before_state={'running': not stopped},
                after_state={'running': started}
            )
            
            self.actions_taken.append(result)
            logger.info(f"网关重启: {'成功' if started else '失败'}")
            return result
            
        except Exception as e:
            duration = (time.time() - action_start) * 1000
            result = HealResult(
                action=HealAction.RESTART_GATEWAY.value,
                target="openclaw_gateway",
                success=False,
                message=f"重启失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration
            )
            self.actions_taken.append(result)
            logger.error(f"网关重启失败: {e}")
            return result
    
    def _heal_memory_system(self) -> HealResult:
        """修复：修复向量记忆系统"""
        action_start = time.time()
        action_key = "memory_system_repair"
        
        if not self._can_attempt_heal(action_key):
            return HealResult(
                action=HealAction.REINIT_CONNECTION.value,
                target="memory_system",
                success=False,
                message="修复冷却中，跳过",
                timestamp=datetime.now().isoformat(),
                duration_ms=0
            )
        
        logger.info("检查并修复向量记忆系统...")
        self._record_heal_attempt(action_key)
        
        try:
            memory_db_dir = self.workspace / 'memory_db'
            repaired_dbs = 0
            
            if memory_db_dir.exists():
                for db_file in memory_db_dir.glob('*.db'):
                    try:
                        # 尝试连接并修复数据库
                        conn = sqlite3.connect(str(db_file))
                        conn.execute("PRAGMA integrity_check")
                        conn.execute("VACUUM")
                        conn.close()
                        repaired_dbs += 1
                    except Exception as e:
                        logger.warning(f"修复数据库 {db_file} 失败: {e}")
            
            duration = (time.time() - action_start) * 1000
            
            result = HealResult(
                action=HealAction.COMPACT_DATABASE.value,
                target="memory_system",
                success=repaired_dbs > 0,
                message=f"修复了 {repaired_dbs} 个数据库",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration,
                before_state={'repaired_dbs': 0},
                after_state={'repaired_dbs': repaired_dbs}
            )
            
            self.actions_taken.append(result)
            logger.info(f"记忆系统修复: {repaired_dbs} 个数据库")
            return result
            
        except Exception as e:
            duration = (time.time() - action_start) * 1000
            result = HealResult(
                action=HealAction.COMPACT_DATABASE.value,
                target="memory_system",
                success=False,
                message=f"修复失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration
            )
            self.actions_taken.append(result)
            logger.error(f"记忆系统修复失败: {e}")
            return result
    
    def _heal_disk_space(self) -> HealResult:
        """修复：释放磁盘空间"""
        action_start = time.time()
        action_key = "disk_space_cleanup"
        
        if not self._can_attempt_heal(action_key):
            return HealResult(
                action=HealAction.CLEAR_LOGS.value,
                target="disk_space",
                success=False,
                message="修复冷却中，跳过",
                timestamp=datetime.now().isoformat(),
                duration_ms=0
            )
        
        logger.info("清理磁盘空间...")
        self._record_heal_attempt(action_key)
        
        try:
            freed_space = 0
            
            # 清理旧日志文件（保留30天）
            cutoff = datetime.now() - timedelta(days=30)
            if self.logs_dir.exists():
                for log_file in self.logs_dir.glob('*.log'):
                    try:
                        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if mtime < cutoff:
                            size = log_file.stat().st_size
                            log_file.unlink()
                            freed_space += size
                    except Exception:
                        pass
            
            # 清理浏览器截图
            screenshot_dir = self.workspace / '.browser-screenshots'
            if screenshot_dir.exists():
                cutoff = datetime.now() - timedelta(days=7)
                for img in screenshot_dir.glob('*.png'):
                    try:
                        mtime = datetime.fromtimestamp(img.stat().st_mtime)
                        if mtime < cutoff:
                            size = img.stat().st_size
                            img.unlink()
                            freed_space += size
                    except Exception:
                        pass
            
            duration = (time.time() - action_start) * 1000
            freed_mb = freed_space / (1024 * 1024)
            
            result = HealResult(
                action=HealAction.CLEAR_LOGS.value,
                target="disk_space",
                success=True,
                message=f"释放空间: {freed_mb:.2f}MB",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration,
                before_state={'freed_mb': 0},
                after_state={'freed_mb': freed_mb}
            )
            
            self.actions_taken.append(result)
            logger.info(f"磁盘空间清理: {freed_mb:.2f}MB")
            return result
            
        except Exception as e:
            duration = (time.time() - action_start) * 1000
            result = HealResult(
                action=HealAction.CLEAR_LOGS.value,
                target="disk_space",
                success=False,
                message=f"清理失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration
            )
            self.actions_taken.append(result)
            logger.error(f"磁盘空间清理失败: {e}")
            return result
    
    def _heal_compact_databases(self) -> HealResult:
        """修复：压缩数据库"""
        action_start = time.time()
        
        try:
            compacted = 0
            memory_db_dir = self.workspace / 'memory_db'
            
            if memory_db_dir.exists():
                for db_file in memory_db_dir.glob('*.db'):
                    try:
                        original_size = db_file.stat().st_size
                        conn = sqlite3.connect(str(db_file))
                        conn.execute("VACUUM")
                        conn.execute("REINDEX")
                        conn.close()
                        new_size = db_file.stat().st_size
                        if new_size < original_size:
                            compacted += 1
                    except Exception:
                        pass
            
            duration = (time.time() - action_start) * 1000
            
            result = HealResult(
                action=HealAction.COMPACT_DATABASE.value,
                target="database_compaction",
                success=True,
                message=f"压缩了 {compacted} 个数据库",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration
            )
            
            self.actions_taken.append(result)
            logger.info(f"数据库压缩: {compacted} 个")
            return result
            
        except Exception as e:
            duration = (time.time() - action_start) * 1000
            result = HealResult(
                action=HealAction.COMPACT_DATABASE.value,
                target="database_compaction",
                success=False,
                message=f"压缩失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration
            )
            self.actions_taken.append(result)
            return result
    
    def _heal_clear_old_logs(self) -> HealResult:
        """修复：清理旧日志"""
        # 已在_disk_space中实现
        return self._heal_disk_space()
    
    def _heal_reinit_connections(self) -> HealResult:
        """修复：重新初始化连接"""
        action_start = time.time()
        
        try:
            # 关闭并重新初始化网络连接
            actions = []
            
            # 清理DNS缓存
            try:
                subprocess.run(['systemctl', 'restart', 'systemd-resolved'], 
                             capture_output=True, timeout=10)
                actions.append("DNS缓存已清理")
            except Exception:
                pass
            
            duration = (time.time() - action_start) * 1000
            
            result = HealResult(
                action=HealAction.REINIT_CONNECTION.value,
                target="network_connections",
                success=len(actions) > 0,
                message="; ".join(actions) if actions else "无需操作",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration
            )
            
            self.actions_taken.append(result)
            logger.info(f"连接重新初始化: {actions}")
            return result
            
        except Exception as e:
            duration = (time.time() - action_start) * 1000
            result = HealResult(
                action=HealAction.REINIT_CONNECTION.value,
                target="network_connections",
                success=False,
                message=f"重新初始化失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration
            )
            self.actions_taken.append(result)
            return result
    
    def _heal_degrade_features(self) -> HealResult:
        """修复：降级非核心功能"""
        action_start = time.time()
        
        try:
            degraded = []
            
            # 创建降级标记文件
            degrade_flag = self.data_dir / 'emergency_degrade.flag'
            degrade_config = {
                'timestamp': datetime.now().isoformat(),
                'disabled_features': [
                    # 'web_search_caching',  # 已删除，使用深度提取+Playwright
                    'detailed_logging',
                    'automatic_backup',
                    'memory_compression'
                ],
                'reason': 'emergency_degrade'
            }
            
            with open(degrade_flag, 'w') as f:
                json.dump(degrade_config, f)
            
            degraded = degrade_config['disabled_features']
            
            duration = (time.time() - action_start) * 1000
            
            result = HealResult(
                action=HealAction.DEGRADE_FEATURES.value,
                target="non_core_features",
                success=True,
                message=f"已降级 {len(degraded)} 个非核心功能",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration,
                after_state={'degraded_features': degraded}
            )
            
            self.actions_taken.append(result)
            logger.warning(f"紧急降级: {degraded}")
            return result
            
        except Exception as e:
            duration = (time.time() - action_start) * 1000
            result = HealResult(
                action=HealAction.DEGRADE_FEATURES.value,
                target="non_core_features",
                success=False,
                message=f"降级失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration
            )
            self.actions_taken.append(result)
            return result
    
    def _build_critical_notification(self) -> str:
        """构建紧急告警消息"""
        lines = [
            "🚨 林林 v5.0 紧急告警 🚨",
            "",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "状态: 系统处于紧急模式",
            "",
            "已执行的自动修复操作:",
        ]
        
        for action in self.actions_taken:
            status = "✓" if action.success else "✗"
            lines.append(f"  {status} {action.action}: {action.message}")
        
        lines.extend([
            "",
            "⚠️ 需要立即人工干预！",
            "部分自动修复失败，系统可能不稳定。",
            "请检查系统状态并执行手动修复。"
        ])
        
        return '\n'.join(lines)
    
    def _build_failure_notification(self) -> str:
        """构建失败通知消息"""
        lines = [
            "⚠️ 林林 v5.0 自动修复失败",
            "",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "失败的修复操作:",
        ]
        
        for action in self.actions_taken:
            if not action.success:
                lines.append(f"  ✗ {action.action}: {action.message}")
        
        lines.extend([
            "",
            "建议人工检查系统状态。"
        ])
        
        return '\n'.join(lines)
    
    def _save_heal_history(self, report: HealReport):
        """保存修复历史"""
        try:
            HEAL_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            history_entry = {
                'timestamp': report.timestamp,
                'trigger_reason': report.trigger_reason,
                'severity': report.severity.value,
                'overall_success': report.overall_success,
                'needs_human_attention': report.needs_human_attention,
                'actions': [
                    {
                        'action': a.action,
                        'target': a.target,
                        'success': a.success,
                        'message': a.message,
                        'duration_ms': a.duration_ms
                    }
                    for a in report.actions_taken
                ]
            }
            
            with open(HEAL_HISTORY_FILE, 'a') as f:
                f.write(json.dumps(history_entry, ensure_ascii=False) + '\n')
            
            # 清理旧历史
            self._cleanup_heal_history()
            
        except Exception as e:
            logger.error(f"保存修复历史失败: {e}")
    
    def _cleanup_heal_history(self):
        """清理旧修复历史"""
        try:
            if not HEAL_HISTORY_FILE.exists():
                return
            
            cutoff = datetime.now() - timedelta(days=30)
            valid_lines = []
            
            with open(HEAL_HISTORY_FILE, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_date = datetime.fromisoformat(entry['timestamp'])
                        if entry_date > cutoff:
                            valid_lines.append(line)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            with open(HEAL_HISTORY_FILE, 'w') as f:
                f.writelines(valid_lines)
                
        except Exception as e:
            logger.error(f"清理修复历史失败: {e}")
    
    def get_heal_summary(self) -> str:
        """获取修复摘要"""
        return self._build_notification_message()
    
    def _build_notification_message(self) -> str:
        """构建通知消息"""
        if not self.actions_taken:
            return "暂无修复操作"
        
        lines = ["自动修复摘要:"]
        for action in self.actions_taken:
            icon = "✓" if action.success else "✗"
            lines.append(f"  {icon} {action.action}: {action.message}")
        
        return '\n'.join(lines)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='林林 v5.0 自动修复系统')
    parser.add_argument('--json', action='store_true', help='输出JSON格式报告')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
    parser.add_argument('--diagnosis-file', '-d', type=str, help='指定诊断报告文件')
    parser.add_argument('--notify', '-n', action='store_true', help='发送通知')
    
    args = parser.parse_args()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info("接收到终止信号，正在退出...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 加载诊断报告
    diagnosis_report = None
    if args.diagnosis_file:
        try:
            with open(args.diagnosis_file, 'r') as f:
                diagnosis_report = json.load(f)
        except Exception as e:
            logger.error(f"加载诊断报告失败: {e}")
    
    # 运行自动修复
    heal_system = AutoHealSystem()
    
    try:
        report = heal_system.run_auto_heal(diagnosis_report)
        
        # 输出结果
        if args.json:
            output = {
                'timestamp': report.timestamp,
                'trigger_reason': report.trigger_reason,
                'severity': report.severity.value,
                'overall_success': report.overall_success,
                'needs_human_attention': report.needs_human_attention,
                'actions': [
                    {
                        'action': a.action,
                        'target': a.target,
                        'success': a.success,
                        'message': a.message,
                        'duration_ms': a.duration_ms
                    }
                    for a in report.actions_taken
                ]
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        elif not args.quiet:
            print(heal_system.get_heal_summary())
        
        # 如果需要通知且级别较高
        if args.notify and report.needs_human_attention and report.notification_message:
            print("\n" + report.notification_message)
        
        # 根据结果设置退出码
        if report.needs_human_attention:
            sys.exit(2)
        elif not report.overall_success:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.exception("自动修复过程中发生错误")
        print(f"自动修复失败: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    main()
