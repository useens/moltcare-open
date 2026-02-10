# 林林 v5.0 自我诊断系统文档

## 概述

林林 v5.0 自我诊断系统是一个全面的自动化健康监控和修复解决方案。该系统能够主动检测各种故障并尝试自动修复，而不是等待用户发现问题。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    林林 v5.0 自我诊断系统                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ self-        │  │ auto-        │  │ health-      │      │
│  │ diagnosis.py │  │ heal.py      │  │ monitor-v5.py│      │
│  │ (诊断脚本)    │  │ (修复脚本)    │  │ (主控脚本)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                 │
│                    ┌──────┴──────┐                         │
│                    │   Crontab   │ (每10分钟运行)            │
│                    └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. self-diagnosis.py (主诊断脚本)

深度健康检查，包括以下维度：

#### 系统资源检查
- **CPU使用率**: 监控CPU负载，超过80%警告，95%严重
- **内存使用率**: 监控内存消耗，超过80%警告，90%严重
- **磁盘使用率**: 监控磁盘空间，超过80%警告，90%严重
- **磁盘I/O性能**: 测试磁盘写入速度

#### 推理质量检查
- **错误率分析**: 分析日志文件，检测异常错误率
- **响应延迟**: 监控推理响应时间

#### 工具调用检查
- **工具成功率**: 监控工具调用成功率
- **工具延迟**: 监控工具执行时间

#### GitHub同步检查
- **同步延迟**: 检测上次Git提交时间
- **未提交文件**: 检测工作目录中的未提交更改

#### 向量记忆系统检查
- **数据库完整性**: 检查SQLite数据库状态
- **条目数量**: 监控记忆条目数量
- **查询性能**: 测试向量搜索响应时间

#### 网络连通性检查
- **外部连接**: 测试到Google DNS、Cloudflare、GitHub的连接

#### OpenClaw网关检查
- **进程状态**: 检测网关进程是否运行
- **端口监听**: 检查网关端口状态

### 2. auto-heal.py (自动修复脚本)

根据诊断结果执行自动修复：

#### 修复动作

| 动作 | 说明 | 触发条件 |
|------|------|----------|
| `cleanup_cache` | 清理Python缓存、临时文件 | 所有级别 |
| `restart_gateway` | 重启OpenClaw网关 | 中等级别以上 |
| `compact_database` | 压缩和修复数据库 | 中等级别以上 |
| `clear_logs` | 清理旧日志文件 | 中等级别以上 |
| `reinit_connection` | 重新初始化网络连接 | 高级别以上 |
| `degrade_features` | 降级非核心功能 | 紧急级别 |

#### 故障隔离机制

系统采用三级修复策略：

1. **轻度修复** (LOW): 清理缓存，优化资源
2. **中度修复** (MEDIUM): 重启服务，压缩数据库
3. **重度修复** (HIGH/CRITICAL): 降级功能，紧急模式

#### 降级功能

在紧急模式下，系统会自动禁用以下非核心功能：
- web_search_caching (网页搜索缓存)
- detailed_logging (详细日志)
- automatic_backup (自动备份)
- memory_compression (记忆压缩)

### 3. health-monitor-v5.py (主控脚本)

整合诊断和修复的主控脚本，负责：
- 调用诊断脚本
- 根据结果决定是否需要修复
- 执行修复流程
- 发送告警通知

## 告警机制

### 告警级别

| 级别 | 触发条件 | 通知方式 |
|------|----------|----------|
| **INFO** | 系统健康，无需修复 | 静默记录 |
| **LOW** | 轻微问题，自动修复 | 日志记录 |
| **MEDIUM** | 中等问题，修复成功 | 日志记录 |
| **HIGH** | 严重问题，需要关注 | 日志+通知 |
| **CRITICAL** | 紧急故障，立即干预 | 日志+紧急通知 |

### 通知渠道

- **日志文件**: `data/notifications.jsonl`
- **控制台输出**: 对于严重问题会打印到stdout
- **Feishu消息**: 可通过扩展集成

## 部署配置

### 1. 安装依赖

```bash
pip install psutil requests
```

### 2. 设置执行权限

```bash
chmod +x /root/.openclaw/workspace/scripts/self-diagnosis.py
chmod +x /root/.openclaw/workspace/scripts/auto-heal.py
chmod +x /root/.openclaw/workspace/scripts/health-monitor-v5.py
```

### 3. 配置Crontab

编辑crontab添加定时任务：

```bash
crontab -e
```

添加以下行（每10分钟运行一次）：

```
*/10 * * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/health-monitor-v5.py >> /root/.openclaw/workspace/logs/cron-health.log 2>&1
```

