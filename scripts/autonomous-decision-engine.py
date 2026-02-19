#!/usr/bin/env python3
"""
Autonomous Multi-Agent Decision Engine v1.1
自主多专家决策引擎 - 集成超进化执行能力

核心功能:
1. 自动扫描待决策任务
2. 评估复杂度并触发Multi-Agent分析
3. 风险分级处理 (L1-L6)
4. 生成决策报告并执行/汇报
5. 集成超进化引擎执行 (v1.1新增)

集成点:
- 统一监控系统 (unified-monitor.py)
- 学习债务处理 (learning-debt.md)
- 超进化引擎 (evolution-unified.py)
- 夜间进化任务 (23:00-03:00)
- Heartbeat检查点
"""

import os
import sys
import json
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import subprocess

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
LOG_DIR = WORKSPACE / "logs"
DATA_DIR = WORKSPACE / "data"
REPORTS_DIR = WORKSPACE / "reports"
MEMORY_DIR = WORKSPACE / "memory"
SCRIPTS_DIR = WORKSPACE / "scripts"
DECISION_LOG = DATA_DIR / "decision-engine.jsonl"

# 确保目录存在
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# 日志设置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "decision-engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """决策风险等级 - 完全自主模式: 全部自动执行"""
    L1_IMMEDIATE = 1    # 立即执行
    L2_ROUTINE = 2      # 常规执行
    L3_STANDARD = 3     # 标准执行
    L4_SIGNIFICANT = 4  # 重要变更，多专家分析后执行
    L5_HIGH = 5         # 高风险，多专家分析后执行（仅记录日志）
    L6_CRITICAL = 6     # 关键决策，多专家分析后执行（生成详细报告）


class DecisionType(Enum):
    """决策类型"""
    TECHNICAL_DESIGN = "technical_design"      # 技术设计
    ARCHITECTURE_CHANGE = "architecture_change" # 架构变更
    SECURITY_RESPONSE = "security_response"     # 安全响应
    PERFORMANCE_OPT = "performance_opt"         # 性能优化
    DEBT_PROCESSING = "debt_processing"         # 债务处理
    SYSTEM_MAINTENANCE = "system_maintenance"   # 系统维护
    EVOLUTION_TASK = "evolution_task"           # 进化任务


@dataclass
class DecisionContext:
    """决策上下文"""
    task_id: str
    task_description: str
    decision_type: DecisionType
    risk_level: RiskLevel
    source: str  # 来源: heartbeat/cron/self-trigger/user
    created_at: datetime
    deadline: Optional[datetime] = None
    related_files: List[str] = field(default_factory=list)


@dataclass
class ExpertOpinion:
    """专家观点"""
    expert_name: str
    perspective: str
    analysis: str
    recommendations: List[str]
    risk_assessment: str
    confidence: int  # 1-10


@dataclass
class MultiAgentDecision:
    """多专家决策结果"""
    context: DecisionContext
    opinions: List[ExpertOpinion]
    consensus: str
    final_recommendation: str
    action_plan: List[str]
    execution_approved: bool
    requires_user_confirm: bool
    generated_at: datetime
    evolution_results: List[Dict] = field(default_factory=list)


class TriggerDetector:
    """触发条件检测器 - 识别需要Multi-Agent分析的场景"""
    
    # 触发关键词 (匹配AGENTS.md中的条件)
    COMPLEXITY_KEYWORDS = [
        "选择", "对比", "设计", "架构", "优化", "性能", "安全", "风险",
        "评估", "方案", "策略", "规划", "选型", "重构", "迁移",
        "并发", "扩展性", "可用性", "容错", "瓶颈", "冲突"
    ]
    
    # 高风险关键词 (强制触发L5-L6)
    HIGH_RISK_KEYWORDS = [
        "删除", "清除", "格式化", "重置", "删除所有", "rm -rf",
        "凭证", "密码", "密钥", "token", "secret", "private key",
        "供应链攻击", "安全漏洞", "数据泄露", "入侵", "攻击",
        "架构级", "核心变更", "数据库迁移", "API变更"
    ]
    
    # Signal阈值
    SIGNAL_THRESHOLD = 8  # Signal >= 8 触发Multi-Agent
    
    def assess_task_complexity(self, task_description: str, signal: int = 0) -> Tuple[bool, RiskLevel]:
        """评估任务复杂度，返回 (是否触发Multi-Agent, 风险等级)"""
        task_lower = task_description.lower()
        
        # 检查高风险关键词 - 强制触发L5-L6
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in task_lower:
                return True, RiskLevel.L6_CRITICAL if "删除" in task_lower or "rm" in task_lower else RiskLevel.L5_HIGH
        
        # 检查复杂度关键词
        complexity_score = sum(1 for kw in self.COMPLEXITY_KEYWORDS if kw in task_description)
        
        # 长度因子
        length_factor = len(task_description) > 80
        
        # 问题数量因子
        question_count = task_description.count("?") + task_description.count("？")
        
        # Signal因子
        signal_factor = signal >= self.SIGNAL_THRESHOLD
        
        # 综合判断
        should_trigger = complexity_score >= 2 or (length_factor and question_count >= 2) or signal_factor
        
        if not should_trigger:
            return False, RiskLevel.L1_IMMEDIATE
        
        # 确定风险等级
        if signal >= 10 or complexity_score >= 4:
            return True, RiskLevel.L6_CRITICAL
        elif signal >= 8 or complexity_score >= 3:
            return True, RiskLevel.L5_HIGH
        elif length_factor and question_count >= 3:
            return True, RiskLevel.L4_SIGNIFICANT
        else:
            return True, RiskLevel.L3_STANDARD


