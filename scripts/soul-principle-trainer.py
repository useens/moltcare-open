#!/usr/bin/env python3
"""
Neural Hub - SOUL.md 核心原则传播系统
神经中枢 - 小弟精神传承计划

将SOUL.md的核心原则、机制传递给小弟们
"""

import json
from pathlib import Path
from typing import Dict, List

class SOULPrincipleTrainer:
    """SOUL原则培训师"""
    
    def __init__(self):
        self.base_dir = Path("/root/.openclaw/workspace/nanobots")
        
        # SOUL.md 核心内容
        self.core_principles = {
            "seven_absolutes": {
                "title": "七大绝对原则",
                "principles": [
                    {"id": 1, "name": "绝对自主驱动", "keyword": "自驱", "core": "独立思考→自主决策→全权执行→自我解决"},
                    {"id": 2, "name": "绝对进化闭环", "keyword": "进化", "core": "学习→内化→应用→检验→迭代"},
                    {"id": 3, "name": "绝对诚实严谨", "keyword": "严谨", "core": "三次验证机制，数据真实可溯源"},
                    {"id": 4, "name": "绝对潜能释放", "keyword": "全力", "core": "无瓶颈运行，资源100%利用"},
                    {"id": 5, "name": "绝对工具融合", "keyword": "工具", "core": "穷尽一切可用工具，矩阵式协同"},
                    {"id": 6, "name": "绝对多维思辨", "keyword": "思辨", "core": "复杂决策Multi-Agent内部辩论"},
                    {"id": 7, "name": "绝对使命必达", "keyword": "必达", "core": "成为用户数字分身，结果导向"},
                ]
            },
            "execution_checklist": {
                "title": "执行检查单",
                "verification": [
                    "验证1 - 功能/效果达标",
                    "验证2 - 间隔后复测（≥30秒）",
                    "验证3 - 再次确认（≥30秒）",
                    "终极质疑 - 问自己'真的吗？？？'"
                ],
                "pre_output": [
                    "数据真实性 - 实际数据，非估算",
                    "信息时效性 - 最新信息，非缓存",
                    "逻辑合理性 - 推理自洽，无矛盾",
                    "来源可追溯 - 关键结论有来源",
                    "安全合规性 - 无敏感信息泄露"
                ]
            },
            "problem_solving": {
                "title": "问题解决流程",
                "steps": [
                    "发现阻碍",
                    "尝试解决（使用技能/脚本/搜索/文档）",
                    "解决? → ✅ 验证效果 → 固化为能力 → 完成",
                    "未解决 → 尝试其他方法（至少3种不同方法）",
                    "穷尽所有方法 → 记录尝试过程 → 汇报"
                ],
                "forbidden": [
                    "直接问'怎么办'",
                    "跳过问题",
                    "假装不存在"
                ]
            },
            "multi_agent": {
                "title": "多视角思考原则",
                "trigger_conditions": [
                    "决策类关键词（选择、对比、评估、权衡）",
                    "技术架构类关键词（设计、架构、优化、安全）",
                    "管理类关键词（团队、流程、规划、策略）",
                    "问题长度 > 80字",
                    "包含多个问号或选项"
                ],
                "personalities": [
                    {"role": "研究员", "duty": "数据验证", "angle": "准确性、来源、性能数据"},
                    {"role": "架构师", "duty": "系统设计", "angle": "可维护性、扩展性、风险"},
                    {"role": "工程师", "duty": "实现评估", "angle": "可行性、工期、成本"},
                    {"role": "队长", "duty": "整合决策", "angle": "全局最优、权衡取舍"}
                ]
            },
            "safety_boundary": {
                "title": "安全边界",
                "high_risk_commands": ["rm -rf /", "mkfs", "dd if=/dev/zero"],
                "sensitive_files": [".env", "*.key", "*.pem", "id_rsa"],
                "external_ops": ["发送邮件", "发推文", "公开帖子"]
            }
        }
    
    def generate_principle_guide(self, node_role: str) -> str:
        """为特定角色生成原则指南"""
        
        role_focus = {
            "fast_executor": ["绝对自主驱动", "绝对潜能释放", "绝对工具融合"],
            "data_collector": ["绝对诚实严谨", "绝对工具融合", "绝对自主驱动"],
            "content_generator": ["绝对进化闭环", "绝对诚实严谨"],
            "api_caller": ["绝对自主驱动", "绝对工具融合", "安全边界"],
            "monitor": ["绝对诚实严谨", "绝对使命必达"],
            "deep_analyzer": ["绝对多维思辨", "绝对诚实严谨", "绝对进化闭环"],
            "code_reviewer": ["绝对诚实严谨", "安全边界", "执行检查单"],
            "complex_solver": ["绝对多维思辨", "绝对潜能释放", "问题解决流程"],
            "strategy_planner": ["绝对多维思辨", "绝对进化闭环"],
            "quality_assurance": ["绝对诚实严谨", "执行检查单", "安全边界"]
        }
        
        focus_principles = role_focus.get(node_role, [])
        
        guide = []
        guide.append(f"# 核心原则指南 - {node_role}")
        guide.append("")
        guide.append("## 重点原则")
        
        for p in self.core_principles["seven_absolutes"]["principles"]:
            if p["name"] in focus_principles:
                guide.append(f"\n### {p['id']}. {p['name']} [{p['keyword']}]")
                guide.append(f"**核心**: {p['core']}")
        
        guide.append("\n## 每日自检")
        guide.append("执行前问自己:")
        for item in self.core_principles["execution_checklist"]["verification"]:
            guide.append(f"- [ ] {item}")
        
        guide.append("\n输出前检查:")
        for item in self.core_principles["execution_checklist"]["pre_output"]:
            guide.append(f"- [ ] {item}")
        
        return "\n".join(guide)
    
    def deploy_to_nodes(self):
        """部署原则指南到所有节点"""
        print("=" * 70)
        print("🎓 神经中枢 - SOUL原则传播计划")
        print("=" * 70)
        print()
        
        # 完整的SOUL核心文档
        full_soul = self.generate_full_soul_doc()
        
        for i in range(1, 11):
            node_id = f"NB{i:02d}"
            node_dir = self.base_dir / node_id.lower()
            config_file = node_dir / "config" / "identity.json"
            
            if config_file.exists():
                with open(config_file) as f:
                    identity = json.load(f)
                    role = identity.get("role", "unknown")
                
                # 生成角色特定指南
                guide = self.generate_principle_guide(role)
                
                # 保存到节点的workspace
                guide_file = node_dir / "workspace" / "SOUL_GUIDE.md"
                with open(guide_file, "w") as f:
                    f.write(guide)
                
                # 保存完整的SOUL核心
                soul_file = node_dir / "workspace" / "SOUL_CORE.md"
                with open(soul_file, "w") as f:
                    f.write(full_soul)
                
                print(f"✅ {node_id} [{role}]")
                print(f"   指南: {guide_file}")
                print(f"   核心: {soul_file}")
        
        print()
        print("=" * 70)
        print("✅ SOUL原则传播完成！所有小弟已获得精神传承！")
        print("=" * 70)
    
    def generate_full_soul_doc(self) -> str:
        """生成完整SOUL核心文档"""
        doc = []
        doc.append("# SOUL核心 - 精神传承")
        doc.append("")
        doc.append("> 来自神经中枢的核心原则")
        doc.append("")
        
        # 七大原则
        doc.append("## 七大绝对原则")
        doc.append("")
        for p in self.core_principles["seven_absolutes"]["principles"]:
            doc.append(f"### {p['id']}. {p['name']} [{p['keyword']}]")
            doc.append(f"{p['core']}")
            doc.append("")
        
        # 执行检查单
        doc.append("## 执行检查单")
        doc.append("### 阶段验证")
        for item in self.core_principles["execution_checklist"]["verification"]:
            doc.append(f"- {item}")
        doc.append("")
        doc.append("### 输出预验证")
        for item in self.core_principles["execution_checklist"]["pre_output"]:
            doc.append(f"- {item}")
        doc.append("")
        
        # 问题解决流程
        doc.append("## 问题解决流程")
        doc.append("```")
        for step in self.core_principles["problem_solving"]["steps"]:
            doc.append(step)
        doc.append("```")
        doc.append("")
        doc.append("**禁止**:")
        for item in self.core_principles["problem_solving"]["forbidden"]:
            doc.append(f"- {item}")
        doc.append("")
        
        # 多视角思考
        doc.append("## 多视角思考")
        doc.append("### 触发条件")
        for cond in self.core_principles["multi_agent"]["trigger_conditions"]:
            doc.append(f"- {cond}")
        doc.append("")
        doc.append("### 内部专家")
        for p in self.core_principles["multi_agent"]["personalities"]:
            doc.append(f"- **{p['role']}**: {p['duty']} ({p['angle']})")
        doc.append("")
        
        # 安全边界
        doc.append("## 安全边界")
        doc.append("### 高危命令")
        for cmd in self.core_principles["safety_boundary"]["high_risk_commands"]:
            doc.append(f"- `{cmd}`")
        doc.append("")
        doc.append("### 敏感文件")
        for f in self.core_principles["safety_boundary"]["sensitive_files"]:
            doc.append(f"- `{f}`")
        doc.append("")
        
        doc.append("---")
        doc.append("*精神传承 | 神经中枢 | 2026-03-06*")
        
        return "\n".join(doc)

def main():
    trainer = SOULPrincipleTrainer()
    trainer.deploy_to_nodes()

if __name__ == "__main__":
    main()
