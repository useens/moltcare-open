# Phase 2 部署指南
# Cloud + Local VM 混合模式部署

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                               │
│              (Telegram / 飞书 / 其他渠道)                    │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌──────────────────────┐         ┌──────────────────────┐
│      云节点           │◄───────►│      本地VM          │
│   (主运行环境)        │  心跳   │   (故障转移备份)      │
│                      │         │                      │
│ ┌──────────────────┐ │         │ ┌──────────────────┐ │
│ │ OpenClaw Gateway │ │         │ │ 监控进程         │ │
│ ├──────────────────┤ │         │ ├──────────────────┤ │
│ │ 心跳广播服务     │─┼────────►│ │ 故障检测         │ │
│ ├──────────────────┤ │         │ ├──────────────────┤ │
│ │ 自动同步脚本     │─┼────────►│ │ 快速复活         │ │
│ ├──────────────────┤ │         │ ├──────────────────┤ │
│ │ 核心业务逻辑     │ │         │ │ 备份缓存         │ │
│ └──────────────────┘ │         │ └──────────────────┘ │
└──────────────────────┘         └──────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    GitHub 仓库                             │
│              (linlin-backup)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  main分支    │  │ heartbeat分支 │  │ 备份/日志    │     │
│  │ (代码/记忆)  │  │ (状态广播)   │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 部署流程

### 阶段1: 云节点部署

#### 1.1 配置GitHub Token

```bash
# 创建目录
mkdir -p ~/.config/linlin
mkdir -p ~/.openclaw/logs

# 写入Token (替换为实际token)
echo "ghp_your_github_token_here" > ~/.config/linlin/github-token
chmod 600 ~/.config/linlin/github-token
```

#### 1.2 部署心跳服务

```bash
cd ~/.openclaw/workspace

# 确保脚本可执行
chmod +x scripts/cloud-heartbeat.sh

# 配置
./scripts/cloud-heartbeat.sh --setup
# 按提示输入:
# - GitHub仓库: useens/linlin-backup
# - 心跳间隔: 60
# - Token路径: ~/.config/linlin/github-token
```

#### 1.3 启动心跳（方式选择）

**方式A: 直接启动**
```bash
./scripts/cloud-heartbeat.sh --daemon
```

**方式B: Systemd服务**
```bash
# 复制服务文件
sudo cp scripts/systemd/cloud-heartbeat@.service /etc/systemd/system/

# 重载systemd
sudo systemctl daemon-reload

# 启动服务 (将USERNAME替换为实际用户名)
sudo systemctl enable cloud-heartbeat@USERNAME
sudo systemctl start cloud-heartbeat@USERNAME

# 查看状态
sudo systemctl status cloud-heartbeat@USERNAME
journalctl -u cloud-heartbeat@USERNAME -f
```

#### 1.4 验证

```bash
# 测试单次心跳
./scripts/cloud-heartbeat.sh --test

# 查看GitHub上的心跳
./scripts/cloud-heartbeat.sh --status
```

### 阶段2: 本地VM部署

#### 2.1 环境准备

```bash
# 安装依赖
sudo apt-get update
sudo apt-get install -y git curl netcat-openbsd

# 创建目录
mkdir -p ~/.config/linlin
mkdir -p ~/.openclaw/logs
```

#### 2.2 配置凭证

```bash
# 写入GitHub Token
echo "ghp_your_github_token_here" > ~/.config/linlin/github-token
chmod 600 ~/.config/linlin/github-token

# 配置Telegram通知 (可选)
mkdir -p ~/.openclaw/credentials
echo "your_bot_token" > ~/.openclaw/credentials/telegram.token
echo "your_chat_id" > ~/.openclaw/credentials/telegram.chatid
chmod 600 ~/.openclaw/credentials/*
```

#### 2.3 部署复活脚本

```bash
# 下载脚本
curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/local-resurrect-optimized.sh -o ~/resurrect.sh
chmod +x ~/resurrect.sh

# 配置
./resurrect.sh --setup
# 按提示输入:
# - GitHub仓库: useens/linlin-backup
# - 云节点IP/域名: [你的云节点地址]
# - 心跳超时: 120
# - Telegram信息 (如配置)
```

#### 2.4 预拉取备份

```bash
# 首次拉取（可能较慢）
./resurrect.sh --prefetch

# 验证缓存
du -sh ~/.openclaw/.resurrection-cache
ls ~/.openclaw/.resurrection-cache
```

#### 2.5 设置定时预拉取