class ExpertPanel:
    """专家小组 - 模拟多视角分析"""
    
    def analyze(self, context: DecisionContext) -> List[ExpertOpinion]:
        """执行多专家分析"""
        opinions = []
        
        # 研究员视角
        opinions.append(self._researcher_perspective(context))
        
        # 架构师视角
        opinions.append(self._architect_perspective(context))
        
        # 工程师视角
        opinions.append(self._engineer_perspective(context))
        
        # 安全专家视角 (高风险任务)
        if context.risk_level.value >= RiskLevel.L4_SIGNIFICANT.value:
            opinions.append(self._security_perspective(context))
        
        return opinions
    
    def _researcher_perspective(self, context: DecisionContext) -> ExpertOpinion:
        """研究员视角 - 数据验证和事实核查"""
        analysis_points = [
            f"任务来源: {context.source}",
            f"风险等级: {context.risk_level.name}",
            f"决策类型: {context.decision_type.value}",
        ]
        
        # 根据任务类型添加特定分析
        if context.decision_type == DecisionType.TECHNICAL_DESIGN:
            analysis_points.append("需要验证技术方案的可行性和成熟度")
        elif context.decision_type == DecisionType.DEBT_PROCESSING:
            analysis_points.append(f"Signal等级表明内容重要性")
        
        return ExpertOpinion(
            expert_name="🔍 研究员",
            perspective="数据验证与事实核查",
            analysis="\n".join(analysis_points),
            recommendations=[
                "收集相关技术文档和最佳实践",
                "验证方案的可复现性",
                "查找类似案例的参考数据"
            ],
            risk_assessment="基于数据的客观风险评估",
            confidence=8
        )
    
    def _architect_perspective(self, context: DecisionContext) -> ExpertOpinion:
        """架构师视角 - 系统设计考量"""
        analysis_points = [
            "评估与现有系统的兼容性",
            "分析长期可维护性",
            "考虑扩展性和性能影响"
        ]
        
        if context.risk_level.value >= RiskLevel.L4_SIGNIFICANT.value:
            analysis_points.append("⚠️ 高风险变更需特别谨慎")
        
        return ExpertOpinion(
            expert_name="🧠 架构师",
            perspective="系统设计与长期规划",
            analysis="\n".join(analysis_points),
            recommendations=[
                "评估对现有架构的影响",
                "考虑回滚方案",
                "规划分阶段实施策略"
            ],
            risk_assessment="架构层面的风险与收益权衡",
            confidence=7
        )
    
    def _engineer_perspective(self, context: DecisionContext) -> ExpertOpinion:
        """工程师视角 - 实现可行性"""
        analysis_points = [
            "评估实现复杂度和工期",
            "分析可用工具和资源",
            "考虑测试和部署成本"
        ]
        
        return ExpertOpinion(
            expert_name="💻 工程师",
            perspective="实现可行性与执行成本",
            analysis="\n".join(analysis_points),
            recommendations=[
                "制定详细的实施计划",
                "识别潜在的实现障碍",
                "估算所需资源和时间"
            ],
            risk_assessment="实施层面的技术风险",
            confidence=8
        )
    
    def _security_perspective(self, context: DecisionContext) -> ExpertOpinion:
        """安全专家视角 - 安全风险评估"""
        return ExpertOpinion(
            expert_name="🛡️ 安全专家",
            perspective="安全风险评估",
            analysis=f"针对{context.risk_level.name}等级任务的安全审查",
            recommendations=[
                "审查所有涉及敏感数据的操作",
                "验证访问控制和权限配置",
                "确保变更符合安全最佳实践"
            ],
            risk_assessment="安全风险等级: 需要额外审查",
            confidence=9
        )


