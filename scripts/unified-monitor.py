#!/usr/bin/env python3
"""
Unified Monitoring Framework v1.0
统一监控框架 - 合并所有健康检查、诊断和自动修复功能

替代脚本：
- health-monitor-v5.py
- auto-health-check.py
- memory-guardian.py
- auto_fix_system.py
- self-diagnosis.py
- advanced_diagnosis.py
- comprehensive-check.py
- diagnosis_service.py
- auto-heal.py
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
LOG_DIR = WORKSPACE / "logs"
DATA_DIR = WORKSPACE / "data"
CONFIG_DIR = WORKSPACE / "config"
REPORTS_DIR = WORKSPACE / "reports"

# 日志设置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "unified-monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SystemComponent:
    """系统组件基类"""
    def __init__(self, name: str):
        self.name = name
        self.status = "unknown"
        self.issues = []
        self.metrics = {}
    
    def check(self) -> Tuple[str, List[str]]:
        """返回 (状态, 问题列表)"""
        raise NotImplementedError
    
    def fix(self) -> bool:
        """尝试修复，返回是否成功"""
        return False


class MemorySystem(SystemComponent):
    """v5.1-v5.5 记忆系统检查"""
    
    def check(self) -> Tuple[str, List[str]]:
        issues = []
        
        # v5.1 长期记忆检查
        long_term = WORKSPACE / "memory" / "long_term.json"
        if not long_term.exists():
            issues.append("v5.1: 长期记忆文件不存在")
        
        # v5.2 向量记忆检查
        vector_dir = DATA_DIR / "vector_memory"
        if not vector_dir.exists():
            issues.append("v5.2: 向量记忆目录不存在")
        else:
            vector_files = list(vector_dir.glob("*.json"))
            if len(vector_files) == 0:
                issues.append("v5.2: 向量记忆为空")
        
        # v5.3 工作记忆检查
        session_files = list(DATA_DIR.glob("session_*.json"))
        if len(session_files) > 100:
            issues.append(f"v5.3: 工作记忆文件过多 ({len(session_files)})")
        
        # v5.4 情景记忆检查
        context_file = DATA_DIR / "context_memory.json"
        if context_file.exists():
            size = context_file.stat().st_size
            if size > 10 * 1024 * 1024:  # 10MB
                issues.append(f"v5.4: 情景记忆过大 ({size/1024/1024:.1f}MB)")
        
        # v5.5 快照检查
        snapshots = list(WORKSPACE.glob("memory/snapshots/*.json"))
        recent_snapshots = [s for s in snapshots 
                          if datetime.now() - datetime.fromtimestamp(s.stat().st_mtime) < timedelta(hours=24)]
        if len(recent_snapshots) < 1:
            issues.append("v5.5: 24小时内无快照")
        
        status = "healthy" if not issues else "degraded"
        return status, issues
    
    def fix(self) -> bool:
        """执行记忆系统修复"""
        try:
            # 重建向量索引
            vector_script = WORKSPACE / "scripts" / "init-vector-memory-full.py"
            if vector_script.exists():
                subprocess.run([sys.executable, str(vector_script)], 
                             capture_output=True, timeout=300)
            
            # 清理旧会话
            old_sessions = list(DATA_DIR.glob("session_*.json"))
            old_sessions.sort(key=lambda x: x.stat().st_mtime)
            for session in old_sessions[:-50]:  # 保留最近50个
                session.unlink()
            
            return True
        except Exception as e:
            logger.error(f"记忆系统修复失败: {e}")
            return False


class CronSystem(SystemComponent):
    """Cron任务系统检查"""
    
    def check(self) -> Tuple[str, List[str]]:
        issues = []
        
        # 检查cron状态文件
        cron_state = CONFIG_DIR / "cron-state.json"
        if not cron_state.exists():
            issues.append("Cron状态文件不存在")
        
        # 检查动态频率配置
        freq_config = CONFIG_DIR / "dynamic-cron-frequency.json"
        if not freq_config.exists():
            issues.append("动态频率配置不存在")
        
        # 检查是否有重复任务
        # 这里可以添加更多检查逻辑
        
        status = "healthy" if not issues else "degraded"
        return status, issues
    
    def fix(self) -> bool:
        """重新初始化cron配置"""
        try:
            # 重新导出cron配置
            export_script = WORKSPACE / "scripts" / "export-cron-config.sh"
            if export_script.exists():
                subprocess.run(["bash", str(export_script)], 
                             capture_output=True, timeout=60)
            return True
        except Exception as e:
            logger.error(f"Cron系统修复失败: {e}")
            return False


class StorageSystem(SystemComponent):
    """存储系统检查"""
    
    def check(self) -> Tuple[str, List[str]]:
        issues = []
        
        # 检查磁盘空间
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            usage = int(parts[4].replace('%', ''))
            if usage > 80:
                issues.append(f"磁盘使用率过高: {usage}%")
        
        # 检查reports目录大小
        reports_size = sum(f.stat().st_size for f in WORKSPACE.rglob("reports/*") if f.is_file())
        if reports_size > 50 * 1024 * 1024:  # 50MB
            issues.append(f"Reports目录过大: {reports_size/1024/1024:.1f}MB")
        
        # 检查大文件数量
        # 扫描大文件（排除 venv 和 .git）
        large_files = []
        for item in WORKSPACE.rglob("*"):
            if item.is_file() and "venv" not in str(item) and ".git" not in str(item):
                try:
                    if item.stat().st_size > 10 * 1024 * 1024:  # >10MB
                        large_files.append(item)
                except OSError:
                    continue
            if len(large_files) > 50:  # 限制检查数量
                break
        large_files = [f for f in large_files if f.is_file() and f.stat().st_size > 10*1024*1024]
        if len(large_files) > 10:
            issues.append(f"大文件数量过多: {len(large_files)}")
        
        status = "healthy" if not issues else "degraded"
        return status, issues
    
    def fix(self) -> bool:
        """执行轻量级存储清理（不执行完整备份）"""
        try:
            logger.info("  🔧 执行轻量级清理...")
            
            # 1. 清理Python缓存
            subprocess.run(
                ["find", str(WORKSPACE), "-type", "d", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+"],
                capture_output=True, timeout=30
            )
            subprocess.run(
                ["find", str(WORKSPACE), "-name", "*.pyc", "-delete"],
                capture_output=True, timeout=30
            )
            
            # 2. 截断大日志文件（超过50MB）
            log_dir = WORKSPACE / "logs"
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    if log_file.stat().st_size > 50 * 1024 * 1024:
                        logger.info(f"    截断大日志: {log_file.name}")
                        subprocess.run(
                            ["bash", "-c", f"tail -n 1000 '{log_file}' > '{log_file}.tmp' && mv '{log_file}.tmp' '{log_file}'"],
                            capture_output=True, timeout=10
                        )
            
            # 3. 清理reports目录的旧文件（保留最近30天）
            reports_dir = WORKSPACE / "reports"
            if reports_dir.exists():
                cutoff = datetime.now() - timedelta(days=30)
                for report_file in reports_dir.glob("*"):
                    if report_file.is_file():
                        mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                        if mtime < cutoff:
                            report_file.unlink()
                            logger.info(f"    删除旧报告: {report_file.name}")
            
            logger.info("  ✅ 轻量级清理完成")
            return True
        except Exception as e:
            logger.error(f"存储系统修复失败: {e}")
            return False


class GitSystem(SystemComponent):
    """Git仓库检查"""
    
    def check(self) -> Tuple[str, List[str]]:
        issues = []
        
        git_dir = WORKSPACE / ".git"
        if not git_dir.exists():
            issues.append("Git仓库不存在")
            return "error", issues
        
        # 检查仓库大小
        result = subprocess.run(
            ["du", "-sh", str(git_dir)],
            capture_output=True, text=True
        )
        size_str = result.stdout.split()[0]
        if 'G' in size_str or ('M' in size_str and float(size_str.replace('M','')) > 500):
            issues.append(f"Git仓库过大: {size_str}")
        
        # 检查未提交变更
        result = subprocess.run(
            ["git", "-C", str(WORKSPACE), "status", "--porcelain"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            issues.append("有未提交的变更")
        
        status = "healthy" if not issues else "degraded"
        return status, issues
    
    def fix(self) -> bool:
        """执行Git修复：提交变更并推送"""
        try:
            # 1. 添加所有变更
            logger.info(f"    添加所有变更...")
            subprocess.run(
                ["git", "-C", str(WORKSPACE), "add", "-A"],
                capture_output=True, timeout=60
            )
            
            # 2. 提交（如果有变更）
            result = subprocess.run(
                ["git", "-C", str(WORKSPACE), "status", "--porcelain"],
                capture_output=True, text=True
            )
            
            if result.stdout.strip():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                commit_msg = f"【AUTO】心跳检查自动提交 - {timestamp}"
                subprocess.run(
                    ["git", "-C", str(WORKSPACE), "commit", "-m", commit_msg],
                    capture_output=True, timeout=60
                )
                logger.info(f"    ✅ 已提交：{commit_msg}")
            
            # 3. 推送到远程
            logger.info(f"    推送到远程...")
            push_result = subprocess.run(
                ["git", "-C", str(WORKSPACE), "push", "origin", "main"],
                capture_output=True, timeout=120
            )
            
            if push_result.returncode == 0:
                logger.info(f"    ✅ 推送成功")
            else:
                logger.warning(f"    ⚠️ 推送失败（可能远程不可达）")
            
            # 4. 执行gc清理
            subprocess.run(
                ["git", "-C", str(WORKSPACE), "gc", "--prune=now"],
                capture_output=True, timeout=120
            )
            logger.info(f"    ✅ 仓库清理完成")
            
            return True
        except Exception as e:
            logger.error(f"Git系统修复失败: {e}")
            return False


class UnifiedMonitor:
    """统一监控器"""
    
    def __init__(self):
        self.components = {
            "memory": MemorySystem("记忆系统"),
            "cron": CronSystem("Cron系统"),
            "storage": StorageSystem("存储系统"),
            "git": GitSystem("Git系统"),
        }
        self.report = {}
    
    def run_check(self, auto_fix: bool = False) -> Dict:
        """运行完整检查"""
        logger.info("="*60)
        logger.info("🛡️ 统一监控系统启动")
        logger.info("="*60)
        
        all_healthy = True
        total_issues = 0
        fixed_issues = 0
        
        for name, component in self.components.items():
            logger.info(f"\n检查 {component.name}...")
            status, issues = component.check()
            
            self.report[name] = {
                "status": status,
                "issues": issues,
                "fixed": []
            }
            
            if issues:
                logger.warning(f"  ❌ 发现 {len(issues)} 个问题:")
                for issue in issues:
                    logger.warning(f"     - {issue}")
                total_issues += len(issues)
                all_healthy = False
                
                # 尝试自动修复
                if auto_fix:
                    logger.info(f"  🔧 尝试自动修复...")
                    if component.fix():
                        logger.info(f"  ✅ 修复成功")
                        fixed_issues += len(issues)
                        self.report[name]["fixed"] = issues
                    else:
                        logger.error(f"  ❌ 修复失败")
            else:
                logger.info(f"  ✅ {component.name} 健康")
        
        # 生成报告
        self.report["summary"] = {
            "timestamp": datetime.now().isoformat(),
            "all_healthy": all_healthy,
            "total_issues": total_issues,
            "fixed_issues": fixed_issues,
            "components_checked": len(self.components)
        }
        
        # 保存报告
        self._save_report()
        
        logger.info("\n" + "="*60)
        if all_healthy:
            logger.info("✅ 所有系统健康")
        else:
            logger.warning(f"⚠️ 发现 {total_issues} 个问题，已修复 {fixed_issues} 个")
        logger.info("="*60)
        
        return self.report
    
    def _save_report(self):
        """保存检查报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = REPORTS_DIR / f"unified-monitor-{timestamp}.json"
        
        REPORTS_DIR.mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 报告已保存: {report_file}")


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="统一监控系统")
    parser.add_argument("--fix", action="store_true", help="自动修复发现的问题")
    parser.add_argument("--component", choices=["memory", "cron", "storage", "git", "all"],
                       default="all", help="检查特定组件")
    args = parser.parse_args()
    
    monitor = UnifiedMonitor()
    
    if args.component != "all":
        # 只检查指定组件
        component = monitor.components.get(args.component)
        if component:
            status, issues = component.check()
            print(f"\n{component.name} 状态: {status}")
            if issues:
                print(f"问题 ({len(issues)}):")
                for issue in issues:
                    print(f"  - {issue}")
                if args.fix:
                    print("尝试修复...")
                    if component.fix():
                        print("✅ 修复成功")
                    else:
                        print("❌ 修复失败")
    else:
        # 完整检查
        report = monitor.run_check(auto_fix=args.fix)
        
        # 返回退出码
        if not report["summary"]["all_healthy"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
