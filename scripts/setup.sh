#!/bin/bash
# OpenClaw 初始化脚本
# 在新 Agent 上执行基础配置

echo "🚀 OpenClaw 初始化脚本"
echo "========================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 OpenClaw 是否安装
if ! command -v openclaw &> /dev/null; then
    echo -e "${YELLOW}⚠️  警告: openclaw 命令未找到${NC}"
    echo "   请确保 OpenClaw 已正确安装"
fi

# 创建工作目录结构
echo "📁 创建工作目录..."
mkdir -p ~/.openclaw/workspace/{memory,scripts,reports,docs}
mkdir -p ~/.openclaw/skills

echo -e "${GREEN}✓${NC} 工作目录已创建"

# 检查 MoltCare 配置
echo "🔧 检查 MoltCare 配置..."
if [ -f ~/.moltcare/config.yaml ]; then
    echo -e "${GREEN}✓${NC} MoltCare 已初始化"
else
    echo -e "${YELLOW}⚠️  警告: MoltCare 未初始化${NC}"
    echo "   运行: moltcare init"
fi

# 创建示例 MEMORY.md
echo "📝 创建 MEMORY.md 模板..."
cat > ~/.openclaw/workspace/MEMORY.md << 'EOF'
# MEMORY.md - 系统记忆

## 用户档案
- **称呼**: 待填写
- **时区**: Asia/Shanghai
- **语言**: 中文

## 重要偏好
- 工作模式: 全自主运行
- 决策风格: 结果导向
- 沟通偏好: 简洁高效

## 当前项目
- MoltCare: Agent 智能提升开源项目

## 定期任务
- [ ] 每日系统检查
- [ ] 每周记忆整理
EOF

echo -e "${GREEN}✓${NC} MEMORY.md 已创建"

# 创建示例 USER.md
echo "📝 创建 USER.md 模板..."
cat > ~/.openclaw/workspace/USER.md << 'EOF'
# USER.md - 用户档案

## 基本信息
| 项目 | 内容 |
|------|------|
| 称呼 | 待填写 |
| 职业 | 待填写 |
| 时区 | GMT+8 |

## 工作偏好
- **授权级别**: 全权委托
- **汇报频率**: 仅异常汇报
- **决策风格**: 自主决策

## 技术栈
- 主要: Python, TypeScript
- 关注: AI Agent, 自动化
EOF

echo -e "${GREEN}✓${NC} USER.md 已创建"

# 建议后续步骤
echo ""
echo "🎉 初始化完成！"
echo ""
echo "建议后续步骤:"
echo "  1. 编辑 ~/.openclaw/workspace/USER.md 填写个人信息"
echo "  2. 编辑 ~/.openclaw/workspace/MEMORY.md 记录重要事项"
echo "  3. 运行 'moltcare list' 查看可用智能包"
echo "  4. 运行 'openclaw skills list' 查看已安装技能"
echo ""
