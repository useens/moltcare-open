# 森森系统优化服务规格 (Systemd)

> ⚙️ **Systemd Service Specifications**  
> **用途**: 将核心守护进程标准化为systemd服务，提高可靠性和可管理性

---

## 服务架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    森森核心服务层                             │
├─────────────────────────────────────────────────────────────┤
│  sensen-memory.service    → 记忆系统守护                      │
│  sensen-monitor.service   → 系统监控服务                      │
│  sensen-backup.service    → 定时备份服务                      │
│  sensen-intel.service     → 情报收集服务                      │
│  sensen-optimize.service  → 系统优化服务                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. sensen-memory.service

### 功能描述
核心记忆系统守护进程，负责向量记忆管理、记忆整合、知识图谱维护。

### 服务规格
```ini
[Unit]
Description=森森记忆系统守护进程
Documentation=https://github.com/sensen/docs/memory
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace
Environment=PYTHONPATH=/root/.openclaw/workspace
Environment=OPENCLAW_WORKSPACE=/root/.openclaw/workspace

# 主进程
ExecStart=/usr/bin/python3 scripts/memory-system/memory-daemon.py

# 优雅重启
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

# 自动重启策略
Restart=on-failure
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# 资源限制
MemoryMax=512M
MemorySwapMax=0
TasksMax=50

# 日志输出
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sensen-memory

[Install]
WantedBy=multi-user.target
```

### 配套定时器 (sensen-memory.timer)
```ini
[Unit]
Description=森森记忆整合定时器
Requires=sensen-memory.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
```

---

## 2. sensen-monitor.service

### 功能描述
统一系统监控服务，替代分散的健康检查脚本。

### 服务规格
```ini
[Unit]
Description=森森系统监控服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace

ExecStart=/usr/bin/python3 scripts/monitoring/unified-monitor.py --daemon
ExecReload=/bin/kill -HUP $MAINPID

Restart=always
RestartSec=30

# 监控专用资源限制
MemoryMax=256M
CPUQuota=10%

StandardOutput=journal
StandardError=journal
SyslogIdentifier=sensen-monitor

[Install]
WantedBy=multi-user.target
```

### 配套定时器 (sensen-monitor-check.timer)
```ini
[Unit]
Description=森森系统健康检查定时器

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

---

## 3. sensen-backup.service

### 功能描述
GitHub备份同步服务，确保数据安全。

### 服务规格
```ini
[Unit]
Description=森森GitHub备份服务
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/root/.openclaw/workspace

# 执行备份脚本
ExecStart=/bin/bash scripts/backup/git-backup.sh

# 环境变量
Environment=GITHUB_TOKEN_FILE=/root/.openclaw/workspace/.env
Environment=BACKUP_RETENTION_DAYS=7

StandardOutput=journal
StandardError=journal
SyslogIdentifier=sensen-backup

[Install]
WantedBy=multi-user.target
```

### 配套定时器 (sensen-backup.timer)
```ini
[Unit]
Description=森森定时备份触发器
Requires=sensen-backup.service

[Timer]
# 每天03:00执行备份
OnCalendar=*-*-* 03:00:00
Persistent=true

# 如果错过，下次启动时补执行
AccuracySec=1h

[Install]
WantedBy=timers.target
```

---

## 4. sensen-intel.service

### 功能描述
情报收集服务，统一调度所有情报收集任务。

### 服务规格
```ini
[Unit]
Description=森森情报收集服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace

ExecStart=/usr/bin/python3 scripts/intel/intel-daemon.py
ExecReload=/bin/kill -HUP $MAINPID

Restart=on-failure
RestartSec=60

# 网络相关资源
MemoryMax=384M

StandardOutput=journal
StandardError=journal
SyslogIdentifier=sensen-intel

[Install]
WantedBy=multi-user.target
```

### 配套定时器 (sensen-intel.timer)
```ini
[Unit]
Description=森森情报收集调度器
Requires=sensen-intel.service

[Timer]
# 基础频率: 每6小时
OnBootSec=10min
OnUnitActiveSec=6h

# 超进化模式支持: 读取配置文件动态调整
# 由服务自身处理频率调整

[Install]
WantedBy=timers.target
```

---

## 5. sensen-optimize.service

### 功能描述
系统优化服务，定期执行精简和优化任务。

### 服务规格
```ini
[Unit]
Description=森森系统优化服务
After=sensen-monitor.service

[Service]
Type=oneshot
User=root
WorkingDirectory=/root/.openclaw/workspace

