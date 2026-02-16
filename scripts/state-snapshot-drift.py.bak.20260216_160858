#!/usr/bin/env python3
"""
P0: 状态快照与漂移检测系统
每小时自动快照 + 多维度漂移检测 + 自动回滚
"""

import json
import os
import sys
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

# 配置
SNAPSHOT_DIR = Path("/root/.openclaw/workspace/memory/snapshots")
DRIFT_LOG = Path("/root/.openclaw/workspace/memory/drift-log.md")
MAX_SNAPSHOTS = 24  # 保留24小时快照
SNAPSHOT_INTERVAL = 3600  # 1小时

# 漂移阈值
DRIFT_THRESHOLDS = {
    "memory_accuracy": 0.8,  # 记忆准确性 < 80% 触发警报
    "response_consistency": 0.7,  # 响应一致性 < 70% 触发
    "file_integrity": 1.0,  # 文件完整性必须100%
}

class StateSnapshot:
    def __init__(self):
        self.timestamp = datetime.now()
        self.snapshot_id = self.timestamp.strftime("%Y%m%d_%H%M%S")
        self.workspace = Path("/root/.openclaw/workspace")
        
    def capture(self):
        """捕获当前状态快照"""
        snapshot = {
            "id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "version": self._get_version(),
            "files": self._capture_file_state(),
            "memory_count": self._count_memories(),
            "git_status": self._capture_git_state(),
            "system_health": self._capture_system_health(),
        }
        return snapshot
    
    def _get_version(self):
        """获取OpenClaw版本"""
        try:
            result = subprocess.run(
                ["openclaw", "version"],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"
    
    def _capture_file_state(self):
        """捕获关键文件状态"""
        critical_files = [
            "SOUL.md", "IDENTITY.md", "AGENTS.md", "USER.md", "MEMORY.md",
            "memory/learning-debt.md"
        ]
        file_state = {}
        for file in critical_files:
            path = self.workspace / file
            if path.exists():
                content = path.read_text(errors='ignore')
                file_state[file] = {
                    "hash": hashlib.sha256(content.encode()).hexdigest()[:16],
                    "size": len(content),
                    "mtime": path.stat().st_mtime
                }
        return file_state
    
    def _count_memories(self):
        """统计记忆数量"""
        memory_dir = self.workspace / "memory" / "debt-learning"
        if memory_dir.exists():
            return len(list(memory_dir.glob("*.md")))
        return 0
    
    def _capture_git_state(self):
        """捕获Git状态"""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.workspace), "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=10
            )
            commit = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            result = subprocess.run(
                ["git", "-C", str(self.workspace), "status", "--short"],
                capture_output=True, text=True, timeout=10
            )
            uncommitted = len([l for l in result.stdout.strip().split('\n') if l.strip()])
            
            return {"commit": commit, "uncommitted": uncommitted}
        except:
            return {"commit": "unknown", "uncommitted": 0}
    
    def _capture_system_health(self):
        """捕获系统健康状态"""
        try:
            # 磁盘使用
            result = subprocess.run(
                ["df", "-h", "/"], capture_output=True, text=True, timeout=5
            )
            disk_line = result.stdout.strip().split('\n')[-1]
            disk_usage = disk_line.split()[4].replace('%', '')
            
            # 内存使用
            result = subprocess.run(
                ["free", "-m"], capture_output=True, text=True, timeout=5
            )
            mem_lines = result.stdout.strip().split('\n')
            mem_info = mem_lines[1].split()
            mem_used = int(mem_info[2])
            mem_total = int(mem_info[1])
            mem_percent = (mem_used / mem_total) * 100
            
            return {
                "disk_percent": int(disk_usage),
                "mem_percent": round(mem_percent, 1),
                "healthy": int(disk_usage) < 80 and mem_percent < 80
            }
        except:
            return {"disk_percent": 0, "mem_percent": 0, "healthy": True}
    
    def save(self):
        """保存快照到文件"""
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snapshot = self.capture()
        snapshot_file = SNAPSHOT_DIR / f"snapshot_{self.snapshot_id}.json"
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        # 更新最新快照链接
        latest_link = SNAPSHOT_DIR / "latest.json"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(snapshot_file.name)
        
        return snapshot_file


