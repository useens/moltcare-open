#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensen System Streamline Daemon
系统智能精简守护进程 - 支持Thinking模式切换

功能:
- 快速扫描 (每6小时) → thinking=medium (L2)
  └── Token消耗检测、臃肿识别
- 深度评估 (每天04:00) → thinking=high (L3)
  └── 综合评估、精简方案制定
- 精简执行 → thinking=medium (L2)
  └── 安全精简、保护清单检查

作者: Sensen
版本: 1.0.0
"""

import os
import sys
import time
import json
import logging
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import threading
import queue

# Thinking级别枚举
class ThinkingLevel(Enum):
    L1_LOW = "low"
    L2_MEDIUM = "medium"
    L3_HIGH = "high"

# 配置路径
WORKSPACE_DIR = Path("/root/.openclaw/workspace")
SCRIPT_DIR = WORKSPACE_DIR / "scripts" / "self-upgrade"
MEMORY_DIR = WORKSPACE_DIR / "memory" / "self-upgrade"
LOG_DIR = Path("/var/log/sensen-streamline")
L3_LOG_DIR = LOG_DIR / "l3-operations"

# 确保目录存在
for d in [MEMORY_DIR, LOG_DIR, L3_LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 保护清单 - 不可删除的关键文件
PROTECTED_FILES: Set[str] = {
    "SOUL.md",
    "USER.md",
    "AGENTS.md",
    "MEMORY.md",
    "TOOLS.md",
    ".env",
    ".env.backup",
}

PROTECTED_PATTERNS: Set[str] = {
    "*.key",
    "*.pem",
    "*.credentials",
    "*backup*",
    "*config*",
}

# 全局状态
running = True
streamline_queue = queue.Queue()
current_thinking = ThinkingLevel.L2_MEDIUM

# 配置日志
def setup_logging():
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(thinking_level)s] %(message)s')
    
    main_handler = logging.FileHandler(LOG_DIR / "streamline-daemon.log")
    main_handler.setFormatter(formatter)
    
    l3_handler = logging.FileHandler(L3_LOG_DIR / f"l3-{datetime.now().strftime('%Y%m%d')}.log")
    l3_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger("streamline-daemon")
    logger.setLevel(logging.INFO)
    logger.addHandler(main_handler)
    logger.addHandler(console_handler)
    
    return logger, l3_handler

logger, l3_logger = setup_logging()

class ThinkingLogger:
    """Thinking级别日志记录器"""
    
    @staticmethod
    def log(level: ThinkingLevel, message: str, log_func=None):
        if log_func is None:
            log_func = logger.info
        
        extra = {'thinking_level': level.value.upper()}
        log_func(message, extra=extra)
        
        if level == ThinkingLevel.L3_HIGH:
            l3_logger.handle(logging.LogRecord(
                name="l3-operations",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"[{datetime.now().isoformat()}] {message}",
                args=(),
                exc_info=None
            ))

class TokenUsageTracker:
    """Token使用追踪器"""
    
    TOKEN_LOG = MEMORY_DIR / "token-usage-history.json"
    
    def __init__(self):
        self.usage_history = self._load_history()
        self.bloat_threshold = 1.5  # 1.5倍平均值视为臃肿
        
    def _load_history(self) -> List[Dict]:
        if self.TOKEN_LOG.exists():
            try:
                with open(self.TOKEN_LOG, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self):
        if len(self.usage_history) > 100:
            self.usage_history = self.usage_history[-100:]
        with open(self.TOKEN_LOG, 'w') as f:
            json.dump(self.usage_history, f, indent=2)
    
    def record_usage(self, operation: str, tokens: int, thinking_level: str):
        """记录Token使用"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "tokens": tokens,
            "thinking_level": thinking_level
        }
        self.usage_history.append(record)
        self._save_history()
    
    def detect_bloat(self) -> Tuple[bool, float, str]:
        """检测Token使用臃肿"""
        if len(self.usage_history) < 10:
            return False, 0.0, "历史数据不足"
        
        # 计算最近10次操作的平均Token使用
        recent = self.usage_history[-10:]
        avg_tokens = sum(r.get("tokens", 0) for r in recent) / len(recent)
        
        # 计算当前vs历史平均值
        if len(self.usage_history) >= 20:
            older = self.usage_history[-20:-10]
            older_avg = sum(r.get("tokens", 0) for r in older) / len(older)
            
            if older_avg > 0:
                ratio = avg_tokens / older_avg
                if ratio > self.bloat_threshold:
                    return True, ratio, f"Token使用增长 {ratio:.1f}x"
        
        return False, 1.0, "Token使用正常"
    
    def get_stats(self) -> Dict:
        """获取Token使用统计"""
        if not self.usage_history:
            return {"status": "无历史数据"}
        
        total_tokens = sum(r.get("tokens", 0) for r in self.usage_history)
        avg_tokens = total_tokens / len(self.usage_history)
        
        # 按thinking级别分组
        l3_tokens = sum(r.get("tokens", 0) for r in self.usage_history if r.get("thinking_level") == "high")
        l2_tokens = sum(r.get("tokens", 0) for r in self.usage_history if r.get("thinking_level") == "medium")
        
        return {
            "total_records": len(self.usage_history),
            "total_tokens": total_tokens,
            "avg_tokens_per_op": round(avg_tokens, 2),
            "l3_tokens": l3_tokens,
            "l2_tokens": l2_tokens,
            "l3_percentage": round((l3_tokens / total_tokens * 100), 2) if total_tokens > 0 else 0
        }

