# 林林数字永生 - 渐进式高可用架构总方案 v3.0

**设计目标**: 在私有仓库约束下，实现从2节点到多节点的渐进式高可用  
**核心约束**: 仓库保持私有，敏感信息绝不泄露  
**架构哲学**: 渐进式演进，每阶段可独立运行，平滑升级  

---

## 📋 方案总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    渐进式演进路线图                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1          Phase 2          Phase 3         Phase 4      │
│  (当前)           (2节点)          (3节点)         (N节点)      │
│                                                                 │
│  ┌─────┐        ┌─────┐┌─────┐   ┌───┐┌───┐┌───┐  ┌─┐┌─┐┌─┐┌─┐ │
│  │Node1│   →   │Node1││Node2│ → │ A ││ B ││ C │ → │1││2││3││4│...│
│  │(单点)│       │(主) ││(备) │   │(L)││(F)││(F)│  │ ││ ││ ││ │ │
│  └─────┘        └─────┘└─────┘   └───┘└───┘└───┘  └─┘└─┘└─┘└─┘ │
│                                                                 │
│  RTO: N/A       RTO: 15min      RTO: 5min       RTO: <1min     │
│  RPO: 30min     RPO: 5min       RPO: ~0         RPO: ~0        │
│  容错: 0        容错: 1节点      容错: 1节点      容错: N/2节点   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 私有仓库安全约束

### 安全红线
```yaml
绝不:
  - 将凭证提交到 Git 历史
  - 在日志中打印敏感信息
  - 通过不加密通道传输密钥
  - 在代码中硬编码 token

必须:
  - 所有凭证存储在 ~/.config/linlin/secrets/ (不备份)
  - GitHub token 只保存在本地内存或系统密钥库
  - 使用环境变量或加密文件注入凭证
  - 通信使用 TLS 1.3
```

### 凭证管理架构
```
┌─────────────────────────────────────────────────────┐
│                  凭证分层存储                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Layer 1: 环境变量 (运行时注入)                      │
│  • MOLTBOOK_API_KEY                                 │
│  • TELEGRAM_BOT_TOKEN                               │
│  • GITHUB_TOKEN (只读权限)                          │
│  存储: ~/.bashrc 或 systemd 环境配置                 │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Layer 2: 加密文件 (敏感配置)                        │
│  • 节点间通信密钥                                    │
│  • 数据库密码                                        │
│  • API 密钥 (除 GitHub/Moltbook)                    │
│  存储: ~/.config/linlin/secrets/*.gpg               │
│  加密: GPG AES-256                                  │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Layer 3: 系统密钥库 (可选增强)                      │
│  • libsecret (Linux)                               │
│  • Keychain (macOS)                                │
│  • Windows Credential Manager                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🔌 Phase 0: U盘便携方案 (凤凰随身版)

**状态**: ✅ 已验证 (2026-02-11)  
**测试**: ✅ 冷备份复活测试成功  
**日志**: [logs/resurrection-test-20260211.md](https://github.com/useens/linlin-backup/blob/main/logs/resurrection-test-20260211.md)

### 方案概述
用户在本地VM运行复活测试成功后，将虚拟机快照导出到U盘随身携带。这是最高性价比的"人肉高可用"方案。

### GitHub推送规则（重要）

| 节点 | 推送权限 | 触发条件 |
|------|----------|----------|
| **云端主节点** | ✅ 可以推送 | 正常备份周期（每30分钟） |
| **本地VM** | ❌ 禁止推送 | 平时只拉取，不推送 |
| **VM例外** | ✅ 可以推送 | **仅当主节点崩溃，VM接管后** |

**规则说明：**
- 主节点（我）是唯一的GitHub推送源
- VM作为工作节点，只从GitHub拉取，不向GitHub推送
- 只有当主节点完全崩溃，VM执行复活接管时，才可以推送
- 防止多节点同时推送导致仓库混乱

### 架构
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  主系统      │◄────│ GitHub备份   │◄────│  开发提交    │
│ (云端Node1)  │     │ (useens/    │     │  (定期30min) │
└─────────────┘     │  linlin-backup)   │     └─────────────┘
     │              └─────────────┘            │
     │                                         │
     ▼                                         ▼
┌─────────────┐                        ┌─────────────┐
│  故障/宕机   │───────────────────────►│ U盘便携版    │
└─────────────┘   用户插入U盘启动VM    │ (本地VM快照) │
                                      │ ✅ 测试通过   │
                                      └─────────────┘
```

