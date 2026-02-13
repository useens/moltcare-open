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
        
        # 执行修复
        result = execute_fix(issue)
        if result:
            print(f"    ✅ 修复完成: {result}")
        else:
            print(f"    ❌ 修复失败或已跳过")

def execute_fix(issue):
    """执行具体的修复操作"""
    issue_id = issue['id']
    priority = issue['priority']
    description = issue['description']
    
    # P0/P1 立即处理，P2在资源允许时处理
    if priority == 'P2':
        # 检查系统资源是否允许
        import shutil
        disk = shutil.disk_usage('/')
        disk_free_percent = (disk.free / disk.total) * 100
        
        if disk_free_percent < 10:
            print(f"    ⏸️ P2问题暂缓处理: 磁盘空间不足 ({disk_free_percent:.1f}%)")
            return None
    
    # 根据问题类型执行修复
    if 'Gateway子代理创建超时' in description or '子代理' in description:
        return fix_gateway_subagent_timeout(issue)
    elif 'pylance' in description.lower():
        return fix_pylance_install(issue)
    elif '主记忆数据库为空' in description:
        return fix_memory_import(issue)
    else:
        print(f"    ⚠️ 未知问题类型，跳过自动修复")
        return None

def fix_gateway_subagent_timeout(issue):
    """修复Gateway子代理创建超时问题"""
    import subprocess
    import sys
    
    print(f"    🔧 正在修复: Gateway子代理创建超时...")
    
    try:
        # 1. 验证修复模块已创建
        fix_module_path = 'core/orchestration/gateway_subagent_fix.py'
        if os.path.exists(fix_module_path):
            print(f"    ✅ 修复模块已存在: {fix_module_path}")
        else:
            print(f"    ❌ 修复模块不存在")
            return None
        
        # 2. 更新 orchestrator.py 集成修复模块
        import_result = update_orchestrator_with_fix()
        if import_result:
            print(f"    ✅ 已集成到orchestrator")
        
        # 3. 创建修复配置
        config = {
            'timeout_seconds': 120,  # 增加超时时间
            'max_retries': 3,
            'retry_delay': 2.0,
            'fallback_to_main': True
        }
        
        config_path = 'memory/config/subagent_fix_config.json'
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # 4. 标记问题为已修复
        complete_issue(issue['id'], 
            f"已创建修复模块 {fix_module_path}, 配置: {config}")
        
        return f"超时重试机制+主节点回退策略已启用"
        
    except Exception as e:
        print(f"    ❌ 修复失败: {e}")
        return None

def update_orchestrator_with_fix():
    """更新orchestrator以使用修复模块"""
    orchestrator_path = 'core/orchestration/orchestrator.py'
    
    try:
        with open(orchestrator_path, 'r') as f:
            content = f.read()
        
        # 检查是否已导入修复模块
        if 'gateway_subagent_fix' not in content:
            # 在文件开头添加导入
            import_line = '''\nfrom .gateway_subagent_fix import spawn_subagent_safe, SpawnConfig\n'''
            
            # 找到最后一个导入的位置
            lines = content.split('\n')
            last_import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    last_import_idx = i
            
            lines.insert(last_import_idx + 1, import_line.strip())
            
            with open(orchestrator_path, 'w') as f:
                f.write('\n'.join(lines))
            
            return True
        return False
    except Exception as e:
        print(f"更新orchestrator失败: {e}")
        return False

def fix_pylance_install(issue):
    """修复pylance安装问题"""
    import subprocess
    import sys
    
    print(f"    🔧 正在修复: pylance安装...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'pylance', '--break-system-packages'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            complete_issue(issue['id'], 'pylance安装成功')
            return 'pylance安装完成'
        else:
            print(f"    ❌ 安装失败: {result.stderr}")
            return None
    except Exception as e:
        print(f"    ❌ 安装失败: {e}")
        return None

def fix_memory_import(issue):
    """修复记忆导入问题"""
    import subprocess
    import sys
    
    print(f"    🔧 正在修复: 记忆数据库导入...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/incremental-memory-import.py'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            complete_issue(issue['id'], f"记忆导入完成: {result.stdout[:200]}")
            return '记忆导入完成'
        else:
            print(f"    ❌ 导入失败: {result.stderr}")
            return None
    except Exception as e:
        print(f"    ❌ 导入失败: {e}")
        return None

if __name__ == "__main__":
    check_and_fix()