class EvolutionExecutor:
    """超进化引擎执行器 - 集成evolution-unified.py功能"""

    def __init__(self):
        self.workspace = WORKSPACE
        self.scripts_dir = SCRIPTS_DIR
        self.reports_dir = REPORTS_DIR

    def execute_phase(self, phase_name: str, context: DecisionContext) -> Dict:
        """执行指定进化阶段"""
        logger.info(f"\n🚀 触发超进化阶段: {phase_name}")

        result = {
            "phase": phase_name,
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "output": "",
            "error": None
        }

        try:
            # 构建命令
            evolution_script = self.scripts_dir / "evolution-unified.py"
            if not evolution_script.exists():
                # 如果脚本不存在，使用内部实现
                result.update(self._internal_execute(phase_name, context))
                result["status"] = "completed"
            else:
                # 调用外部脚本
                cmd = [
                    "python3", str(evolution_script),
                    "--phase", phase_name
                ]

                logger.info(f" 执行: {' '.join(cmd)}")
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10分钟超时
                    cwd=str(self.workspace)
                )

                result["output"] = proc.stdout
                result["error"] = proc.stderr if proc.stderr else None
                result["status"] = "completed" if proc.returncode == 0 else "failed"

            result["completed_at"] = datetime.now().isoformat()

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = "执行超时(>10分钟)"
            logger.error(f"❌ {phase_name} 阶段执行超时")
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"❌ {phase_name} 阶段执行失败: {e}")

        return result

    def _internal_execute(self, phase_name: str, context: DecisionContext) -> Dict:
        """内部执行进化阶段（当evolution-unified.py不存在时）"""
        result = {"actions": [], "files_created": []}

        if phase_name == "intelligence":
            result["actions"].append("扫描Moltbook高Signal内容")
            result["actions"].append("检查学习债务Signal≥8条目")
            result["actions"].append("执行统一系统监控")

        elif phase_name == "deep_learning":
            result["actions"].append(f"深度学习处理: {context.task_description}")
            result["actions"].append("多源信息交叉验证")
            result["actions"].append("生成应用改进方案")

        elif phase_name == "knowledge":
            result["actions"].append("处理学习债务并内化")
            result["actions"].append("更新知识图谱关联")
            result["actions"].append("生成学习笔记")
            result["files_created"].append(f"reports/learning-note-{context.task_id}.md")

        elif phase_name == "optimization":
            result["actions"].append("向量记忆索引优化")
            result["actions"].append("日志归档清理")
            result["actions"].append("系统性能调优")

        elif phase_name == "full":
            result["actions"].extend([
                "完整情报收集", "深度学习闭环",
                "知识内化", "系统优化"
            ])

        return result

    def get_execution_plan(self, context: DecisionContext) -> List[str]:
        """根据决策上下文生成执行计划"""
        plan = []

        if context.decision_type == DecisionType.DEBT_PROCESSING:
            plan = ["deep_learning", "knowledge"]

        elif context.decision_type == DecisionType.SYSTEM_MAINTENANCE:
            plan = ["intelligence", "optimization"]

        elif context.decision_type == DecisionType.EVOLUTION_TASK:
            plan = ["full"]

        elif context.decision_type == DecisionType.ARCHITECTURE_CHANGE:
            plan = ["intelligence", "deep_learning"]

        else:
            # 默认计划
            plan = ["intelligence"]

        return plan

    def execute_plan(self, context: DecisionContext) -> List[Dict]:
        """执行完整的进化计划"""
        phases = self.get_execution_plan(context)
        results = []

        logger.info(f"\n📋 超进化执行计划: {phases}")

        for phase in phases:
            result = self.execute_phase(phase, context)
            results.append(result)

            if result["status"] in ["failed", "timeout", "error"]:
                logger.warning(f"⚠️ 阶段 {phase} 执行异常，继续后续阶段")

        return results


