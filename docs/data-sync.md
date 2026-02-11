# 双节点数据双向同步系统

## 概述

本系统实现云端主节点与本地VM的双向数据同步，支持定时同步、事件触发同步和手动同步三种模式。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      主节点 (云端)                            │
│  ~/.openclaw/workspace/                                      │
│  ├── scripts/data-sync.sh      # 主同步脚本                  │
│  ├── memory/                   # 记忆数据                    │
│  ├── scripts/                  # 脚本文件                    │
│  └── .sync-state/              # 同步状态                    │
└───────────────────────┬─────────────────────────────────────┘
                        │ SSH反向隧道 :4444
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      VM节点 (本地)                            │
│  /opt/linlin/                                                │
│  ├── sync-receiver.sh          # 同步接收器                  │
│  ├── workspace/                # 同步数据                    │
│  └── .sync-state/              # 同步状态                    │
└─────────────────────────────────────────────────────────────┘
```

## 文件清单

### 主节点 (云端)

| 文件路径 | 说明 |
|---------|------|
| `~/.openclaw/workspace/scripts/data-sync.sh` | 主同步脚本 |
| `~/.openclaw/workspace/scripts/systemd/linlin-data-sync.timer` | Systemd定时器配置 |
| `~/.openclaw/workspace/scripts/systemd/linlin-data-sync@.service` | Systemd服务配置 |
| `~/.openclaw/workspace/scripts/systemd/linlin-data-sync-watch@.service` | 监控模式服务配置 |
| `~/.openclaw/workspace/docs/data-sync.md` | 本文档 |

### VM节点 (本地)

| 文件路径 | 说明 |
|---------|------|
| `/opt/linlin/sync-receiver.sh` | 同步接收器脚本 |
| `/opt/linlin/workspace/` | VM端同步目录 |

## 功能特性

### 1. 同步内容

- **memory/**: 记忆数据、日志、知识图谱等
- **scripts/**: 脚本文件
- **credentials/**: 凭据文件（可选，默认不同步）

### 2. 同步触发方式

| 方式 | 说明 | 配置 |
|-----|------|------|
| 定时同步 | 每30分钟自动同步 | Systemd Timer |
| 事件触发 | 文件变更时同步 | Watch Mode |
| 手动同步 | 一键执行同步 | CLI命令 |

### 3. 冲突解决策略

| 策略 | 说明 | 使用场景 |
|-----|------|---------|
| `timestamp` | 时间戳优先，保留较新版本 | 默认策略 |
| `manual` | 手动合并，标记冲突文件 | 重要文件 |
| `newer` | 同timestamp | 向后兼容 |

### 4. 同步特性

- **双向检测变更**: 检测两端文件变更
- **自动合并无冲突变更**: 无冲突时自动合并
- **冲突标记与通知**: 冲突时标记文件并通知
- **断点续传**: 支持rsync的partial传输

## 安装与配置

### 主节点配置

#### 1. 初始化同步系统

```bash
cd ~/.openclaw/workspace
./scripts/data-sync.sh init
```

#### 2. 测试VM连接

```bash
./scripts/data-sync.sh test
```

#### 3. 安装Systemd定时器（推荐）

```bash
# 复制服务文件到系统目录
sudo cp scripts/systemd/linlin-data-sync@.service /etc/systemd/system/
sudo cp scripts/systemd/linlin-data-sync.timer /etc/systemd/system/

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用并启动定时器（替换<username>为实际用户名）
sudo systemctl enable linlin-data-sync@<username>.timer
sudo systemctl start linlin-data-sync@<username>.timer

# 查看定时器状态
sudo systemctl list-timers --all | grep linlin
```

#### 4. 安装监控模式（可选）

```bash
# 复制服务文件
sudo cp scripts/systemd/linlin-data-sync-watch@.service /etc/systemd/system/
sudo systemctl daemon-reload

# 启用并启动监控服务
sudo systemctl enable linlin-data-sync-watch@<username>.service
sudo systemctl start linlin-data-sync-watch@<username>.service

# 需要先安装 inotify-tools
sudo apt-get install inotify-tools
```

### VM节点配置

#### 1. 部署接收器脚本

```bash
# 在主节点执行，将脚本复制到VM
scp -P 4444 ~/.openclaw/workspace/scripts/sync-receiver.sh linlin@localhost:/tmp/
ssh -p 4444 linlin@localhost "sudo mkdir -p /opt/linlin && sudo mv /tmp/sync-receiver.sh /opt/linlin/ && sudo chmod +x /opt/linlin/sync-receiver.sh"
```

#### 2. 初始化VM接收器

```bash
ssh -p 4444 linlin@localhost "/opt/linlin/sync-receiver.sh init"
```

#### 3. 安装为系统服务（可选）

```bash
ssh -p 4444 linlin@localhost "/opt/linlin/sync-receiver.sh install-service"
ssh -p 4444 linlin@localhost "sudo systemctl start linlin-sync-receiver"
```

## 使用指南

### 命令行接口

```bash
# 初始化同步系统
./scripts/data-sync.sh init