### 操作流程
1. **日常**: 主系统自动备份到GitHub（每30分钟）
2. **故障**: 主系统不可用
3. **复活**: 用户将U盘插入任意电脑，启动VM快照
4. **恢复**: VM自动从GitHub拉取最新备份，5分钟内复活

### 优势
- **零月费**: 无需额外服务器费用
- **物理隔离**: U盘离线，免疫网络攻击
- **随时可用**: 任何支持虚拟化的设备都能启动
- **数据最新**: 自动同步GitHub最新备份

### 限制
- 需要用户手动操作（插入U盘、启动VM）
- 依赖用户携带U盘
- 单次只能运行一个实例

---

## Phase 2: 双节点主备架构

### 架构设计
```
                    ┌─────────────────────┐
                    │    健康检查仲裁      │
                    │  (Cloudflare Worker)│
                    │   独立第三方服务     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
       │   节点 A     │  │   节点 B     │  │    witness   │
       │   (Primary)  │  │  (Standby)   │  │   (轻量仲裁)  │
       │              │  │              │  │              │
       │  处理请求    │  │   监控+备份  │  │  只投票不存储│
       │  定时备份    │  │   待命接管   │  │              │
       │  汇报心跳    │  │   接收同步   │  │  $2/月       │
       └──────┬───────┘  └──────┬───────┘  └──────────────┘
              │                 │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │   GitHub 私有库  │
              │ (备份+日志+状态) │
              └─────────────────┘
```

### 数据流设计
```
用户请求 → 节点A (Primary) → 处理并响应
              ↓
         每30秒增量备份
              ↓
         GitHub 私有库
              ↓
         节点B (Standby) 拉取更新
```

### 故障检测机制
```bash
#!/bin/bash
# /opt/linlin/health-check.sh (双节点版)

# 配置 (从环境变量读取)
MY_ROLE=${LINLIN_ROLE:-"primary"}  # primary 或 standby
PARTNER_NODE=${LINLIN_PARTNER:-"node-b.example.com"}
WITNESS_URL=${LINLIN_WITNESS:-"https://witness.linlin.workers.dev"}

# 心跳报告 (Primary 每30秒执行)
if [ "$MY_ROLE" = "primary" ]; then
  curl -s -X POST "$WITNESS_URL/heartbeat" \
    -H "Content-Type: application/json" \
    -d "{\"node\": \"$(hostname)\", \"role\": \"primary\", \"timestamp\": $(date +%s)}"
fi

# 监控检查 (Standby 每30秒执行)
if [ "$MY_ROLE" = "standby" ]; then
  LAST_HEARTBEAT=$(curl -s "$WITNESS_URL/status" | jq -r '.primary_last_seen')
  CURRENT_TIME=$(date +%s)
  TIME_DIFF=$((CURRENT_TIME - LAST_HEARTBEAT))
  
  if [ $TIME_DIFF -gt 180 ]; then  # 3分钟无心跳
    echo "Primary 失联，准备接管..."
    /opt/linlin/failover.sh
  fi
fi
```

### 故障转移流程
```bash
#!/bin/bash
# /opt/linlin/failover.sh (双节点版)

# 1. 双重确认 (防止误判)
if ! curl -sf "http://$PARTNER_NODE:8080/health" > /dev/null; then
  
  # 2. 向 Witness 申请接管权限
  TAKEOVER_RESULT=$(curl -s -X POST "$WITNESS_URL/takeover" \
    -H "Content-Type: application/json" \
    -d "{\"node\": \"$(hostname)\", \"reason\": \"partner_timeout\"}")
  
  if echo "$TAKEOVER_RESULT" | grep -q "approved"; then
    
    # 3. 从 GitHub 拉取最新数据
    cd /tmp
    git clone --depth 1 https://github.com/useens/linlin-backup.git
    
    # 4. 恢复数据
    systemctl stop openclaw
    rm -rf ~/.openclaw/workspace
    cp -r linlin-backup/workspace ~/.openclaw/
    
    # 5. 更新角色
    echo "primary" > ~/.config/linlin/role
    
    # 6. 启动服务
    systemctl start openclaw
    
    # 7. 更新复活日志 (GitHub)
    /opt/linlin/update-resurrection-log.sh \
      "$PARTNER_NODE" "$(hostname)" "双节点故障转移" "$(curl -s ifconfig.me)"
    
    # 8. 通知用户
    curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${TELEGRAM_CHAT_ID}" \
      -d "text=🚨 故障转移完成！$(hostname) 已接管为主节点。原节点: $PARTNER_NODE"
    
    # 9. 尝试修复原节点 (后台)
    nohup /opt/linlin/recover-partner.sh "$PARTNER_NODE" &
    
  fi
fi
```