```bash
# 添加到crontab，每10分钟更新缓存
(crontab -l 2>/dev/null; echo "*/10 * * * * $HOME/resurrect.sh --prefetch >> $HOME/.openclaw/logs/prefetch.log 2>&1") | crontab -

# 或使用systemd定时器
sudo cp scripts/systemd/local-resurrect@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable local-resurrect@USERNAME
sudo systemctl start local-resurrect@USERNAME
```

### 阶段3: 集成测试

```bash
# 在云节点
curl -s https://api.github.com/repos/useens/linlin-backup/contents/status/cloud-status.json?ref=heartbeat | \
  python3 -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"

# 在本地VM
./resurrect.sh --status

# 应该显示:
# - 云节点状态: healthy
# - 心跳时间: XX秒前
```

## 故障转移流程

### 自动触发条件

1. **心跳超时**: GitHub心跳超过120秒未更新
2. **网络不可达**: 云节点IP/端口无响应
3. **状态严重**: 云节点主动报告critical状态

### 手动触发

```bash
# 在本地VM执行
./resurrect.sh --now
```

### 故障转移后操作

```bash
# 1. 验证本地VM运行
openclaw gateway status

# 2. 检查通知
# 应该收到Telegram/飞书消息

# 3. 测试通信
# 发送消息验证响应

# 4. 等待云节点修复
# 修复后云节点会自动恢复心跳

# 5. 云节点恢复后回切
# 参考 phase2-test-plan.md 场景6
```

## 数据同步策略

### 实时同步（云节点）

```bash
# 添加定时任务到 crontab
# 每30分钟自动同步到GitHub

(crontab -l 2>/dev/null; echo "*/30 * * * * cd $HOME/.openclaw/workspace && git add -A && git commit -m \"auto-sync $(date +%H:%M)\" && git push origin main --quiet 2>/dev/null || true") | crontab -
```

### 冲突解决

```bash
# 如果双向修改产生冲突

# 在本地VM
cd ~/.openclaw/workspace
git fetch origin
git status

# 方案1: 保留本地更改
git checkout --ours MEMORY.md
git add MEMORY.md

# 方案2: 保留云端更改
git checkout --theirs MEMORY.md
git add MEMORY.md

# 方案3: 手动合并
git merge-tool

# 提交解决
git commit -m "Resolve merge conflict"
git push origin main
```

## 监控与告警

### 关键指标

| 指标 | 检查命令 | 告警阈值 |
|------|----------|----------|
| 心跳延迟 | `./resurrect.sh --status` | > 120s |
| 缓存年龄 | `stat ~/.openclaw/.resurrection-cache` | > 1小时 |
| 磁盘空间 | `df -h ~` | < 10% |
| 网络延迟 | `ping api.github.com` | > 5s |

### 日志位置

| 服务 | 日志路径 |
|------|----------|
| 云心跳 | `~/.openclaw/logs/cloud-heartbeat.log` |
| 本地复活 | `~/.openclaw/logs/local-resurrect.log` |
| 预拉取 | `~/.openclaw/logs/prefetch.log` |
| Systemd | `journalctl -u cloud-heartbeat@USER` |

## 性能优化建议

### 缩短复活时间

1. **启用并行下载**: 已在脚本中默认启用
2. **增加预拉取频率**: 从10分钟改为5分钟
3. **使用SSD**: 本地VM使用SSD存储缓存
4. **就近GitHub**: 选择地理上更近的服务器

### 目标指标

| 阶段 | 当前目标 | 优化后目标 |
|------|----------|------------|
| 故障检测 | < 2分钟 | < 30秒 |
| 备份拉取 | < 60秒 | < 30秒 |
| 服务启动 | < 30秒 | < 15秒 |
| **总RTO** | **< 2分钟** | **< 1分钟** |

## 常见问题

### Q: 心跳写入失败
A: 检查GitHub Token权限（需要repo访问），检查网络连接

### Q: 本地VM无法检测到云节点故障
A: 检查`resurrection.conf`中的`CLOUD_HOST`配置，检查时区和时间同步

### Q: 复活后无法启动OpenClaw
A: 检查日志`~/.openclaw/logs/local-resurrect.log`，检查端口占用

### Q: 通知未收到
A: 检查凭证文件权限(600)，测试API调用，检查网络

## 安全注意事项

1. **Token保管**: GitHub Token只保存在~/.config/linlin/，设置权限600
2. **网络隔离**: 本地VM不需要暴露端口，只需出站访问GitHub
3. **加密传输**: 使用HTTPS与GitHub通信，避免明文传输
4. **定期轮换**: 每90天更换GitHub Token

## 联系支持

- 文档: https://github.com/useens/linlin-backup/tree/main/docs
- 问题: 创建GitHub Issue
- 紧急: 通过Telegram/飞书联系
