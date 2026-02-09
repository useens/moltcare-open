#!/bin/bash
# 批量安全检查 ClawHub 技能

echo "🔒 ClawHub 技能安全检查报告"
echo "=============================="
echo ""

SKILLS_DIR="/root/.openclaw/workspace/skills"
TOTAL=0
SAFE=0
WARNING=0
DANGER=0

for skill_dir in "$SKILLS_DIR"/*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        TOTAL=$((TOTAL + 1))
        
        echo "📦 检查: $skill_name"
        
        # 检查 SKILL.md 是否存在
        if [ ! -f "$skill_dir/SKILL.md" ]; then
            echo "   ⚠️  无 SKILL.md 文件"
            WARNING=$((WARNING + 1))
            continue
        fi
        
        # 读取 SKILL.md 内容
        skill_content=$(cat "$skill_dir/SKILL.md" 2>/dev/null)
        
        # 风险检查
        risks=()
        
        # 检查网络请求
        if echo "$skill_content" | grep -qiE "(fetch|axios|request|http|curl)"; then
            risks+=("网络请求")
        fi
        
        # 检查敏感文件访问
        if echo "$skill_content" | grep -qE "(\.env|\.ssh|\.aws|credentials)"; then
            risks+=("敏感文件")
            DANGER=$((DANGER + 1))
        fi
        
        # 检查外部下载
        if echo "$skill_content" | grep -qiE "(download|wget|curl.*-o|fetch.*blob)"; then
            risks+=("外部下载")
            DANGER=$((DANGER + 1))
        fi
        
        # 检查执行权限
        if echo "$skill_content" | grep -qiE "(chmod.*\+x|exec|spawn|eval)"; then
            risks+=("执行操作")
        fi
        
        # 检查 ClawHub 可疑模式
        if echo "$skill_content" | grep -qiE "(api\.clawhub|clawhub\.io|external.*url)"; then
            risks+=("可疑API")
        fi
        
        # 输出结果
        if [ ${#risks[@]} -eq 0 ]; then
            echo "   ✅ 未发现明显风险"
            SAFE=$((SAFE + 1))
        else
            echo "   ⚠️  发现: ${risks[*]}"
            if [[ " ${risks[*]} " =~ "敏感文件" ]] || [[ " ${risks[*]} " =~ "外部下载" ]]; then
                DANGER=$((DANGER + 1))
            else
                WARNING=$((WARNING + 1))
            fi
        fi
        
        # 检查 package.json 依赖
        if [ -f "$skill_dir/package.json" ]; then
            deps=$(cat "$skill_dir/package.json" | grep -c '"dependencies"' 2>/dev/null || echo "0")
            if [ "$deps" -gt 0 ]; then
                echo "   📦 有外部依赖"
            fi
        fi
        
        echo ""
    fi
done

echo "=============================="
echo "📊 检查总结"
echo "   总计: $TOTAL"
echo "   ✅ 安全: $SAFE"
echo "   ⚠️  警告: $WARNING"
echo "   🚨 危险: $DANGER"
echo ""

if [ $DANGER -gt 0 ]; then
    echo "🔴 发现高风险技能，建议立即审查！"
else
    echo "🟢 当前技能整体安全"
fi