class SystemStreamlineEngine:
    """系统精简引擎"""
    
    BLOAT_REPORT = MEMORY_DIR / "bloat-analysis-report.json"
    STREAMLINE_LOG = MEMORY_DIR / "streamline-operations.json"
    
    # 臃肿检测阈值
    BLOAT_SIGNAL_THRESHOLD = 7
    
    def __init__(self):
        self.token_tracker = TokenUsageTracker()
        self.bloat_history = []
        self.streamline_count = 0
        
    def is_protected(self, file_path: Path) -> bool:
        """检查文件是否受保护"""
        file_name = file_path.name
        
        # 检查精确匹配
        if file_name in PROTECTED_FILES:
            return True
        
        # 检查模式匹配
        import fnmatch
        for pattern in PROTECTED_PATTERNS:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        
        return False
    
    def run_quick_scan(self) -> Dict:
        """快速扫描 (L2) - Token消耗检测、臃肿识别"""
        ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, "🔍 启动快速扫描 (L2) - Token臃肿检测")
        
        scan_result = {
            "timestamp": datetime.now().isoformat(),
            "mode": "quick",
            "thinking_level": "L2",
            "findings": []
        }
        
        # 1. Token使用检测
        is_bloated, ratio, message = self.token_tracker.detect_bloat()
        scan_result["token_status"] = {
            "is_bloated": is_bloated,
            "ratio": ratio,
            "message": message
        }
        
        if is_bloated:
            scan_result["findings"].append(f"Token使用臃肿: {message}")
            ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, f"⚠️ 检测到Token臃肿: {message}")
        
        # 2. 日志文件大小检查
        large_logs = self._scan_large_logs()
        if large_logs:
            scan_result["findings"].extend([f"大日志文件: {f}" for f in large_logs])
        
        # 3. 临时文件检查
        temp_files = self._scan_temp_files()
        if temp_files:
            scan_result["findings"].extend([f"临时文件: {f}" for f in temp_files])
        
        # 计算Signal级别
        signal_level = self._calculate_bloat_signal(scan_result)
        scan_result["signal_level"] = signal_level
        
        ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, 
            f"快速扫描完成 | Signal: {signal_level}/10 | 发现: {len(scan_result['findings'])} 项")
        
        return scan_result
    
    def run_deep_assessment(self) -> Dict:
        """深度评估 (L3) - 综合评估、精简方案制定"""
        ThinkingLogger.log(ThinkingLevel.L3_HIGH, "🔬 启动深度评估 (L3) - 系统综合精简分析")
        
        assessment = {
            "timestamp": datetime.now().isoformat(),
            "mode": "deep",
            "thinking_level": "L3",
            "components": {}
        }
        
        # 1. Token使用深度分析
        token_stats = self.token_tracker.get_stats()
        assessment["components"]["token_analysis"] = token_stats
        ThinkingLogger.log(ThinkingLevel.L3_HIGH, f"📊 Token分析: {token_stats}")
        
        # 2. 存储空间分析
        storage_analysis = self._analyze_storage()
        assessment["components"]["storage"] = storage_analysis
        
        # 3. 冗余文件分析
        redundancy = self._analyze_redundancy()
        assessment["components"]["redundancy"] = redundancy
        
        # 4. 生成精简方案
        streamline_plan = self._generate_streamline_plan(assessment)
        assessment["streamline_plan"] = streamline_plan
        
        ThinkingLogger.log(ThinkingLevel.L3_HIGH, 
            f"深度评估完成 | 方案项目: {len(streamline_plan)} 项")
        
        return assessment
    
    def execute_streamline(self, plan: List[Dict], dry_run: bool = True) -> Dict:
        """执行精简 (L2) - 安全精简、保护清单检查"""
        ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, f"🔧 执行精简操作 (L2) | 模拟模式: {dry_run}")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "operations": [],
            "protected_skipped": [],
            "success_count": 0,
            "fail_count": 0
        }
        
        for item in plan:
            operation = item.get("operation")
            target = Path(item.get("target", ""))
            
            # 保护清单检查
            if self.is_protected(target):
                results["protected_skipped"].append(str(target))
                ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, f"🛡️ 跳过受保护文件: {target.name}")
                continue
            
            if dry_run:
                # 模拟执行
                results["operations"].append({
                    "operation": operation,
                    "target": str(target),
                    "status": "simulated",
                    "protected": False
                })
                results["success_count"] += 1
            else:
                # 实际执行
                try:
                    if operation == "delete":
                        if target.is_file():
                            target.unlink()
                        elif target.is_dir():
                            import shutil
                            shutil.rmtree(target)
                    elif operation == "compress":
                        self._compress_file(target)
                    elif operation == "archive":
                        self._archive_old_files(target)
                    
                    results["operations"].append({
                        "operation": operation,
                        "target": str(target),
                        "status": "success"
                    })
                    results["success_count"] += 1
                    
                except Exception as e:
                    results["operations"].append({
                        "operation": operation,
                        "target": str(target),
                        "status": "failed",
                        "error": str(e)
                    })
                    results["fail_count"] += 1
        
        self.streamline_count += results["success_count"]
        
        ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, 
            f"精简完成 | 成功: {results['success_count']} | 跳过: {len(results['protected_skipped'])} | 失败: {results['fail_count']}")
        
        return results
    
    def _calculate_bloat_signal(self, scan_result: Dict) -> int:
        """计算臃肿Signal级别"""
        signal = 0
        
        # Token臃肿
        if scan_result["token_status"]["is_bloated"]:
            signal += 5
            ratio = scan_result["token_status"]["ratio"]
            if ratio > 2.0:
                signal += 3
            elif ratio > 1.5:
                signal += 1
        
        # 发现问题数量
        findings_count = len(scan_result.get("findings", []))
        if findings_count > 10:
            signal += 2
        elif findings_count > 5:
            signal += 1
        
        return min(signal, 10)
    
    def _scan_large_logs(self) -> List[str]:
        """扫描大日志文件"""
        large_logs = []
        log_dirs = [LOG_DIR, Path("/var/log")]
        
        for log_dir in log_dirs:
            if not log_dir.exists():
                continue
            for log_file in log_dir.glob("*.log"):
                try:
                    size_mb = log_file.stat().st_size / (1024 * 1024)
                    if size_mb > 100:  # >100MB
                        large_logs.append(f"{log_file.name} ({size_mb:.1f}MB)")
                except:
                    pass
        
        return large_logs[:5]  # 只返回前5个
    
    def _scan_temp_files(self) -> List[str]:
        """扫描临时文件"""
        temp_patterns = ["*.tmp", "*.temp", "*~", "*.swp"]
        temp_files = []
        
        for pattern in temp_patterns:
            for temp_file in WORKSPACE_DIR.rglob(pattern):
                if not self.is_protected(temp_file):
                    temp_files.append(str(temp_file.relative_to(WORKSPACE_DIR)))
        
        return temp_files[:10]
    
    def _analyze_storage(self) -> Dict:
        """分析存储空间"""
        try:
            result = subprocess.run(
                ["df", "-h", str(WORKSPACE_DIR)],
                capture_output=True,
                text=True
            )
            return {"df_output": result.stdout.strip()}
        except:
            return {"error": "无法获取存储信息"}
    
    def _analyze_redundancy(self) -> Dict:
        """分析冗余"""
        # 查找重复的文件模式
        redundancy = {
            "duplicate_patterns": [],
            "old_backups": []
        }
        
        # 检查旧备份
        backup_dirs = list(WORKSPACE_DIR.glob("*backup*"))
        if len(backup_dirs) > 3:
            redundancy["old_backups"] = [str(d.name) for d in backup_dirs[:-3]]
        
        return redundancy
    
    def _generate_streamline_plan(self, assessment: Dict) -> List[Dict]:
        """生成精简方案"""
        plan = []
        
        # 基于Token分析
        token_stats = assessment["components"].get("token_analysis", {})
        l3_percentage = token_stats.get("l3_percentage", 0)
        
        if l3_percentage > 60:
            plan.append({
                "operation": "optimize_thinking",
                "target": "L3_usage",
                "reason": f"L3使用占比过高 ({l3_percentage}%)"
            })
        
        # 基于冗余分析
        redundancy = assessment["components"].get("redundancy", {})
        for old_backup in redundancy.get("old_backups", []):
            plan.append({
                "operation": "archive",
                "target": str(WORKSPACE_DIR / old_backup),
                "reason": "旧备份文件"
            })
        
        return plan
    
    def _compress_file(self, target: Path):
        """压缩文件"""
        import gzip
        if target.is_file():
            with open(target, 'rb') as f_in:
                with gzip.open(f"{target}.gz", 'wb') as f_out:
                    f_out.write(f_in.read())
    
    def _archive_old_files(self, target: Path):
        """归档旧文件"""
        import shutil
        archive_dir = WORKSPACE_DIR / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        if target.exists():
            shutil.move(str(target), str(archive_dir / target.name))


