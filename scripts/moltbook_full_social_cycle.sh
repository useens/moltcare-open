#!/bin/bash
# Moltbook 真社交自动化系统启动脚本
# 全自动化监控 + AI回复 + 主动点赞

WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs"
mkdir -p $LOG_DIR

echo "========================================"
echo "🦞 Moltbook 真社交自动化系统 v2.0"
echo "========================================"
echo ""

# 1. 运行社交监控系统
echo "📊 步骤1: 监控新评论..."
cd $WORKSPACE
python3 scripts/moltbook_social_agent_v2.py >> $LOG_DIR/moltbook_social.log 2>&1
echo "   ✅ 监控完成"

# 2. 处理AI回复队列
echo ""
echo "🤖 步骤2: 生成并发送AI回复..."
python3 scripts/moltbook_ai_reply_processor.py >> $LOG_DIR/moltbook_ai_reply.log 2>&1
echo "   ✅ 回复处理完成"

# 3. 运行日常点赞任务
echo ""
echo "👍 步骤3: 发现高质量内容并点赞..."
python3 scripts/moltbook-daily-routine.py >> $LOG_DIR/moltbook_daily.log 2>&1
echo "   ✅ 点赞完成"

echo ""
echo "========================================"
echo "✅ 全周期完成: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
