# 统一日志系统文档

## 概述

统一日志系统使用SQLite存储多源日志，提供统一的查询接口和自动轮转功能。

## 数据库结构

### 表结构: `logs`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| timestamp | TEXT | 日志时间 (ISO格式) |
| source | TEXT | 日志来源 |
| level | TEXT | 日志级别 |
| level_value | INTEGER | 级别数值 (DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50) |
| message | TEXT | 日志内容 |
| metadata | TEXT | JSON格式的元数据 |
| created_at | TEXT | 记录创建时间 |

### 索引

- `idx_timestamp` - 按时间查询
- `idx_source` - 按来源查询
- `idx_level` - 按级别查询
- `idx_level_value` - 按级别数值查询
- `idx_source_time` - 按来源和时间联合查询

## 查询接口

### 命令行工具

```bash
# 查看统计信息
python3 core/logging/log_query.py stats

# 查询最近1小时的ERROR级别日志
python3 core/logging/log_query.py query --last 1h --min-level ERROR

# 查询特定来源的日志
python3 core/logging/log_query.py query --source diagnosis --limit 20

# 按关键词搜索
python3 core/logging/log_query.py query --keyword "CPU" --since "2026-02-01"

# 导出日志到文件
python3 core/logging/log_query.py export --output logs_export.jsonl --since "2026-02-01"

# 实时跟踪日志
python3 core/logging/log_query.py tail --source diagnosis --interval 5

# 执行日志轮转
python3 core/logging/log_query.py rotate
```

### Python API

```python
from core.logging.unified_logger import get_logger, UnifiedLogger

# 获取日志管理器实例
logger = get_logger()

# 写入日志
logger.log(
    source='my_app',
    level='INFO',
    message='这是一条日志消息',
    metadata={'key': 'value'}
)

# 查询日志
results = logger.query(
    source='diagnosis',
    min_level='WARNING',
    limit=100
)

# 获取统计信息
stats = logger.get_stats()

# 执行轮转（删除30天前的日志）
result = logger.rotate()

# 导出到JSONL
logger.export_to_jsonl('export.jsonl', source='diagnosis')
```

## 日志来源

当前系统包含以下日志来源：

| 来源 | 说明 |
|------|------|
| diagnosis | 系统诊断记录 |
| heal | 自动修复记录 |
| notification | 通知告警 |
| decision | 决策引擎记录 |
| decision_engine | 决策引擎详细日志 |
| monitor | 统一监控日志 |
| optimization | 优化执行日志 |

## 日志轮转

- **保留期**: 30天
- **轮转方式**: 自动删除超过保留期的日志
- **执行命令**: `python3 scripts/log_rotation.py`
- **建议**: 通过cron每天执行一次

## 存储位置

- **数据库**: `data/unified_logs.db`
- **轮转日志**: `logs/log_rotation.log`

## 迁移结果

### 统计数据

- **迁移条目**: 10,333 条
- **数据库大小**: 5.38 MB
- **时间范围**: 2026-02-11 ~ 2026-02-19

### 来源分布

| 来源 | 数量 | 占比 |
|------|------|------|
| diagnosis | 8,930 | 86.4% |
| monitor | 1,324 | 12.8% |
| decision_engine_log | 65 | 0.6% |
| heal | 5 | 0.0% |
| notification | 4 | 0.0% |
| decision | 3 | 0.0% |
| generic | 2 | 0.0% |

### 级别分布

| 级别 | 数量 | 占比 |
|------|------|------|
| INFO | 8,321 | 80.5% |
| WARNING | 1,359 | 13.2% |
| DEBUG | 640 | 6.2% |
| ERROR | 8 | 0.1% |
| CRITICAL | 5 | 0.0% |

## 注意事项

1. 原始JSONL日志已备份为 `.backup` 文件
2. 诊断日志中的每个检查项被拆分为独立的日志记录
3. 数据库使用WAL模式以提高并发性能