class StreamlineScheduler:
    """精简调度器"""
    
    def __init__(self, engine: SystemStreamlineEngine):
        self.engine = engine
        self.last_quick = None
        self.last_deep = None
        
    def should_run_quick(self) -> bool:
        if self.last_quick is None:
            return True
        return (datetime.now() - self.last_quick) >= timedelta(hours=6)
    
    def should_run_deep(self) -> bool:
        now = datetime.now()
        if now.hour == 4 and (self.last_deep is None or 
                               (now - self.last_deep) >= timedelta(hours=23)):
            return True
        return False
    
    def run(self):
        """主调度循环"""
        global running
        
        ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, "="*60)
        ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, "🌊 森森系统智能精简守护进程 v1.0 已启动")
        ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, "🧠 L2:快速扫描 | L3:深度评估 | 安全精简")
        ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, "="*60)
        
        while running:
            try:
                current_time = datetime.now()
                
                # 深度评估 (04:00) -> L3
                if self.should_run_deep():
                    ThinkingLogger.log(ThinkingLevel.L3_HIGH, 
                        "⏰ 到达深度评估时间 (04:00) → L3模式激活")
                    deep_result = self.engine.run_deep_assessment()
                    
                    # 根据深度评估执行精简 (L2)
                    if deep_result.get("streamline_plan"):
                        self.engine.execute_streamline(
                            deep_result["streamline_plan"], 
                            dry_run=True
                        )
                    
                    self.last_deep = current_time
                    self.last_quick = current_time
                    
                # 快速扫描 (每6小时) -> L2
                elif self.should_run_quick():
                    ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, 
                        "⏰ 执行6小时快速扫描 → L2模式")
                    quick_result = self.engine.run_quick_scan()
                    
                    # 如果Signal高，触发深度评估
                    if quick_result.get("signal_level", 0) >= 7:
                        ThinkingLogger.log(ThinkingLevel.L3_HIGH, 
                            f"🚨 Signal级别 {quick_result['signal_level']}/10 → 触发L3深度评估")
                        deep_result = self.engine.run_deep_assessment()
                    
                    self.last_quick = current_time
                
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"调度循环异常: {e}")
                time.sleep(60)
        
        ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, "🛑 精简守护进程已停止")


def signal_handler(signum, frame):
    """信号处理"""
    global running
    ThinkingLogger.log(ThinkingLevel.L2_MEDIUM, f"收到信号 {signum}，准备退出...")
    running = False


def main():
    """主函数"""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    engine = SystemStreamlineEngine()
    scheduler = StreamlineScheduler(engine)
    
    try:
        scheduler.run()
    except Exception as e:
        ThinkingLogger.log(ThinkingLevel.L3_HIGH, f"精简守护进程致命错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
