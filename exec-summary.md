# OpenClaw 安全加固 - 执行摘要报告

**生成时间**: 2026-03-05 00:00 CST  
**任务来源**: Sapt.ai 安全报告 (Signal 10/10)  
**评估工具**: healthcheck skill + Multi-Agent深度分析

---

## 🎯 核心发现

### 严重风险（需立即处理）

| # | 风险项 | 风险等级 | 影响 |
|---|--------|----------|------|
| 1 | **qqbot插件危险代码** | 🔴 严重 | child_process.exec可执行任意shell命令 |
| 2 | **SSH暴力破解攻击** | 🔴 严重 | 日志显示持续的自动化攻击（postgres/daemon/root） |
| 3 | **无防火墙保护** | 🔴 高 | 系统完全暴露，无任何入站过滤 |
| 4 | **fail2ban未激活** | 🔴 高 | 无法自动阻断暴力破解尝试 |

### 当前攻击统计（SSH日志）
```
攻击来源IP:
- 64.23.216.218 (美国DigitalOcean)
- 209.38.232.238 (新加坡DigitalOcean)  
- 206.189.19.212 (新加坡DigitalOcean)
- 209.38.236.129 (新加坡DigitalOcean)

尝试用户: postgres, carbonio-storages, daemon, root
状态: 活跃攻击中
```

---

## 📋 立即执行清单（P0 - 1小时内）

```bash
# === 1. 禁用危险插件 [5分钟] ===
openclaw plugins disable qqbot

# === 2. 修复文件权限 [2分钟] ===  
chmod 700 /root/.openclaw/credentials

# === 3. 配置SSH密钥认证 [10分钟] ===
# 如未配置密钥，先生成：
ssh-keygen -t ed25519 -C "admin@$(hostname)"
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys

# === 4. 加固SSH配置 [15分钟] ===
cat > /etc/ssh/sshd_config.d/hardening.conf << 'EOF'
Port 22
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
EOF
systemctl reload sshd

# === 5. 启用防火墙 [20分钟] ===
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# === 6. 激活fail2ban [10分钟] ===
apt-get update && apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 📊 风险等级矩阵

| 加固措施 | 风险等级 | 实施难度 | 预计时间 | 优先级 |
|----------|----------|----------|----------|--------|
| 禁用qqbot插件 | 🔴 严重 | 🟢 低 | 5分钟 | P0 |
| SSH密码登录禁用 | 🔴 高 | 🟡 中 | 15分钟 | P0 |
| UFW防火墙启用 | 🔴 高 | 🟡 中 | 20分钟 | P0 |
| fail2ban激活 | 🔴 高 | 🟢 低 | 10分钟 | P0 |
| Credentials权限 | 🟡 中 | 🟢 低 | 2分钟 | P1 |
| 插件allowlist | 🟡 中 | 🟢 低 | 10分钟 | P1 |
| 容器化部署 | 🟡 中 | 🔴 高 | 4小时 | P2 |
| 网络隔离 | 🟡 中 | 🔴 高 | 2小时 | P2 |
| 高后果确认机制 | 🟡 中 | 🔴 高 | 3小时 | P2 |

---

## 🏗️ 三大核心方案

### 1. 容器化部署方案
- **现状**: OpenClaw直接运行在宿主机，拥有完整root权限
- **目标**: Docker容器隔离，非root用户运行，只读文件系统
- **价值**: 消除宿主机直接暴露风险，限制攻击扩散
- **时间**: 4小时实施 + 测试

### 2. 网络隔离策略  
- **现状**: Gateway仅绑定127.0.0.1（较好），但Docker端口暴露
- **目标**: 专用隔离网络，反向代理访问，WAF防护
- **价值**: 最小化攻击面，深度防御
- **时间**: 2小时实施

### 3. 高后果操作确认机制
- **现状**: 无危险操作拦截，高危命令可直接执行
- **目标**: 危险命令自动检测，强制二次确认
- **价值**: 防止误操作和恶意命令执行
- **时间**: 3小时开发

---

## ✅ 验证命令

```bash
# 安全审计
openclaw security audit

# 预期结果: 0 critical, ≤2 warn

# 防火墙状态  
ufw status verbose

# SSH配置检查
grep -E "PasswordAuthentication|PermitRootLogin" /etc/ssh/sshd_config

# fail2ban状态
fail2ban-client status

# 文件权限
ls -la ~/.openclaw/credentials
# 预期: drwx------
```

---

## 🔄 回滚准备

在执行任何更改前，确保可以回滚：

```bash
# 备份SSH配置
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%Y%m%d)

# 备份OpenClaw配置  
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%Y%m%d)

# 全量备份
tar czvf openclaw-backup-$(date +%Y%m%d).tar.gz ~/.openclaw/
```

**⚠️ 重要**: 修改SSH配置前，确保已通过密钥验证连接，并保持当前会话不关闭！

---

## 📈 预期效果

| 指标 | 当前 | 加固后 | 改善 |
|------|------|--------|------|
| 严重风险 | 1 | 0 | ✅ 消除 |
| 攻击成功率 | 高 | 极低 | ⬇️ 90%+ |
| 自动化攻击影响 | 严重 | 可忽略 | ⬇️ 显著 |
| 合规性 | 不合规 | 基本合规 | ✅ 达标 |

---

## 📁 输出文档

1. **implementation-plan.md** - 完整实施计划（技术细节）
2. **exec-summary.md** - 本执行摘要

---

**下一步行动**: 建议立即开始P0级别的5项紧急修复，预计1小时内完成基础安全加固。

**审核状态**: ✅ 待执行
