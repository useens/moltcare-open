"""认知维度进化策略"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 尝试导入核心模块
try:
    from ...core import state
except ImportError:
    # 备用导入（当作为脚本直接运行时）
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core import state

class DeepReasoningStrategy:
    """深化推理策略 - 提升推理链深度"""
    
    def __init__(self):
        self.name = "deep_reasoning_upgrade"
    
    def execute(self, decision: Dict) -> Dict[str, Any]:
        """执行深化推理策略"""
        actions = []
        
        # 1. 记录推理深度目标
        reasoning_log = Path("/root/.openclaw/workspace/memory/self-upgrade/reasoning-depth.log")
        reasoning_log.parent.mkdir(parents=True, exist_ok=True)
        with open(reasoning_log, "a") as f:
            f.write(f"TARGET: reasoning depth >= 5 layers | {datetime.now().isoformat()}\n")
        actions.append({"action": "set_reasoning_depth_target", "target": 5})
        
        # 2. 更新系统配置，启用深度推理模式
        config_file = Path("/root/.openclaw/workspace/memory/self-upgrade/config.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        import json
        if config_file.exists():
            config = json.loads(config_file.read_text())
        else:
            config = {}
        config["reasoning_mode"] = "deep"
        config["min_reasoning_depth"] = 5
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        actions.append({"action": "enable_deep_reasoning_mode"})
        
        # 3. 创建推理模板
        template = Path("/root/.openclaw/workspace/memory/self-upgrade/reasoning-template.md")
        with open(template, "w") as f:
            f.write("""# 深度推理模板

## 第一层：问题理解
- 核心问题是什么？
- 相关背景有哪些？
- 隐含的约束是什么？

## 第二层：信息收集
- 已知信息列表
- 未知/待查信息
- 信息来源验证

## 第三层：方案生成
- 方案A: ...
- 方案B: ...
- 方案C: ...

## 第四层：深入分析
- 每个方案的优缺点
- 风险评估
- 资源需求分析

## 第五层：综合决策
- 最优方案选择
- 执行计划
- 预期结果
""")
        actions.append({"action": "create_reasoning_template"})
        
        return {
            "status": "success",
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }
    
    def validate(self) -> bool:
        """验证"""
        config_file = Path("/root/.openclaw/workspace/memory/self-upgrade/config.json")
        if config_file.exists():
            import json
            config = json.loads(config_file.read_text())
            return config.get("reasoning_mode") == "deep"
        return False
    
    def rollback(self):
        """回滚"""
        config_file = Path("/root/.openclaw/workspace/memory/self-upgrade/config.json")
        if config_file.exists():
            import json
            config = json.loads(config_file.read_text())
            config["reasoning_mode"] = "normal"
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

class CounterArgumentStrategy:
    """反证框架策略 - 检测矛盾"""
    
    def __init__(self):
        self.name = "counter_argument_framework"
    
    def execute(self, decision: Dict) -> Dict[str, Any]:
        """执行反证框架策略"""
        actions = []
        
        # 创建反证检查清单
        checklist = Path("/root/.openclaw/workspace/memory/self-upgrade/counter-argument-checklist.md")
        with open(checklist, "w") as f:
            f.write("""# 反证检查清单

每次决策前必须检查：

## 逻辑一致性
- [ ] 结论是否与前提矛盾？
- [ ] 是否有循环论证？
- [ ] 是否忽略了反例？

## 事实验证
- [ ] 关键事实来源是否可靠？
- [ ] 是否有相反的证据？
- [ ] 数据是否过时？

## 假设检查
- [ ] 假设是否合理？
- [ ] 如果假设不成立，结论是否变化？
- [ ] 是否考虑了极端情况？

