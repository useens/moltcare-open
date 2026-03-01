#!/usr/bin/env python3
"""
Git活动监控器 - 追踪迭代频率
"""
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")

def monitor_git_activity():
    """监控Git提交活动"""
    # 获取近7天提交数
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    result = subprocess.run(
        ["git", "-C", str(WORKSPACE), "log", f"--since={week_ago}", "--oneline"],
        capture_output=True,
        text=True
    )
    
    commits = [l for l in result.stdout.strip().split('\n') if l.strip()]
    commit_count = len(commits)
    
    # 获取今日提交
    today = datetime.now().strftime("%Y-%m-%d")
    result_today = subprocess.run(
        ["git", "-C", str(WORKSPACE), "log", f"--since={today}", "--oneline"],
        capture_output=True,
        text=True
    )
    today_commits = len([l for l in result_today.stdout.strip().split('\n') if l.strip()])
    
    print(f"Git活动统计:")
    print(f"  近7天提交: {commit_count}")
    print(f"  今日提交: {today_commits}")
    
    # 记录活动
    activity = {
        "timestamp": datetime.now().isoformat(),
        "commits_last_7_days": commit_count,
        "commits_today": today_commits,
        "iteration_frequency": "high" if commit_count >= 10 else "medium" if commit_count >= 5 else "low"
    }
    
    activity_file = WORKSPACE / "memory" / "git-activity.json"
    activity_file.write_text(json.dumps(activity, indent=2))
    
    print(f"✅ Git活动已记录: {activity_file}")
    
    return activity

if __name__ == "__main__":
    monitor_git_activity()
