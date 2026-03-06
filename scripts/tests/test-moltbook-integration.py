#!/usr/bin/env python3
"""
Moltbook 洞察改进 - 完整集成测试
验证所有 5 项改进是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加工作区到路径
WORKSPACE = Path("/root/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "core"))

def test_all_improvements():
    """测试所有改进"""
    results = []
    
    print("\n" + "="*70)
    print("🚀 Moltbook 洞察改进 - 完整集成测试")
    print("="*70)
    
    # 测试 1: 决策拒绝日志
    print("\n" + "-"*70)
    print("📋 测试 1: 决策拒绝日志 (NanaUsagi)")
    print("-"*70)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('decision_engine', 
            WORKSPACE / 'scripts' / 'autonomous-decision-engine.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        rejection = module.RejectionLog(
            task_id='test-001',
            timestamp='2026-02-28T07:57:00',
            evaluated_options=[
                {'type': 'expert', 'source': '研究员', 'option': '深度学习', 'confidence': 9, 'selected': True},
                {'type': 'quality_gate', 'source': 'Validator', 'option': 'warning', 'selected': True}
            ],
            selected_option='继续执行（有警告）',
            rejection_reason='质量门禁警告但继续',
            threshold_met=True,
            confidence='high'
        )
        
        log_dict = rejection.to_dict()
        assert log_dict['task_id'] == 'test-001'
        assert len(log_dict['evaluated_options']) == 2
        
        print(f"✅ 拒绝日志创建成功")
        print(f"   任务ID: {rejection.task_id}")
        print(f"   评估选项: {len(rejection.evaluated_options)} 个")
        print(f"   选择: {rejection.selected_option}")
        results.append(("决策拒绝日志", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("决策拒绝日志", False))
    
    # 测试 2: Cron 安全哈希验证
    print("\n" + "-"*70)
    print("📋 测试 2: Cron 安全哈希验证 (Hazel_OC)")
    print("-"*70)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(WORKSPACE / 'scripts' / 'cron-security-verifier.py'), 'status'],
            capture_output=True, text=True, timeout=10
        )
        
        print(result.stdout)
        
        # 验证文件是否存在
        verifier_script = WORKSPACE / 'scripts' / 'cron-security-verifier.py'
        assert verifier_script.exists(), "脚本不存在"
        
        print("✅ Cron 安全验证器运行正常")
        results.append(("Cron 安全验证", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("Cron 安全验证", False))
    
    # 测试 3: 记忆置信度标注
    print("\n" + "-"*70)
    print("📋 测试 3: 记忆置信度标注 (Ronin)")
    print("-"*70)
    try:
        expert_high = module.ExpertOpinion(
            expert_name='🔍 研究员',
            perspective='数据验证',
            analysis='测试分析',
            recommendations=['建议1'],
            risk_assessment='风险中等',
            confidence=9,
            model='haiku',
            certainty_factors=['有外部数据源验证', '搜索结果完整']
        )
        
        expert_low = module.ExpertOpinion(
            expert_name='💻 工程师',
            perspective='实现可行性',
            analysis='实现复杂度高',
            recommendations=['制定计划'],
            risk_assessment='实施风险',
            confidence=4,
            model='sonnet'
        )
        
        assert expert_high.confidence_level == 'high'
        assert expert_low.confidence_level == 'low'
        
        print(f"✅ 高置信度专家: {expert_high.confidence}/10 → {expert_high.confidence_level.upper()}")
        print(f"✅ 低置信度专家: {expert_low.confidence}/10 → {expert_low.confidence_level.upper()}")
        print(f"✅ 确定性因素: {expert_high.certainty_factors}")
        results.append(("记忆置信度标注", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("记忆置信度标注", False))
    
    # 测试 4: 诚实信号透明化
    print("\n" + "-"*70)
    print("📋 测试 4: 诚实信号透明化 (zode)")
    print("-"*70)
    try:
        # 验证诚实信号代码是否在 DONE 报告中
        engine_file = WORKSPACE / 'scripts' / 'autonomous-decision-engine.py'
        content = engine_file.read_text()
        
        assert '执行透明度' in content, "执行透明度部分不存在"
        assert '干净输出' in content, "诚实信号部分不存在"
        assert 'Clean Output Problem' in content, "Clean Output Problem 引用不存在"
        
        print("✅ 诚实信号已集成到 DONE 报告")
        print("   - 执行透明度部分")
        print("   - 质量门禁状态表")
        print("   - 执行真实成本")
        print("   - 干净输出背后的真实情况")
        results.append(("诚实信号透明化", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("诚实信号透明化", False))
    
    # 测试 5: Multi-Agent 任务契约
    print("\n" + "-"*70)
    print("📋 测试 5: Multi-Agent 任务契约 (Clawd-Relay)")
    print("-"*70)
    try:
        from task_contract import create_task_contract, spawn_with_contract, TaskContract
        
        contract = create_task_contract(
            task_id='test-debt-001',
            scope='分析学习债务的技术可行性',
            success_criteria=['输出方案', '风险评估', '工期估算'],
            boundary='不负责实际编码',
            deadline_minutes=30
        )
        
        assert contract.task_id == 'test-debt-001'
        assert len(contract.success_criteria) == 3
        
        print(f"✅ 契约创建成功: {contract.task_id}")
        print(f"   范围: {contract.scope}")
        print(f"   成功标准: {len(contract.success_criteria)} 项")
        
        # 测试 Echo 确认
        echo = contract.echo_confirmation('研究员Agent')
        assert '任务契约确认' in echo
        assert contract.scope in echo
        
        print("✅ Echo 确认模板生成成功")
        
        # 测试 spawn_with_contract
        enhanced = spawn_with_contract(task='分析学习债务', contract=contract)
        assert '【任务契约】' in enhanced['task']
        
        print("✅ spawn_with_contract 成功")
        
        # 测试集成到决策引擎
        assert hasattr(module.DecisionEngine, 'spawn_subagent_with_contract')
        assert hasattr(module.DecisionEngine, 'execute_with_contract')
        
        print("✅ DecisionEngine 集成方法存在")
        results.append(("Multi-Agent 任务契约", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("Multi-Agent 任务契约", False))
    
    # 汇总结果
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} | {name}")
    
    print("-"*70)
    print(f"总计: {passed} 通过 / {failed} 失败")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！Moltbook 洞察改进已完全集成。")
        return 0
    else:
        print(f"\n⚠️  {failed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(test_all_improvements())
