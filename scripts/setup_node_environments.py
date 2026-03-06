#!/usr/bin/env python3
"""
Command Center - Node Environment Setup
为10个小弟创建隔离执行环境

功能:
- 每个小弟独立工作目录
- 独立skill目录
- 独立配置文件
- 安全沙箱环境
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

# 基础路径
BASE_DIR = Path("/root/.openclaw/workspace/nanobots")
CC_DIR = Path("/root/.openclaw/workspace")

# 10个小弟配置
NODES = [
    {"id": "NB01", "model": "step", "role": "fast_executor", "port": 18801},
    {"id": "NB02", "model": "step", "role": "data_collector", "port": 18802},
    {"id": "NB03", "model": "step", "role": "content_generator", "port": 18803},
    {"id": "NB04", "model": "step", "role": "api_caller", "port": 18804},
    {"id": "NB05", "model": "step", "role": "monitor", "port": 18805},
    {"id": "NB06", "model": "ds", "role": "deep_analyzer", "port": 18806},
    {"id": "NB07", "model": "ds", "role": "code_reviewer", "port": 18807},
    {"id": "NB08", "model": "ds", "role": "complex_solver", "port": 18808},
    {"id": "NB09", "model": "ds", "role": "strategy_planner", "port": 18809},
    {"id": "NB10", "model": "ds", "role": "quality_assurance", "port": 18810},
]

# 允许安装的skill白名单
ALLOWED_SKILLS = {
    "web_search": {
        "description": "网络搜索",
        "source": "builtin",
        "risk_level": "low"
    },
    "web_fetch": {
        "description": "网页内容获取",
        "source": "builtin",
        "risk_level": "low"
    },
    "github": {
        "description": "GitHub操作",
        "source": "builtin",
        "risk_level": "low"
    },
    "obsidian": {
        "description": "Obsidian笔记管理",
        "source": "local",
        "risk_level": "low"
    },
    "weather": {
        "description": "天气查询",
        "source": "builtin",
        "risk_level": "low"
    },
    "video_frames": {
        "description": "视频帧提取",
        "source": "local",
        "risk_level": "low"
    },
    "summarize": {
        "description": "内容摘要",
        "source": "local",
        "risk_level": "low"
    },
    "web_intelligence": {
        "description": "网页智能分析",
        "source": "local",
        "risk_level": "medium"
    },
    "agent_reach": {
        "description": "Agent Reach网络访问",
        "source": "local",
        "risk_level": "medium"
    },
    "browser": {
        "description": "浏览器自动化",
        "source": "local",
        "risk_level": "medium"
    },
    "docker_essentials": {
        "description": "Docker基础操作",
        "source": "local",
        "risk_level": "medium"
    },
    "fd_find": {
        "description": "文件查找",
        "source": "local",
        "risk_level": "low"
    },
    "bat_cat": {
        "description": "增强版cat",
        "source": "local",
        "risk_level": "low"
    },
}

# 禁止的命令
FORBIDDEN_COMMANDS = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf /root",
    "mkfs",
    "dd if=/dev/zero",
    "fdisk",
    "format",
    "> /dev/sda",
    "shutdown",
    "reboot",
    "poweroff",
    "kill -9 1",
    "chmod -R 777 /",
    "curl *| sh",
    "wget *| sh",
]

def create_node_environment(node: dict):
    """为单个节点创建环境"""
    node_id = node["id"]
    node_dir = BASE_DIR / node_id.lower()
    
    print(f"🚀 创建 {node_id} 环境...")
    
    # 创建目录结构
    dirs = [
        node_dir,
        node_dir / "skills",
        node_dir / "workspace",
        node_dir / "data",
        node_dir / "logs",
        node_dir / "tmp",
        node_dir / "config",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    # 创建安全策略文件
    security_config = {
        "node_id": node_id,
        "model": node["model"],
        "role": node["role"],
        "created_at": datetime.now().isoformat(),
        "security_policy": {
            "allowed_skills": list(ALLOWED_SKILLS.keys()),
            "forbidden_commands": FORBIDDEN_COMMANDS,
            "read_paths": [
                str(node_dir / "**"),
                "/tmp/**",
            ],
            "write_paths": [
                str(node_dir / "workspace/**"),
                str(node_dir / "data/**"),
                str(node_dir / "tmp/**"),
                str(node_dir / "logs/**"),
            ],
            "exec_whitelist": [
                "python3", "pip", "node", "npm",
                "curl", "wget", "git",
                "grep", "awk", "sed", "cat", "head", "tail",
                "ls", "cd", "pwd", "echo", "mkdir", "touch",
                "tar", "zip", "unzip", "gzip",
                "ffmpeg", "ffprobe",
            ],
            "network": {
                "outbound": "allow",
                "inbound": "localhost_only"
            }
        },
        "installed_skills": [],
        "task_stats": {
            "total": 0,
            "success": 0,
            "failed": 0
        }
    }
    
    with open(node_dir / "config" / "security.json", "w") as f:
        json.dump(security_config, f, indent=2)
    
    # 创建节点身份文件
    identity = {
        "id": node_id,
        "name": f"Nanobot {node_id}",
        "model": node["model"],
        "role": node["role"],
        "port": node["port"],
        "capabilities": get_capabilities(node["role"]),
        "reporting_to": "CommandCenter",
        "status": "active"
    }
    
    with open(node_dir / "config" / "identity.json", "w") as f:
        json.dump(identity, f, indent=2)
    
    # 创建技能安装审计日志
    with open(node_dir / "logs" / "skill_audit.log", "w") as f:
        f.write(f"# {node_id} Skill Installation Audit Log\n")
        f.write(f"# Created: {datetime.now().isoformat()}\n\n")
    
    # 创建任务执行日志
    with open(node_dir / "logs" / "task_execution.log", "w") as f:
        f.write(f"# {node_id} Task Execution Log\n")
        f.write(f"# Created: {datetime.now().isoformat()}\n\n")
    
    print(f"   ✅ {node_id} 环境创建完成")
    print(f"      目录: {node_dir}")
    print(f"      角色: {node['role']}")
    print(f"      安全策略: 已配置")
    
    return node_dir

def get_capabilities(role: str) -> list:
    """根据角色获取能力列表"""
    capabilities = {
        "fast_executor": ["quick_tasks", "simple_queries", "status_checks"],
        "data_collector": ["web_scraping", "api_calls", "data_download"],
        "content_generator": ["text_generation", "template_filling", "formatting"],
        "api_caller": ["external_apis", "webhooks", "integrations"],
        "monitor": ["health_checks", "status_monitoring", "alerts"],
        "deep_analyzer": ["complex_analysis", "problem_solving", "research"],
        "code_reviewer": ["code_analysis", "bug_detection", "refactoring"],
        "complex_solver": ["multi_step_tasks", "algorithm_design", "optimization"],
        "strategy_planner": ["planning", "strategy", "architecture_design"],
        "quality_assurance": ["testing", "validation", "quality_checks"],
    }
    return capabilities.get(role, ["general_tasks"])

def create_allowed_skills_manifest():
    """创建允许安装的skill清单"""
    manifest_path = CC_DIR / "config" / "allowed_skills.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, "w") as f:
        json.dump(ALLOWED_SKILLS, f, indent=2)
    
    print(f"\n📋 允许安装的skill清单已创建: {manifest_path}")
    print(f"   共 {len(ALLOWED_SKILLS)} 个skill")

def main():
    print("=" * 70)
    print("🤖 创建10个小弟的隔离执行环境")
    print("=" * 70)
    print()
    
    # 创建基础目录
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 为每个节点创建环境
    for node in NODES:
        create_node_environment(node)
        print()
    
    # 创建skill清单
    create_allowed_skills_manifest()
    
    print()
    print("=" * 70)
    print("✅ 所有小弟环境创建完成!")
    print("=" * 70)
    print()
    print("📁 目录结构:")
    print(f"   {BASE_DIR}/")
    for node in NODES:
        print(f"   ├── {node['id'].lower()}/")
        print(f"   │   ├── skills/      # 安装的skill")
        print(f"   │   ├── workspace/   # 工作目录")
        print(f"   │   ├── data/        # 数据文件")
        print(f"   │   ├── logs/        # 执行日志")
        print(f"   │   ├── tmp/         # 临时文件")
        print(f"   │   └── config/      # 配置文件")
    print()
    print("🔒 安全策略:")
    print(f"   - 允许安装 {len(ALLOWED_SKILLS)} 个skill")
    print(f"   - 禁止 {len(FORBIDDEN_COMMANDS)} 个危险命令")
    print(f"   - 每个小弟只能访问自己的工作目录")
    print()

if __name__ == "__main__":
    main()
