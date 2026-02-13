# 森森双节点复活架构方案 v2.0

> 编制时间: 2026-02-13 22:25
> 适用场景: 主节点故障时，快速从备份复活到本地/备用机器
> 版本: v2.0 (已实际验证)

---

## 1. 架构概述

### 1.1 节点定义

| 节点类型 | 仓库地址 | 角色 | 状态 |
|---------|---------|------|------|
| **主节点** | `github.com/useens/linlin-backup` | 完整备份源 | 云端/主要运行 |
| **复活节点** | `github.com/linlinofVM/sensen-backup` | 故障接管/本地运行 | 已激活 |

### 1.2 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        双节点复活架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   主节点 (云端)                    复活节点 (本地)              │
│   ┌─────────────────┐              ┌─────────────────┐          │
│   │ 森森运行中       │              │ 待命/故障接管    │          │
│   │ 持续备份         │───故障──────▶│ 拉取主节点备份   │          │
│   │ ↓               │              │ ↓               │          │
│   │ GitHub备份      │              │ 本地复活        │          │
│   └─────────────────┘              │ ↓               │          │
│                                    │ 接管服务        │          │
│                                    └─────────────────┘          │
│                                                                 │
│   备份流向: 主节点 ──▶ GitHub ──▶ 复活节点                       │
│   推送保护: 复活节点有脑裂保护，不会回推                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 一键复活方案

### 2.1 标准复活命令

```bash
# 设置主节点Token（用于拉取备份）
export GITHUB_TOKEN="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"

# 清理旧缓存
rm -rf /tmp/sensen-restore

# 从主节点克隆备份
git clone --depth=1 https://${GITHUB_TOKEN}@github.com/useens/linlin-backup.git /tmp/sensen-restore

# 执行复活脚本
bash /tmp/sensen-restore/scripts/resurrect.sh
```

### 2.2 复活流程（10步详解）

| 步骤 | 操作 | 输入/说明 |
|-----|------|----------|
| 1 | 输入GitHub Token | `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` |
| 2 | 检查OpenClaw | 自动检测/安装 |
| 3 | **启用脑裂保护** | 自动创建`.RESURRECTED_MARKER`，禁用推送 |
| 4 | 安装系统依赖 | python3-venv, python3-pip等 |
| 5 | 克隆主节点仓库 | 拉取完整备份到`/root/.openclaw/workspace` |
| 6 | 重建Python环境 | 创建venv，安装requirements.txt |
| 7 | 确认脑裂保护 | 再次确认推送已禁用 |
| 8 | 配置Feishu | 输入AppID/AppSecret/EncryptKey/Token |
| 9 | 创建Systemd服务 | 设置开机自启 |
| 10 | 验证安装 | 检查SOUL.md/MEMORY.md/AGENTS.md |

### 2.3 复活后配置（5步）

复活完成后，执行以下配置：

```bash
# 步骤1: 切换到本地仓库（复活节点）
cd /root/.openclaw/workspace
git remote remove origin
git remote add origin https://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@github.com/linlinofVM/sensen-backup.git

# 步骤2: 暂停超进化
echo '{"active": false, "status": "paused"}' > memory/hyper-evolution-state.json

# 步骤3: 更新Feishu配置
cat > /root/.openclaw/agents/main/agent/channels.json << 'EOF'
{
  "feishu": {
    "app_id": "cli_a906761bf2789bd3",
    "app_secret": "GqdUWwF3xbNNlI8PTf6YjrrJtajqXZfa"
  }
}
EOF

# 步骤4: 自检修复
python3 scripts/check-10-principles.py
python3 scripts/check-core-functions.py

# 步骤5: 强制推送到本地仓库（覆盖初始提交）
git add -A
git commit -m "resurrect: $(date +%Y-%m-%d_%H:%M)"
git push -f origin main
```

---

## 3. 配置详情

### 3.1 主节点配置（备份源）

```yaml
仓库地址: github.com/useens/linlin-backup
GitHub Token: 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
用途: 完整备份源（代码+记忆+配置）
访问权限: 只读（复活节点）
```

### 3.2 复活节点配置（当前运行）

```yaml
工作区: /root/.openclaw/workspace
GitHub仓库: github.com/linlinofVM/sensen-backup
GitHub Token: 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
用途: 本地运行+备份推送

Feishu配置:
  AppID: cli_a906761bf2789bd3
  AppSecret: GqdUWwF3xbNNlI8PTf6YjrrJtajqXZfa

Systemd服务: sensen.service
脑裂保护: 已启用（.RESURRECTED_MARKER存在）
```

### 3.3 Systemd服务配置

