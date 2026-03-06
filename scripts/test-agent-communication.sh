#!/bin/bash
# 测试AI Agent群聊通信系统

echo "🧪 测试AI Agent群聊通信系统"
echo "=============================="
echo ""

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub

# 1. 神经中枢发送群聊消息
echo "1️⃣ 神经中枢发送群聊消息..."
cat >> $HUB_DIR/group_chat.jsonl <> $HUB_DIR/group_chat.jsonl | wc -l
echo "  条群聊消息"

echo ""
echo "3️⃣ 最新群聊消息:"
tail -3 $HUB_DIR/group_chat.jsonl | python3 -m json.tool 2>/dev/null | grep -E '"from"|"content"' | head -10

echo ""
echo "4️⃣ 私信测试:"
# 神经中枢给nanobot-1发私信
cat >> $HUB_DIR/private_chat/nanobot-1_inbox.jsonl <> $HUB_DIR/private_chat/nanobot-1_inbox.jsonl | wc -l
echo ""
echo "nanobot-1收件箱最新消息:"
tail -1 $HUB_DIR/private_chat/nanobot-1_inbox.jsonl | python3 -m json.tool 2>/dev/null | grep -E '"from"|"content"|"to"'

echo ""
echo "✅ 通信测试完成"
echo ""
echo "💡 说明:"
echo "  - 群聊消息已发送"
echo "  - 私信已发送给nanobot-1"
echo "  - Agent会定期检查新消息并回复"
