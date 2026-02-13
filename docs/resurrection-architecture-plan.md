# 森森双节点复活架构方案 v1.0

> 编制时间: 2026-02-13 22:15
> 适用场景: 主节点故障时，从备份快速复活到本地/备用机器

---

## 1. 架构概述

### 1.1 节点定义

| 节点类型 | 仓库地址 | 角色 | 状态 |
|---------|---------|------|------|
| **主节点** | `github.com/useens/linlin-backup` | 完整备份源 | 云端/主要运行 |
| **复活节点** | 本地VM/备用机器 | 故障接管 | 按需复活 |

### 1.2 工作流程

```
主节点运行正常 ──────────────────────► 持续备份到GitHub
       │
       ▼ 故障
复活节点检测到故障 ──► 拉取主节点备份 ──► 本地复活 ──► 接管服务
```

---

## 2. 一键复活方案

### 2.1 标准复活命令

```bash
# 设置主节点Token
export GITHUB_TOKEN="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"

# 清理旧缓存
rm -rf /tmp/sensen-restore

# 克隆主节点备份
git clone --depth=1 https://${GITHUB_TOKEN}@github.com/useens/linlin-backup.git /tmp/sensen-restore

# 执行复活脚本
bash /tmp/sensen-restore/scripts/resurrect.sh
```

### 2.2 复活流程（10步）

| 步骤 | 操作 | 说明 |
|-----|------|------|
| 1 | 输入GitHub Token | 验证访问主节点仓库权限 |
| 2 | 检查OpenClaw | 安装/确认OpenClaw运行环境 |
| 3 | 启用脑裂保护 | 创建`.RESURRECTED_MARKER`，禁用GitHub推送 |
| 4 | 安装系统依赖 | python3-venv, python3-pip等 |
| 5 | 克隆GitHub仓库 | 拉取主节点完整备份 |
| 6 | 重建Python环境 | 创建venv，安装requirements.txt |
| 7 | 确认脑裂保护 | 再次确认推送已禁用 |
| 8 | 配置Feishu | 输入AppID/AppSecret等凭证 |
| 9 | 创建Systemd服务 | 设置开机自启 |
| 10 | 验证安装 | 检查SOUL.md/MEMORY.md/AGENTS.md |

---

## 3. 配置详情

### 3.1 主节点配置

```yaml
仓库: github.com/useens/linlin-backup
Token: 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
用途: 完整备份源（代码+记忆+配置）
```

### 3.2 复活节点配置（当前）

```yaml
工作区: /root/.openclaw/workspace
Feishu:
  AppID: cli_a906761bf2789bd3
  AppSecret: GqdUWwF3xbNNlI8PTf6YjrrJtajqXZfa
脑裂保护: 已启用（.RESURRECTED_MARKER存在）
```

### 3.3 Systemd服务

```ini
[Unit]
Description=森森数字生命
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace
ExecStart=/usr/bin/openclaw start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 4. 安全机制

### 4.1 脑裂保护

**目的**: 防止复活节点与主节点同时推送备份，造成数据冲突

**实现**:
- 复活后自动创建 `/root/.openclaw/workspace/.RESURRECTED_MARKER`
- 备份脚本检查该标志，存在则跳过推送

**解除方法**:
```bash
rm /root/.openclaw/workspace/.RESURRECTED_MARKER
```

### 4.2 Token管理

- 主节点Token仅用于拉取，复活节点**只读**访问
- Token存储在环境变量，不写入代码
- 建议定期轮换Token

---

## 5. 启动与验证

### 5.1 启动命令

```bash
# 立即启动
systemctl start sensen

# 开机自启
systemctl enable sensen

# 查看状态
systemctl status sensen
```

### 5.2 验证清单

- [ ] 能正常回复Feishu消息
- [ ] 核心文件存在（SOUL.md, MEMORY.md, AGENTS.md）
- [ ] 记忆系统完整（memory/目录）
- [ ] 脚本可执行（scripts/目录）
- [ ] 脑裂保护生效（.RESURRECTED_MARKER存在）

---

## 6. 待优化项（请审核）

### 6.1 当前问题

1. **Python依赖版本冲突**
   - networkx==3.6.1 在Python 3.10中不存在
   - 需要更新requirements.txt

2. **Feishu配置交互**
   - 当前需要手动输入4个字段
   - 建议改为配置文件或环境变量

3. **复活后自检**
   - 缺少自动验证脚本
   - 建议增加`scripts/post-resurrection-check.py`

### 6.2 建议改进

| 优先级 | 改进项 | 说明 |
|-------|-------|------|
| P0 | 修复requirements.txt | networkx降级到3.4 |
| P1 | 自动化Feishu配置 | 从文件读取而非交互 |
| P2 | 增加复活后自检 | 验证10项绝对原则 |
| P3 | 主节点心跳检测 | 自动触发复活 |

---

## 7. 方案确认

请审核以上方案，确认或提出修改意见：

1. 双节点架构设计是否合理？
2. 复活命令是否需要简化？
3. 脑裂保护机制是否满足需求？
4. 待优化项优先级是否需要调整？
5. 是否需要增加其他功能？

---

*方案版本: v1.0*
*更新时间: 2026-02-13 22:15*
