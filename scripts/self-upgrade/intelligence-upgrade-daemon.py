#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensen Intelligence Upgrade Daemon
智能水平升级守护进程 - 不死进程实现

功能:
- 每6小时执行一次智能水平评估
- 对比历史数据识别退化/进步
- 自动触发升级任务
- 记录执行日志

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
from typing import Dict, List, Optional, Tuple
import threading
import queue

# 配置路径
WORKSPACE_DIR = Path("/root/.openclaw/workspace")
SCRIPT_DIR = WORKSPACE_DIR / "scripts" / "self-upgrade"
MEMORY_DIR = WORKSPACE_DIR / "memory" / "self-upgrade"
LOG_DIR = Path("/var/log/sensen-upgrade")

# 确保目录存在
for d in [MEMORY_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "daemon.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("intelligence-upgrade")

# 全局状态
running = True
assessment_queue = queue.Queue()


class IntelligenceAssessment:
    """智能水平评估器"""
    
    METRICS_FILE = MEMORY_DIR / "intelligence-metrics.json"
    HISTORY_FILE = MEMORY_DIR / "assessment-history.json"
    
    # 评估阈值
    DEGRADATION_THRESHOLD = -0.15  # 退化阈值 -15%
    IMPROVEMENT_THRESHOLD = 0.10   # 进步阈值 +10%
    
    def __init__(self):
        self.metrics = self._load_metrics()
        self.history = self._load_history()
        self.last_deep_assessment = None
        
    def _load_metrics(self) -> Dict:
        """加载当前指标"""
        if self.METRICS_FILE.exists():
            try:
                with open(self.METRICS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载指标失败: {e}")
        return self._init_metrics()
    
    def _load_history(self) -> List[Dict]:
        """加载历史记录"""
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载历史失败: {e}")
        return []
    
    def _init_metrics(self) -> Dict:
        """初始化默认指标"""
        return {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "dimensions": {
                "code_quality": 0.75,
                "execution_efficiency": 0.70,
                "error_recovery": 0.65,
                "learning_speed": 0.60,
                "autonomy": 0.80,
                "verification": 0.70
            },
            "overall_score": 0.70,
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_metrics(self):
        """保存当前指标"""
        self.metrics["last_updated"] = datetime.now().isoformat()
        with open(self.METRICS_FILE, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def _save_history(self):
        """保存历史记录"""
        # 只保留最近100条
        if len(self.history) > 100:
            self.history = self.history[-100:]
        with open(self.HISTORY_FILE, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def run_assessment(self, mode: str = "medium") -> Dict:
        """
        执行智能水平评估
        
        Args:
            mode: 评估模式 - "high"(深度), "medium"(快速), "emergency"(紧急)
        
        Returns:
            评估结果字典
        """
        logger.info(f"开始{mode}级别智能水平评估...")
        
        timestamp = datetime.now().isoformat()
        
        # 执行评估脚本
        assessment_result = self._execute_assessment(mode)
        
        # 计算得分
        new_score = self._calculate_score(assessment_result)
        old_score = self.metrics["overall_score"]
        change = (new_score - old_score) / old_score if old_score > 0 else 0
        
        # 记录历史
        record = {
            "timestamp": timestamp,
            "mode": mode,
            "old_score": old_score,
            "new_score": new_score,
            "change_percent": round(change * 100, 2),
            "details": assessment_result
        }
        self.history.append(record)
        self._save_history()
        
        # 更新指标
        self.metrics["overall_score"] = new_score
        self._update_dimensions(assessment_result)
        self._save_metrics()
        
        logger.info(f"评估完成: {old_score:.2f} → {new_score:.2f} ({change:+.1%})")
        
        # 检测异常
        if change < self.DEGRADATION_THRESHOLD:
            logger.warning(f"⚠️ 检测到智能水平退化: {change:.1%}")
            self._trigger_upgrade("degradation", record)
        elif change > self.IMPROVEMENT_THRESHOLD:
            logger.info(f"✅ 检测到智能水平提升: {change:.1%}")
        
        return record
    
    def _execute_assessment(self, mode: str) -> Dict:
        """执行评估脚本"""
        # 优先使用 Python 版本
        script_path = SCRIPT_DIR / "run-assessment.py"
        if not script_path.exists():
            script_path = SCRIPT_DIR / "run-assessment.sh"
        
        if not script_path.exists():
            logger.warning(f"评估脚本不存在: {script_path}")
            return self._mock_assessment(mode)
        
        try:
            env = os.environ.copy()
            env["ASSESSMENT_MODE"] = mode
            
            if script_path.suffix == '.py':
                cmd = ["python3", str(script_path), mode]
            else:
                cmd = ["bash", str(script_path), mode]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            if result.returncode == 0:
                try:
                    # 从stdout最后一行解析JSON
                    lines = result.stdout.strip().split('\n')
                    for line in reversed(lines):
                        line = line.strip()
                        if line and line.startswith('{'):
                            return json.loads(line)
                    # 如果没找到JSON，尝试解析全部
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    logger.warning(f"评估脚本输出解析失败: {e}，使用模拟数据")
                    return self._mock_assessment(mode)
            else:
                logger.error(f"评估脚本执行失败: {result.stderr}")
                return self._mock_assessment(mode)
                
        except subprocess.TimeoutExpired:
            logger.error("评估脚本执行超时")
            return self._mock_assessment(mode)
        except Exception as e:
            logger.error(f"执行评估失败: {e}")
            return self._mock_assessment(mode)
    
    def _mock_assessment(self, mode: str) -> Dict:
        """模拟评估结果(当脚本不可用时)"""
        import random
        
        base_score = self.metrics["overall_score"]
        variance = 0.05 if mode == "high" else 0.03 if mode == "medium" else 0.08
        
        return {
            "code_quality": min(1.0, max(0.1, base_score + random.uniform(-variance, variance))),
            "execution_efficiency": min(1.0, max(0.1, base_score + random.uniform(-variance, variance))),
            "error_recovery": min(1.0, max(0.1, base_score + random.uniform(-variance, variance))),
            "learning_speed": min(1.0, max(0.1, base_score + random.uniform(-variance, variance))),
            "autonomy": min(1.0, max(0.1, base_score + random.uniform(-variance, variance))),
            "verification": min(1.0, max(0.1, base_score + random.uniform(-variance, variance))),
            "is_mock": True,
            "mode": mode
        }
    
    def _calculate_score(self, result: Dict) -> float:
        """计算综合得分"""
        dimensions = [
            result.get("code_quality", 0.5),
            result.get("execution_efficiency", 0.5),
            result.get("error_recovery", 0.5),
            result.get("learning_speed", 0.5),
            result.get("autonomy", 0.5),
            result.get("verification", 0.5)
        ]
        return round(sum(dimensions) / len(dimensions), 2)
    
    def _update_dimensions(self, result: Dict):
        """更新各维度指标"""
        for key in self.metrics["dimensions"]:
            if key in result:
                self.metrics["dimensions"][key] = round(result[key], 2)
    
    def _trigger_upgrade(self, trigger_type: str, record: Dict):
        """触发升级流程"""
        logger.info(f"🚀 触发自动升级流程: {trigger_type}")
        
        upgrade_script = SCRIPT_DIR / "verify-upgrade.py"
        if upgrade_script.exists():
            try:
                subprocess.Popen(
                    ["python3", str(upgrade_script), trigger_type, json.dumps(record)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info("升级流程已启动")
            except Exception as e:
                logger.error(f"启动升级流程失败: {e}")
        else:
            logger.warning(f"升级验证脚本不存在: {upgrade_script}")


class AssessmentScheduler:
    """评估调度器"""
    
    def __init__(self, assessor: IntelligenceAssessment):
        self.assessor = assessor
        self.last_quick = None
        self.last_deep = None
        
    def should_run_quick(self) -> bool:
        """是否应该执行快速评估"""
        if self.last_quick is None:
            return True
        return (datetime.now() - self.last_quick) >= timedelta(hours=6)
    
    def should_run_deep(self) -> bool:
        """是否应该执行深度评估"""
        now = datetime.now()
        # 每天02:00执行深度评估
        if now.hour == 2 and (self.last_deep is None or 
                               (now - self.last_deep) >= timedelta(hours=23)):
            return True
        return False
    
    def run(self):
        """主调度循环"""
        global running
        
        logger.info("="*60)
        logger.info("🌲 森森智能水平升级守护进程已启动")
        logger.info("="*60)
        
        while running:
            try:
                current_time = datetime.now()
                
                # 检查深度评估
                if self.should_run_deep():
                    logger.info("⏰ 到达深度评估时间 (02:00)")
                    self.assessor.run_assessment("high")
                    self.last_deep = current_time
                    self.last_quick = current_time
                    
                # 检查快速评估
                elif self.should_run_quick():
                    logger.info("⏰ 执行6小时快速评估")
                    self.assessor.run_assessment("medium")
                    self.last_quick = current_time
                
                # 处理队列中的紧急评估
                try:
                    emergency = assessment_queue.get(timeout=1)
                    if emergency == "emergency":
                        logger.warning("🚨 收到紧急评估请求")
                        self.assessor.run_assessment("emergency")
                except queue.Empty:
                    pass
                
                time.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"调度循环异常: {e}")
                time.sleep(60)
        
        logger.info("🛑 守护进程已停止")


def signal_handler(signum, frame):
    """信号处理"""
    global running
    logger.info(f"收到信号 {signum}，准备退出...")
    running = False


def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建评估器和调度器
    assessor = IntelligenceAssessment()
    scheduler = AssessmentScheduler(assessor)
    
    # 启动调度
    try:
        scheduler.run()
    except Exception as e:
        logger.critical(f"守护进程致命错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