# 执行完整双向同步
./scripts/data-sync.sh sync

# 同步指定目录
./scripts/data-sync.sh sync memory
./scripts/data-sync.sh sync scripts

# 单向推送（主节点 -> VM）
./scripts/data-sync.sh push
./scripts/data-sync.sh push memory

# 单向拉取（VM -> 主节点）
./scripts/data-sync.sh pull
./scripts/data-sync.sh pull scripts

# 启动文件监控模式
./scripts/data-sync.sh watch

# 启动后台守护进程
./scripts/data-sync.sh daemon

# 停止守护进程
./scripts/data-sync.sh stop

# 查看同步状态
./scripts/data-sync.sh status

# 查看未解决的冲突
./scripts/data-sync.sh conflicts

# 测试VM连接
./scripts/data-sync.sh test

# 显示帮助
./scripts/data-sync.sh --help
```

### 高级选项

```bash
# 使用手动冲突解决策略
./scripts/data-sync.sh --conflict manual sync

# 设置同步间隔（秒）
./scripts/data-sync.sh --interval 600 daemon

# 启用调试模式
./scripts/data-sync.sh --debug sync
```

## 监控与日志

### 查看日志

```bash
# 同步日志
tail -f ~/.openclaw/workspace/logs/data-sync.log

# 冲突日志
cat ~/.openclaw/workspace/logs/sync-conflicts.log

# Systemd服务日志
sudo journalctl -u linlin-data-sync@<username> -f
sudo journalctl -u linlin-data-sync-watch@<username> -f
```

### 查看定时器状态

```bash
sudo systemctl list-timers --all | grep linlin
```

## 故障排除

### 常见问题

#### 1. 无法连接到VM

**症状**: `无法连接到VM节点，请检查SSH隧道`

**解决**:
```bash
# 检查SSH隧道
ssh -p 4444 linlin@localhost echo "测试"

# 检查端口监听
ss -tlnp | grep 4444
```

#### 2. 同步失败

**症状**: `同步到VM失败`

**解决**:
```bash
# 检查VM端目录权限
ssh -p 4444 linlin@localhost "ls -la /opt/linlin/"

# 手动测试rsync
rsync -avz -e "ssh -p 4444" /path/to/test/file linlin@localhost:/opt/linlin/workspace/
```

#### 3. 冲突文件过多

**症状**: 大量冲突文件堆积

**解决**:
```bash
# 查看冲突
./scripts/data-sync.sh conflicts

# 手动解决后删除标记文件
rm ~/.openclaw/workspace/.sync-state/conflicts/*/CONFLICT_INFO.txt
```

#### 4. 监控模式无法启动

**症状**: `inotifywait 未安装`

**解决**:
```bash
sudo apt-get install inotify-tools
```

## 安全注意事项

1. **SSH密钥**: 使用SSH密钥认证，避免密码
2. **访问控制**: VM端接收器限制允许的主机
3. **敏感数据**: credentials目录默认不同步
4. **日志保护**: 日志文件可能包含敏感信息，注意权限设置

## 配置参考

### 环境变量

| 变量 | 说明 | 默认值 |
|-----|------|-------|
| `DEBUG` | 启用调试模式 | `0` |
| `SYNC_INTERVAL` | 同步间隔（秒） | `1800` |
| `CONFLICT_STRATEGY` | 冲突策略 | `timestamp` |

### 配置文件

同步状态存储在 `~/.openclaw/workspace/.sync-state/`:
- `*.state`: 各目录同步状态
- `*.manifest`: 文件校验清单
- `conflicts/`: 冲突文件目录

## 更新与维护

### 更新同步脚本

```bash
cd ~/.openclaw/workspace
git pull  # 如果有版本控制
./scripts/data-sync.sh init
```

### 清理旧日志

```bash
# 保留最近30天的日志
find ~/.openclaw/workspace/logs -name "*.log" -mtime +30 -delete
```

### 重建同步状态

```bash
# 如果状态损坏，可以重建
rm -rf ~/.openclaw/workspace/.sync-state
./scripts/data-sync.sh init
./scripts/data-sync.sh sync
```

## 技术支持

- 查看日志: `~/.openclaw/workspace/logs/data-sync.log`
- 提交Issue: 使用项目管理工具
- 文档更新: 编辑 `docs/data-sync.md`

---

*文档版本: 1.0*  
*最后更新: 2026-02-11*
