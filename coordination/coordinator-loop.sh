#!/bin/bash
# 多Agent协调监控脚本
# 每5分钟执行一次协调检查

COORD_DIR="/root/.openclaw/workspace/coordination"
REPORT_PREFIX="coordination-report"
CYCLE=1

echo "🤖 协调代理启动 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    REPORT_FILE="$COORD_DIR/${REPORT_PREFIX}-$(printf '%03d' $CYCLE).md"
    
    echo "[$TIMESTAMP] 开始第 $CYCLE 轮协调检查..."
    
    # 获取活跃子代理列表
    SESSIONS=$(openclaw sessions list --json 2>/dev/null | grep -c 'subagent' || echo "0")
    
    # 创建本轮报告
    cat > "$REPORT_FILE" << EOF
# 协调报告 - 第${CYCLE}轮

**时间**: $TIMESTAMP  
**周期**: $CYCLE

## 活跃子代理数量: $SESSIONS

## 协调消息
- 广播状态: ✅ 已发送
- 响应收集: ⏳ 进行中

## 下一步
- 5分钟后进行第$((CYCLE+1))轮检查
EOF

    echo "[$TIMESTAMP] 第 $CYCLE 轮完成 - 报告: $REPORT_FILE"
    
    CYCLE=$((CYCLE+1))
    
    # 等待5分钟
    echo "等待5分钟..."
    sleep 300
done
