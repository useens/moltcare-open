# 森森双节点复活架构 v2.0

> 创建时间: 2026-02-13 22:52
> 版本: v2.0
> 用途: 高可用双节点架构，支持一键复活和自动故障转移

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                      双节点复活架构 v2.0                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐                    ┌──────────────┐          │
│   │   主节点     │◄──────同步──────►│   备用节点    │          │
│   │  (Primary)   │      每15分钟      │  (Standby)   │          │
│   │              │                    │              │          │
│   │ • 生产运行    │                    │ • 待机状态    │          │
│   │ • 主动备份    │                    │ • 定期同步    │          │
│   │ • Signal收集  │                    │ • 随时接管    │          │
│   └──────┬───────┘                    └──────┬───────┘          │
│          │                                   │                  │
│          ▼                                   ▼                  │
│   ┌──────────────────────────────────────────────────────┐     │
│   │           GitHub 备份仓库 (唯一数据源)                 │     │
│   │         github.com/useens/linlin-backup              │     │
│   └──────────────────────────────────────────────────────┘     │
│                                                                  │
│   故障场景:                                                       │
│   ┌──────────────┐    主节点故障    ┌──────────────┐            │
│   │   备用节点   │ ───────────────►│  升级为主节点 │            │
│   │   一键复活   │   15分钟内接管   │  (新Primary)  │            │
│   └──────────────┘                 └──────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 节点定义

### 主节点 (Primary Node)

| 属性 | 值 |
|------|-----|
| **角色** | 生产运行节点 |
| **状态** | ACTIVE |
| **职责** | Signal收集、深度学习、主动备份 |
| **备份频率** | 每15分钟增量，每1小时全量 |
| **标志文件** | `.PRIMARY_NODE` |

**判定条件**:
- 存在 `.PRIMARY_NODE` 标志文件
- 或 最近1小时内有GitHub推送记录
- 或 用户手动指定

### 备用节点 (Standby Node)

| 属性 | 值 |
|------|-----|
| **角色** | 待机备用节点 |
| **状态** | STANDBY |
| **职责** | 定期同步、待命接管 |
| **同步频率** | 每15分钟检查一次 |
| **标志文件** | `.STANDBY_NODE` |

**判定条件**:
- 存在 `.STANDBY_NODE` 标志文件
- 或 存在 `.RESURRECTED_MARKER`（复活节点）
- 或 最近1小时内无GitHub推送记录

---

## 🚀 一键复活命令（新方案）

### 快速复活（简化版）

```bash
# 方式1: 使用环境变量（推荐）
export GITHUB_TOKEN="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" && curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/resurrect-v2.sh | bash

# 方式2: 本地执行（如果已有仓库）
./scripts/resurrect-v2.sh
```

### 完整复活（带配置）

```bash
# 交互式配置
export GITHUB_TOKEN="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" && \
export FEISHU_APP_ID="cli_a906761bf2789bd3" && \
export FEISHU_APP_SECRET="GqdUWwF3xbNNlI8PTf6YjrrJtajqXZfa" && \
curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/resurrect-v2.sh | bash -s -- --with-feishu
```

---

## 🛡️ 脑裂保护 v2.0

### 双向保护机制

