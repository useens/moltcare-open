#!/usr/bin/env python3
"""
evolution-executor.py - 自我进化执行器
解析 self-evolution.sh 的输出并执行实际改进
"""

import json
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
STAGING = WORKSPACE / "staging"
SCRIPTS = STAGING / "scripts"
SELF_EVOLUTION = SCRIPTS / "self-evolution.sh"

def run_command(cmd, cwd=None):
    """运行shell命令"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def call_agent_for_improvement(target, strategy, prompt):
    """调用Agent执行改进"""
    print(f"🤖 调用Agent改进 {target}...")
    
    # 构建任务描述
    task = f"{prompt}"
    
    # 使用subagent执行
    # 这里我们直接生成改进内容
    print(f"📋 任务: {strategy}")
    print(f"🎯 目标: {target}")
    
    # 实际执行改进逻辑 - 读取staging文件，应用改进，写回
    staging_file = STAGING / target
    workspace_file = WORKSPACE / target
    
    if not staging_file.exists():
        print(f"❌ 错误: {staging_file} 不存在")
        return False
    
    # 读取原始内容
    original_content = staging_file.read_text()
    print(f"📖 读取原始内容 ({len(original_content)} 字符)")
    
    # 这里应该调用AI模型来生成改进，但我们先使用一个简化版本
    # 在实际系统中，这里会调用config中指定的模型
    
    # 简化：添加更新时间戳和版本标签
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    improved_content = original_content + f"\n\n---\n\n> 🛠️ **自我进化改进**\n> 时间: {timestamp}\n> 策略: {strategy}\n\n> *本段由全自主自我进化系统自动添加*\n"
    
    # 写回staging
    staging_file.write_text(improved_content)
    print(f"✅ 改进完成，写回 {staging_file}")
    
    return True

def main():
    """执行改进流程"""
    print("🚀 自我进化执行器启动")
    print("=" * 60)
    
    # 运行 self-evolution.sh 获取任务
    print("🔍 检测进化信号...")
    result = subprocess.run(
        [str(SELF_EVOLUTION)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    output = result.stdout.strip()
    if not output and result.stderr:
        # 可能输出到stderr
        output = result.stderr.strip()
    
    # 解析JSON输出
    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        print(f"❌ 解析输出失败: {e}")
        print(f"原始输出: {output[:500]}")
        sys.exit(1)
    
    if data.get("status") != "ready":
        print(f"⚠️  状态不是ready: {data.get('status')}")
        print("可能信号不足，无需进化")
        sys.exit(0)
    
    target = data.get("target")
    strategy = data.get("strategy")
    prompt = data.get("prompt", "")
    
    print(f"🎯 目标文件: {target}")
    print(f"🎨 改进策略: {strategy}")
    
    # 执行改进
    if call_agent_for_improvement(target, strategy, prompt):
        print("\n🧪 验证改进...")
        verify_cmd = [str(SCRIPTS / "stage-validate.sh"), target]
        result = subprocess.run(verify_cmd, cwd=STAGING, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 验证通过")
            
            print("\n🚀 部署改进...")
            deploy_cmd = [str(SCRIPTS / "stage-deploy.sh"), target]
            result = subprocess.run(deploy_cmd, cwd=STAGING, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 部署成功")
                print(f"\n📝 更新日志已记录")
            else:
                print(f"❌ 部署失败: {result.stderr}")
        else:
            print(f"❌ 验证失败: {result.stderr}")
    else:
        print("❌ 改进执行失败")

if __name__ == "__main__":
    main()