# UnifiedLogger 使用文档

## 概述

`UnifiedLogger` 是一个简化版的日志聚合系统，使用SQLite存储，支持基本查询功能。

## 数据库结构

```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,          -- 日志来源（如 upgrade-daemon, decision-engine）
    level TEXT NOT NULL,           -- 日志级别（INFO, WARN, ERROR等）
    message TEXT,                  -- 日志消息
    timestamp TEXT NOT NULL,       -- 时间戳（ISO 8601格式）
    extra_metadata TEXT,           -- 额外元数据（JSON格式）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_source ON logs(source);
CREATE INDEX idx_level ON logs(level);
CREATE INDEX idx_timestamp ON logs(timestamp);
```

## 基本使用

### 1. 初始化

```python
from core.unified_logger import UnifiedLogger

# 创建logger实例（默认路径：data/unified_logs.db）
logger = UnifiedLogger()

# 或指定自定义路径
logger = UnifiedLogger(db_path='/path/to/logs.db')
```

### 2. 写入日志

```python
# 基本日志
logger.log(
    source='my-app',
    level='INFO',
    message='系统正在启动'
)

# 带自定义时间戳
logger.log(
    source='my-app',
    level='WARN',
    message='内存使用率超过80%',
    timestamp='2026-02-19T15:00:00.000000'
)

# 带额外元数据
logger.log(
    source='my-app',
    level='ERROR',
    message='数据库连接失败',
    extra={'error_code': 500, 'retry_count': 3}
)
```

### 3. 查询日志

```python
# 查询所有日志（默认返回最近100条）
results = logger.query()

# 按来源查询
results = logger.query(source='upgrade-daemon')

# 按级别查询
results = logger.query(level='ERROR')

# 组合查询
results = logger.query(source='decision-engine', level='INFO', limit=50)

# 处理结果
for row in results:
    print(f"[{row['timestamp']}] [{row['level']}] {row['message']}")

# 解析额外元数据
import json
if row['extra_metadata']:
    extra = json.loads(row['extra_metadata'])
```

### 4. 时间范围查询

```python
# 按时间范围查询
start_time = '2026-02-19 10:00:00'
end_time = '2026-02-19 14:00:00'

results = logger.query_by_time_range(start_time, end_time)

# 按来源和时间范围组合查询
results = logger.query_by_time_range(
    start_time='2026-02-19 10:00:00',
    end_time='2026-02-19 14:00:00',
    source='unified-monitor'
)
```

### 5. 获取统计信息

```python
stats = logger.get_stats()

print(f"总记录数: {stats['total_count']}")
print(f"时间范围: {stats['time_range']['earliest']} 到 {stats['time_range']['latest']}")

# 按来源统计
for source, count in stats['by_source'].items():
    print(f"{source}: {count} 条")

# 按级别统计
for level, count in stats['by_level'].items():
    print(f"{level}: {count} 条")
```

### 6. 获取所有来源

```python
sources = logger.get_sources()
print(f"所有日志来源: {', '.join(sources)}")
```

### 7. 从文件迁移日志

```python
# 迁移单个日志文件
success, skip = logger.migrate_from_file(
    log_file='logs/myapp.log',
    source_name='myapp'
)
print(f"成功: {success}, 跳过: {skip}")

# 支持的日志格式：
# 格式1: [2026-02-19T02:00:00.156077] [INFO] message
# 格式2: [2026-02-19 10:46:20,672] INFO: message
```

### 8. 关闭连接

```python
# 使用完毕后关闭
logger.close()

# 或使用 with 语句（如果实现了上下文管理器）
# with UnifiedLogger() as logger:
#     logger.log('app', 'INFO', 'Message')
```

## 当前数据库状态

- **数据库路径**: `data/unified_logs.db`
- **文件大小**: 384KB
- **总记录数**: 1,977 条
- **日志来源**:
  - unified-monitor: 1,870 条
  - upgrade-daemon: 59 条
  - decision-engine: 44 条
  - test-source: 4 条

- **日志级别分布**:
  - INFO: 1,703 条
  - WARNING: 270 条
  - WARN: 3 条
  - ERROR: 1 条

- **时间范围**: 2026-02-18T12:15:39 到 2026-02-19T14:00:00

## 性能优化建议

1. **批量写入**: 大量日志时使用事务批量插入
2. **索引优化**: 按需添加复合索引
3. **定期归档**: 考虑按月创建不同的数据库文件
4. **清理测试数据**: 定期清理 test-source 等测试数据

## 扩展建议

1. 添加日志轮转功能
2. 实现实时写入接口
3. 添加日志导出功能（CSV, JSON）
4. 实现Web查询界面
5. 添加告警规则配置

## 故障排查

### 数据库锁定
- 确保正确关闭连接：`logger.close()`
- 避免多个进程同时写入

### 查询慢
- 检查索引是否正确创建
- 限制查询结果数量：使用 `limit` 参数

### 内存占用
- 大量日志查询时使用分页
- 考虑使用游标逐条处理