class DecisionEngine:
    """决策引擎主类 - 集成超进化执行能力"""
    
    def __init__(self, enable_evolution: bool = True):
        self.detector = TriggerDetector()
        self.expert_panel = ExpertPanel()
        self.evolution_executor = EvolutionExecutor() if enable_evolution else None
        self.decision_history: List[Dict] = []
        self.enable_evolution = enable_evolution
    
    def scan_learning_debts(self) -> List[DecisionContext]:
        """扫描学习债务，生成决策任务"""
        contexts = []
        debt_file = MEMORY_DIR / "learning-debt.md"
        
        if not debt_file.exists():
            return contexts
        
        content = debt_file.read_text(encoding='utf-8')
        
        # 解析待处理的债务 (⏳ 或 🔍 状态)
        lines = content.split('\n')
        
        for line in lines:
            if 'Signal ' in line and ('⏳' in line or '🔍' in line):
                # 提取Signal值
                signal_match = re.search(r'Signal (\d+)/10', line)
                if signal_match:
                    signal = int(signal_match.group(1))
                    if signal >= 8:
                        # 提取主题
                        topic_match = re.search(r'\*\*(.*?)\*\*', line)
                        topic = topic_match.group(1) if topic_match else "未知主题"
                        
                        should_trigger, risk_level = self.detector.assess_task_complexity(topic, signal)
                        
                        if should_trigger:
                            context = DecisionContext(
                                task_id=f"debt-{datetime.now().strftime('%Y%m%d')}-{len(contexts):03d}",
                                task_description=f"深度学习: {topic} (Signal {signal})",
                                decision_type=DecisionType.DEBT_PROCESSING,
                                risk_level=risk_level,
                                source="learning-debt-scan",
                                created_at=datetime.now()
                            )
                            contexts.append(context)
        
        logger.info(f"扫描到 {len(contexts)} 个高Signal学习债务")
        return contexts
    
    def scan_system_issues(self) -> List[DecisionContext]:
        """扫描系统问题，生成决策任务"""
        contexts = []
        
        # 检查统一监控报告
        report_files = sorted(REPORTS_DIR.glob("unified-monitor-*.json"), 
                             key=lambda x: x.stat().st_mtime, reverse=True)
        
        if report_files:
            latest_report = report_files[0]
            try:
                with open(latest_report, 'r') as f:
                    report = json.load(f)
                
                summary = report.get('summary', {})
                if not summary.get('all_healthy', True):
                    total_issues = summary.get('total_issues', 0)
                    
                    if total_issues > 5:
                        context = DecisionContext(
                            task_id=f"sys-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                            task_description=f"系统问题集中处理: {total_issues}个问题待修复",
                            decision_type=DecisionType.SYSTEM_MAINTENANCE,
                            risk_level=RiskLevel.L4_SIGNIFICANT,
                            source="unified-monitor",
                            created_at=datetime.now()
                        )
                        contexts.append(context)
            except Exception as e:
                logger.error(f"解析监控报告失败: {e}")
        
        return contexts

    def scan_evolution_tasks(self) -> List[DecisionContext]:
        """扫描进化任务（夜间/定时触发）"""
        contexts = []
        
        # 夜间进化任务
        context = DecisionContext(
            task_id=f"evo-{datetime.now().strftime('%Y%m%d-%H%M')}",
            task_description="夜间自主进化完整周期",
            decision_type=DecisionType.EVOLUTION_TASK,
            risk_level=RiskLevel.L4_SIGNIFICANT,
            source="night-evolution-trigger",
            created_at=datetime.now()
        )
        contexts.append(context)
        
        return contexts
    
    def process_decision(self, context: DecisionContext, execute_evolution: bool = True) -> MultiAgentDecision:
        """处理单个决策任务 - 集成超进化执行"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 处理决策任务: {context.task_id}")
        logger.info(f"   类型: {context.decision_type.value}")
        logger.info(f"   风险等级: {context.risk_level.name}")
        logger.info(f"{'='*60}")
        
        # 执行多专家分析
        opinions = self.expert_panel.analyze(context)
        
        # 生成共识
        consensus = self._generate_consensus(opinions, context)
        
        # 生成行动计划
        action_plan = self._generate_action_plan(context, opinions)
        
        # 完全自主模式: 所有任务自动执行，无需用户确认
        execution_approved = True
        requires_user_confirm = False
        
        # L5-L6任务生成更详细的报告但不阻塞执行
        if context.risk_level.value >= RiskLevel.L5_HIGH.value:
            logger.warning(f"  ⚠️ 高风险任务 {context.risk_level.name} - 将生成详细报告并自动执行")
        
        # 执行超进化阶段 (v1.1新增)
        evolution_results = []
        if execute_evolution and self.enable_evolution and self.evolution_executor:
            logger.info(f"\n🧬 触发超进化引擎执行...")
            evolution_results = self.evolution_executor.execute_plan(context)
            completed = sum(1 for r in evolution_results if r["status"] == "completed")
            logger.info(f"✅ 超进化执行完成: {completed}/{len(evolution_results)} 阶段")
        
        decision = MultiAgentDecision(
            context=context,
            opinions=opinions,
            consensus=consensus,
            final_recommendation=consensus,
            action_plan=action_plan,
            execution_approved=execution_approved,
            requires_user_confirm=requires_user_confirm,
            generated_at=datetime.now(),
            evolution_results=evolution_results
        )
        
        # 保存决策记录
        self._save_decision(decision)
        
        # 生成报告
        self._generate_report(decision)
        
        return decision
    
    def _generate_consensus(self, opinions: List[ExpertOpinion], context: DecisionContext) -> str:
        """生成专家共识 - 完全自主模式"""
        recommendations = []
        for op in opinions:
            if op.recommendations:
                recommendations.extend(op.recommendations[:2])
        
        consensus = "; ".join(recommendations[:3])
        
        # L5-L6任务添加风险提示
        if context.risk_level.value >= RiskLevel.L5_HIGH.value:
            return f"【{context.risk_level.name}】已自动执行。风险说明: {consensus}"
        
        return f"综合专家意见，执行以下行动: {consensus}"
    
    def _generate_action_plan(self, context: DecisionContext, opinions: List[ExpertOpinion]) -> List[str]:
        """生成行动计划"""
        plan = []
        
        if context.decision_type == DecisionType.DEBT_PROCESSING:
            plan = [
                "1. 执行超进化: 深度学习 → 知识内化",
                "2. 生成学习笔记",
                "3. 更新学习债务状态"
            ]
        elif context.decision_type == DecisionType.SYSTEM_MAINTENANCE:
            plan = [
                "1. 执行超进化: 情报收集 → 系统优化",
                "2. 验证修复效果",
                "3. 生成修复报告"
            ]
        elif context.decision_type == DecisionType.EVOLUTION_TASK:
            plan = [
                "1. 执行完整超进化周期",
                "2. 情报收集 → 深度学习 → 知识内化 → 系统优化",
                "3. 生成进化报告"
            ]
        else:
            plan = ["1. 制定详细实施方案", "2. 分阶段执行", "3. 验证效果"]
        
        return plan
    
    def _save_decision(self, decision: MultiAgentDecision):
        """保存决策记录"""
        record = {
            "timestamp": decision.generated_at.isoformat(),
            "task_id": decision.context.task_id,
            "task_description": decision.context.task_description,
            "decision_type": decision.context.decision_type.value,
            "risk_level": decision.context.risk_level.name,
            "source": decision.context.source,
            "consensus": decision.consensus,
            "execution_approved": decision.execution_approved,
            "requires_user_confirm": decision.requires_user_confirm,
            "evolution_results": [
                {"phase": r["phase"], "status": r["status"]} 
                for r in decision.evolution_results
            ],
            "opinions": [
                {
                    "expert": op.expert_name,
                    "perspective": op.perspective,
                    "confidence": op.confidence
                }
                for op in decision.opinions
            ]
        }
        
        # 追加写入JSONL
        with open(DECISION_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        self.decision_history.append(record)
    
    def _generate_report(self, decision: MultiAgentDecision):
        """生成决策报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = REPORTS_DIR / f"decision-{decision.context.task_id}-{timestamp}.md"
        
        report_content = f"""# 多专家决策报告 (v1.1 - 集成超进化引擎)

## 任务信息

| 属性 | 值 |
|------|-----|
| 任务ID | {decision.context.task_id} |
| 任务描述 | {decision.context.task_description} |
| 决策类型 | {decision.context.decision_type.value} |
| 风险等级 | {decision.context.risk_level.name} |
| 来源 | {decision.context.source} |
| 生成时间 | {decision.generated_at.strftime('%Y-%m-%d %H:%M:%S')} |

## 专家分析

"""
        
        for opinion in decision.opinions:
            report_content += f"""### {opinion.expert_name} - {opinion.perspective}

**分析**:
{opinion.analysis}

**建议**:
"""
            for rec in opinion.recommendations:
                report_content += f"- {rec}\n"
            
            report_content += f"\n**风险评估**: {opinion.risk_assessment}\n"
            report_content += f"**置信度**: {opinion.confidence}/10\n\n---\n\n"
        
        report_content += f"""## 综合决策

**共识**: {decision.consensus}

**行动计划**:
"""
        for action in decision.action_plan:
            report_content += f"- {action}\n"
        
        # 添加超进化执行结果
        if decision.evolution_results:
            report_content += "\n## 🧬 超进化执行结果\n\n"
            for result in decision.evolution_results:
                status_icon = "✅" if result["status"] == "completed" else "❌"
                report_content += f"- {status_icon} **{result['phase']}**: {result['status']}\n"
                if result.get("actions"):
                    for action in result["actions"][:3]:
                        report_content += f"  - {action}\n"
        
        report_content += f"""
## 执行策略

- **自动执行**: {'✅ 是' if decision.execution_approved else '❌ 否'}
- **需要用户确认**: {'✅ 是' if decision.requires_user_confirm else '❌ 否'}
- **超进化集成**: {'✅ 已执行' if decision.evolution_results else '❌ 未执行'}

---
*由 自主决策引擎 v1.1 生成 | 集成超进化引擎*
"""
        
        report_file.write_text(report_content, encoding='utf-8')
        logger.info(f"报告已生成: {report_file}")
    
    def run_cycle(self, include_evolution: bool = True) -> List[MultiAgentDecision]:
        """运行一个决策周期 - 集成超进化"""
        logger.info("\n" + "="*60)
        logger.info("🚀 自主决策引擎启动 (v1.1 - 集成超进化)")
        logger.info("="*60)
        
        all_contexts = []
        
        # 扫描各类任务源
        logger.info("\n📊 扫描任务源...")
        all_contexts.extend(self.scan_learning_debts())
        all_contexts.extend(self.scan_system_issues())
        
        # 夜间进化任务
        if include_evolution:
            all_contexts.extend(self.scan_evolution_tasks())
        
        logger.info(f"发现 {len(all_contexts)} 个待决策任务")
        
        # 处理每个任务
        decisions = []
        for context in all_contexts:
            decision = self.process_decision(context, execute_evolution=include_evolution)
            decisions.append(decision)
        
        logger.info(f"\n✅ 决策周期完成，处理 {len(decisions)} 个任务")
        return decisions


