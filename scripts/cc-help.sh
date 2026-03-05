#!/bin/bash
# Nanobot Command Center - Quick Commands
# 快捷命令参考

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           🤖 NANOBOT COMMAND CENTER - 快捷命令             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 系统状态"
echo "  cc-p0.sh status       查看P0系统完整状态"
echo "  cc-p0.sh start        启动P0系统"
echo "  cc-p0.sh stop         停止P0系统"
echo ""

echo "🎯 智能委托 (自动路由)"
echo "  delegate '任务内容'              自动决定交给小弟还是自己"
echo "  delegate '任务' --to NB01        指定NB01处理"
echo "  delegate '任务' --broadcast      广播到所有10个节点"
echo "  delegate '任务' --self           强制自己处理(Multi-Agent)"
echo ""

echo "📋 任务队列管理"
echo "  cc-p0.sh process 10              手动处理10个队列任务"
echo "  nb_relay_v2.py queue             查看待处理队列"
echo "  nb_relay_v2.py stats             查看系统统计"
echo ""

echo "🤖 直接控制节点"
echo "  nb-relay.py send NB01 '消息'     直接发送消息到NB01"
echo "  nb-relay.py broadcast '消息'     广播到所有节点"
echo "  nb-cluster.sh status             查看节点集群状态"
echo ""

echo "📡 飞书通知"
echo "  feishu-sync.py high node.NB01 '节点NB01任务完成'"
echo "  feishu-sync.py critical system '系统告警'"
echo ""

echo "💡 使用建议"
echo "  1. 日常简单任务用 'delegate' 自动路由"
echo "  2. 重要决策用 'delegate --self' 自己深度思考"
echo "  3. 批量任务用 'delegate --broadcast' 分发到所有节点"
echo "  4. 定期用 'cc-p0.sh status' 检查系统健康"
echo ""