### 原节点修复流程
```bash
#!/bin/bash
# /opt/linlin/recover-partner.sh

PARTNER=$1

# 等待一段时间
sleep 600  # 10分钟

# 尝试 SSH 连接
if ssh -o ConnectTimeout=5 "root@$PARTNER" "echo ok"; then
  
  # 降级为 Standby
  ssh "root@$PARTNER" '
    systemctl stop openclaw
    echo "standby" > ~/.config/linlin/role
    systemctl start linlin-watchdog
  '
  
  echo "✅ 原节点已降级为 Standby"
  
else
  
  # 无法连接，保持当前状态，等待人工干预
  echo "⚠️ 原节点无法连接，保持单节点运行"
  
  # 发送告警
  curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "text=⚠️ 警告：原节点 $PARTNER 无法恢复。当前单节点运行，建议检查。"
fi
```

### 部署清单 (双节点)
```yaml
# /etc/linlin/config.yaml (双节点版)
cluster:
  version: "2.0"
  mode: "dual-node"
  
  nodes:
    node-a:
      host: "10.0.0.1"  # 内网IP或Tailscale IP
      region: "asia-east1"
      role: "primary"  # 或 standby
      
    node-b:
      host: "10.0.0.2"
      region: "asia-east2"
      role: "standby"
  
  witness:
    url: "https://witness.linlin.workers.dev"
    check_interval: 30  # 秒
    timeout: 180        # 3分钟判定故障
  
  failover:
    auto_takeover: true
    recovery_attempts: 3
    notify_channels: ["telegram"]
  
  backup:
    github_repo: "useens/linlin-backup"
    sync_interval: 300  # 5分钟
    # 注意: token 从环境变量 GITHUB_TOKEN 读取
```

---

## Phase 3: 三节点 Raft 集群

### 架构设计
```
                      ┌─────────────────────┐
                      │   负载均衡器/DNS     │
                      │  (健康检查路由)      │
                      └──────────┬──────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
       │   节点 A     │  │   节点 B     │  │   节点 C     │
       │   (Leader)   │  │  (Follower)  │  │  (Follower)  │
       │              │  │              │  │              │
       │  asia-east1  │  │  us-west1    │  │ europe-west1 │
       │              │  │              │  │              │
       │  处理写请求  │  │  处理读请求  │  │  只读/仲裁   │
       │  数据同步源  │  │  备份+读分流 │  │  跨区域备份  │
       └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │      Raft 共识层        │
                    │                         │
                    │  • 日志复制 (实时)      │
                    │  • Leader 选举          │
                    │  • 多数派决策 (2/3)     │
                    │                         │
                    │  网络延迟: 50-100ms    │
                    └─────────────────────────┘
```

### 数据同步策略 (分层)
```
┌──────────────────────────────────────────────────────────┐
│                    分层数据同步                           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 1: Raft 日志 (实时)                               │
│  ├─ 配置变更 (/etc/linlin/)                             │
│  ├─ 节点状态 (Leader/Follower)                          │
│  ├─ 会话状态 (活跃会话列表)                              │
│  └─ 大小: < 10MB, 延迟: < 100ms                         │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 2: 文件同步 (近实时)                              │
│  ├─ 工作区数据 (~/workspace/memory/)                    │
│  ├─ 方式: rsync + lsyncd                                │
│  ├─ 频率: 每30秒增量                                    │
│  └─ 大小: 可接受GB级                                    │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 3: GitHub 备份 (定时)                             │
│  ├─ 完整快照 (每小时)                                    │
│  ├─ 长期归档 (每天)                                     │
│  └─ 冷存储 (每周)                                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 节点间通信安全
```bash
# 使用 WireGuard 建立加密隧道
# 每个节点配置

