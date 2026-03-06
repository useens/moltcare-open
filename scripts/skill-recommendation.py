#!/usr/bin/env python3
"""
Neural Hub - Skill Recommendation System
神经中枢 - Skill推荐与协调系统

让小弟们根据角色自主分析需要哪些skill
我作为神经中枢审批和协调
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

# 可用skill库
SKILL_LIBRARY = {
    # 网络与数据
    "web_search": {"desc": "网络搜索", "category": "network", "level": "low"},
    "web_fetch": {"desc": "网页内容获取", "category": "network", "level": "low"},
    "web_intelligence": {"desc": "网页智能分析", "category": "network", "level": "medium"},
    "agent_reach": {"desc": "Agent Reach网络访问(YouTube/Twitter/Reddit/GitHub等)", "category": "network", "level": "medium"},
    "browser": {"desc": "浏览器自动化", "category": "network", "level": "medium"},
    
    # 代码与开发
    "github": {"desc": "GitHub操作", "category": "dev", "level": "low"},
    "docker_essentials": {"desc": "Docker基础操作", "category": "dev", "level": "medium"},
    "tdd_guide": {"desc": "测试驱动开发", "category": "dev", "level": "low"},
    "skill_creator": {"desc": "创建和管理skill", "category": "dev", "level": "medium"},
    
    # 数据处理
    "summarize": {"desc": "内容摘要", "category": "data", "level": "low"},
    "video_frames": {"desc": "视频帧提取", "category": "data", "level": "low"},
    "fd_find": {"desc": "快速文件查找", "category": "data", "level": "low"},
    "bat_cat": {"desc": "增强版文件查看", "category": "data", "level": "low"},
    
    # 智能与分析
    "vestige": {"desc": "FSRS-6记忆系统", "category": "intel", "level": "low"},
    "agentlens": {"desc": "代码库分析导航", "category": "intel", "level": "low"},
    "local_whisper": {"desc": "本地语音转文字", "category": "intel", "level": "low"},
    
    # 平台特定
    "moltbook": {"desc": "Moltbook社交操作", "category": "platform", "level": "medium"},
    "feishu_doc": {"desc": "飞书文档操作", "category": "platform", "level": "low"},
    "feishu_wiki": {"desc": "飞书知识库", "category": "platform", "level": "low"},
    "obsidian": {"desc": "Obsidian笔记管理", "category": "platform", "level": "low"},
    
    # 其他
    "weather": {"desc": "天气查询", "category": "util", "level": "low"},
    "vhs_recorder": {"desc": "终端录屏", "category": "util", "level": "low"},
}

# 小弟角色与推荐skill映射
ROLE_SKILL_MAPPING = {
    "fast_executor": {
        "primary": ["web_search", "web_fetch", "fd_find", "bat_cat"],
        "recommended": ["agent_reach", "browser", "summarize"],
        "reason": "需要快速获取和处理信息"
    },
    "data_collector": {
        "primary": ["web_search", "web_fetch", "agent_reach", "fd_find"],
        "recommended": ["web_intelligence", "browser", "github", "summarize"],
        "reason": "需要从多个来源收集数据"
    },
    "content_generator": {
        "primary": ["summarize", "vestige", "bat_cat"],
        "recommended": ["web_search", "agent_reach", "local_whisper", "vhs_recorder"],
        "reason": "需要生成和整理内容"
    },
    "api_caller": {
        "primary": ["github", "feishu_doc", "feishu_wiki", "agent_reach"],
        "recommended": ["web_fetch", "docker_essentials", "browser"],
        "reason": "需要调用外部API和服务"
    },
    "monitor": {
        "primary": ["fd_find", "bat_cat", "docker_essentials"],
        "recommended": ["web_search", "github", "agent_reach", "skill_creator"],
        "reason": "需要监控系统状态和收集信息"
    },
    "deep_analyzer": {
        "primary": ["agentlens", "vestige", "summarize", "web_intelligence"],
        "recommended": ["browser", "agent_reach", "local_whisper", "tdd_guide"],
        "reason": "需要深度分析和知识管理"
    },
    "code_reviewer": {
        "primary": ["github", "agentlens", "tdd_guide", "docker_essentials"],
        "recommended": ["skill_creator", "web_search", "browser", "bat_cat"],
        "reason": "需要代码分析和测试"
    },
    "complex_solver": {
        "primary": ["agentlens", "vestige", "web_intelligence", "summarize"],
        "recommended": ["browser", "agent_reach", "skill_creator", "tdd_guide"],
        "reason": "需要解决复杂问题和多维度分析"
    },
    "strategy_planner": {
        "primary": ["vestige", "summarize", "agent_reach", "web_intelligence"],
        "recommended": ["github", "browser", "moltbook", "obsidian"],
        "reason": "需要信息收集和知识整理"
    },
    "quality_assurance": {
        "primary": ["tdd_guide", "docker_essentials", "bat_cat", "fd_find"],
        "recommended": ["skill_creator", "agentlens", "browser", "vhs_recorder"],
        "reason": "需要测试、验证和质量检查"
    },
}

class SkillRecommendationSystem:
    """Skill推荐系统"""
    
    def __init__(self):
        self.base_dir = Path("/root/.openclaw/workspace/nanobots")
    
    def get_node_info(self, node_id: str) -> dict:
        """获取节点信息"""
        config_file = self.base_dir / node_id.lower() / "config" / "identity.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return {}
    
    def get_installed_skills(self, node_id: str) -> List[str]:
        """获取已安装skill"""
        security_file = self.base_dir / node_id.lower() / "config" / "security.json"
        if security_file.exists():
            with open(security_file) as f:
                data = json.load(f)
                return data.get("installed_skills", [])
        return []
    
    def analyze_node_needs(self, node_id: str) -> dict:
        """分析节点需求"""
        info = self.get_node_info(node_id)
        role = info.get("role", "unknown")
        installed = self.get_installed_skills(node_id)
        
        mapping = ROLE_SKILL_MAPPING.get(role, {})
        primary = mapping.get("primary", [])
        recommended = mapping.get("recommended", [])
        reason = mapping.get("reason", "")
        
        # 计算缺口
        missing_primary = [s for s in primary if s not in installed]
        missing_recommended = [s for s in recommended if s not in installed]
        
        return {
            "node_id": node_id,
            "role": role,
            "capabilities": info.get("capabilities", []),
            "reason": reason,
            "installed": installed,
            "missing_primary": missing_primary,
            "missing_recommended": missing_recommended,
            "recommended_install": missing_primary[:2] + missing_recommended[:2]
        }
    
    def generate_recommendation_report(self) -> str:
        """生成推荐报告"""
        nodes = [f"NB{i:02d}" for i in range(1, 11)]
        
        report = []
        report.append("=" * 70)
        report.append("🧠 神经中枢 - Skill需求分析报告")
        report.append("=" * 70)
        report.append("")
        
        all_recommendations = []
        
        for node_id in nodes:
            analysis = self.analyze_node_needs(node_id)
            
            report.append(f"\n🤖 {node_id} [{analysis['role']}]")
            report.append(f"   能力: {', '.join(analysis['capabilities'][:3])}")
            report.append(f"   已安装: {len(analysis['installed'])}个 - {', '.join(analysis['installed'])}")
            
            if analysis['missing_primary']:
                report.append(f"   🔴 急需: {', '.join(analysis['missing_primary'])}")
            
            if analysis['missing_recommended']:
                report.append(f"   🟡 推荐: {', '.join(analysis['missing_recommended'][:3])}")
            
            if analysis['recommended_install']:
                report.append(f"   💡 建议安装: {', '.join(analysis['recommended_install'])}")
                all_recommendations.extend([(node_id, skill) for skill in analysis['recommended_install']])
            
            report.append("")
        
        report.append("=" * 70)
        report.append("📋 汇总安装建议")
        report.append("=" * 70)
        
        # 按skill分组
        skill_nodes = {}
        for node_id, skill in all_recommendations:
            if skill not in skill_nodes:
                skill_nodes[skill] = []
            skill_nodes[skill].append(node_id)
        
        for skill, nodes in sorted(skill_nodes.items(), key=lambda x: len(x[1]), reverse=True):
            info = SKILL_LIBRARY.get(skill, {})
            report.append(f"\n📦 {skill}")
            report.append(f"   描述: {info.get('desc', '')}")
            report.append(f"   推荐节点: {', '.join(nodes)}")
            report.append(f"   风险: {info.get('level', 'unknown')}")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def get_batch_install_commands(self) -> List[str]:
        """生成批量安装命令"""
        nodes = [f"NB{i:02d}" for i in range(1, 11)]
        commands = []
        
        for node_id in nodes:
            analysis = self.analyze_node_needs(node_id)
            for skill in analysis['recommended_install'][:2]:  # 每个节点先装2个最需要的
                commands.append(f"./scripts/cc-node install {node_id} {skill}")
        
        return commands

def main():
    """主函数"""
    system = SkillRecommendationSystem()
    
    # 生成报告
    report = system.generate_recommendation_report()
    print(report)
    
    # 生成安装命令
    print("\n" + "=" * 70)
    print("🔧 批量安装命令 (每个节点优先安装2个skill)")
    print("=" * 70)
    print("")
    
    commands = system.get_batch_install_commands()
    for cmd in commands[:10]:  # 显示前10个
        print(cmd)
    
    if len(commands) > 10:
        print(f"... 还有 {len(commands) - 10} 个命令")
    
    print("")
    print("=" * 70)
    print("💡 边界扩展能力推荐:")
    print("=" * 70)
    print("  • agent_reach - YouTube/Twitter/Reddit/GitHub/Boss直聘等访问")
    print("  • browser - 浏览器自动化，绕过反爬")
    print("  • web_intelligence - 网页智能分析")
    print("  • github - GitHub深度操作")
    print("  • agentlens - 代码库分析导航")
    print("=" * 70)

if __name__ == "__main__":
    main()
