# OpenClaw 安全加固实施计划

> **任务来源**: Sapt.ai 安全报告 (Signal 10/10)  
> **生成时间**: 2026-03-05  
> **评估模型**: Multi-Agent深度安全分析

---

## 📊 执行摘要

当前OpenClaw部署存在**1个严重风险**、**7个警告**和**1个信息提示**。本计划提供从容器化部署、网络隔离到高后果操作确认机制的完整加固方案。

---

## 🔴 风险评估矩阵

| 风险项 | 风险等级 | 实施难度 | 预计完成时间 | 紧急程度 |
|--------|----------|----------|--------------|----------|
| qqbot插件危险代码模式 | **严重** | 低 | 5分钟 | P0 |
| SSH配置不安全 | **高** | 中 | 15分钟 | P0 |
| 无防火墙保护 | **高** | 中 | 20分钟 | P0 |
| fail2ban未激活 | **高** | 低 | 10分钟 | P0 |
| Credentials目录权限过宽 | **中** | 低 | 2分钟 | P1 |
| 多用户环境隔离不足 | **中** | 高 | 2小时 | P2 |
| 插件无allowlist | **中** | 低 | 10分钟 | P1 |
| 扩展工具宽松策略 | **中** | 中 | 30分钟 | P2 |
| 反向代理头配置 | **低** | 低 | 5分钟 | P3 |

---

## 🎯 加固措施详解

### 一、立即执行（P0 - 严重风险）

#### 1.1 qqbot插件危险代码处理 [严重/难度:低/5分钟]

**风险描述**:
```
CRITICAL: plugins.code_safety
Plugin "qqbot" contains dangerous code patterns
Found 1 critical issue(s) in 47 scanned file(s):
- [dangerous-exec] Shell command execution detected (child_process) (bin/qqbot-cli.js:109)
```

**影响分析**:
- 攻击者可能通过qqbot通道执行任意shell命令
- 插件来源未经验证，存在供应链攻击风险
- child_process.exec可直接执行系统命令

**加固措施**:
```bash
# 方案A: 立即禁用qqbot插件（推荐）
openclaw plugins disable qqbot

# 方案B: 如必须使用，严格限制权限
# 在openclaw.json中添加沙箱配置
```

**配置修改**:
```json
{
  "plugins": {
    "entries": {
      "qqbot": {
        "enabled": false
      }
    }
  }
}
```

**验证**:
```bash
openclaw security audit | grep qqbot
# 预期: 无qqbot相关警告
```

---

#### 1.2 SSH安全配置加固 [高/难度:中/15分钟]

**当前风险配置**:
```
Port 22
PermitRootLogin yes
PasswordAuthentication yes
```

**风险分析**:
- 日志显示持续的暴力破解攻击（postgres, carbonio-storages, daemon等无效用户）
- root密码登录 enabled 允许直接root访问
- 攻击来源: 64.23.216.218, 209.38.232.238, 206.189.19.212 等

**加固措施**:

```bash
# 1. 备份原配置
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%Y%m%d)

# 2. 修改SSH配置
cat > /etc/ssh/sshd_config.d/hardening.conf << 'EOF'
# OpenClaw Security Hardening
Port 22
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 60
AllowUsers root@10.0.0.* root@127.0.0.1
EOF

# 3. 确保有SSH密钥再禁用密码登录
# 检查现有密钥
ls -la ~/.ssh/authorized_keys

# 4. 测试配置
sshd -t

# 5. 重启SSH（保持现有连接）
systemctl reload sshd
```

**回滚计划**:
```bash
# 如果无法连接，通过控制台执行:
cp /etc/ssh/sshd_config.bak.20260305 /etc/ssh/sshd_config
systemctl restart sshd
```

---

#### 1.3 防火墙配置 [高/难度:中/20分钟]

**当前状态**: 无活动防火墙规则

**加固措施**:

