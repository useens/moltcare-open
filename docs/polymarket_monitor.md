# Polymarket 概率飙升监测系统

实时监测 Polymarket 预测市场上概率快速变化的事件，自动预警并跟踪预测准确率。

## 功能特性

- 🔍 **实时监测**: 每10分钟扫描一次市场，检测概率显著变化事件
- 📊 **智能预警**: 变化幅度≥10%且交易量达标时自动触发预警
- 📈 **准确率跟踪**: 自动跟进事件结果，统计累计预测准确率
- 📱 **飞书通知**: 实时推送预警消息到飞书
- 📅 **日报周报**: 自动发送统计报告

## 安装

```bash
# 1. 确保依赖已安装
pip install requests

# 2. 添加cron任务
crontab config/polymarket_cron.txt
```

## 使用方法

### 命令行

```bash
# 启动持续监测服务
./scripts/polymarket_service.sh start

# 停止服务
./scripts/polymarket_service.sh stop

# 查看状态
./scripts/polymarket_service.sh status

# 手动执行一次扫描
./scripts/polymarket_service.sh scan

# 查看统计数据
./scripts/polymarket_service.sh stats

# 查看活跃预警
./scripts/polymarket_service.sh list
```

### Python API

```python
from scripts.polymarket_monitor import PolymarketMonitor

# 创建监测器
monitor = PolymarketMonitor()

# 执行单次扫描
alerts = monitor.scan_once()

# 获取统计数据
stats = monitor.get_statistics()
print(f"准确率: {stats['accuracy_rate']:.1f}%")

# 手动标记事件结果
monitor.resolve_event("event_id", "Yes")  # 或 "No"
```

## 配置

编辑 `polymarket_monitor.py` 中的 `AlertConfig` 调整参数：

```python
@dataclass
class AlertConfig:
    min_change_percent: float = 10.0  # 最小变化百分比触发预警
    min_volume: float = 100000       # 最小交易量（USD）
    min_liquidity: float = 50000     # 最小流动性
    check_interval: int = 60         # 检查间隔（秒）
    top_n: int = 10                  # 每次报告前N个事件
```

## 飞书通知配置

创建 `config/feishu_webhook.json`:

```json
{
  "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
}
```

## 数据库结构

使用 SQLite 存储所有数据：

- **events**: 事件记录（预警历史、结果、准确率）
- **statistics**: 累计统计

数据库文件: `polymarket_monitor.db`

## 自动化任务

Cron 配置 (`config/polymarket_cron.txt`):

| 频率 | 任务 |
|------|------|
| 每10分钟 | 扫描概率变化 |
| 每小时 | 检查已结束市场 |
| 每天8:00 | 发送日报 |
| 每周一9:00 | 发送周报 |

## 准确率统计逻辑

- **预测方向**: 系统根据概率变化方向预测（上涨=预测Yes，下跌=预测No）
- **准确性判断**: 事件结束时对比预测方向与实际结果
- **准确率计算**: 正确预测数 / 已解决预测数 × 100%

## 文件结构

```
scripts/
├── polymarket_monitor.py      # 核心监测模块
├── polymarket_feishu.py       # 飞书通知模块
├── polymarket_service.sh      # 服务控制脚本
├── polymarket_cron_check.py   # 结束市场检查
└── polymarket_daily_report.py # 日报生成

config/
└── polymarket_cron.txt        # Cron配置

polymarket_monitor.db          # SQLite数据库
```

## 注意事项

1. Polymarket API 是公开的，无需认证
2. 系统通过 GraphQL 获取市场数据
3. 历史数据保留在本地 SQLite 中
4. 准确率统计需要手动或自动跟进事件结果

## 未来改进

- [ ] 支持 Discord/Telegram 通知
- [ ] 添加更多筛选条件（类别、时间等）
- [ ] 预测模型优化
- [ ] Web 管理界面
