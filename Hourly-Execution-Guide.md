# 每小时 Template Mining 执行指南

> 用户指令: 每小时执行一次完整流程

---

## 方案一: Cron 自动执行 (推荐)

### 1. 添加到 crontab

```bash
# 编辑 crontab
crontab -e

# 添加以下行 (每小时执行一次)
0 * * * * /root/.openclaw/workspace/moltcare-open/scripts/hourly-mining.sh >> /root/.openclaw/workspace/moltcare-open/logs/cron.log 2>>1
```

### 2. 验证设置

```bash
# 查看当前 crontab
crontab -l

# 检查是否有错误
grep CRON /var/log/syslog | tail -10
```

---

## 方案二: 手动触发执行

### 当前执行
```bash
~/.openclaw/workspace/moltcare-open/scripts/hourly-mining.sh
```

### 后台持续执行 (使用 while 循环)
```bash
#!/bin/bash
# 保存为 run-hourly.sh

while true; do
    ~/.openclaw/workspace/moltcare-open/scripts/hourly-mining.sh
    
    # 计算到下一个小时的等待时间
    CURRENT_MIN=$(date +%M)
    CURRENT_SEC=$(date +%S)
    WAIT_MIN=$((60 - 10#$CURRENT_MIN))
    WAIT_SEC=$((60 - 10#$CURRENT_SEC))
    TOTAL_WAIT=$((WAIT_MIN * 60 + WAIT_SEC))
    
    echo "等待 ${TOTAL_WAIT} 秒到下一个小时..."
    sleep $TOTAL_WAIT
done
```

---

## 方案三: 通过 OpenClaw 定时触发

如果 OpenClaw 支持定时任务，配置如下:

```yaml
# config.yaml
scheduled_tasks:
  - name: hourly-template-mining
    schedule: "0 * * * *"
    command: ~/.openclaw/workspace/moltcare-open/scripts/hourly-mining.sh
```

---

## 输出监控

### 查看最新报告
```bash
ls -lt ~/.openclaw/workspace/moltcare-open/research/hourly/ | head -5
```

### 查看待审查队列
```bash
cat ~/.openclaw/workspace/moltcare-open/research/review_queue.txt
```

### 查看执行日志
```bash
tail -f ~/.openclaw/workspace/moltcare-open/logs/mining_*.log
```

---

## 高价值发现通知

当发现高价值模板时:
1. 会写入 `review_queue.txt`
2. 报告会标记 "⚠️ 需要关注"
3. 建议在下次交互时汇报给用户

---

*设置时间: 2026-03-11*
