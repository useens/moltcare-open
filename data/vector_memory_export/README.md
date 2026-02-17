# 向量记忆导出说明

**最后导出**: Wed Feb 18 03:01:12 AM CST 2026
**原始位置**: data/vector_memory/

## 恢复流程

1. 从GitHub克隆代码仓库
2. 从备份恢复向量数据:
   

3. 验证向量记忆:
   python3 scripts/unified-monitor.py --component memory

## 注意事项
- 向量数据是二进制格式，不适合Git管理
- 通过Cron每天03:00自动备份到 /backups/local/
- 保留最近10个备份，超过的自动清理
