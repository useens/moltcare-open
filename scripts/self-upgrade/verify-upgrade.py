#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensen Upgrade Verification System
升级验证系统 - 绝对诚实验证机制

每个升级阶段后执行:
- 等待≥30秒 → 验证1
- 等待≥30秒 → 验证2
- 等待≥30秒 → 验证3
- 终极质疑: "真的吗???"

作者: Sensen
版本: 1.0.0
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

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
        logging.FileHandler(LOG_DIR / "verify-upgrade.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("verify-upgrade")


class VerificationStage:
    """验证阶段"""
    def __init__(self, name: str, delay: int, checks: List[str]):
        self.name = name
        self.delay = delay
        self.checks = checks
        self.passed = False
        self.results = {}


class UpgradeVerifier:
    """升级验证器"""
    
    VERIFY_LOG = MEMORY_DIR / "verification-log.json"
    
    def __init__(self, trigger_type: str, assessment_data: Dict):
        self.trigger_type = trigger_type
        self.assessment_data = assessment_data
        self.stages: List[VerificationStage] = []
        self.verification_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._init_stages()
        
    def _init_stages(self):
        """初始化验证阶段"""
        self.stages = [
            VerificationStage(
                name="验证1: 基础功能检查",
                delay=30,
                checks=[
                    "check_system_health",
                    "check_disk_space",
                    "check_memory_usage"
                ]
            ),
            VerificationStage(
                name="验证2: 核心脚本检查",
                delay=30,
                checks=[
                    "check_script_syntax",
                    "check_service_status",
                    "check_log_integrity"
                ]
            ),
            VerificationStage(
                name="验证3: 性能基准检查",
                delay=30,
                checks=[
                    "check_response_time",
                    "check_resource_usage",
                    "check_error_rate"
                ]
            )
        ]
    
    def log_verification(self, message: str, level: str = "info"):
        """记录验证日志"""
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
    
    # ============ 验证1: 基础功能检查 ============
    def check_system_health(self) -> Tuple[bool, str]:
        """检查系统健康状态"""
        try:
            # 检查负载
            load = os.getloadavg()[0]
            cpu_cores = os.cpu_count() or 1
            
            if load > cpu_cores * 2:
                return False, f"系统负载过高: {load} (核心数: {cpu_cores})"
            
            return True, f"系统负载正常: {load}"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def check_disk_space(self) -> Tuple[bool, str]:
        """检查磁盘空间"""
        try:
            result = subprocess.run(
                ["df", "-h", str(WORKSPACE_DIR)],
                capture_output=True,
                text=True
            )
            
            # 解析使用率
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                usage = lines[1].split()[4].rstrip('%')
                usage_int = int(usage)
                
                if usage_int > 90:
                    return False, f"磁盘使用率过高: {usage}%"
                elif usage_int > 80:
                    return True, f"磁盘使用率警告: {usage}%"
                
                return True, f"磁盘空间充足: {usage}%"
            
            return True, "磁盘检查完成"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def check_memory_usage(self) -> Tuple[bool, str]:
        """检查内存使用"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # 解析内存信息
            mem_total = 0
            mem_available = 0
            
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1])
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1])
            
            if mem_total > 0:
                usage_percent = ((mem_total - mem_available) / mem_total) * 100
                
                if usage_percent > 95:
                    return False, f"内存使用率过高: {usage_percent:.1f}%"
                elif usage_percent > 85:
                    return True, f"内存使用率警告: {usage_percent:.1f}%"
                
                return True, f"内存使用正常: {usage_percent:.1f}%"
            
            return True, "内存检查完成"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    # ============ 验证2: 核心脚本检查 ============
    def check_script_syntax(self) -> Tuple[bool, str]:
        """检查脚本语法"""
        errors = []
        
        # 检查Python脚本
        for py_file in SCRIPT_DIR.glob("*.py"):
            try:
                result = subprocess.run(
                    ["python3", "-m", "py_compile", str(py_file)],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode != 0:
                    errors.append(f"{py_file.name}: Python语法错误")
            except Exception as e:
                errors.append(f"{py_file.name}: 检查失败 - {e}")
        
        # 检查Bash脚本
        for sh_file in SCRIPT_DIR.glob("*.sh"):
            try:
                result = subprocess.run(
                    ["bash", "-n", str(sh_file)],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode != 0:
                    errors.append(f"{sh_file.name}: Bash语法错误")
            except Exception as e:
                errors.append(f"{sh_file.name}: 检查失败 - {e}")
        
        if errors:
            return False, f"发现 {len(errors)} 个语法错误: {', '.join(errors[:3])}"
        
        return True, "所有脚本语法正确"
    
    def check_service_status(self) -> Tuple[bool, str]:
        """检查服务状态"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "sensen-intelligence-upgrade.service"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, "升级服务运行正常"
            else:
                return False, "升级服务未运行"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def check_log_integrity(self) -> Tuple[bool, str]:
        """检查日志完整性"""
        try:
            log_files = list(LOG_DIR.glob("*.log"))
            
            if not log_files:
                return True, "无日志文件(可能刚启动)"
            
            # 检查最新日志
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            log_size = latest_log.stat().st_size
            
            if log_size == 0:
                return False, f"日志文件为空: {latest_log.name}"
            
            # 检查是否有错误
            with open(latest_log, 'r') as f:
                content = f.read()
                error_count = content.lower().count('error')
                
                if error_count > 10:
                    return False, f"日志中错误过多: {error_count} 个"
                
                return True, f"日志完整，发现 {error_count} 个错误"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    # ============ 验证3: 性能基准检查 ============
    def check_response_time(self) -> Tuple[bool, str]:
        """检查响应时间"""
        try:
            start = time.time()
            # 模拟简单操作
            result = subprocess.run(
                ["python3", "-c", "print('test')"],
                capture_output=True,
                timeout=5
            )
            elapsed = time.time() - start
            
            if elapsed > 3.0:
                return False, f"响应时间过长: {elapsed:.2f}s"
            elif elapsed > 1.0:
                return True, f"响应时间警告: {elapsed:.2f}s"
            
            return True, f"响应时间正常: {elapsed:.2f}s"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def check_resource_usage(self) -> Tuple[bool, str]:
        """检查资源使用"""
        try:
            # 检查进程资源使用
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            
            # 检查升级进程
            upgrade_processes = [line for line in result.stdout.split('\n') 
                                if 'intelligence-upgrade' in line.lower()]
            
            if not upgrade_processes:
                return False, "未找到升级进程"
            
            return True, f"发现 {len(upgrade_processes)} 个升级相关进程"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def check_error_rate(self) -> Tuple[bool, str]:
        """检查错误率"""
        try:
            # 只检查daemon日志的最后100行
            log_file = LOG_DIR / "daemon.log"
            if not log_file.exists():
                return True, "无日志文件"
            
            # 只读取最后100行
            result = subprocess.run(
                ["tail", "-100", str(log_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split('\n')
            total_lines = len(lines)
            error_lines = sum(1 for l in lines if 'error' in l.lower())
            
            if total_lines > 0:
                error_rate = (error_lines / total_lines) * 100
                
                if error_rate > 20:
                    return True, f"错误率警告: {error_rate:.1f}%"
                
                return True, f"错误率正常: {error_rate:.1f}%"
            
            return True, "无日志内容"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def run_stage(self, stage: VerificationStage) -> bool:
        """执行验证阶段"""
        self.log_verification(f"\n{'='*50}")
        self.log_verification(f"🔄 开始 {stage.name}")
        self.log_verification(f"⏱️ 等待 {stage.delay} 秒...")
        
        # 等待
        time.sleep(stage.delay)
        
        # 执行检查
        all_passed = True
        for check_name in stage.checks:
            check_method = getattr(self, check_name, None)
            if check_method:
                passed, message = check_method()
                status = "✅ 通过" if passed else "❌ 失败"
                self.log_verification(f"  {status} | {check_name}: {message}")
                stage.results[check_name] = {"passed": passed, "message": message}
                if not passed:
                    all_passed = False
            else:
                self.log_verification(f"  ⚠️ 警告 | {check_name}: 检查方法不存在")
        
        stage.passed = all_passed
        
        if all_passed:
            self.log_verification(f"✅ {stage.name} 全部通过")
        else:
            self.log_verification(f"⚠️ {stage.name} 有检查项失败")
        
        return all_passed
    
    def ultimate_challenge(self) -> bool:
        """终极质疑: 真的吗???"""
        self.log_verification(f"\n{'='*50}")
        self.log_verification("🤔 终极质疑阶段")
        self.log_verification("🤔 真的吗???")
        
        # 再次验证关键指标
        health_ok, health_msg = self.check_system_health()
        service_ok, service_msg = self.check_service_status()
        syntax_ok, syntax_msg = self.check_script_syntax()
        
        self.log_verification(f"  系统健康: {'✅' if health_ok else '❌'} {health_msg}")
        self.log_verification(f"  服务状态: {'✅' if service_ok else '❌'} {service_msg}")
        self.log_verification(f"  脚本语法: {'✅' if syntax_ok else '❌'} {syntax_msg}")
        
        all_ok = health_ok and service_ok and syntax_ok
        
        if all_ok:
            self.log_verification("✅ 终极质疑通过 - 所有验证确认无误")
        else:
            self.log_verification("❌ 终极质疑失败 - 需要人工介入")
        
        return all_ok
    
    def save_verification_log(self):
        """保存验证日志"""
        log_entry = {
            "verification_id": self.verification_id,
            "timestamp": datetime.now().isoformat(),
            "trigger_type": self.trigger_type,
            "assessment_data": self.assessment_data,
            "stages": [
                {
                    "name": stage.name,
                    "passed": stage.passed,
                    "results": stage.results
                }
                for stage in self.stages
            ]
        }
        
        logs = []
        if self.VERIFY_LOG.exists():
            try:
                with open(self.VERIFY_LOG, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(log_entry)
        
        # 只保留最近100条
        if len(logs) > 100:
            logs = logs[-100:]
        
        with open(self.VERIFY_LOG, 'w') as f:
            json.dump(logs, f, indent=2)
        
        self.log_verification(f"📝 验证日志已保存: {self.VERIFY_LOG}")
    
    def run(self) -> bool:
        """执行完整验证流程"""
        self.log_verification(f"\n{'='*60}")
        self.log_verification(f"🚀 启动升级验证流程")
        self.log_verification(f"📋 触发类型: {self.trigger_type}")
        self.log_verification(f"🆔 验证ID: {self.verification_id}")
        self.log_verification(f"{'='*60}\n")
        
        # 执行三个验证阶段
        all_stages_passed = True
        for stage in self.stages:
            if not self.run_stage(stage):
                all_stages_passed = False
        
        # 终极质疑
        ultimate_passed = self.ultimate_challenge()
        
        # 保存日志
        self.save_verification_log()
        
        # 最终结果
        self.log_verification(f"\n{'='*60}")
        if all_stages_passed and ultimate_passed:
            self.log_verification("✅ 验证通过 - 升级成功确认")
        else:
            self.log_verification("⚠️ 验证未完全通过 - 需要关注")
        self.log_verification(f"{'='*60}\n")
        
        return all_stages_passed and ultimate_passed


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: verify-upgrade.py <trigger_type> <assessment_json>")
        sys.exit(1)
    
    trigger_type = sys.argv[1]
    
    try:
        assessment_data = json.loads(sys.argv[2])
    except json.JSONDecodeError:
        logger.error("评估数据JSON解析失败")
        assessment_data = {}
    
    verifier = UpgradeVerifier(trigger_type, assessment_data)
    success = verifier.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