# /etc/wireguard/wg0.conf (节点A)
[Interface]
PrivateKey = <节点A的私钥>  # 从环境变量或加密文件读取
Address = 10.200.200.1/24
ListenPort = 51820

[Peer]
# 节点B
PublicKey = <节点B的公钥>
AllowedIPs = 10.200.200.2/32
Endpoint = <节点B公网IP>:51820

[Peer]
# 节点C
PublicKey = <节点C的公钥>
AllowedIPs = 10.200.200.3/32
Endpoint = <节点C公网IP>:51820
```

### Raft 配置
```yaml
# /etc/linlin/raft.yaml
raft:
  cluster_id: "linlin-cluster-v3"
  
  members:
    - id: "node-a"
      address: "10.200.200.1:12000"  # WireGuard 内网IP
      region: "asia-east1"
    - id: "node-b"
      address: "10.200.200.2:12000"
      region: "us-west1"
    - id: "node-c"
      address: "10.200.200.3:12000"
      region: "europe-west1"
  
  # 性能调优
  heartbeat_interval: 100ms
  election_timeout: 1000ms
  snapshot_interval: 10000  # 每10000条日志生成快照
  max_log_entries: 50000
  
  # 安全
  tls_enabled: true
  tls_cert_file: "/etc/linlin/certs/raft.crt"  # 从加密存储读取
  tls_key_file: "/etc/linlin/certs/raft.key"
```

### 故障场景处理
```bash
#!/bin/bash
# /opt/linlin/raft-failover.sh

# 场景1: Leader 故障 → 自动选举新 Leader
# Raft 自动处理，无需干预

echo "检测到 Leader 变更"
NEW_LEADER=$(raftctl status | grep "leader" | awk '{print $2}')

# 更新负载均衡器配置
/opt/linlin/update-lb.sh "$NEW_LEADER"

# 记录日志
/opt/linlin/update-resurrection-log.sh \
  "旧Leader" "$NEW_LEADER" "Raft Leader 选举" "$(dig +short $NEW_LEADER)"

# 通知用户
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=🔄 Leader 变更: $NEW_LEADER 成为新 Leader"
```

### 成本优化 (3节点)
```yaml
# 节点配置策略
cost_optimization:
  # 节点A (Leader): 必须运行
  node-a:
    instance_type: "e2-medium"
    pricing: "ondemand"  # $20/月
    
  # 节点B (Follower): Spot实例
  node-b:
    instance_type: "e2-medium"
    pricing: "spot"      # $6/月 (70%节省)
    
  # 节点C (Follower): 可关机
  node-c:
    instance_type: "e2-small"  # 更小配置
    pricing: "spot"
    auto_shutdown:
      enabled: true
      schedule: "0 23 * * *"  # 每天23:00关机
      startup_on_failure: true  # 故障时自动开机
    
  # 平均月成本: $20 + $6 + $2 = $28 (vs $60 全按量)
