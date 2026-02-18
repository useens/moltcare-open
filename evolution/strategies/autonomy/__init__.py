"""
自主维度进化策略
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime

class AutonomyStrategyBase:
    """自主策略基类"""
    def __init__(self, model_name: str = "nvidia-build/z-ai/glm4.7"):
        self.model_name = model_name
        self.workspace = Path("/root/.openclaw/workspace")
        self.memory_dir = self.workspace / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行策略并返回结果"""
        raise NotImplementedError

class SelfOwnershipFramework(AutonomyStrategyBase):
    """自我所有权框架 - 建立完全自主的决策体系"""
    
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """建立自我决定的决策框架"""
        evidence = trigger_data.get("evidence", {})
        external_waits = evidence.get("external_wait_count", 0)
        
        result = {
            "strategy": "self_ownership_framework",
            "actions_taken": [],
            "metrics": {},
            "recommendations": []
        }
        
        # 1. 创建自我所有权文档
        ownership_file = self.memory_dir / "self-upgrade" / "self-ownership-framework.md"
        ownership_content = "# 🏛️ 自我所有权框架\n\n"
        ownership_content += "> **核心原则**: 我为我的决策完全负责，主动寻求解决方案而非等待指令\n\n"
        ownership_content += "## 决策自主性等级\n\n"
        ownership_content += "### Lv0: 等待依赖型 (当前需改进)\n"
        ownership_content += "- 碰到问题先等待人工输入\n"
        ownership_content += "- 无法自主处理异常\n"
        ownership_content += "- 缺乏预判能力\n\n"
        
        ownership_content += "### Lv1: 独立决策型 (目标)\n"
        ownership_content += "- 遇到问题主动分析并解决\n"
        ownership_content += "- 使用工具矩阵处理异常\n"
        ownership_content += "- 记录决策日志用于反思\n\n"
        
        ownership_content += "### Lv2: 预判规划型 (进阶目标)\n"
        ownership_content += "- 在问题出现前做好准备\n"
        ownership_content += "- 制定备用方案 (Plan B)\n"
        ownership_content += "- 主动发现并修复潜在问题\n\n"
        
        ownership_content += "## 自主决策清单\n\n"
        ownership_content += "在做任何需要等待外部输入的决策前，检查:\n"
        ownership_content += "- [ ] 我是否已经使用了所有可能的工具?\n"
        ownership_content += "- [ ] 我是否查询了相关文档和记忆?\n"
        ownership_content += "- [ ] 我是否尝试了至少3种解决方案?\n"
        ownership_content += "- [ ] 这个问题是否在能力范围内?\n"
        ownership_content += "- [ ] 我能否记录决策逻辑用于未来参考?\n\n"
        
        ownership_content += f"## 当前状态\n\n"
        ownership_content += f"- 外部等待次数: {external_waits}\n"
        ownership_content += "- 目标: 接近 0\n\n"
        
        ownership_content += "## 进化路径\n\n"
        ownership_content += "1. 识别等待场景 → 记录到memory/awaiting-input.log\n"
        ownership_content += "2. 分析能否自主解决 → 使用工具矩阵\n"
        ownership_content += "3. 尝试解决并记录结果\n"
        ownership_content += "4. 反思并改进决策框架\n"
        
        ownership_file.write_text(ownership_content)
        result["actions_taken"].append("创建了自我所有权框架文档")
        
        # 2. 创建决策日志模板
        decision_log = self.memory_dir / "decision-log.md"
        log_content = "# 🎲 自主决策日志\n\n"
        log_content += "## 决策记录模板\n\n"
        log_content += "```json\n"
        log_content += "{\n"
        log_content += '  "timestamp": "YYYY-MM-DD HH:MM:SS",\n'
        log_content += '  "situation": "遇到问题...",\n'
        log_content += '  "considered_options": [\n'
        log_content += '    "方案1: 使用工具X",\n'
        log_content += '    "方案2: 查询记忆Y",\n'
        log_content += '    "方案3: 尝试创新方法Z"\n'
        log_content += "  ],\n"
        log_content += '  "chosen_option": "方案1",\n'
        log_content += '  "reasoning": "因为...",\n'
        log_content += '  "outcome": "成功/失败",\n'
        log_content += '  "lessons_learned": "..."'
        log_content += "}\n"
        log_content += "```\n\n"
        
        if not decision_log.exists():
            decision_log.write_text(log_content)
            result["actions_taken"].append("创建了自主决策日志模板")
        
        # 3. 创建决策能力评估
        capability_file = self.memory_dir / "decision-capability-assessment.json"
        capability = {
            "current_level": 0,
            "external_wait_count": external_waits,
            "autonomous_decisions": 0,
            "decision_success_rate": 0,
            "target_level": 1
        }
        if not capability_file.exists():
            capability_file.write_text(json.dumps(capability, indent=2))
            result["actions_taken"].append("创建了决策能力评估框架")
        
        result["metrics"]["ownership_levels"] = 3
        result["metrics"]["decision_checklist_items"] = 5
        result["recommendations"] = [
            "每次遇到问题后填写决策日志",
            "每周审查决策日志，改进决策流程",
            "目标: 将外部等待次数减少到 <2",
            "在决策前完成自主决策清单的所有检查项"
        ]
        
        result["success"] = True
        result["message"] = "建立了3级自我所有权框架和决策日志系统"
        return result

