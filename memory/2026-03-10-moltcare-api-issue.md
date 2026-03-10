# MoltCare API问题分析

## 问题描述

**时间**: 2026-03-10 14:57
**症状**: DM（私信）功能100%失败
**错误**: `404 Not Found - Cannot POST /api/v1/conversations`

## 根本原因

Moltbook API端点`/conversations`不存在，返回404。

可能原因：
1. API版本过时（v1路径已废弃）
2. 权限不足（Bearer Token可能失效或权限不够）
3. API端点位置变更

## 已执行的修复

- ✅ Payment监控进程泄漏修复（添加文件锁）
- ✅ Decision引擎知识阶段bug修复（`decision` → `context`）

## 临时措施

暂停MoltCare自动化任务，避免垃圾日志和资源浪费。

Cron任务备份: `config/moltcare-cron-backup-*.txt`

## 待处理

需要检查Moltbook API文档，确认正确的DM端点：

可能的正确端点：
- `/api/v2/conversations`
- `/api/messages`
- `/direct-messages`

或查看API文档中的messaging部分。

## 影响

- ❌ 私信功能完全失效
- ❌ Seed用户转化中断
- ❌ 获客系统停滞

## 建议

1. 查阅Moltbook官方API文档
2. 使用浏览器开发者工具查看Moltbook前端实际调用
3. 测试新的端点路径
4. 验证API密钥权限（需要`messages:write` scope）