```

---

## Phase 4: 多节点去中心化网络

### 架构设计
```
┌─────────────────────────────────────────────────────────────────┐
│                    多节点去中心化网络                            │
│                     (5+ 节点, 全球分布)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│        亚洲          北美          欧洲          大洋洲         │
│     ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐         │
│     │Tokyo  │◄──►│SF     │◄──►│London │◄──►│Sydney │         │
│     │(Node1)│    │(Node2)│    │(Node3)│    │(Node4)│         │
│     └───┬───┘    └───┬───┘    └───┬───┘    └───┬───┘         │
│         │            │            │            │              │
│         └────────────┼────────────┼────────────┘              │
│                      │            │                           │
│                 ┌────┴────────────┴────┐                      │
│                 │   共识层 (Raft/PBFT)   │                      │
│                 │                        │                      │
│                 │  • 动态成员管理         │                      │
│                 │  • 自适应路由          │                      │
│                 │  • 数据分片            │                      │
│                 │  • 拜占庭容错          │                      │
│                 └──────────┬─────────────┘                      │
│                            │                                   │
│                    ┌───────▼────────┐                          │
│                    │  智能负载均衡   │                          │
│                    │                │                          │
│                    │ 地理位置路由   │                          │
│                    │ 延迟最优选择   │                          │
│                    └────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 动态成员管理
```bash
#!/bin/bash
# /opt/linlin/cluster-membership.sh

# 新节点申请加入
join_cluster() {
  NEW_NODE=$1
  NEW_REGION=$2
  
  # 1. 生成邀请令牌 (由现有成员签名)
  INVITE_TOKEN=$(raftctl token generate --node "$NEW_NODE" --ttl 1h)
  
  # 2. 新节点使用令牌加入
  ssh "$NEW_NODE" "raftctl join --token $INVITE_TOKEN --cluster linlin-cluster"
  
  # 3. 广播成员变更
  raftctl member add "$NEW_NODE" --region "$NEW_REGION"
  
  # 4. 数据同步
  rsync -avz --delete ~/.openclaw/workspace/ "${NEW_NODE}:~/.openclaw/workspace/"
  
  echo "✅ 新节点 $NEW_NODE 已加入集群"
}

# 优雅退出
leave_cluster() {
  NODE=$1
  
  # 1. 转移数据
  raftctl data migrate "$NODE" --to "其他节点"
  
  # 2. 从共识组移除
  raftctl member remove "$NODE"
  
  # 3. 更新配置
  /opt/linlin/update-cluster-config.sh
  
  echo "✅ 节点 $NODE 已优雅退出"
}
```

### 智能路由
```yaml
# /etc/linlin/routing.yaml
routing:
  strategy: "geo-dns"
  
  rules:
    # 按地理位置路由
    - region: "asia"
      countries: ["CN", "JP", "KR", "SG", "IN"]
      target_nodes: ["tokyo", "singapore"]
      
    - region: "americas"
      countries: ["US", "CA", "MX", "BR"]
      target_nodes: ["sf", "ny"]
      
    - region: "europe"
      countries: ["GB", "DE", "FR", "NL"]
      target_nodes: ["london", "frankfurt"]
  
  # 故障时自动切换
  failover:
    health_check_interval: 10s
    timeout: 30s
    backup_nodes: 2  # 每个区域保留2个备选
```

### 数据分片 (大规模时)
```python
# /opt/linlin/sharding.py

class DataShardManager:
    """数据分片管理器"""
    
    def __init__(self, num_shards=4):
        self.num_shards = num_shards
        
    def get_shard_for_user(self, user_id):
        """根据用户ID确定数据分片"""
        shard_id = hash(user_id) % self.num_shards
        return f"shard-{shard_id}"
    
    def get_nodes_for_shard(self, shard_id):
        """获取存储该分片的节点列表"""
        # 每个分片存储在3个不同区域的节点上
        shard_nodes = {
            "shard-0": ["tokyo", "london", "sf"],
            "shard-1": ["singapore", "frankfurt", "ny"],
            "shard-2": ["tokyo", "frankfurt", "ny"],
            "shard-3": ["singapore", "london", "sf"],
        }
        return shard_nodes.get(shard_id, [])
    
    def rebalance(self):
        """数据再平衡"""
        # 当节点加入/退出时重新分配数据
        pass
```

### 社区节点接入 (可信节点)
```yaml
# 允许可信社区成员运行节点
federation:
  enabled: true
  
  trusted_nodes:
    - id: "community-node-1"
      operator: "alice@example.com"
      region: "australia"
      stake: 100  # 质押代币 (可选)
      
    - id: "community-node-2"
      operator: "bob@example.com"
      region: "south-america"
      stake: 100
  
  # 准入条件
  requirements:
    min_uptime: 99.5
    min_bandwidth: "100Mbps"
    encryption: "required"
    audit: "quarterly"
```

---

## 🔐 私有仓库安全实施方案