```bash
# 1. 启用UFW
ufw --force enable

# 2. 默认拒绝策略
ufw default deny incoming
ufw default allow outgoing

# 3. 允许必要端口
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# 4. OpenClaw相关端口（仅本地）
# Gateway已在127.0.0.1绑定，无需外部开放

# 5. Docker容器端口管理
# 限制暴露的Docker端口
ufw allow from 10.0.0.0/8 to any port 6379 comment 'Redis internal only'
ufw allow from 10.0.0.0/8 to any port 3306 comment 'MySQL internal only'

# 6. 查看状态
ufw status verbose
```

**Docker防火墙集成**:
```bash
# 创建docker-user链，防止Docker绕过UFW
iptables -N DOCKER-USER 2>/dev/null || true
iptables -F DOCKER-USER
iptables -A DOCKER-USER -i ext_if -p tcp --dport 6379 -j DROP
iptables -A DOCKER-USER -i ext_if -p tcp --dport 3306 -j DROP
iptables -A DOCKER-USER -j RETURN
```

---

#### 1.4 激活fail2ban [高/难度:低/10分钟]

**当前状态**: inactive

**配置优化**:
```bash
# 1. 安装并启动
apt-get update && apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# 2. 强化配置
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 300
maxretry = 3
banaction = ufw
backend = systemd

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
findtime = 300
bantime = 3600

[sshd-ddos]
enabled = true
port = 22
filter = sshd-ddos
logpath = /var/log/auth.log
maxretry = 2

# OpenClaw Gateway暴力破解保护
[openclaw-auth]
enabled = true
port = 18789
filter = openclaw
logpath = /root/.openclaw/logs/gateway.log
maxretry = 5
findtime = 60
bantime = 1800
EOF

# 3. 创建OpenClaw过滤器
cat > /etc/fail2ban/filter.d/openclaw.conf << 'EOF'
[Definition]
failregex = ^.*authentication failure.*from <HOST>.*$
            ^.*unauthorized access attempt.*from <HOST>.*$
ignoreregex = ^.*127.0.0.1.*$
EOF

systemctl restart fail2ban
fail2ban-client status
```

---

### 二、高优先级加固（P1 - 中等风险）

#### 2.1 Credentials目录权限修复 [中/难度:低/2分钟]

**风险描述**:
```
Credentials dir is readable by others
/root/.openclaw/credentials mode=755
```

**修复**:
```bash
chmod 700 /root/.openclaw/credentials
chmod 600 /root/.openclaw/credentials/* 2>/dev/null
ls -la /root/.openclaw/credentials
```

---

#### 2.2 插件Allowlist配置 [中/难度:低/10分钟]

**风险描述**:
```
Extensions exist but plugins.allow is not set
Found 2 extension(s) under /root/.openclaw/extensions
```

**加固配置**:
```json
{
  "plugins": {
    "allow": ["feishu"],
    "deny": ["qqbot"],
    "entries": {
      "feishu": {
        "enabled": true,
        "permissions": {
          "tools": ["feishu_doc", "feishu_wiki", "feishu_drive", "feishu_bitable_get_meta"],
          "denyTools": ["exec", "process"]
        }
      }
    }
  }
}
```

---

### 三、架构级加固（P2 - 长期改进）

#### 3.1 容器化部署方案 [高价值/难度:高/4小时]

**当前架构问题**:
- OpenClaw直接运行在宿主机，拥有完整系统访问权限
- 插件可以访问宿主机文件系统
- 无资源隔离

**容器化方案**:

