#!/usr/bin/env python3
"""
向量记忆系统紧急修复 - 主执行脚本
按顺序执行所有修复阶段
"""

import subprocess
import sys
import os

WORKSPACE = '/root/.openclaw/workspace/memory/vector'

stages = [
    ('阶段1: 数据整合', f'{WORKSPACE}/fix_stage1.py'),
    ('阶段2: 向量重建', f'{WORKSPACE}/fix_stage2.py'),
    ('阶段3: 去重清理', f'{WORKSPACE}/fix_stage3.py'),
    ('阶段4: LanceDB重建', f'{WORKSPACE}/fix_stage4.py'),
    ('阶段5: 验证与报告', f'{WORKSPACE}/fix_stage5.py'),
]

print("=" * 70)
print("🚨 向量记忆系统紧急修复 - 主执行脚本")
print("=" * 70)
print()

# 检查依赖
print("📋 检查依赖...")
result = subprocess.run([sys.executable, '-c', 'import sentence_transformers'], 
                       capture_output=True, text=True)
if result.returncode != 0:
    print("  安装 sentence-transformers...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'sentence-transformers', '-q'])
    print("  ✓ 安装完成")
else:
    print("  ✓ sentence-transformers 已安装")

# 检查其他依赖
for pkg in ['lancedb', 'pandas', 'numpy']:
    result = subprocess.run([sys.executable, '-c', f'import {pkg}'], 
                           capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  安装 {pkg}...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '-q'])

print()

# 执行各阶段
for i, (name, script) in enumerate(stages, 1):
    print()
    print("=" * 70)
    print(f"▶️  执行 {name}")
    print("=" * 70)
    
    if not os.path.exists(script):
        print(f"❌ 脚本不存在: {script}")
        sys.exit(1)
    
    result = subprocess.run([sys.executable, script], cwd=WORKSPACE)
    
    if result.returncode != 0:
        print(f"❌ {name} 失败")
        sys.exit(1)
    
    print(f"✅ {name} 完成")

print()
print("=" * 70)
print("🎉 所有修复阶段执行完成!")
print("=" * 70)
print()
print("📄 查看完整报告:")
print(f"   cat {WORKSPACE}/REPAIR_REPORT.md")