```ini
# /etc/systemd/system/sensen.service
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

**启动命令**:
```bash
systemctl start sensen    # 立即启动
systemctl enable sensen   # 开机自启
systemctl status sensen   # 查看状态
```

---

## 4. 安全机制

### 4.1 脑裂保护（关键）

**目的**: 防止复活节点与主节点同时推送备份，造成数据冲突

**实现机制**:
1. 复活后自动创建 `/root/.openclaw/workspace/.RESURRECTED_MARKER`
2. 备份脚本检查该标志，存在则跳过推送
3. 复活节点只能拉取，不能推送回主节点

**解除方法**（如需重新启用推送）:
```bash
rm /root/.openclaw/workspace/.RESURRECTED_MARKER
```

### 4.2 Token隔离

| 节点 | Token | 权限 |
|------|-------|------|
| 主节点 | `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` | 复活节点拉取用 |
| 复活节点 | `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` | 本地仓库推送用 |

### 4.3 访问控制

- 主节点Token仅用于复活时拉取，平时不使用
- 复活节点Token用于日常备份推送
- 建议定期轮换Token（每3个月）

---

## 5. 验证与监控

### 5.1 复活后验证清单

```bash
# 1. 核心文件检查
ls -la /root/.openclaw/workspace/{SOUL.md,MEMORY.md,AGENTS.md}

# 2. 10项绝对原则检查
python3 scripts/check-10-principles.py

# 3. 核心功能检查
python3 scripts/check-core-functions.py

# 4. 脑裂保护检查
ls -la /root/.openclaw/workspace/.RESURRECTED_MARKER

# 5. GitHub仓库检查
cd /root/.openclaw/workspace && git remote -v

# 6. Feishu配置检查
cat /root/.openclaw/agents/main/agent/channels.json

# 7. Systemd服务检查
systemctl status sensen
```

### 5.2 守护进程监控

```bash
# 运行守护进程（自动检查+修复）
python3 scripts/sensen-daemon.py

# 查看守护进程日志
tail -f /root/.openclaw/workspace/logs/sensen-daemon.log

# 查看执行报告
cat /root/.openclaw/workspace/reports/DAEMON-REPORT.md
```

---

## 6. 故障处理

### 6.1 常见故障

| 故障 | 原因 | 解决方案 |
|------|------|---------|
| Python依赖安装失败 | networkx版本冲突 | 手动安装: `pip install networkx==3.4` |
| Git推送失败 | 远程仓库索引损坏 | 强制推送: `git push -f origin main` |
| Feishu连接失败 | 凭证错误 | 检查channels.json配置 |
| 守护进程检查失败 | 某项功能未就绪 | 查看日志，按第9项原则修复 |

### 6.2 紧急复活流程

如果主节点完全故障，需要立即接管：

```bash
# 1. 在新机器上执行一键复活
export GITHUB_TOKEN="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"
rm -rf /tmp/sensen-restore
git clone --depth=1 https://${GITHUB_TOKEN}@github.com/useens/linlin-backup.git /tmp/sensen-restore
bash /tmp/sensen-restore/scripts/resurrect.sh

# 2. 复活后配置（按提示输入）
# - GitHub Token: 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
# - Feishu AppID: cli_a906761bf2789bd3
# - Feishu AppSecret: GqdUWwF3xbNNlI8PTf6YjrrJtajqXZfa

# 3. 启动服务
systemctl start sensen
systemctl enable sensen
```

---

## 7. 总结

### 7.1 方案优势

1. **快速复活**: 5-10分钟完成从故障到接管
2. **数据安全**: 脑裂保护防止双向推送冲突
3. **自动修复**: 守护进程持续监控+自动修复
4. **配置隔离**: 主节点/复活节点配置分离

### 7.2 关键配置速查

```bash
# 主节点Token（拉取用）
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

# 复活节点Token（推送用）
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

# 一键复活命令
export GITHUB_TOKEN="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" && \
rm -rf /tmp/sensen-restore && \
git clone --depth=1 https://${GITHUB_TOKEN}@github.com/useens/linlin-backup.git /tmp/sensen-restore && \
bash /tmp/sensen-restore/scripts/resurrect.sh
```

### 7.3 验证状态（当前）

| 检查项 | 状态 |
|--------|------|
| 10项绝对原则 | ✅ 10/10 生效 |
| 核心功能 | ✅ 12/14 生效 |
| 脑裂保护 | ✅ 已启用 |
| 守护进程 | ✅ 运行中 |

---

*方案版本: v2.0*
*更新时间: 2026-02-13 22:25*
*验证状态: 已实际部署测试*