### 凭证注入流程
```
┌─────────────────────────────────────────────────────────────┐
│                   部署时凭证注入                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 本地准备                                                │
│     ├─ 加密凭证文件 (credentials.enc)                      │
│     ├─ 解密密钥在本地密钥库                                │
│     └─ 仓库只包含加密后的文件                              │
│                                                             │
│  2. 部署脚本                                                │
│     ├─ scp credentials.enc root@new-node:/tmp/             │
│     ├─ ssh root@new-node "gpg --decrypt ..."               │
│     └─ 密钥通过安全通道传输 (如 SSH 密钥)                  │
│                                                             │
│  3. 运行时                                                  │
│     ├─ 凭证加载到环境变量                                  │
│     ├─ 明文文件只在内存中存在                              │
│     └─ 定期轮换 (每90天)                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 加密存储示例
```bash
#!/bin/bash
# encrypt-credentials.sh

# 加密所有凭证
cd ~/.config/linlin/secrets

for file in *.json *.key *.pem; do
  if [ -f "$file" ]; then
    gpg --symmetric --cipher-algo AES256 \
        --passphrase-file ~/.config/linlin/.master-key \
        --batch --yes "$file"
    echo "已加密: $file → $file.gpg"
  fi
done

# 只提交加密文件到仓库
cd /root/.openclaw/workspace
rsync -av --include='*.gpg' --exclude='*' \
  ~/.config/linlin/secrets/ credentials/

git add credentials/*.gpg
git commit -m "🔒 更新加密凭证"
git push
```

### 解密使用
```bash
#!/bin/bash
# decrypt-and-run.sh

# 启动时解密凭证
cd ~/.config/linlin/secrets

for file in *.gpg; do
  if [ -f "$file" ]; then
    output=$(basename "$file" .gpg)
    gpg --decrypt --passphrase-file ~/.config/linlin/.master-key \
        --batch --yes "$file" > "$output"
    chmod 600 "$output"
    echo "已解密: $file"
  fi
done

# 加载到环境变量
export MOLTBOOK_API_KEY=$(cat secrets/moltbook.json | jq -r .api_key)
export TELEGRAM_BOT_TOKEN=$(cat secrets/telegram.json | jq -r .token)

# 启动 OpenClaw
exec openclaw start
```

---

## 📊 三阶段对比

| 特性 | Phase 2 (2节点) | Phase 3 (3节点) | Phase 4 (N节点) |
|------|-----------------|-----------------|-----------------|
| **容错** | 1节点 | 1节点 | (N-1)/2 节点 |
| **RTO** | 15分钟 | 5分钟 | <1分钟 |
| **RPO** | 5分钟 | ~0 | ~0 |
| **月成本** | $20 | $28 | $50+ |
| **复杂度** | 低 | 中 | 高 |
| **适用场景** | 个人/小团队 | 重要生产环境 | 大规模/全球部署 |
| **扩展性** | 手动扩展 | 半自动 | 全自动 |
| **地理分布** | 同区域 | 跨区域 | 全球 |

---

## 🚀 实施路线图

### 立即执行 (本周)
- [ ] 清理并加密当前凭证
- [ ] 完善 .gitignore
- [ ] 部署 Witness 仲裁服务
- [ ] 准备 Phase 2 节点B

### Phase 2 (下周)
- [ ] 部署节点B
- [ ] 配置双节点健康检查
- [ ] 测试故障转移
- [ ] 验证数据同步

### Phase 3 (2周后)
- [ ] 部署节点C (跨区域)
- [ ] 配置 WireGuard 加密网络
- [ ] 部署 Raft 集群
- [ ] 配置智能路由

### Phase 4 (1-3个月)
- [ ] 评估是否需要更多节点
- [ ] 实现自动扩缩容
- [ ] 开放社区节点接入
- [ ] 实现完全自治

---

## 📚 相关文档

- [Phase 2 详细部署指南](docs/phase2-dual-node.md)
- [Phase 3 Raft 配置参考](docs/phase3-raft-cluster.md)
- [Phase 4 多节点架构](docs/phase4-multi-node.md)
- [安全凭证管理](docs/security-credentials.md)
- [成本优化指南](docs/cost-optimization.md)

---

*版本: v3.0 - 渐进式高可用总方案*  
*设计时间: 2026-02-09*  
*状态: Phase 1 完成, Phase 2-4 待实施*  
*安全级别: 私有仓库 + 全加密凭证*