```dockerfile
# Dockerfile.openclaw
FROM node:22-alpine

# 安全基础
RUN addgroup -g 1000 openclaw && \
    adduser -u 1000 -G openclaw -s /bin/sh -D openclaw

# 安装依赖
RUN apk add --no-cache python3 py3-pip git openssh-client

# 设置工作目录
WORKDIR /app

# 安装OpenClaw
RUN npm install -g openclaw

# 创建必要的目录结构
RUN mkdir -p /app/.openclaw && \
    chown -R openclaw:openclaw /app

# 切换到非root用户
USER openclaw

# 配置环境
ENV OPENCLAW_HOME=/app/.openclaw
ENV PATH="/app/.openclaw/bin:${PATH}"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD openclaw status || exit 1

# 暴露端口
EXPOSE 18789

ENTRYPOINT ["openclaw"]
CMD ["gateway", "start"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  openclaw:
    build:
      context: .
      dockerfile: Dockerfile.openclaw
    container_name: openclaw-secure
    restart: unless-stopped
    
    # 安全选项
    security_opt:
      - no-new-privileges:true
    
    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 512M
    
    # 只读根文件系统
    read_only: true
    
    # 临时文件系统
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /app/.openclaw/logs:noexec,nosuid,size=50m
    
    # 网络隔离
    networks:
      - openclaw-internal
    
    # 卷映射（最小权限）
    volumes:
      - type: bind
        source: ./workspace
        target: /app/.openclaw/workspace
        read_only: false
      - type: bind
        source: ./config/openclaw.json
        target: /app/.openclaw/openclaw.json
        read_only: true
    
    # 环境变量
    environment:
      - NODE_ENV=production
      - OPENCLAW_LOG_LEVEL=warn
    
    # 端口映射（仅本地）
    ports:
      - "127.0.0.1:18789:18789"

networks:
  openclaw-internal:
    driver: bridge
    internal: false
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**迁移步骤**:
```bash
# 1. 备份现有配置
tar czvf openclaw-backup-$(date +%Y%m%d).tar.gz ~/.openclaw/

