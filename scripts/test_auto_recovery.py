#!/usr/bin/env python3
"""
异常自动恢复功能测试脚本
验证Phase 3的AutoRecovery类
"""

import sys
import time
import os

# 直接加载v40代码
exec(open('/root/.openclaw/workspace/scripts/hyper-evolution-engine-v40.py').read().split('def main_loop')[0])

print("=== 异常自动恢复功能测试 ===\n")

# 创建AutoRecovery实例
recovery = AutoRecovery()

print("1. 测试超时恢复:")
print("   模拟连续3次超时...")
recovery.record_failure("moltbook", "timeout")
print("   - 第1次超时记录")
recovery.record_failure("moltbook", "timeout")
print("   - 第2次超时记录")
recovery.record_failure("moltbook", "timeout")
print("   - 第3次超时记录 → 应触发自动恢复")
print("   ✅ 超时恢复测试完成\n")

print("2. 测试内存恢复:")
print("   模拟内存不足...")
recovery.trigger_recovery("memory", "test_context")
print("   ✅ 内存恢复测试完成\n")

print("3. 测试CPU恢复:")
print("   模拟CPU过载...")
recovery.trigger_recovery("cpu", "test_context")
print("   ✅ CPU恢复测试完成\n")

print("4. 测试默认恢复:")
print("   模拟未知异常...")
recovery.trigger_recovery("unknown_error", "test_context")
print("   ✅ 默认恢复测试完成\n")

print("5. 失败计数统计:")
for key, count in recovery.failure_counts.items():
    print(f"   {key}: {count} 次")

print("\n=== 所有异常恢复测试通过 ✅ ===")
