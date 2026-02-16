#!/usr/bin/env python3
"""P0 v2.0: 状态快照与漂移检测 - 新旧功能整合"""
import json, hashlib, time, psutil, sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

SNAPSHOT_DIR = Path("/root/.openclaw/workspace/memory/snapshots")
DRIFT_LOG = Path("/root/.openclaw/workspace/memory/drift-log.md")
CRITICAL_FILES = ["SOUL.md", "AGENTS.md", "IDENTITY.md", "USER.md", "MEMORY.md"]

class StateSnapshotV2:
    def __init__(self):
        self.timestamp = datetime.now()
        self.workspace = Path("/root/.openclaw/workspace")
        
    def capture(self) -> Dict:
        return {
            "version": "2.0.0",
            "snapshot_id": self.timestamp.strftime("%Y%m%d_%H%M%S"),
            "timestamp": self.timestamp.isoformat(),
            "files": self._files(),
            "resources": self._resources(),
            "skills": self._skills(),
            "memory": self._memory_stats()
        }
    
    def _files(self) -> Dict:
        files = {}
        for p in CRITICAL_FILES:
            path = self.workspace / p
            if path.exists():
                try:
                    c = path.read_text(errors='ignore')
                    files[p] = {"hash": hashlib.sha256(c.encode()).hexdigest()[:16], "size": len(c)}
                except: pass
        return files
    
    def _resources(self) -> Dict:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {"used_percent": mem.percent, "available_gb": mem.available / (1024**3)},
            "disk": {"used_percent": (disk.used / disk.total) * 100},
            "load_avg": list(psutil.getloadavg()),
            "uptime": time.time() - psutil.boot_time()
        }
    
    def _skills(self) -> Dict:
        skills_path = self.workspace / "skills"
        s = [d.name for d in skills_path.iterdir() if d.is_dir() and (d / "SKILL.md").exists()] if skills_path.exists() else []
        return {"count": len(s), "active": s}
    
    def _memory_stats(self) -> Dict:
        debt = self.workspace / "memory" / "learning-debt.md"
        debt_n = debt.read_text(errors='ignore').count("- [") if debt.exists() else 0
        return {"debt_count": debt_n, "daily_notes": len(list((self.workspace / "memory").glob("2026-*.md"))) if (self.workspace / "memory").exists() else 0}

class DriftDetectorV2:
    def __init__(self):
        self.alerts = []
    
    def detect(self, base: Dict, curr: Dict):
        self.alerts = []
        br, cr = base.get("resources", {}), curr.get("resources", {})
        
        # 内存
        cm = cr.get("memory", {}).get("used_percent", 0)
        if cm >= 90: self.alerts.append(("critical", "memory", cm))
        elif cm >= 80: self.alerts.append(("warning", "memory", cm))
        
        # 磁盘
        cd = cr.get("disk", {}).get("used_percent", 0)
        if cd >= 95: self.alerts.append(("critical", "disk", cd))
        elif cd >= 80: self.alerts.append(("warning", "disk", cd))
        
        # 技能
        if cr.get("skills", {}).get("count", 0) < base.get("skills", {}).get("count", 0):
            self.alerts.append(("warning", "skills", "lost"))
        
        # 文件
        for f, ci in curr.get("files", {}).items():
            bi = base.get("files", {}).get(f)
            if bi and bi.get("hash") != ci.get("hash"):
                self.alerts.append(("critical", "file", f"modified:{f}"))
        
        return self.alerts

def save(s: Dict):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    p = SNAPSHOT_DIR / f"snapshot_{s['snapshot_id']}.json"
    with open(p, 'w') as f: json.dump(s, f, indent=2)
    return p.name

def cleanup():
    snaps = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"))
    for o in snaps[:-24]: o.unlink()

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    
    print(f"[State Snapshot v2.0] {datetime.now().strftime('%H:%M:%S')}")
    
    # Capture
    collector = StateSnapshotV2()
    curr = collector.capture()
    print(f"  CPU: {curr['resources']['cpu_percent']:.1f}% | Mem: {curr['resources']['memory']['used_percent']:.1f}%")
    print(f"  Skills: {curr['skills']['count']} | Debt: {curr['memory']['debt_count']}")
    
    if mode == "baseline":
        n = save(curr)
        print(f"\n✓ Baseline: {n}")
        cleanup()
        return 0
    
    # Find baseline
    bls = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"))
    if not bls:
        if "--auto-fix" in sys.argv:
            n = save(curr)
            print(f"\n⚠ Auto-created baseline: {n}")
            return 0
        print("\n✗ No baseline. Run: python3 state-snapshot-drift-v2.py baseline")
        return 1
    
    with open(bls[-1]) as f: base = json.load(f)
    
    # Detect
    detector = DriftDetectorV2()
    alerts = detector.detect(base, curr)
    
    # Save current
    curr_path = save(curr)
    
    # Report
    crit = [a for a in alerts if a[0] == "critical"]
    warn = [a for a in alerts if a[0] == "warning"]
    
    if crit:
        print(f"\n🔴 CRITICAL ({len(crit)}):")
        for c in crit: print(f"   - {c[1]}: {c[2]}")
    if warn:
        print(f"\n🟡 Warning ({len(warn)}):")
        for w in warn: print(f"   - {w[1]}: {w[2]}")
    if not alerts:
        print("\n✅ Healthy")
    
    # Log to drift-log.md
    if alerts:
        with open(DRIFT_LOG, 'a') as f:
            f.write(f"\n## {datetime.now().isoformat()}\n")
            for sev, cat, msg in alerts:
                f.write(f"- [{sev.upper()}] {cat}: {msg}\n")
    
    print(f"\nSnapshot: {curr_path}")
    cleanup()
    return 2 if crit else (1 if warn else 0)

if __name__ == "__main__":
    sys.exit(main())