# 2. 创建容器化目录
mkdir -p ~/openclaw-container/{workspace,config}
cp ~/.openclaw/openclaw.json ~/openclaw-container/config/
cp -r ~/.openclaw/workspace/* ~/openclaw-container/workspace/

# 3. 构建并启动
cd ~/openclaw-container
docker-compose up -d --build

# 4. 验证
openclaw status
```

---

#### 3.2 网络隔离策略 [中/难度:高/2小时]

**当前网络暴露**:
- Gateway绑定127.0.0.1:18789（相对安全）
- Docker容器使用host网络模式（不安全）
- 多个服务暴露公网端口

**隔离架构**:

```
┌─────────────────────────────────────────────────────────┐
│                    外部网络 (Internet)                   │
└──────────────────────┬──────────────────────────────────┘
                       │
              ┌────────▼─────────┐
              │   反向代理 (Nginx) │
              │   - SSL终止       │
              │   - 速率限制      │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │   WAF/防火墙      │
              └────────┬─────────┘
                       │
┌──────────────────────┼──────────────────────────────────┐
│                      │                                   │
│  ┌───────────────────▼─────────────┐                     │
│  │    OpenClaw Gateway             │                     │
│  │    - 仅监听127.0.0.1            │                     │
│  │    - 反向代理访问               │                     │
│  └───────────────────┬─────────────┘                     │
│                      │                                   │
│  ┌───────────────────▼─────────────┐                     │
│  │    沙箱容器 (Docker)            │                     │
│  │    - 只读文件系统               │                     │
│  │    - 无特权模式                 │                     │
│  │    - 资源限制                   │                     │
│  └─────────────────────────────────┘                     │
│                                                          │
│  ┌──────────────────────────────────┐                   │
│  │    工具网络隔离                   │                   │
│  │    - exec: 受限命令集             │                   │
│  │    - browser: 隔离会话            │                   │
│  │    - fs: workspaceOnly=true       │                   │
│  └──────────────────────────────────┘                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**实施步骤**:

```bash
# 1. 创建隔离网络
docker network create --driver bridge --subnet 172.30.0.0/24 openclaw-isolated

# 2. 配置OpenClaw使用沙箱模式
# 在openclaw.json中:
{
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "all",
        "containers": {
          "enabled": true,
          "image": "openclaw-sandbox:latest"
        }
      },
      "tools": {
        "fs": {
          "workspaceOnly": true
        },
        "exec": {
          "allowlist": [
            "git", "npm", "node", "python3", "pip3",
            "cat", "ls", "grep", "awk", "sed"
          ],
          "denylist": [
            "rm -rf /", "mkfs", "dd", "fdisk",
            "wget", "curl"  # 网络下载需谨慎
          ]
        }
      }
    }
  }
}

# 3. Nginx反向代理配置
cat > /etc/nginx/sites-available/openclaw << 'EOF'
server {
    listen 443 ssl http2;
    server_name openclaw.example.com;
    
    # SSL配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.3;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 速率限制
    limit_req_zone $binary_remote_addr zone=openclaw:10m rate=10r/s;
    limit_req zone=openclaw burst=20 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF
```

---

#### 3.3 高后果操作确认机制 [高价值/难度:高/3小时]

**需求**: 对危险操作实施二次确认

**实现方案**:

```typescript
// ~/.openclaw/extensions/safety-guard/index.ts
import { Extension, ToolRequest, ToolResponse } from '@openclaw/sdk';

// 高风险命令列表
const HIGH_RISK_COMMANDS = [
  { pattern: /rm\s+-rf\s+\//, level: 'critical', description: '删除根目录' },
  { pattern: /mkfs/, level: 'critical', description: '格式化文件系统' },
  { pattern: /dd\s+if=.*of=\/dev/, level: 'critical', description: '直接写入块设备' },
  { pattern: /curl.*\|.*sh/, level: 'high', description: '管道执行远程脚本' },
  { pattern: /wget.*-O-\s*\|.*sh/, level: 'high', description: '管道执行远程脚本' },
  { pattern: /chmod\s+777\s+\//, level: 'high', description: '全局权限修改' },
  { pattern: /passwd\s+root/, level: 'high', description: '修改root密码' },
  { pattern: /systemctl\s+(stop|disable)\s+sshd/, level: 'high', description: '禁用SSH服务' },
  { pattern: /ufw\s+disable/, level: 'high', description: '禁用防火墙' },
  { pattern: /docker\s+run.*--privileged/, level: 'high', description: '特权容器' },
];

// 高风险文件操作
const HIGH_RISK_PATHS = [
  '/etc/passwd',
  '/etc/shadow',
  '/etc/ssh/sshd_config',
  '/root/.ssh',
  '/root/.openclaw/credentials',
  '~/.openclaw/credentials',
];

export class SafetyGuardExtension implements Extension {
  name = 'safety-guard';
  
  async onToolRequest(request: ToolRequest): Promise<ToolRequest | null> {
    // 检查exec命令
    if (request.tool === 'exec' && request.params.command) {
      const risk = this.assessCommandRisk(request.params.command);
      if (risk.level === 'critical') {
        // 关键操作直接阻止
        return null; // 拒绝执行
      }
      if (risk.level === 'high') {
        // 高风险操作需要确认
        return {
          ...request,
          meta: {
            ...request.meta,
            requiresConfirmation: true,
            riskDescription: risk.description,
            confirmationTimeout: 300, // 5分钟超时
          }
        };
      }
    }
    
    // 检查文件操作
    if (['write', 'edit', 'apply_patch'].includes(request.tool)) {
      const filePath = request.params.file_path || request.params.path;
      if (this.isSensitivePath(filePath)) {
        return {
          ...request,
          meta: {
            ...request.meta,
            requiresConfirmation: true,
            riskDescription: `正在修改敏感文件: ${filePath}`,
            confirmationTimeout: 300,
          }
        };
      }
    }
    
    return request;
  }
  
  private assessCommandRisk(command: string): { level: string; description: string } {
    for (const risk of HIGH_RISK_COMMANDS) {
      if (risk.pattern.test(command)) {
        return { level: risk.level, description: risk.description };
      }
    }
    return { level: 'low', description: '' };
  }
  
  private isSensitivePath(path: string): boolean {
    return HIGH_RISK_PATHS.some(sensitive => 
      path?.includes(sensitive.replace('~', '/root'))
    );
  }
}
```

**配置集成**:
```json
{
  "tools": {
    "safety": {
      "confirmationRequired": {
        "commands": [
          "rm -rf",
          "mkfs",
          "dd",
          "chmod 777"
        ],
        "paths": [
          "/etc/*",
          "/root/.ssh/*",
          "~/.openclaw/credentials/*"
        ],
        "actions": [
          "systemctl stop",
          "ufw disable",
          "docker run --privileged"
        ]
      }
    }
  }
}
```

---

## 📅 实施时间表

### 第一阶段：紧急修复（1小时内）

| 时间 | 任务 | 负责人 | 验证方式 |
|------|------|--------|----------|
| 0:00-0:05 | 禁用qqbot插件 | 系统管理员 | `openclaw security audit` |
| 0:05-0:15 | 生成并配置SSH密钥 | 系统管理员 | `ssh -i key user@host` |
| 0:15-0:30 | 修改SSH配置（禁用密码登录） | 系统管理员 | 尝试密码登录失败 |
| 0:30-0:40 | 启用并配置UFW防火墙 | 系统管理员 | `ufw status verbose` |
| 0:40-0:50 | 激活fail2ban | 系统管理员 | `fail2ban-client status` |
| 0:50-1:00 | 修复credentials权限 | 系统管理员 | `ls -la ~/.openclaw/credentials` |

### 第二阶段：配置加固（2小时内）

| 时间 | 任务 | 负责人 | 验证方式 |
|------|------|--------|----------|
| 1:00-1:30 | 配置插件allowlist | 系统管理员 | 检查openclaw.json |
| 1:30-2:00 | 配置工具沙箱策略 | 系统管理员 | 测试受限命令 |
| 2:00-3:00 | 设计网络隔离方案 | 架构师 | 文档评审 |

### 第三阶段：架构升级（1周内）

| 时间 | 任务 | 负责人 | 验证方式 |
|------|------|--------|----------|
| Day 1-2 | 容器化方案开发 | 开发团队 | Docker构建成功 |
| Day 3-4 | 安全隔离测试 | QA团队 | 渗透测试通过 |
| Day 5-7 | 生产环境迁移 | 运维团队 | 服务正常运行 |

---

## ✅ 验证清单

### 基础安全验证
- [ ] qqbot插件已禁用
- [ ] SSH密码登录已禁用
- [ ] SSH密钥登录正常
- [ ] UFW防火墙已启用
- [ ] fail2ban已激活
- [ ] credentials目录权限为700
- [ ] 插件allowlist已配置

### 高级安全验证
- [ ] 容器化部署测试通过
- [ ] 网络隔离策略生效
- [ ] 高后果操作确认机制工作正常
- [ ] 安全审计无严重/高风险警告

### 持续监控
- [ ] 设置定期安全审计cron任务
- [ ] 配置日志监控告警
- [ ] 建立安全事件响应流程

---

## 🔄 回滚计划

| 变更项 | 回滚命令 | 预计时间 |
|--------|----------|----------|
| SSH配置 | `cp /etc/ssh/sshd_config.bak.* /etc/ssh/sshd_config && systemctl restart sshd` | 1分钟 |
| 防火墙 | `ufw disable` | 5秒 |
| fail2ban | `systemctl stop fail2ban` | 5秒 |
| 插件禁用 | `openclaw plugins enable qqbot` | 5秒 |
| 容器化 | `docker-compose down && openclaw gateway start` | 30秒 |

---

## 📊 风险降低效果评估

| 指标 | 加固前 | 加固后 | 改善 |
|------|--------|--------|------|
| 严重风险数 | 1 | 0 | ✅ 消除 |
| 高风险数 | 2 | 0 | ✅ 消除 |
| 中等风险数 | 5 | 1 | ⬇️ 80% |
| 攻击面 | 大 | 小 | ⬇️ 显著 |
| 暴力破解成功率 | 可能 | 极低 | ⬇️ 显著 |

---

## 📝 附录

### A. 参考文档
- OpenClaw安全最佳实践: https://docs.openclaw.ai/security
- SSH加固指南: https://wiki.debian.org/SSH
- Docker安全: https://docs.docker.com/engine/security/

### B. 工具清单
- `openclaw security audit` - 安全审计
- `ufw` - 防火墙管理
- `fail2ban` - 入侵防护
- `lynis` - 系统安全扫描（可选）

### C. 紧急联系
- 安全事件响应: [待填写]
- 系统管理员: [待填写]
- OpenClaw支持: https://github.com/useens/openclaw/issues

---

**文档版本**: v1.0  
**最后更新**: 2026-03-05  
**审核状态**: 待审核