class DriftDetector:
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.snapshots = self._load_snapshots()
    
    def _load_snapshots(self):
        """加载历史快照"""
        if not SNAPSHOT_DIR.exists():
            return []
        
        snapshots = []
        for f in sorted(SNAPSHOT_DIR.glob("snapshot_*.json")):
            try:
                with open(f) as fp:
                    snapshots.append(json.load(fp))
            except:
                pass
        return snapshots[-MAX_SNAPSHOTS:]  # 只保留最近24个
    
    def detect_drift(self):
        """检测漂移"""
        if len(self.snapshots) < 2:
            return {"status": "insufficient_data", "drift_score": 0}
        
        current = self.snapshots[-1]
        previous = self.snapshots[-2]
        
        drift_report = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "drift_score": 0,
            "indicators": {}
        }
        
        # 1. 文件完整性检测
        file_changes = self._detect_file_changes(current, previous)
        if file_changes.get("critical_modified", 0) > 0:
            drift_report["indicators"]["file_integrity"] = {
                "status": "warning" if file_changes["critical_modified"] <= 2 else "critical",
                "details": f"{file_changes['critical_modified']} critical files modified"
            }
            drift_report["drift_score"] += file_changes["critical_modified"] * 10
        
        # 2. 记忆数量变化检测
        mem_change = current.get("memory_count", 0) - previous.get("memory_count", 0)
        if mem_change < 0:
            drift_report["indicators"]["memory_loss"] = {
                "status": "warning",
                "details": f"Memory count decreased by {abs(mem_change)}"
            }
            drift_report["drift_score"] += abs(mem_change) * 5
        
        # 3. 系统健康检测
        if not current.get("system_health", {}).get("healthy", True):
            drift_report["indicators"]["system_health"] = {
                "status": "critical",
                "details": "System resources critical"
            }
            drift_report["drift_score"] += 50
        
        # 4. Git状态检测
        if current.get("git_status", {}).get("uncommitted", 0) > 10:
            drift_report["indicators"]["git_drift"] = {
                "status": "warning",
                "details": f"{current['git_status']['uncommitted']} uncommitted changes"
            }
            drift_report["drift_score"] += current['git_status']['uncommitted']
        
        # 确定总体状态
        if drift_report["drift_score"] >= 50:
            drift_report["status"] = "critical"
        elif drift_report["drift_score"] >= 20:
            drift_report["status"] = "warning"
        
        return drift_report
    
    def _detect_file_changes(self, current, previous):
        """检测文件变化"""
        critical_files = ["SOUL.md", "IDENTITY.md", "AGENTS.md", "USER.md"]
        changes = {"critical_modified": 0, "total_changes": 0}
        
        curr_files = current.get("files", {})
        prev_files = previous.get("files", {})
        
        for file in critical_files:
            curr_hash = curr_files.get(file, {}).get("hash")
            prev_hash = prev_files.get(file, {}).get("hash")
            if curr_hash and prev_hash and curr_hash != prev_hash:
                changes["critical_modified"] += 1
        
        return changes
    
    def should_rollback(self):
        """判断是否需要回滚"""
        if len(self.snapshots) < 2:
            return False
        
        # 获取最近3个快照的漂移报告
        recent_drifts = []
        for i in range(-3, 0):
            if abs(i) <= len(self.snapshots):
                current = self.snapshots[i]
                previous = self.snapshots[i-1] if i-1 >= -len(self.snapshots) else self.snapshots[0]
                
                # 简化检测
                if current.get("system_health", {}).get("healthy") is False:
                    recent_drifts.append("system_unhealthy")
                
                # 检测关键文件丢失
                curr_files = set(current.get("files", {}).keys())
                prev_files = set(previous.get("files", {}).keys())
                if len(prev_files - curr_files) > 0:
                    recent_drifts.append("files_missing")
        
        # 如果连续出现严重问题，触发回滚
        return recent_drifts.count("system_unhealthy") >= 2 or \
               recent_drifts.count("files_missing") >= 2


