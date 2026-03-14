#!/bin/bash
# MoltCare 安装后引导
# 非强制，可选配置

echo ""
echo "🦞 MoltCare Foundation Pack 已安装"
echo "===================================="
echo ""
echo "快速开始:"
echo ""
echo "  1. 配置你的偏好 (推荐)"
echo "     $ ~/.openclaw/workspace/scripts/onboarding.sh"
echo ""
echo "  2. 手动编辑 USER.md"
echo "     $ nano ~/.openclaw/workspace/USER.md"
echo ""
echo "  3. 直接开始使用"
echo "     发送消息给你的 Agent，它会读取默认配置工作"
echo ""
echo "文档:"
echo "  - SOUL.md    - Agent 的灵魂定义"
echo "  - AGENTS.md  - 操作手册"
echo "  - USER.md    - 你的用户画像"
echo ""
echo "配置是可选的，Agent 在不了解你时也能正常工作。"
echo "配置后 Agent 会更了解你的偏好，提供更好的服务。"
echo ""

# 询问是否现在配置
read -t 10 -p "是否现在运行配置向导? (y/N, 10秒后自动跳过) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    ~/.openclaw/workspace/scripts/onboarding.sh
else
    echo "跳过配置。随时运行 ~/.openclaw/workspace/scripts/onboarding.sh 来配置。"
fi