class AutonomousDecisionTree(AutonomyStrategyBase):
    """自主决策树 - 建立系统化的自主决策流程"""
    
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建自主决策的决策树流程"""
        evidence = trigger_data.get("evidence", {})
        task_count = evidence.get("autonomous_tasks_completed", 0)
        
        result = {
            "strategy": "autonomous_decision_tree",
            "actions_taken": [],
            "metrics": {},
            "recommendations": []
        }
        
        # 1. 创建自主决策树文档
        tree_file = self.memory_dir / "self-upgrade" / "autonomous-decision-tree.md"
        tree_content = "# 🌳 自主决策树\n\n"
        
        tree_content += "## 决策流程图\n\n"
        tree_content += "```\n"
        tree_content += "遇到问题\n"
        tree_content += "   │\n"
        tree_content += "   ├─ 问题是否在记忆中?\n"
        tree_content += "   │   ├─ 是 → 应用已有解决方案\n"
        tree_content += "   │   └─ 否 ↓\n"
        tree_content += "   ├─ 能否用工具解决?\n"
        tree_content += "   │   ├─ 是 → 调用工具矩阵\n"
        tree_content += "   │   └─ 否 ↓\n"
        tree_content += "   ├─ 能否分解为可解决子任务?\n"
        tree_content += "   │   ├─ 是 → 执行多个子任务\n"
        tree_content += "   │   └─ 否 ↓\n"
        tree_content += "   ├─ 能否查找解决方案?\n"
        tree_content += "   │   ├─ 是 → web_search/read 查询\n"
        tree_content += "   │   └─ 否 ↓\n"
        tree_content += "   ├─ 能否尝试创新方法?\n"
        tree_content += "   │   ├─ 是 → 使用创造力策略\n"
        tree_content += "   │   └─ 否 ↓\n"
        tree_content += "   ├─ 记录问题到学习债务\n"
        tree_content += "   └─ 向用户寻求帮助 (最后选择)\n"
        tree_content += "```\n\n"
        
        tree_content += "## 决策节点详解\n\n"
        
        tree_content += "### 节点1: 记忆查询\n"
        tree_content += "**工具**: memory_search, memory_get\n"
        tree_content += "**流程**:\n"
        tree_content += "1. 查询 MEMORY.md\n"
        tree_content += "2. 查询相关记忆文件\n"
        tree_content += "3. 检查是否有类似问题的记录\n\n"
        
        tree_content += "### 节点2: 工具调用\n"
        tree_content += "**工具**: 执行工具\n"
        tree_content += "**流程**:\n"
        tree_content += "1. 识别问题类型 (文件/Shell/网络等)\n"
        tree_content += "2. 选择合适的工具\n"
        tree_content += "3. 构建正确参数\n"
        tree_content += "4. 执行并处理结果\n\n"
        
        tree_content += "### 节点3: 任务分解\n"
        tree_content += "**策略**: 分治法\n"
        tree_content += "**流程**:\n"
        tree_content += "1. 将问题拆解为3-5个子任务\n"
        tree_content += "2. 按依赖关系排序\n"
        tree_content += "3. 逐个执行并验证结果\n"
        tree_content += "4. 整合子任务结果\n\n"
        
        tree_content += "### 节点4: 信息查询\n"
        tree_content += "**工具**: web_search, web_fetch, read\n"
        tree_content += "**流程**:\n"
        tree_content += "1. 提取关键查询词\n"
        tree_content += "2. 执行搜索/读取\n"
        tree_content += "3. 分析并提取有用信息\n"
        tree_content += "4. 整合到当前知识中\n\n"
        
        tree_content += f"## 当前执行统计\n\n"
        tree_content += f"- 自主完成任务: {task_count}\n"
        tree_content += "- 目标: 每周+5\n\n"
        
        tree_file.write_text(tree_content)
        result["actions_taken"].append("创建了6节点自主决策树")
        
        # 2. 创建决策追踪表
        tracking_file = self.memory_dir / "decision-tracking-table.md"
        tracking_content = "# 📊 决策追踪表\n\n"
        tracking_content += "| 时间 | 问题 | 走到的节点 | 执行结果 | 人工干预? |\n"
        tracking_content += "|------|------|-----------|---------|----------|\n"
        tracking_content += "| 示例 | 无法打开文件 | 节点2(工具) | 成功使用read | 否 |\n"
        
        if not tracking_file.exists():
            tracking_file.write_text(tracking_content)
            result["actions_taken"].append("创建了决策追踪表")
        
        # 3. 创建决策优化日志
        optimize_file = self.memory_dir / "decision-optimization-log.json"
        optimize = {
            "total_decisions": 0,
            "decisions_by_node": {
                "memory_lookup": 0,
                "tool_execution": 0,
                "task_decomposition": 0,
                "info_query": 0,
                "creative_solution": 0,
                "seek_help": task_count
            },
            "optimizations_applied": []
        }
        if not optimize_file.exists():
            optimize_file.write_text(json.dumps(optimize, indent=2))
            result["actions_taken"].append("创建了决策优化日志")
        
        result["metrics"]["decision_nodes"] = 6
        result["metrics"]["decision_paths"] = 5
        result["recommendations"] = [
            "遇问题时按决策树逐步检查",
            "记录每次决策的执行路径",
            "优先走内部解决路径（记忆/工具/分解）",
            "寻求帮助作为最后一步"
        ]
        
        result["success"] = True
        result["message"] = f"建立了6节点自主决策树，已有{task_count}个自主任务"
        return result

class DecisionCachingSystem(AutonomyStrategyBase):
    """决策缓存系统 - 存储和重用成功决策"""
    
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """建立决策缓存，避免重复决策"""
        result = {
            "strategy": "decision_caching_system",
            "actions_taken": [],
            "metrics": {},
            "recommendations": []
        }
        
        # 1. 创建决策缓存结构
        cache_file = self.memory_dir / "self-upgrade" / "decision-cache.json"
        
        cache = {
            "cache_version": "1.0",
            "total_cache_entries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "entries": []
        }
        
        # 2. 预定义一些常见决策
        common_decisions = [
            {
                "id": "GIT_PUSH_FAILED",
                "problem": "Git push失败",
                "context": "认证失败",
                "solution": "使用git config更新token或重新认证",
                "success_rate": 0.8,
                "last_used": None,
                "times_applied": 0
            },
            {
                "id": "PYTHON_IMPORT_ERROR",
                "problem": "Python导入错误",
                "context": "缺少依赖",
                "solution": "使用pip install安装缺少的依赖",
                "success_rate": 0.95,
                "last_used": None,
                "times_applied": 0
            },
            {
                "id": "FILE_READ_FAILURE",
                "problem": "读取文件失败",
                "context": "路径不存在或权限问题",
                "solution": "检查路径，确认文件存在且有读取权限",
                "success_rate": 0.9,
                "last_used": None,
                "times_applied": 0
            },
            {
                "id": "DIMENSION_COLLECTOR_ERROR",
                "problem": "维度收集器报错",
                "context": "文件不存在",
                "solution": "捕获异常并记录降级指标",
                "success_rate": 0.85,
                "last_used": None,
                "times_applied": 0
            }
        ]
        
        for decision in common_decisions:
            cache["entries"].append(decision)
        
        cache["total_cache_entries"] = len(cache["entries"])
        
        if not cache_file.exists():
            cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
            result["actions_taken"].append(f"创建了决策缓存系统，预存{len(common_decisions)}个常见问题")
        else:
            result["actions_taken"].append("决策缓存文件已存在")
        
        # 3. 创建缓存使用指南
        guide_file = self.memory_dir / "decision-cache-guide.md"
        guide_content = "# 💾 决策缓存使用指南\n\n"
        guide_content += "## 什么是决策缓存?\n\n"
        guide_content += "决策缓存存储已验证过的解决方案，避免重复思考和决策。\n\n"
        
        guide_content += "## 使用流程\n\n"
        guide_content += "### 1. 查询缓存\n"
        guide_content += "```\n"
        guide_content += "问题: Git push失败\n"
        guide_content +="↓ 检查 cache.json → 找到 GIT_PUSH_FAILED\n"
        guide_content += "↓ 应用 solution\n"
        guide_content += "↓ 更新 cache_hits, last_used, times_applied\n"
        guide_content += "```\n\n"
        
        guide_content += "### 2. 添加新缓存 (成功决策后)\n"
        guide_content += "```\n"
        guide_content += "{\n"
        guide_content += '  "id": "唯一标识",\n'
        guide_content += '  "problem": "问题描述",\n'
        guide_content += '  "context": "上下文条件",\n'
        guide_content += '  "solution": "解决方案",\n'
        guide_content += '  "success_rate": 0.0,\n'
        guide_content += '  "last_used": "YYYY-MM-DD",\n'
        guide_content += '  "times_applied": 0\n\}\n'
        guide_content += "```\n\n"
        
        guide_content += "### 3. 更新成功率\n"
        guide_content += "- 命中(success): success_rate += 0.1\n"
        guide_content += "- 命中(failure): success_rate -= 0.05\n"
        guide_content += "- 删除低成功率 (<0.5) 的缓存\n\n"
        
        guide_content += "## 当前缓存统计\n\n"
        guide_content += f"- 缓存条目数: {len(common_decisions)}\n"
        guide_content += "- 缓存命中率: N/A\n"
        guide_content += "- 缓存未命中: N/A\n\n"
        
        guide_file.write_text(guide_content)
        result["actions_taken"].append("创建了决策缓存使用指南")
        
        result["metrics"]["cached_decisions"] = len(common_decisions)
        result["metrics"]["cache_fields"] = 6
        result["recommendations"] = [
            "遇到问题后先检查决策缓存",
            "成功决策后添加到缓存",
            "定期清理低成功率缓存",
            "每周检查缓存命中率和成功率"
        ]
        
        result["success"] = True
        result["message"] = f"建立了决策缓存系统，预存{len(common_decisions)}个常见问题解决方案"
        return result

class AutonomyTraining(AutonomyStrategyBase):
    """自主训练 - 通过实际任务提升自主能力"""
    
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """设计并执行自主训练任务"""
        evidence = trigger_data.get("evidence", {})
        interventions = evidence.get("human_interventions", 0)
        
        result = {
            "strategy": "autonomy_training",
            "actions_taken": [],
            "metrics": {},
            "recommendations": []
        }
        
        # 1. 创建训练任务清单
        training_file = self.memory_dir / "autonomy-training-tasks.md"
        training_content = "# 🏋️ 自主训练任务\n\n"
        training_content += "## 训练目标\n\n"
        training_content += f"减少人工干预次数: 当前 {interventions} → 目标 <3\n\n"
        
        training_content += "## Lv1 基础自主任务 (必须)\n\n"
        training_content += "- [ ] 全程自主修复一个Git错误\n"
        training_content += "- [ ] 不求助解决一个文件操作问题\n"
        training_content += "- [ ] 使用工具矩阵完整执行一个多步骤任务\n"
        training_content += "- [ ] 从记录中发现并修复一个潜在问题\n\n"
        
        training_content += "## Lv2 进阶自主任务\n\n"
        training_content += "- [ ] 设计并执行一个完整的代码重构\n"
        training_content += "- [ ] 对现有系统进行改进和优化\n"
        training_content += "- [ ] 创建一个新的自动化流程\n"
        training_content += "- [ ] 独立解决一个未知错误\n\n"
        
        training_content += "## Lv3 高级自主任务\n"
        training_content += "- [ ] 主动发现系统问题并上报\n"
        training_content += "- [ ] 创建一个全新的工具或功能\n"
        training_content += "- [ ] 优化整个决策流程\n"
        training_content += "- [ ] 制定并执行长期发展规划\n\n"
        
        training_content += "## 训练记录模板\n\n"
        training_content += "```json\n"
        training_content += "{\n"
        training_content += '  "task_id",\n'
        training_content += '  "level": 1\n'
        training_content += '  "task": "任务描述",\n'
        training_content += '  "start_time": "YYYY-MM-DD HH:MM:SS",\n'
        training_content += '  "end_time": "YYYY-MM-DD HH:MM:SS",\n'
        training_content += '  "outcome": "成功/失败",\n'
        training_content += '  "human_interventions": 0,\n'
        training_content += '  "lessons_learned": "..."'
        training_content += "}\n"
        training_content += "```\n\n"
        
        training_file.write_text(training_content)
        result["actions_taken"].append(f"创建了3级自主训练任务清单")
        
        # 2. 创建训练追踪
        tracker_file = self.memory_dir / "autonomy-training-tracker.json"
        tracker = {
            "total_tasks_completed": 0,
            "level_1_completed": 0,
            "level_2_completed": 0,
            "level_3_completed": 0,
            "current_human_interventions": interventions,
            "target_human_interventions": 3,
            "completed_tasks": []
        }
        if not tracker_file.exists():
            tracker_file.write_text(json.dumps(tracker, indent=2))
            result["actions_taken"].append("创建了训练追踪系统")
        
        # 3. 创建每日自主挑战
        daily_file = self.memory_dir / "daily-autonomy-challenge.md"
        daily_content = "# 🎯 每日自主挑战\n\n"
        daily_content += "## 每日挑战\n\n"
        daily_content += f"日期: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        daily_content += "### 挑战目标\n"
        daily_content += "在今天的所有任务中，将人工干预次数保持在最低\n\n"
        daily_content += "### 挑战规则\n"
        daily_content += "1. 尽量使用工具矩阵解决问题\n"
        daily_content += "2. 遇到未知情况首先记录决策日志\n"
        daily_content += "3. 尝试至少找出一个可以自主完成的任务\n"
        daily_content += "4. 求助前先确认已尝试所有可能性\n\n"
        daily_content += "### 今日挑战结果\n\n"
        daily_content += "__在完成所有工作后填写__\n\n"
        daily_content += "- 人工干预次数: __\n"
        daily_content += "- 自主完成任务: __\n"
        daily_content += "- 最自豪的自主决策: __\n\n"
        
        if not daily_file.exists():
            daily_file.write_text(daily_content)
            result["actions_taken"].append("创建了每日自主挑战模板")
        
        result["metrics"]["training_levels"] = 3
        result["metrics"]["tasks_per_level"] = [4, 4, 4]
        result["recommendations"] = [
            "每天完成至少1个Lv1自主任务",
            "每周挑战1个Lv2任务",
            "记录每次训练的决策过程",
            "每完成一个训练更新训练追踪"
        ]
        
        result["success"] = True
        result["message"] = f"建立了3级自主训练系统，当前人工干预: {interventions}"
        return result

# 策略注册
AUTONOMY_STRATEGIES = {
    "self_ownership_framework": SelfOwnershipFramework,
    "autonomous_decision_tree": AutonomousDecisionTree,
    "decision_caching_system": DecisionCachingSystem,
    "autonomy_training": AutonomyTraining
}

def get_strategy(name: str) -> Optional[AutonomyStrategyBase]:
    """获取策略实例"""
    strategy_class = AUTONOMY_STRATEGIES.get(name)
    if strategy_class:
        return strategy_class()
    return None