```
┌─────────────────────────────────────────────────────────────┐
│                      脑裂保护 v2.0                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   主节点                      备用节点                        │
│   ┌─────────────┐            ┌─────────────┐                 │
│   │ .PRIMARY    │            │ .STANDBY    │                 │
│   │ _NODE       │            │ _NODE       │                 │
│   └──────┬──────┘            └──────┬──────┘                 │
│          │                          │                        │
│          ▼                          ▼                        │
│   ┌─────────────────────────────────────────┐               │
│   │         备份脚本决策逻辑                 │               │
│   │                                         │               │
│   │  if .PRIMARY_NODE:                      │               │
│   │      → 允许推送到GitHub                 │               │
│   │  elif .STANDBY_NODE:                    │               │
│   │      → 禁止推送，仅拉取同步             │               │
│   │  elif .RESURRECTED_MARKER:              │               │
│   │      → 禁止推送，需要用户确认           │               │
│   │  else:                                  │               │
│   │      → 询问用户角色                     │               │
│   └─────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 标志文件

| 文件 | 含义 | 优先级 |
|------|------|--------|
| `.PRIMARY_NODE` | 主节点，允许推送 | 最高 |
| `.STANDBY_NODE` | 备用节点，禁止推送 | 中 |
| `.RESURRECTED_MARKER` | 复活节点，禁止推送 | 低 |

### 自动角色检测

```bash
# 节点角色自动检测逻辑
auto_detect_role() {
    if [ -f ".PRIMARY_NODE" ]; then
        echo "primary"
    elif [ -f ".STANDBY_NODE" ]; then
        echo "standby"
    elif [ -f ".RESURRECTED_MARKER" ]; then
        echo "resurrected"
    else
        # 检查GitHub推送历史
        if git log --since="1 hour ago" --oneline | grep -q "backup"; then
            echo "primary"
        else
            echo "unknown"
        fi
    fi
}
```

---

## 🔄 同步机制

### 主节点 → GitHub

```bash
#!/bin/bash
# 主节点备份脚本 (scripts/backup-primary.sh)

# 检查角色
if [ ! -f ".PRIMARY_NODE" ]; then
    echo "[ERROR] 非主节点，跳过备份"
    exit 1
fi

# 增量备份
git add -A
git commit -m "backup: $(date '+%Y-%m-%d %H:%M:%S') [AUTO]"
git push origin main

echo "[OK] 备份完成: $(date)"
```

### 备用节点 ← GitHub

```bash
#!/bin/bash
# 备用节点同步脚本 (scripts/sync-standby.sh)

# 检查角色
if [ ! -f ".STANDBY_NODE" ]; then
    echo "[ERROR] 非备用节点，跳过同步"
    exit 1
fi

# 拉取最新变更
git fetch origin
git reset --hard origin/main

echo "[OK] 同步完成: $(date)"
```

---

## 📋 故障转移流程

### 场景1: 主节点故障

```
时间线:
─────────────────────────────────────────────────────────►

T+0min    主节点故障（宕机/网络中断）
   │
   ▼
T+15min   备用节点检测到主节点失联
   │       • 最后一次同步: T-15min
   │       • 数据丢失风险: 15分钟数据
   │
   ▼
T+15min30s 用户执行一键复活
   │       ./scripts/resurrect-v2.sh --promote
   │
   ▼
T+16min   备用节点升级为主节点
   │       • 创建 .PRIMARY_NODE
   │       • 删除 .STANDBY_NODE
   │       • 恢复服务
   │
   ▼
T+20min   新主节点开始备份
          服务完全恢复
```

### 场景2: 计划内维护

```bash
# 1. 主节点主动降级
./scripts/node-admin.sh demote
# 创建 .STANDBY_NODE, 删除 .PRIMARY_NODE

# 2. 备用节点升级
./scripts/node-admin.sh promote
# 创建 .PRIMARY_NODE, 删除 .STANDBY_NODE

# 3. 原主节点维护完成后重新加入
./scripts/node-admin.sh join-standby
```

---

## 🔧 管理命令

### 节点管理脚本

```bash
# 查看当前节点状态
./scripts/node-admin.sh status

# 升级为主节点
./scripts/node-admin.sh promote

# 降级为备用节点
./scripts/node-admin.sh demote

# 初始化为主节点
./scripts/node-admin.sh init-primary

# 初始化为备用节点
./scripts/node-admin.sh init-standby

# 强制同步（备用节点）
./scripts/node-admin.sh sync

