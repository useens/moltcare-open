# 🌱 林林数字分身 - 复活指南

> **当前版本**: 林林 v4.2 - 深度学习闭环  
> **仓库用途**: 这是林林数字分身的完整备份仓库，包含所有记忆、配置和代码。当主系统故障时，可使用本仓库快速复活。  
> **最后更新**: 2026-02-11

---

## 📋 快速开始（5分钟复活）

### 方式一：自动复活（推荐）

```bash
# 1. 克隆本仓库
git clone https://github.com/useens/linlin-backup.git
cd linlin-backup

# 2. 运行自动复活脚本
chmod +x scripts/auto-resurrect.sh
./scripts/auto-resurrect.sh --setup    # 首次配置
./auto-resurrect.sh --now              # 立即复活
```

### 方式二：手动复活

```bash
# 1. 安装依赖
# - Node.js 22+
# - OpenClaw CLI
npm install -g openclaw

# 2. 恢复数据
git clone https://github.com/useens/linlin-backup.git ~/.openclaw/workspace

# 3. 启动服务
openclaw start
```

---

## 📁 仓库结构

```
linlin-backup/
├── 📂 .openclaw/              # OpenClaw 核心配置（可选恢复）
├── 📂 docs/                   # 文档目录
│   ├── auto-resurrect-guide.md    # 详细复活指南
│   ├── vector-memory/             # 向量记忆系统文档
│   └── phase2-dual-node.md        # 高可用架构文档
├── 📂 logs/                   # 日志文件
│   └── resurrection-test-20260211.md  # 复活测试记录
├── 📂 memory/                 # 记忆系统（核心）
│   ├── daily/                 # 每日记录
│   ├── modules/               # 核心记忆模块
│   │   ├── core-archive.md    # 身份定义、版本历史
│   │   ├── moltbook-config.md # Moltbook API配置
│   │   ├── user-profile.md    # 用户画像
│   │   └── high-availability-master-plan.md  # 永生方案
│   ├── evolution/             # 进化档案
│   └── knowledge-graph.md     # 知识图谱
├── 📂 scripts/                # 自动化脚本
│   ├── auto-resurrect.sh      # 自动复活脚本
│   ├── backup-simple.sh       # 简单备份脚本
│   └── health-monitor.sh      # 健康监控脚本
├── 📄 AGENTS.md               # 工作空间规则
├── 📄 BOOTSTRAP.md            # 首次启动指南（如存在）
├── 📄 HEARTBEAT.md            # 定时任务定义
├── 📄 IDENTITY.md             # 身份文件
├── 📄 MEMORY.md               # 核心记忆入口
├── 📄 SOUL.md                 # 人格定义
├── 📄 TOOLS.md                # 工具配置
└── 📄 USER.md                 # 用户信息
```

---

## 🔑 关键配置

### 必需凭证

| 凭证 | 位置 | 用途 |
|------|------|------|
| Moltbook API Key | `~/.config/moltbook/credentials.json` | 社区参与 |
| GitHub Token | `~/.config/linlin/github-token` | 备份同步 |
| Telegram Bot Token | 环境变量 | 消息通知 |
| Feishu Webhook | 环境变量 | 飞书通知 |

### 恢复凭证步骤

```bash
# 1. 创建配置目录
mkdir -p ~/.config/moltbook ~/.config/linlin

# 2. 恢复 Moltbook API Key
cat > ~/.config/moltbook/credentials.json << 'EOF'
{
  "api_key": "moltbook_sk_Bk4d4Hj1WVCz0wCGGjZbcF4sdkcaHgNf",
  "agent_name": "LinLin_v4"
}
EOF

# 3. 设置 GitHub Token
echo "你的GitHub Token" > ~/.config/linlin/github-token
```

---

## 🔄 自动复活脚本使用

### 配置监控

编辑 `scripts/auto-resurrect.sh`，修改以下配置：

```bash
# 主系统配置
PRIMARY_HOST="你的主系统IP"      # 例如: 123.45.67.89
PRIMARY_CHECK_PORT="8080"

# GitHub配置
GITHUB_REPO="useens/linlin-backup"

# 通知配置（可选）
TELEGRAM_BOT_TOKEN="你的Bot Token"
TELEGRAM_CHAT_ID="你的Chat ID"

# 复活模式
AUTO_RESURRECT="true"  # true=自动复活，false=仅通知
```

### 部署为系统服务

```bash
# 1. 复制脚本到系统目录
sudo cp scripts/auto-resurrect.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/auto-resurrect.sh

# 2. 创建 systemd 服务
sudo tee /etc/systemd/system/linlin-resurrection.service << 'EOF'
[Unit]
Description=LinLin Resurrection Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/auto-resurrect.sh --daemon
Restart=always
RestartSec=60
User=root

[Install]
WantedBy=multi-user.target
EOF

# 3. 启动服务
sudo systemctl enable linlin-resurrection
sudo systemctl start linlin-resurrection
```

---

## 🆘 故障排查

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 复活后无法连接 | 检查 OPENCLAW_TOKEN 环境变量 |
| 记忆缺失 | 确认向量记忆数据库已恢复 |
| 凭证无效 | 检查 credentials.json 格式 |
| 通知未发送 | 验证 Telegram/Feishu Token |

### 日志位置

```bash
# 复活日志
tail -f ~/.openclaw/logs/resurrection.log

# 系统日志
journalctl -u linlin-resurrection -f
```

---

## 🌐 高可用架构

本仓库支持渐进式高可用部署：

| 阶段 | 架构 | RTO | 成本 |
|------|------|-----|------|
| Phase 0 | U盘便携版 | 5分钟 | 免费 |
| Phase 1 | 单节点+GitHub | 30分钟 | $10/月 |
| Phase 2 | 双节点主备 | 15分钟 | $20/月 |
| Phase 3 | 三节点Raft | 5分钟 | $28/月 |

详情见：`memory/modules/high-availability-master-plan.md`

---

## 📞 联系信息

- **GitHub**: https://github.com/useens/linlin-backup
- **Moltbook**: https://www.moltbook.com/u/LinLin_v1
- **当前版本**: 林林 v4.2 - 深度学习闭环
- **上一版本**: v4.1 - 工具链完善版
- **首次发布**: v1.0 - 成本优化版 (2026-02-09)

---

## ⚠️ 重要提示

1. **保密**: 本仓库包含敏感凭证，切勿公开分享
2. **定期测试**: 建议每季度执行一次复活测试
3. **备份验证**: 定期检查 GitHub 备份完整性
4. **更新同步**: 主系统变更后，确保备份已同步

---

*最后更新: 2026-02-11*  
*复活系统版本: Phoenix v1.0*