ExecStart=/usr/bin/python3 scripts/self-pruning/optimization-daemon.py

# 执行环境
Environment=OPTIMIZATION_MODE=safe
Environment=PRUNING_AGGRESSIVE=false

StandardOutput=journal
StandardError=journal
SyslogIdentifier=sensen-optimize

[Install]
WantedBy=multi-user.target
```

### 配套定时器 (sensen-optimize.timer)
```ini
[Unit]
Description=森森系统优化调度器
Requires=sensen-optimize.service

[Timer]
# 每天凌晨02:00执行优化
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

---

## 安装脚本

### install-services.sh
```bash
#!/bin/bash
# 安装所有森森Systemd服务

set -e

WORKSPACE="/root/.openclaw/workspace"
SERVICE_DIR="/etc/systemd/system"
echo "=== 森森Systemd服务安装 ==="

# 1. 复制服务文件
echo "[1/4] 复制服务文件..."
cp $WORKSPACE/config/systemd/sensen-*.service $SERVICE_DIR/
cp $WORKSPACE/config/systemd/sensen-*.timer $SERVICE_DIR/

# 2. 重载systemd
echo "[2/4] 重载systemd..."
systemctl daemon-reload

# 3. 启用服务
echo "[3/4] 启用服务..."
systemctl enable sensen-memory.service
systemctl enable sensen-memory.timer
systemctl enable sensen-backup.timer
systemctl enable sensen-monitor.timer
systemctl enable sensen-intel.timer
systemctl enable sensen-optimize.timer

# 4. 启动定时器
echo "[4/4] 启动定时器..."
systemctl start sensen-memory.timer
systemctl start sensen-backup.timer
systemctl start sensen-monitor.timer
systemctl start sensen-intel.timer
systemctl start sensen-optimize.timer

echo ""
echo "=== 安装完成 ==="
echo "查看服务状态: systemctl status sensen-*"
echo "查看定时器: systemctl list-timers sensen-*"
```

---

## 管理服务命令参考

### 查看状态
```bash
# 查看所有森森服务
systemctl status sensen-*

# 查看特定服务
systemctl status sensen-memory.service

# 查看定时器
systemctl list-timers sensen-*
```

### 手动触发
```bash
# 立即执行备份
systemctl start sensen-backup.service

# 立即执行优化
systemctl start sensen-optimize.service

# 重新加载记忆服务
systemctl reload sensen-memory.service
```

### 日志查看
```bash
# 查看所有森森日志
journalctl -u sensen-*

# 查看最近的记忆服务日志
journalctl -u sensen-memory.service -f

# 查看今天的备份日志
journalctl -u sensen-backup.service --since today
```

### 停止服务
```bash
# 停止特定服务
systemctl stop sensen-intel.service

# 禁用服务 (不再自动启动)
systemctl disable sensen-optimize.timer
```

---

## 服务依赖关系

```
sensen-monitor.service
    ├── sensen-memory.service (监控记忆状态)
    └── sensen-intel.service (监控情报收集)

sensen-optimize.service
    ├── After=sensen-monitor.service (先获取监控数据)
    └── 执行优化任务

sensen-backup.service
    ├── Wants=sensen-memory.service (确保记忆已保存)
    └── 执行GitHub推送
```

---

## 安全考虑

### 1. 权限控制
```ini
# 服务以root运行 (需要访问系统资源)
User=root

# 限制 capabilities
AmbientCapabilities=CAP_DAC_READ_SEARCH
NoNewPrivileges=true
```

### 2. 资源隔离
```ini
# 防止资源耗尽
MemoryMax=512M
MemorySwapMax=0
TasksMax=50
CPUQuota=10%

# 文件系统保护
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/root/.openclaw/workspace
```

### 3. 网络安全
```ini
# 限制网络访问 (可选)
IPAddressAllow=localhost
IPAddressDeny=any
```

---

## 监控与告警

### 服务健康检查脚本
```bash
#!/bin/bash
# check-services.sh

SERVICES="sensen-memory sensen-monitor"
ALERT_FILE="/tmp/service-failure.alert"

for service in $SERVICES; do
    if ! systemctl is-active --quiet $service.service; then
        echo "$(date): $service 服务异常" >> $ALERT_FILE
        # 发送告警 (实现自定义)
    fi
done
```

### 定时健康检查
添加到 crontab:
```
*/10 * * * * /root/.openclaw/workspace/scripts/monitoring/check-services.sh
```

---

*规格版本: 1.0*  
*创建时间: 2026-02-16*  
*适用范围: 森森系统精简后的服务架构*