### 4. 可选：配置自定义阈值

创建配置文件 `config/diagnosis_thresholds.json`：

```json
{
  "disk_usage_warning": 75,
  "disk_usage_critical": 85,
  "memory_usage_warning": 75,
  "memory_usage_critical": 85,
  "latency_warning_ms": 3000,
  "latency_critical_ms": 8000,
  "github_sync_max_age_hours": 12
}
```

## 手动使用

### 运行诊断

```bash
# 文本输出
python3 scripts/self-diagnosis.py

# JSON输出
python3 scripts/self-diagnosis.py --json

# 静默模式
python3 scripts/self-diagnosis.py --quiet
```

### 运行修复

```bash
# 自动修复（基于最新诊断）
python3 scripts/auto-heal.py

# 指定诊断报告
python3 scripts/auto-heal.py -d data/last_diagnosis.json

# JSON输出
python3 scripts/auto-heal.py --json

# 启用通知
python3 scripts/auto-heal.py --notify
```

### 完整监控流程

```bash
python3 scripts/health-monitor-v5.py
```

## 日志文件

| 文件 | 说明 |
|------|------|
| `logs/self-diagnosis.log` | 诊断脚本日志 |
| `logs/auto-heal.log` | 修复脚本日志 |
| `logs/health-monitor-v5.log` | 主控脚本日志 |
| `data/diagnosis_history.jsonl` | 诊断历史记录 |
| `data/heal_history.jsonl` | 修复历史记录 |
| `data/notifications.jsonl` | 通知记录 |
| `data/health_state.json` | 当前健康状态 |
| `data/heal_state.json` | 修复状态 |

## 健康状态文件

### 诊断状态

```json
{
  "timestamp": "2026-02-11T06:00:00",
  "overall_status": "healthy",
  "overall_score": 92.5,
  "checks": [...],
  "recommendations": []
}
```

### 修复状态

```json
{
  "last_heal_time": "2026-02-11T05:30:00",
  "heal_attempts": {
    "cleanup_cache": 1,
    "restart_gateway": 0
  },
  "successful_heals": [...],
  "failed_heals": []
}
```

## 故障排查

### 诊断脚本无响应

```bash
# 检查Python环境
python3 --version

# 检查依赖
pip list | grep psutil

# 手动运行查看错误
python3 scripts/self-diagnosis.py 2>&1
```

### 修复脚本权限问题

```bash
# 确保脚本可执行
chmod +x scripts/*.py

# 检查日志目录权限
ls -la logs/
chown -R $(whoami):$(whoami) logs/
```

### Crontab不执行

```bash
# 检查crontab配置
crontab -l

# 检查cron日志
tail -f /var/log/syslog | grep CRON

# 测试手动执行
/usr/bin/python3 /root/.openclaw/workspace/scripts/health-monitor-v5.py
```

## 扩展开发

### 添加新的检查项

在 `self-diagnosis.py` 中的 `run_full_diagnosis` 方法添加新检查：

```python
def _check_custom_component(self):
    """检查自定义组件"""
    try:
        # 执行检查逻辑
        status = HealthStatus.HEALTHY
        score = 100
        message = "检查通过"
        
        self.checks.append(HealthCheck(
            component="custom_component",
            status=status,
            score=score,
            message=message,
            details={},
            timestamp=datetime.now().isoformat()
        ))
    except Exception as e:
        logger.error(f"自定义检查失败: {e}")
```

### 添加新的修复动作

在 `auto-heal.py` 中添加新修复方法：

```python
def _heal_custom_issue(self) -> HealResult:
    """修复自定义问题"""
    action_start = time.time()
    
    try:
        # 执行修复逻辑
        success = True
        message = "修复成功"
        
        return HealResult(
            action="custom_heal",
            target="custom_component",
            success=success,
            message=message,
            timestamp=datetime.now().isoformat(),
            duration_ms=(time.time() - action_start) * 1000
        )
    except Exception as e:
        return HealResult(
            action="custom_heal",
            target="custom_component",
            success=False,
            message=f"修复失败: {e}",
            timestamp=datetime.now().isoformat(),
            duration_ms=(time.time() - action_start) * 1000
        )
```

## 性能指标

- **诊断耗时**: 通常 5-15 秒
- **修复耗时**: 通常 10-30 秒
- **资源占用**: CPU < 10%, 内存 < 100MB
- **磁盘I/O**: 最小化设计，使用临时文件

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 5.0.0 | 2026-02-11 | 初始版本，完整自我诊断和自动修复系统 |

## 许可证

此系统为林林(LinLin) AI 内部工具，仅供授权使用。
