#!/usr/bin/env python3
"""
Autonomous Multi-Agent Decision Engine v1.0
自主多专家决策引擎 - 后台自动触发多视角分析

核心功能:
1. 自动扫描待决策任务
2. 评估复杂度并触发Multi-Agent分析
3. 风险分级处理 (L1-L6)
4. 生成决策报告并执行/汇报

集成点:
- 统一监控系统 (unified-monitor.py)
- 学习债务处理 (learning-debt.md)
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
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
LOG_DIR = WORKSPACE / "logs"
DATA_DIR = WORKSPACE / "data"
REPORTS_DIR = WORKSPACE / "reports"
MEMORY_DIR = WORKSPACE / "memory"
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
    related_files: List[str] = None
    
    def __post_init__(self):
        if self.related_files is None:
            self.related_files = []


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
        """
        评估任务复杂度，返回 (是否触发Multi-Agent, 风险等级)
        """
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
            analysis=f"针对{risk_level.name}等级任务的安全审查",
            recommendations=[
                "审查所有涉及敏感数据的操作",
                "验证访问控制和权限配置",
                "确保变更符合安全最佳实践"
            ],
            risk_assessment="安全风险等级: 需要额外审查",
            confidence=9
        )


class DecisionEngine:
    """决策引擎主类"""
    
    def __init__(self):
        self.detector = TriggerDetector()
        self.expert_panel = ExpertPanel()
        self.decision_history: List[Dict] = []
    
    def scan_learning_debts(self) -> List[DecisionContext]:
        """扫描学习债务，生成决策任务"""
        contexts = []
        debt_file = MEMORY_DIR / "learning-debt.md"
        
        if not debt_file.exists():
            return contexts
        
        content = debt_file.read_text(encoding='utf-8')
        
        # 解析待处理的债务 (⏳ 或 🔍 状态)
        # 简化实现：查找Signal 8+的条目
        pattern = r'\[.*?Signal (\d+)/10.*?\].*?⏳|🔍.*?待处理'
        matches = re.findall(pattern, content, re.DOTALL)
        
        # 实际解析实现
        lines = content.split('\n')
        current_debt = None
        
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
    
    def process_decision(self, context: DecisionContext) -> MultiAgentDecision:
        """处理单个决策任务"""
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
        
        decision = MultiAgentDecision(
            context=context,
            opinions=opinions,
            consensus=consensus,
            final_recommendation=consensus,
            action_plan=action_plan,
            execution_approved=execution_approved,
            requires_user_confirm=requires_user_confirm,
            generated_at=datetime.now()
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
                "1. 阅读并提取核心概念",
                "2. 关联已有知识图谱",
                "3. 生成学习笔记",
                "4. 更新学习债务状态"
            ]
        elif context.decision_type == DecisionType.SYSTEM_MAINTENANCE:
            plan = [
                "1. 执行统一监控修复",
                "2. 验证修复效果",
                "3. 生成修复报告"
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
        
        report_content = f"""# 多专家决策报告

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
        
        report_content += f"""
## 执行策略

- **自动执行**: {'✅ 是' if decision.execution_approved else '❌ 否'}
- **需要用户确认**: {'✅ 是' if decision.requires_user_confirm else '❌ 否'}

"""
        
        if decision.requires_user_confirm:
            report_content += """## ⚠️ 等待用户确认

此决策被标记为高风险，需要用户确认后才能执行。
"""
        
        report_file.write_text(report_content, encoding='utf-8')
        logger.info(f"报告已生成: {report_file}")
    
    def run_cycle(self) -> List[MultiAgentDecision]:
        """运行一个决策周期"""
        logger.info("\n" + "="*60)
        logger.info("🚀 自主决策引擎启动")
        logger.info("="*60)
        
        all_contexts = []
        
        # 扫描各类任务源
        logger.info("\n📊 扫描任务源...")
        all_contexts.extend(self.scan_learning_debts())
        all_contexts.extend(self.scan_system_issues())
        
        logger.info(f"发现 {len(all_contexts)} 个待决策任务")
        
        # 处理每个任务
        decisions = []
        for context in all_contexts:
            decision = self.process_decision(context)
            decisions.append(decision)
        
        logger.info(f"\n✅ 决策周期完成，处理 {len(decisions)} 个任务")
        return decisions


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自主多专家决策引擎")
    parser.add_argument("--cycle", action="store_true", help="运行完整决策周期")
    parser.add_argument("--debt-check", action="store_true", help="仅检查学习债务")
    parser.add_argument("--system-check", action="store_true", help="仅检查系统问题")
    args = parser.parse_args()
    
    engine = DecisionEngine()
    
    if args.cycle:
        decisions = engine.run_cycle()
        print(f"\n处理完成: {len(decisions)} 个决策任务")
        
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
        # 默认运行完整周期
        decisions = engine.run_cycle()
        print(f"\n处理完成: {len(decisions)} 个决策任务")


if __name__ == "__main__":
    main()