## 他人观点
- [ ] 有不同意见者会怎么说？
- [ ] 他们的反驳点是什么？
- [ ] 如何回应反驳？
""")
        actions.append({"action": "create_counter_argument_checklist"})
        
        return {
            "status": "success",
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }
    
    def validate(self) -> bool:
        """验证"""
        checklist = Path("/root/.openclaw/workspace/memory/self-upgrade/counter-argument-checklist.md")
        return checklist.exists()
    
    def rollback(self):
        """回滚"""
        checklist = Path("/root/.openclaw/workspace/memory/self-upgrade/counter-argument-checklist.md")
        if checklist.exists():
            checklist.unlink()

class AbstractionLadderStrategy:
    """抽象阶梯策略 - 提升抽象思维能力"""
    
    def __init__(self):
        self.name = "abstraction_ladder"
    
    def execute(self, decision: Dict) -> Dict[str, Any]:
        """执行抽象阶梯策略"""
        actions = []
        
        # 创建抽象阶梯模板
        template = Path("/root/.openclaw/workspace/memory/self-upgrade/abstraction-ladder.md")
        with open(template, "w") as f:
            f.write("""# 抽象阶梯

从具体到抽象，逐层提升：

## L0: 具体细节
- 具体的对象、事件、数字

## L1: 归纳模式
- 从细节中总结出的规律

## L2: 分类范畴
- 将规律归入更大的类别

## L3: 原理原则
- 范畴背后的通用原则

## L4: 概念框架
- 原则之间的关系网络

## L5: 抽象理论
- 跨领域的通用理论

---

思考时，先沿阶梯上升（抽象），找到本质原理；
再沿阶梯下降（具体），应用到实际问题。
""")
        actions.append({"action": "create_abstraction_ladder"})
        
        return {
            "status": "success",
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }
    
    def validate(self) -> bool:
        """验证"""
        template = Path("/root/.openclaw/workspace/memory/self-upgrade/abstraction-ladder.md")
        return template.exists()
    
    def rollback(self):
        """回滚"""
        template = Path("/root/.openclaw/workspace/memory/self-upgrade/abstraction-ladder.md")
        if template.exists():
            template.unlink()

class LogicalConsistencyStrategy:
    """逻辑一致性检查策略"""
    
    def __init__(self):
        self.name = "logical_consistency_checker"
    
    def execute(self, decision: Dict) -> Dict[str, Any]:
        """执行逻辑一致性检查策略"""
        actions = []
        
        # 创建逻辑一致性检查脚本
        checker = Path("/root/.openclaw/workspace/scripts/check-logical-consistency.py")
        with open(checker, "w") as f:
            f.write('''#!/usr/bin/env python3
"""逻辑一致性检查"""
import sys
from pathlib import Path

def check_statement(statement: str) -> list:
    """检查语句的逻辑问题（简化版）"""
    issues = []
    
    # 检查矛盾词
    contradictions = ["不...不", "没...没", "从不...总是"]
    for pattern in contradictions:
        if pattern in statement:
            issues.append(f"可能包含矛盾: {pattern}")
    
    # 检查绝对化陈述
    absolutes = ["总是", "从不", "绝对", "必定"]
    for word in absolutes:
        if word in statement.split():
            issues.append(f"使用绝对化词汇: {word}")
    
    return issues

if __name__ == "__main__":
    if len(sys.argv) > 1:
        statement = " ".join(sys.argv[1:])
        issues = check_statement(statement)
        if issues:
            print("发现逻辑问题:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ 未发现明显逻辑问题")
''')
        checker.chmod(0o755)
        actions.append({"action": "create_logical_checker_script"})
        
        return {
            "status": "success",
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }
    
    def validate(self) -> bool:
        """验证"""
        checker = Path("/root/.openclaw/workspace/scripts/check-logical-consistency.py")
        return checker.exists()
    
    def rollback(self):
        """回滚"""
        checker = Path("/root/.openclaw/workspace/scripts/check-logical-consistency.py")
        if checker.exists():
            checker.unlink()

# 策略注册
STRATEGIES = {
    "deep_reasoning_upgrade": DeepReasoningStrategy(),
    "counter_argument_framework": CounterArgumentStrategy(),
    "abstraction_ladder": AbstractionLadderStrategy(),
    "logical_consistency_checker": LogicalConsistencyStrategy()
}
