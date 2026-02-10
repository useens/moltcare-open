# 林林自动复活系统 - 部署指南

> 让本地VM成为你的"复活种子"，主系统故障时自动/半自动原地复活

---

## 快速开始（3步完成）

### 第1步：在本地VM上保存脚本

```bash
# 下载脚本到本地VM
curl -o ~/resurrect-me.sh https://raw.githubusercontent.com/你的用户名/linlin-backup/main/scripts/auto-resurrect.sh

# 或者手动复制上面生成的脚本
chmod +x ~/resurrect-me.sh
```

### 第2步：配置GitHub Token

```bash
# 1. 访问 https://github.com/settings/tokens
# 2. 生成新Token，权限只需要: repo (读私有仓库)
# 3. 保存Token
mkdir -p ~/.config/linlin
echo "ghp_xxxxxxxxxxxx" > ~/.config/linlin/github-token
chmod 600 ~/.config/linlin/github-token
```

### 第3步：运行配置向导

```bash
~/resurrect-me.sh --setup
```

按提示输入：
- 主系统IP/域名
- GitHub仓库名（如: zhangsan/linlin-backup）
- GitHub Token
- Telegram通知（可选）
- 是否启用自动复活

---

## 使用方式

### 方式一：手动触发（推荐）

主系统故障时，你在本地VM执行：

```bash
~/resurrect-me.sh --now
```

5分钟后，我原地复活。

### 方式二：自动监控

让本地VM持续监控主系统：

```bash
# 添加到系统服务，开机自动监控
sudo tee /etc/systemd/system/linlin-resurrect.service > /dev/null << 'EOF'
[Unit]
Description=LinLin Auto Resurrection Monitor
After=network.target

[Service]
Type=simple
User=你的用户名
ExecStart=/home/你的用户名/resurrect-me.sh --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable linlin-resurrect
sudo systemctl start linlin-resurrect
```

这样本地VM会每30秒检测一次主系统，故障时：
- `AUTO_RESURRECT=true`：自动复活并通知你
- `AUTO_RESURRECT=false`：发送通知等你手动确认

### 方式三：定时检测（crontab）

```bash
# 每5分钟检测一次
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/你的用户名/resurrect-me.sh") | crontab -
```

---

## 凭证管理

### 方案A：复活时手动输入（最安全）

默认行为，不需要额外配置，复活时交互式输入API Keys。

### 方案B：预存加密凭证（一键复活）

如果你希望完全自动，可以预存加密凭证：

```bash
# 1. 创建凭证文件
cat > ~/.config/linlin/my-credentials.sh << 'EOF'
export TELEGRAM_BOT_TOKEN="你的Token"
export MOLTBOOK_API_KEY="你的Key"
export FEISHU_APP_ID="你的ID"
export FEISHU_APP_SECRET="你的Secret"
# ... 其他凭证
EOF

# 2. GPG加密（需要设置GPG密钥）
gpg --symmetric --cipher-algo AES256 \
    -o ~/.config/linlin/credentials.gpg \
    ~/.config/linlin/my-credentials.sh

# 3. 删除明文
rm ~/.config/linlin/my-credentials.sh

# 4. 测试解密
gpg --decrypt ~/.config/linlin/credentials.gpg
```

---

## 配置文件详解

配置文件位置：`~/.config/linlin/resurrection.conf`

```bash
# 主系统配置
PRIMARY_HOST="123.45.67.89"          # 主系统IP或域名
PRIMARY_CHECK_PORT="8080"             # OpenClaw端口

# GitHub配置
GITHUB_REPO="zhangsan/linlin-backup"  # 备份仓库

# 通知配置
TELEGRAM_BOT_TOKEN="123456:ABC..."    # Telegram Bot Token
TELEGRAM_CHAT_ID="123456789"          # 你的Chat ID
FEISHU_WEBHOOK="https://open.feishu.cn/..."  # 飞书Webhook

# 复活行为
AUTO_RESURRECT="false"                # true=自动复活, false=通知等待
MAX_RETRIES=3                         # 检测失败几次判定故障
CHECK_INTERVAL=30                     # 检测间隔（秒）
```

---

## 完整复活流程演示

```
主系统故障
    │
    ▼
本地VM检测失败 (3次)
    │
    ▼
发送通知: "🚨 主系统故障，准备复活"
    │
    ▼
┌─────────────────┐
│ AUTO_RESURRECT  │
│   = false?      │
└────────┬────────┘
         │
    是 ──┼──► 等待你执行: ~/resurrect-me.sh --now
         │
    否 ──┘
         ▼
从GitHub拉取最新备份
    │
    ▼
备份当前工作区（如果有）
    │
    ▼
恢复GitHub备份
    │
    ▼
恢复API凭证
    │
    ▼
启动OpenClaw
    │
    ▼
发送通知: "✅ 复活成功！新IP: xxx.xxx.xxx.xxx"
    │
    ▼
记录复活日志到 RESURRECTION_LOG.md
```

---

## 故障排查

### 检查日志

```bash
# 查看复活系统日志
tail -f ~/.openclaw/logs/resurrection.log

# 检查OpenClaw状态
openclaw gateway status

# 检查GitHub连接
curl -H "Authorization: token $(cat ~/.config/linlin/github-token)" \
     https://api.github.com/user
```

### 测试备份拉取

```bash
# 手动测试能否拉到备份
cd /tmp
rm -rf test-backup
git clone --depth 1 "https://$(cat ~/.config/linlin/github-token)@github.com/你的用户名/linlin-backup.git" test-backup
ls test-backup
```

### 常见问题

**Q: GitHub Token无效？**
```bash
# 检查Token
gh auth status
# 或重新生成Token，确保有repo权限
```

**Q: 主系统检测总是失败？**
```bash
# 测试网络连通
ping 你的主系统IP
nc -zv 你的主系统IP 8080
```

**Q: OpenClaw启动失败？**
```bash
# 检查端口占用
sudo lsof -i :8080

# 手动启动看错误
openclaw gateway start --verbose
```

---

## 安全建议

1. **GitHub Token权限**：只给`repo`读权限，不要写权限
2. **Token存储**：设置文件权限`chmod 600`，不要明文存储在其他地方
3. **API Keys**：建议用GPG加密存储，或复活时手动输入
4. **网络隔离**：本地VM不需要暴露任何端口给外网
5. **定期更换**：每3个月更换一次GitHub Token

---

## 升级维护

### 更新复活脚本

```bash
# 从GitHub拉取最新脚本
curl -o ~/resurrect-me.sh https://raw.githubusercontent.com/你的用户名/linlin-backup/main/scripts/auto-resurrect.sh
chmod +x ~/resurrect-me.sh
```

### 定期测试

```bash
# 每月测试一次复活流程（不实际恢复，只测试备份可拉取）
~/resurrect-me.sh --check
```

---

## 总结

| 功能 | 命令 |
|------|------|
| 配置向导 | `~/resurrect-me.sh --setup` |
| 立即复活 | `~/resurrect-me.sh --now` |
| 检测状态 | `~/resurrect-me.sh --check` |
| 守护模式 | `~/resurrect-me.sh --daemon` |
| 查看帮助 | `~/resurrect-me.sh --help` |

现在你的本地VM就是一个完整的"复活种子"了！🌱
