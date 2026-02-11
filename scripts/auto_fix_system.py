#!/usr/bin/env python3
"""
问题发现→自动修复 闭环系统
确保第2轮发现的每个问题都有跟踪和修复计划
"""
import os
import json
from datetime import datetime

ISSUES_FILE = "memory/issues/auto_fix_queue.json"

def load_issues():
    """加载待修复问题队列"""
    if os.path.exists(ISSUES_FILE):
        with open(ISSUES_FILE) as f:
            return json.load(f)
    return {"pending": [], "completed": [], "created_at": datetime.now().isoformat()}

def save_issues(issues):
    """保存问题队列"""
    os.makedirs(os.path.dirname(ISSUES_FILE), exist_ok=True)
    with open(ISSUES_FILE, 'w') as f:
        json.dump(issues, f, indent=2)

def add_issue(issue_id, description, priority, fix_action, deadline):
    """添加新问题到队列"""
    issues = load_issues()
    
    # 检查是否已存在
    for issue in issues["pending"]:
        if issue["id"] == issue_id:
            return False
    
    issues["pending"].append({
        "id": issue_id,
        "description": description,
        "priority": priority,  # P0/P1/P2
        "fix_action": fix_action,
        "deadline": deadline,
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    })
    
    save_issues(issues)
    return True

def complete_issue(issue_id, result):
    """标记问题为已修复"""
    issues = load_issues()
    
    for issue in issues["pending"]:
        if issue["id"] == issue_id:
            issue["status"] = "completed"
            issue["completed_at"] = datetime.now().isoformat()
            issue["result"] = result
            issues["completed"].append(issue)
            issues["pending"].remove(issue)
            save_issues(issues)
            return True
    
    return False

def get_pending_issues():
    """获取待修复问题"""
    issues = load_issues()
    return issues["pending"]

def check_and_fix():
    """检查并修复待处理问题"""
    pending = get_pending_issues()
    
    if not pending:
        print("✅ 无待修复问题")
        return
    
    print(f"🔄 发现 {len(pending)} 个待修复问题:")
    
    for issue in pending:
        print(f"  - [{issue['priority']}] {issue['id']}: {issue['description']}")
        print(f"    修复动作: {issue['fix_action']}")
        print(f"    截止时间: {issue['deadline']}")

if __name__ == "__main__":
    check_and_fix()
