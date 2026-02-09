#!/bin/bash
# 影响者监控脚本 - 每日8点执行
# 监控安全专家、技术领袖、社区动态

set -e

WORKSPACE="/root/.openclaw/workspace"
INTEL_DIR="$WORKSPACE/memory/intel"
DATE=$(date +%Y-%m-%d)

echo "=== 影响者监控开始 $DATE ==="

# 安全监控目标
# 注意: 实际X/Twitter API需要认证，这里使用Nitter实例或其他公开API

# 1. ClawHub官方安全公告
echo "[1/4] 检查 ClawHub 安全公告..."
curl -s "https://api.github.com/repos/openclaw/openclaw/issues?labels=security&state=open&per_page=5" > "$INTEL_DIR/clawhub_security_${DATE}.json" 2>/dev/null || echo "  - GitHub API 失败"

# 2. OpenClaw releases
echo "[2/4] 检查 OpenClaw 新版本..."
curl -s "https://api.github.com/repos/openclaw/openclaw/releases/latest" > "$INTEL_DIR/openclaw_release_${DATE}.json" 2>/dev/null || echo "  - 版本检查失败"

# 3. 技能仓库更新
echo "[3/4] 检查技能仓库更新..."
curl -s "https://api.github.com/repos/VoltAgent/awesome-openclaw-skills/commits?per_page=5" > "$INTEL_DIR/skills_repo_${DATE}.json" 2>/dev/null || echo "  - 技能仓库检查失败"

# 4. 生成监控摘要
echo "[4/4] 生成监控摘要..."
cat > "$INTEL_DIR/influencer_digest_${DATE}.md" << EOF
# 影响者监控日报 - $DATE

## 监控对象

### 安全情报
- [ ] @evilcos X/Twitter (需API)
- [x] OpenClaw GitHub Security Issues
- [x] ClawHub 官方动态

### 技术前沿
- [x] OpenClaw 最新Release
- [x] 技能仓库更新
- [ ] Discord社区热门话题 (需API)

### 技能生态
- [x] awesome-openclaw-skills 提交记录
- [ ] ClawHub新技能发布 (需爬取)

## 数据文件
$(ls -la $INTEL_DIR/*_${DATE}.json 2>/dev/null | wc -l) 个JSON文件

## 待分析
等待agent检查：
1. 新安全漏洞披露
2. OpenClaw版本更新
3. 新技能发布
4. 社区最佳实践变化

---
*安全监控是持续过程*
EOF

echo "=== 监控完成 ==="
ls -lh $INTEL_DIR/*_${DATE}.json 2>/dev/null || echo "警告: 部分数据源失败"
