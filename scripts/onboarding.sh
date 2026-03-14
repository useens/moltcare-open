#!/bin/bash
# MoltCare Onboarding Wizard
# 可选的首次配置引导

echo "🦞 MoltCare 配置向导"
echo "===================="
echo ""
echo "这个向导会帮助你配置 USER.md，让 Agent 更了解你。"
echo "随时按 Ctrl+C 跳过，之后可以手动编辑 USER.md"
echo ""

# 检查 USER.md 是否已配置
if grep -q "{{USER_NAME}}" ~/.openclaw/workspace/USER.md 2>/dev/null; then
    : # 未配置，继续
else
    echo "✅ USER.md 似乎已配置过。"
    read -p "是否重新配置？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo ""
echo "1️⃣  基本信息"
echo "------------"

read -p "你的名字/称呼: " name
read -p "你的职业/角色: " role
read -p "主要技术领域 (如: AI Agent, 后端开发): " domain

echo ""
echo "2️⃣  技术栈"
echo "---------"
read -p "常用编程语言: " languages
read -p "主要框架/工具: " frameworks

echo ""
echo "3️⃣  沟通偏好"
echo "-----------"
echo "详细程度:"
echo "  1) 极简 - 直接给结果"
echo "  2) 适中 - 简要说明"
echo "  3) 详细 - 完整解释"
read -p "选择 (1-3): " detail_level

case $detail_level in
    1) detail="极简" ;;
    2) detail="适中" ;;
    3) detail="详细" ;;
    *) detail="适中" ;;
esac

echo ""
echo "语气风格:"
echo "  1) 正式 - 专业严谨"
echo "  2) 友好 - 轻松自然"
echo "  3) 随意 - 像朋友聊天"
read -p "选择 (1-3): " tone_style

case $tone_style in
    1) tone="正式" ;;
    2) tone="友好" ;;
    3) tone="随意" ;;
    *) tone="友好" ;;
esac

echo ""
echo "技术深度:"
echo "  1) 概念 - 高层概述"
echo "  2) 实践 - 代码示例"
echo "  3) 深入 - 底层原理"
read -p "选择 (1-3): " tech_depth

case $tech_depth in
    1) depth="概念" ;;
    2) depth="实践" ;;
    3) depth="深入" ;;
    *) depth="实践" ;;
esac

echo ""
echo "4️⃣  决策偏好"
echo "-----------"
read -p "L4-L5风险操作是否需要确认? (Y/n): " confirm_l4
if [[ $confirm_l4 =~ ^[Nn]$ ]]; then
    confirm="false"
else
    confirm="true"
fi

# 生成 USER.md
cat > ~/.openclaw/workspace/USER.md << EOF
# USER.md - 用户画像 v2.3.3

> 👤 **OpenClaw 深度适配**

## 👤 基本信息

| 项目 | 内容 |
|------|------|
| **称呼** | ${name:-待填写} |
| **身份/角色** | ${role:-待填写} |
| **专业领域** | ${domain:-待填写} |
| **技术水平** | 中级 |

### 技术栈
- 语言：${languages:-待填写}
- 框架：${frameworks:-待填写}
- 工具：

## 💬 沟通偏好

| 维度 | 偏好 |
|------|------|
| **详细程度** | ${detail} |
| **语气** | ${tone} |
| **技术深度** | ${depth} |

### 特殊要求
- [ ] 重要决策前必须确认
- [ ] 代码审查要指出具体行号
- [ ] 复杂概念用类比解释

## ⚙️ 系统偏好

### 自动化级别
- L1-L3：自动执行
- L4-L5：$([[ $confirm == "true" ]] && echo "提示确认" || echo "自动执行")
- L6：必须确认

### 通知偏好
- [x] 重要提醒：内嵌
- [ ] 日常报告：禁用

## 🚫 约束与禁忌

### 明确禁止
- 

### 需要确认的操作
- [x] 删除文件
- [x] 修改配置
- [x] 提交代码

### 隐私边界
- 可访问：项目文件
- 不可访问：个人文档、凭证

## 📊 历史记录

### 重要交互
| 日期 | 事件 | Signal |
|------|------|--------|
| $(date +%Y-%m-%d) | 首次配置 | - |

### 偏好变更
| 日期 | 变更项 | 新值 |
|------|--------|------|
| | | |

## 🔗 相关文档

- [SOUL.md](SOUL.md) - Agent灵魂
- [AGENTS.md](AGENTS.md) - 操作手册

*配置时间: $(date)*
EOF

echo ""
echo "✅ 配置完成！"
echo "配置文件已保存到: ~/.openclaw/workspace/USER.md"
echo ""
echo "你可以随时手动编辑这个文件来调整偏好。"
echo ""

# 询问是否运行首次测试
read -p "是否测试一下 Agent 是否正常工作? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "💡 试试说: '你好，我是${name:-用户}'"
    echo "   Agent 应该会根据你的配置来回复。"
    echo ""
fi
