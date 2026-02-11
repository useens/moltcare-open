#!/bin/bash
#
# 技能注册工具
# 用于记录新技能的安装状态到快照文件
#

SKILL_SNAPSHOT="${HOME}/.openclaw/workspace/memory/modules/skill-state-snapshot.md"

echo "🛠️  林林技能注册工具"
echo "===================="
echo ""
echo "此工具帮助记录技能状态，确保复活时能正确恢复"
echo ""

# 检查快照文件
if [ ! -f "$SKILL_SNAPSHOT" ]; then
    echo "❌ 技能快照文件不存在: $SKILL_SNAPSHOT"
    exit 1
fi

# 交互式输入
echo "请输入技能信息:"
echo ""

read -rp "技能名称 (如: browser-cli): " skill_name
read -rp "安装位置 (local/tool/global): " install_location
read -rp "安装类型 (npm/pip/system/binary): " install_type
read -rp "是否关键技能 (y/N): " is_critical

echo ""
echo "依赖列表 (每行一个，空行结束):"
deps=()
while true; do
    read -rp "依赖: " dep
    [ -z "$dep" ] && break
    deps+=("$dep")
done

echo ""
echo "系统依赖 (如: chromium, ffmpeg，空行结束):"
sys_deps=()
while true; do
    read -rp "系统依赖: " sys_dep
    [ -z "$sys_dep" ] && break
    sys_deps+=("$sys_dep")
done

echo ""
read -rp "恢复命令 (如: npm install && npm link): " restore_cmd
read -rp "验证命令 (如: browser --version): " verify_cmd
read -rp "备注: " note

# 确定关键性标记
critical="false"
[ "$is_critical" = "y" ] && critical="true"

# 构建YAML内容
yaml_entry="
### $(date +%Y) 新增: $skill_name

\`\`\`yaml
name: $skill_name
location: ~/.openclaw/workspace/
install_type: $install_type
package_manager: $install_type

dependencies:"

for dep in "${deps[@]}"; do
    yaml_entry="$yaml_entry
  - $dep"
done

yaml_entry="$yaml_entry
  
system_deps:"

for sys_dep in "${sys_deps[@]}"; do
    yaml_entry="$yaml_entry
  - name: $sys_dep"
done

yaml_entry="$yaml_entry
  
restore_steps:
  - \"$restore_cmd\"
  
verify_cmd: \"$verify_cmd\"
critical: $critical
note: \"$note\"
\`\`\`
"

# 追加到快照文件
echo -e "$yaml_entry" >> "$SKILL_SNAPSHOT"

echo ""
echo "✅ 技能 '$skill_name' 已注册到快照文件"
echo "📁 位置: $SKILL_SNAPSHOT"
echo ""
echo "下次复活时将自动恢复此技能"
