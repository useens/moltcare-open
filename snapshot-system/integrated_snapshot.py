#!/usr/bin/env python3
"""集成快照系统 - P0完整工作流"""
import json, sys
from pathlib import Path
from datetime import datetime
from snapshot_collector import collect_snapshot, save_snapshot
from drift_detector import DriftDetector

SNAPSHOT_DIR = Path('/root/.openclaw/workspace/snapshot-system/snapshots')

def run_workflow():
    print("=" * 60)
    print("状态快照与漂移检测系统 v1.0.0")
    print("=" * 60)
    print(f"时间: {datetime.now().isoformat()}")
    
    # Step 1: 采集
    print("\n📸 Step 1: 采集当前状态...")
    current = collect_snapshot('check', 'integrated')
    current_path = save_snapshot(current)
    print(f"   ✓ {Path(current_path).name}")
    
    # Step 2: 找基线
    baselines = sorted(SNAPSHOT_DIR.glob('snapshot_baseline_*.json'))
    if not baselines:
        print("❌ 无基线，请先创建基线")
        return 1
    baseline_path = baselines[-1]
    with open(baseline_path) as f:
        baseline = json.load(f)
    
    # Step 3: 检测
    print("\n🔍 Step 2: 漂移检测...")
    detector = DriftDetector()
    alerts = detector.detect(baseline, current)
    
    critical = [a for a in alerts if a.severity == 'critical']
    warning = [a for a in alerts if a.severity == 'warning']
    
    if critical:
        print(f"   🔴 严重: {len(critical)}个")
        for a in critical[:3]:
            print(f"      - {a.category}/{a.metric}")
    if warning:
        print(f"   🟡 警告: {len(warning)}个")
    if not alerts:
        print("   ✅ 系统健康")
    
    print("\n" + "=" * 60)
    print(f"基线: {baseline_path.name}")
    print(f"当前: {Path(current_path).name}")
    
    return 2 if critical else (1 if warning else 0)

if __name__ == '__main__':
    sys.exit(run_workflow())
