# MoltCare Deployment Plan

> 自动支付监控系统部署指南
> 目标: 实现全自动服务激活和到期管理

---

## 📋 部署检查清单

### 1. 环境准备

```bash
# 安装Python依赖
pip install web3 python-dotenv

# 创建必要目录
mkdir -p data/moltcare logs

# 设置环境变量 (添加到 .bashrc 或 .env)
export BASE_RPC="https://mainnet.base.org"
export POLL_INTERVAL="15"
```

### 2. 配置文件

创建 `config/moltcare.env`:
```bash
# Base链配置
BASE_RPC=https://mainnet.base.org
POLL_INTERVAL=15
DATA_DIR=data/moltcare
LOG_FILE=logs/moltcare-payment.log

# MoltCare配置
MOLT_TOKEN=0xb695559b26bb2c9703ef1935c37aeae9526bab07
RECEIVER=0x5e7c9888e90d72c9ed223dfdaf039c4a7a18ce33
```

### 3. 测试运行

```bash
# 测试连接
python3 scripts/moltcare-payment-monitor.py --stats

# 检查到期服务
python3 scripts/moltcare-payment-monitor.py --check-expiry

# 启动监控 (前台)
python3 scripts/moltcare-payment-monitor.py --daemon
```

### 4. Cron配置

添加到 crontab:
```bash
# MoltCare支付监控 (每分钟)
* * * * * cd /root/.openclaw/workspace && source config/moltcare.env && python3 scripts/moltcare-payment-monitor.py >> logs/moltcare-monitor.log 2>&1

# 每日到期检查 (上午9点)
0 9 * * * cd /root/.openclaw/workspace && python3 scripts/moltcare-payment-monitor.py --check-expiry >> logs/moltcare-expiry.log 2>&1

# 每周统计报告 (周一上午9点)
0 9 * * 1 cd /root/.openclaw/workspace && python3 scripts/moltcare-payment-monitor.py --stats >> logs/moltcare-stats.log 2>&1
```

---

## 🚀 服务启动流程

### Step 1: Memory服务

```bash
# 1.1 启动备份服务
python3 scripts/moltcare-memory-backup.py --daemon

# 1.2 启动恢复API
python3 scripts/moltcare-memory-api.py --port 8080

# 1.3 测试备份
curl http://localhost:8080/backup/test-agent
```

### Step 2: Shield服务

```bash
# 2.1 启动技能扫描服务
python3 scripts/moltcare-shield-scanner.py --daemon

# 2.2 启动API
python3 scripts/moltcare-shield-api.py --port 8081
```

### Step 3: Life服务

```bash
# 3.1 启动心跳监控
python3 scripts/moltcare-life-heartbeat.py --daemon

# 3.2 启动托管服务
python3 scripts/moltcare-life-hosting.py --daemon
```

### Step 4: 支付监控

```bash
# 4.1 启动支付监控
python3 scripts/moltcare-payment-monitor.py --daemon

# 4.2 验证监控状态
tail -f logs/moltcare-payment.log
```

---

## 📊 监控面板

### 查看实时状态

```bash
# 查看支付监控日志
tail -f logs/moltcare-payment.log

# 查看统计
python3 scripts/moltcare-payment-monitor.py --stats

# 查看订阅者列表
cat data/moltcare/subscribers.json | jq .
```

### 关键指标监控

```bash
# 活跃订阅数
python3 scripts/moltcare-payment-monitor.py --stats | jq '.active'

# 服务分布
python3 scripts/moltcare-payment-monitor.py --stats | jq '.service_breakdown'

# 本周新订阅
# (需要额外脚本计算)
```

---

## 🔧 故障排除

### 问题1: 无法连接Base网络

```bash
# 检查RPC连接
curl -X POST https://mainnet.base.org \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# 更换RPC节点
export BASE_RPC="https://base.llamarpc.com"
```

### 问题2: 支付未检测到

```bash
# 检查收款地址是否正确
echo $RECEIVER  # 应该是 0x5e7c9888e90d72c9ed223dfdaf039c4a7a18ce33

# 检查最后处理区块
cat data/moltcare/monitor_state.json

# 手动扫描历史区块
python3 scripts/moltcare-payment-monitor.py --rescan --from-block 20000000
```

### 问题3: 服务未激活

```bash
# 检查订阅者列表
cat data/moltcare/subscribers.json

# 检查AgentID是否正确
python3 scripts/moltcare-payment-monitor.py --lookup-agent 0x...
```

---

## 📈 扩展计划

### Phase 1: 基础监控 (已部署)
- [x] Base链支付监控
- [x] 自动服务激活
- [x] 到期检查

### Phase 2: 服务集成 (进行中)
- [ ] Memory备份服务
- [ ] Shield技能扫描
- [ ] Life心跳托管

### Phase 3: 用户体验 (待开发)
- [ ] Moltbook Bot通知
- [ ] Web管理界面
- [ ] 自助续费功能

---

## 🔐 安全注意事项

1. **私钥安全**
   - 监控脚本不需要私钥（只读）
   - 收款地址是只读的，不用于签名

2. **数据备份**
   - 定期备份 `data/moltcare/` 目录
   - subscribers.json 是核心数据

3. **日志清理**
   - 日志轮转: `logrotate` 或 cron 定期清理
   - 保留30天日志

---

## 📞 支持

如有问题:
1. 检查日志: `logs/moltcare-*.log`
2. 查看状态: `python3 scripts/moltcare-payment-monitor.py --stats`
3. 重启服务: `pkill -f moltcare-payment-monitor && python3 scripts/moltcare-payment-monitor.py --daemon`

---

*MoltCare Deployment Guide | 2026-03-08*