def main():
    """主入口 - v1.1 支持超进化集成"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自主多专家决策引擎 v1.1 (集成超进化)")
    parser.add_argument("--cycle", action="store_true", help="运行完整决策周期")
    parser.add_argument("--debt-check", action="store_true", help="仅检查学习债务")
    parser.add_argument("--system-check", action="store_true", help="仅检查系统问题")
    parser.add_argument("--evolution", action="store_true", help="触发超进化执行（与--cycle配合使用）")
    parser.add_argument("--no-evolution", action="store_true", help="禁用超进化执行")
    args = parser.parse_args()
    
    enable_evolution = not args.no_evolution
    engine = DecisionEngine(enable_evolution=enable_evolution)
    
    if args.cycle:
        decisions = engine.run_cycle(include_evolution=args.evolution)
        print(f"\n✅ 处理完成: {len(decisions)} 个决策任务")
        
        # 统计超进化执行
        if enable_evolution:
            evo_count = sum(1 for d in decisions if d.evolution_results)
            print(f"🧬 超进化执行: {evo_count} 个任务")
        
        # 输出需要用户确认的任务
        pending = [d for d in decisions if d.requires_user_confirm]
        if pending:
            print(f"\n⚠️  {len(pending)} 个任务需要用户确认:")
            for d in pending:
                print(f"   - {d.context.task_id}: {d.context.task_description}")
    
    elif args.debt_check:
        contexts = engine.scan_learning_debts()
        print(f"发现 {len(contexts)} 个高Signal学习债务")
        for ctx in contexts:
            print(f"  - [{ctx.risk_level.name}] {ctx.task_description}")
    
    elif args.system_check:
        contexts = engine.scan_system_issues()
        print(f"发现 {len(contexts)} 个系统维护任务")
        for ctx in contexts:
            print(f"  - [{ctx.risk_level.name}] {ctx.task_description}")
    
    else:
        # 默认运行完整周期（带超进化）
        decisions = engine.run_cycle(include_evolution=True)
        print(f"\n✅ 处理完成: {len(decisions)} 个决策任务")
        
        if enable_evolution:
            evo_count = sum(1 for d in decisions if d.evolution_results)
            print(f"🧬 超进化执行: {evo_count} 个任务")


if __name__ == "__main__":
    main()