class AutoRollback:
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.snapshots = self._load_snapshots()
    
    def _load_snapshots(self):
        """加载历史快照"""
        if not SNAPSHOT_DIR.exists():
            return []
        
        snapshots = []
        for f in sorted(SNAPSHOT_DIR.glob("snapshot_*.json")):
            try:
                with open(f) as fp:
                    snapshots.append((f, json.load(fp)))
            except:
                pass
        return snapshots
    
    def find_healthy_snapshot(self):
        """找到最近的健康快照"""
        for snapshot_file, snapshot in reversed(self.snapshots):
            if snapshot.get("system_health", {}).get("healthy", False):
                return snapshot
        return None
    
    def rollback(self, target_snapshot=None):
        """执行回滚到健康状态"""
        if target_snapshot is None:
            target_snapshot = self.find_healthy_snapshot()
        
        if target_snapshot is None:
            return {"status": "failed", "reason": "no_healthy_snapshot_found"}
        
        rollback_report = {
            "timestamp": datetime.now().isoformat(),
            "target_snapshot": target_snapshot.get("id"),
            "actions": [],
            "status": "in_progress"
        }
        
        # 1. 恢复关键文件（通过git）
        target_commit = target_snapshot.get("git_status", {}).get("commit")
        if target_commit and target_commit != "unknown":
            try:
                subprocess.run(
                    ["git", "-C", str(self.workspace), "stash"],
                    capture_output=True, timeout=30
                )
                subprocess.run(
                    ["git", "-C", str(self.workspace), "reset", "--hard", target_commit],
                    capture_output=True, timeout=30
                )
                rollback_report["actions"].append(f"reset_to_commit:{target_commit}")
            except Exception as e:
                rollback_report["actions"].append(f"git_reset_failed:{str(e)}")
        
        # 2. 记录回滚事件
        rollback_file = SNAPSHOT_DIR / f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(rollback_file, 'w') as f:
            json.dump(rollback_report, f, indent=2)
        
        rollback_report["status"] = "completed"
        return rollback_report


def main():
    """主入口"""
    import argparse
    parser = argparse.ArgumentParser(description="P0: State Snapshot & Drift Detection")
    parser.add_argument("action", choices=["snapshot", "detect", "rollback", "full"])
    parser.add_argument("--auto-fix", action="store_true", help="Auto fix detected issues")
    args = parser.parse_args()
    
    if args.action == "snapshot":
        snapshot = StateSnapshot()
        snapshot_file = snapshot.save()
        print(f"✅ Snapshot saved: {snapshot_file}")
    
    elif args.action == "detect":
        detector = DriftDetector()
        report = detector.detect_drift()
        
        print(json.dumps(report, indent=2))
        
        if report["status"] == "critical":
            print("\n🚨 CRITICAL DRIFT DETECTED")
            if args.auto_fix:
                print("Auto-rollback triggered...")
                rollback = AutoRollback()
                result = rollback.rollback()
                print(json.dumps(result, indent=2))
    
    elif args.action == "rollback":
        rollback = AutoRollback()
        result = rollback.rollback()
        print(json.dumps(result, indent=2))
    
    elif args.action == "full":
        # 完整流程：快照 → 检测 → 必要时回滚
        print("📸 Capturing snapshot...")
        snapshot = StateSnapshot()
        snapshot_file = snapshot.save()
        print(f"✅ Snapshot: {snapshot_file.name}")
        
        print("\n🔍 Detecting drift...")
        detector = DriftDetector()
        report = detector.detect_drift()
        print(f"Status: {report['status']} (score: {report['drift_score']})")
        
        if report["status"] == "critical":
            print("\n🚨 Critical drift detected!")
            if args.auto_fix:
                print("Auto-rollback triggered...")
                rollback = AutoRollback()
                result = rollback.rollback()
                print(f"Rollback status: {result['status']}")
        elif report["status"] == "warning":
            print("\n⚠️  Warning: Minor drift detected, monitoring...")
        else:
            print("\n✅ System healthy")


if __name__ == "__main__":
    main()
