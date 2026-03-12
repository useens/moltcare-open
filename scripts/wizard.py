#!/usr/bin/env python3
"""
MoltCare Wizard - 交互式配置向导
引导新用户完成初始配置
"""

import sys
import os
from pathlib import Path

# 颜色定义
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

def print_step(step_num, total, text):
    print(f"{Colors.CYAN}[{step_num}/{total}]{Colors.ENDC} {Colors.BOLD}{text}{Colors.ENDC}\n")

def ask_question(question, default=None, options=None):
    """提问并获取用户输入"""
    if options:
        print(f"{Colors.BLUE}?{Colors.ENDC} {question}")
        for i, opt in enumerate(options, 1):
            marker = "→" if opt == default else " "
            print(f"  {marker} {i}. {opt}")
        while True:
            try:
                choice = input(f"\n选择 (1-{len(options)}): ").strip()
                if not choice and default:
                    return default
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]
            except ValueError:
                pass
            print(f"{Colors.WARNING}请输入有效的选项编号{Colors.ENDC}")
    else:
        prompt = f"{Colors.BLUE}?{Colors.ENDC} {question}"
        if default:
            prompt += f" [{default}]"
        prompt += ": "
        
        answer = input(prompt).strip()
        return answer if answer else default

def run_wizard():
    """运行配置向导"""
    print_header("🦞 MoltCare 配置向导")
    
    print(f"{Colors.CYAN}欢迎使用 MoltCare！让我帮你快速配置 Agent。{Colors.ENDC}")
    print("这个向导会帮你设置：")
    print("  • 用户基本信息")
    print("  • 沟通偏好")
    print("  • 自动化级别")
    print("")
    
    input(f"按 Enter 开始...")
    
    # 收集配置
    config = {}
    
    # Step 1: 基本信息
    print_step(1, 4, "基本信息")
    config['user_name'] = ask_question("怎么称呼你？", "用户")
    config['user_role'] = ask_question("你的身份/职业是？", "开发者")
    config['tech_level'] = ask_question(
        "你的技术水平？",
        "中级",
        ["初级", "中级", "高级", "专家"]
    )
    
    # Step 2: 沟通偏好
    print_step(2, 4, "沟通偏好")
    config['detail_level'] = ask_question(
        "你喜欢什么样的回复详细程度？",
        "适中",
        ["简洁", "适中", "详细"]
    )
    config['tone'] = ask_question(
        "你喜欢什么样的语气？",
        "友好",
        ["正式", "友好", "随意"]
    )
    config['output_format'] = ask_question(
        "你喜欢什么输出格式？",
        "混合",
        ["文本", "表格", "代码", "混合"]
    )
    
    # Step 3: 自动化级别
    print_step(3, 4, "自动化设置")
    print(f"{Colors.CYAN}风险等级说明：{Colors.ENDC}")
    print("  L1-L3: 本地文件操作、代码编辑")
    print("  L4-L6: 网络请求、数据删除、外部服务")
    print("")
    
    config['l1_action'] = ask_question(
        "低风险操作 (L1-L3) 应该？",
        "自动执行",
        ["自动执行", "提示后执行"]
    )
    config['l4_action'] = ask_question(
        "高风险操作 (L4-L6) 应该？",
        "必须确认",
        ["提示后执行", "必须确认"]
    )
    
    # Step 4: 确认
    print_step(4, 4, "确认配置")
    print(f"{Colors.GREEN}你的配置：{Colors.ENDC}\n")
    print(f"  称呼: {config['user_name']}")
    print(f"  身份: {config['user_role']}")
    print(f"  技术水平: {config['tech_level']}")
    print(f"  回复详细程度: {config['detail_level']}")
    print(f"  语气: {config['tone']}")
    print(f"  输出格式: {config['output_format']}")
    print(f"  低风险操作: {config['l1_action']}")
    print(f"  高风险操作: {config['l4_action']}")
    print("")
    
    confirm = ask_question("保存这个配置？", "是", ["是", "否"])
    
    if confirm == "是":
        # 保存配置到 USER.md
        save_config(config)
        print(f"\n{Colors.GREEN}✓ 配置已保存！{Colors.ENDC}")
        print(f"\n你可以随时编辑 ~/.openclaw/workspace/USER.md 修改配置")
    else:
        print(f"\n{Colors.WARNING}配置已取消{Colors.ENDC}")

def save_config(config):
    """保存配置到 USER.md"""
    user_md_path = Path.home() / ".openclaw/workspace/USER.md"
    
    if not user_md_path.exists():
        print(f"{Colors.WARNING}警告: USER.md 不存在，请先运行 'moltcare apply foundation'{Colors.ENDC}")
        return
    
    # 读取现有内容
    content = user_md_path.read_text(encoding='utf-8')
    
    # 替换变量
    replacements = {
        '{{USER_NAME}}': config['user_name'],
        '{{USER_ROLE}}': config['user_role'],
        '{{TECH_LEVEL}}': config['tech_level'],
        '{{DETAIL_LEVEL}}': config['detail_level'],
        '{{TONE}}': config['tone'],
        '{{OUTPUT_FORMAT}}': config['output_format'],
        '{{L1_ACTION}}': config['l1_action'],
        '{{L4_ACTION}}': config['l4_action'],
    }
    
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    
    # 写回文件
    user_md_path.write_text(content, encoding='utf-8')

if __name__ == '__main__':
    try:
        run_wizard()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}向导已取消{Colors.ENDC}")
        sys.exit(1)