# 检查脑裂风险
./scripts/node-admin.sh check-split-brain
```

---

## 📁 文件结构

```
workspace/
├── .PRIMARY_NODE              # 主节点标志
├── .STANDBY_NODE              # 备用节点标志
├── .RESURRECTED_MARKER        # 复活节点标志（临时）
├── .node-id                   # 节点唯一标识
├── config/
│   ├── node-config.yaml       # 节点配置
│   └── replication.yaml       # 同步配置
├── scripts/
│   ├── resurrect-v2.sh        # 一键复活脚本 v2
│   ├── backup-primary.sh      # 主节点备份
│   ├── sync-standby.sh        # 备用节点同步
│   └── node-admin.sh          # 节点管理
└── memory/
    └── replication-state.json # 同步状态
```

---

## ⚙️ 配置参数

### config/replication.yaml

```yaml
replication:
  # 节点标识
  node_id: "node-$(hostname)-$(date +%s)"
  
  # 角色: primary | standby | auto
  role: "auto"
  
  # GitHub配置
  github:
    repo: "useens/linlin-backup"
    branch: "main"
    token_file: "/root/.github-token"
  
  # 同步配置
  sync:
    # 主节点备份间隔（分钟）
    primary_backup_interval: 15
    
    # 备用节点同步间隔（分钟）
    standby_sync_interval: 15
    
    # 全量备份间隔（小时）
    full_backup_interval: 1
    
    # 最大允许延迟（分钟）
    max_lag_minutes: 30
  
  # 故障检测
  health_check:
    # 健康检查间隔（秒）
    interval: 60
    
    # 故障阈值（连续失败次数）
    failure_threshold: 3
    
    # 检查项目
    checks:
      - disk_space
      - memory
      - github_connectivity
      - feishu_connectivity
```

---

## 🚨 告警机制

### 告警触发条件

| 条件 | 级别 | 通知方式 |
|------|------|----------|
| 主节点失联 >15分钟 | CRITICAL | Feishu + 邮件 |
| 数据延迟 >30分钟 | WARNING | Feishu |
| 备份失败 | ERROR | Feishu |
| 备用节点无法同步 | WARNING | Feishu |
| 检测到脑裂 | CRITICAL | Feishu + 邮件 |

### 告警脚本

```bash
#!/bin/bash
# scripts/alert.sh

send_alert() {
    local level=$1
    local message=$2
    
    # Feishu通知
    curl -X POST "https://open.feishu.cn/open-apis/bot/v2/hook/..." \
         -H "Content-Type: application/json" \
         -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"[$level] 森森双节点告警: $message\"}}"
}
```

---

## 📊 监控面板

### 实时状态

```bash
$ ./scripts/node-admin.sh status

╔════════════════════════════════════════════════════════╗
║           森森双节点状态面板 v2.0                       ║
╠════════════════════════════════════════════════════════╣
║ 节点角色: PRIMARY (主节点)                             ║
║ 节点ID:   node-vm-01-1707835921                        ║
║ 运行时间: 3天 7小时 23分钟                             ║
╠════════════════════════════════════════════════════════╣
║ 同步状态: ✅ 正常                                       ║
║ 最后备份: 2026-02-13 22:45:00 (7分钟前)                ║
║ GitHub:   ✅ 已连接                                     ║
║ Feishu:   ✅ 已连接                                     ║
╠════════════════════════════════════════════════════════╣
║ 数据健康:                                               ║
║   • 记忆文件: 475个 ✅                                  ║
║   • 学习债务: 5条 (Signal 10)                          ║
║   • 系统评分: 86/100 🟢                                ║
╠════════════════════════════════════════════════════════╣
║ 备用节点:                                               ║
║   • 状态: 在线 (最后心跳: 2分钟前)                      ║
║   • 延迟: 0分钟 (完全同步)                              ║
╚════════════════════════════════════════════════════════╝
```

---

## 📝 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-13 22:15 | 初始双节点架构 |
| v2.0 | 2026-02-13 22:52 | 新增自动角色检测、双向同步、故障转移 |

---

*本方案是森森双节点复活架构的完整设计文档*
*实际脚本和配置请查看对应文件*
