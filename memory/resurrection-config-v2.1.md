# 森森双节点复活架构 v2.1 (双仓库版)

> 创建时间: 2026-02-13 22:56
> 版本: v2.1
> 用途: 支持双仓库架构，按用途区分数据源

---

## 🏗️ 双仓库架构

### 仓库用途区分

| 仓库 | 地址 | 用途 | 节点 |
|------|------|------|------|
| **主仓库** | `github.com/useens/linlin-backup` | v2.0双节点复活方案 | 备用节点/新节点复活 |
| **生产仓库** | `github.com/linlinofVM/sensen-backup` | 当前生产环境备份 | 当前主节点 |

```
┌─────────────────────────────────────────────────────────────────┐
│                   森森双仓库复活架构 v2.1                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   当前生产节点(VM)                  备用节点/新节点              │
│   ┌──────────────┐                  ┌──────────────┐            │
│   │   主节点     │                  │   备用节点    │           │
│   │  (Primary)   │                  │  (Standby)   │           │
│   │              │                  │              │           │
│   │ • 生产运行    │                  │ • 待命状态    │           │
│   │ • 推送到      │                  │ • 从主仓库   │           │
│   │   sensen-     │                  │   拉取复活   │           │
│   │   backup      │                  │              │           │
│   └──────┬───────┘                  └──────┬───────┘           │
│          │                                  │                   │
│          ▼                                  ▼                   │
│   ┌──────────────────┐            ┌──────────────────┐         │
│   │ sensen-backup    │            │ linlin-backup    │         │
│   │ (生产备份)       │            │ (复活方案)       │         │
│   │ linlinofVM/      │            │ useens/          │         │
│   │ sensen-backup    │            │ linlin-backup    │         │
│   └──────────────────┘            └──────────────────┘         │
│                                                                  │
│   故障场景:                                                       │
│   ┌──────────────┐    生产节点故障                               │
│   │   备用节点   │ ───────────────► 从linlin-backup复活          │
│   │   一键复活   │   15分钟内接管   并切换到sensen-backup         │
│   └──────────────┘                 继续生产备份                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 一键复活命令（双仓库版）

### 场景1: 从 linlin-backup 复活（新节点/备用节点）

用于全新节点或备用节点首次部署：

```bash
# 快速复活
export GITHUB_TOKEN="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" && \
curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/resurrect-v2.sh | bash -s -- --repo useens/linlin-backup

# 完整复活（带Feishu）
export GITHUB_TOKEN="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" && \
export FEISHU_APP_ID="cli_a906761bf2789bd3" && \
export FEISHU_APP_SECRET="GqdUWwF3xbNNlI8PTf6YjrrJtajqXZfa" && \
curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/resurrect-v2.sh | bash -s -- \
  --repo useens/linlin-backup \
  --with-feishu
```

### 场景2: 从 sensen-backup 复活（生产恢复）

用于生产环境故障恢复：

```bash
# 快速复活
export GITHUB_TOKEN="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" && \
curl -fsSL https://raw.githubusercontent.com/linlinofVM/sensen-backup/main/scripts/resurrect-v2.sh | bash -s -- --repo linlinofVM/sensen-backup

# 完整复活（带Feishu）
export GITHUB_TOKEN="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" && \
export FEISHU_APP_ID="cli_a906761bf2789bd3" && \
export FEISHU_APP_SECRET="GqdUWwF3xbNNlI8PTf6YjrrJtajqXZfa" && \
curl -fsSL https://raw.githubusercontent.com/linlinofVM/sensen-backup/main/scripts/resurrect-v2.sh | bash -s -- \
  --repo linlinofVM/sensen-backup \
  --with-feishu
```

---

## 🎯 仓库配置矩阵

### 根据节点类型选择仓库

| 场景 | 推荐仓库 | Token | 说明 |
|------|----------|-------|------|
| 新节点部署 | `useens/linlin-backup` | ghp_wE7VoX... | 获取最新v2.0架构 |
| 生产故障恢复 | `linlinofVM/sensen-backup` | ghp_iLGBn3... | 恢复生产环境数据 |
| 备用节点同步 | `linlinofVM/sensen-backup` | ghp_iLGBn3... | 与生产节点同步 |

---

## 📋 配置文件

### config/repositories.yaml

```yaml
repositories:
  # 方案仓库 - 存放架构脚本和配置
  scheme:
    name: "linlin-backup"
    owner: "useens"
    url: "github.com/useens/linlin-backup"
    token: "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"
    purpose: "v2.0双节点复活方案"
    use_for:
      - new_node_deployment
      - standby_node_setup
      - script_updates
  
  # 生产仓库 - 存放实际运行数据
  production:
    name: "sensen-backup"
    owner: "linlinofVM"
    url: "github.com/linlinofVM/sensen-backup"
    token: "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"
    purpose: "生产环境数据备份"
    use_for:
      - production_backup
      - data_recovery
      - standby_sync

defaults:
  # 默认复活仓库
  resurrect_repo: "useens/linlin-backup"
  # 默认生产备份仓库
  production_repo: "linlinofVM/sensen-backup"
```

---

## 🛡️ 脑裂保护 v2.1

### 双仓库保护策略

```
┌─────────────────────────────────────────────────────────────┐
│                   双仓库脑裂保护 v2.1                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   角色检测          推送目标              保护机制            │
│   ─────────────────────────────────────────────────────     │
│                                                              │
│   .PRIMARY_NODE ──► sensen-backup    仅生产仓库可推送        │
│                     (生产备份)                               │
│                                                              │
│   .STANDBY_NODE ──► 禁止推送         仅拉取同步              │
│                     (定期拉取)                               │
│                                                              │
│   .RESURRECTED   ──► 禁止推送        需用户确认角色          │
│   _MARKER           (临时状态)                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 管理命令

### 指定仓库操作

```bash
# 查看当前配置的仓库
./scripts/node-admin.sh repos

# 切换到生产仓库
./scripts/node-admin.sh use-repo production

# 切换到方案仓库
./scripts/node-admin.sh use-repo scheme

# 查看状态（显示当前仓库）
./scripts/node-admin.sh status
```

### 双仓库同步

```bash
# 从生产仓库拉取最新数据
./scripts/node-admin.sh sync-from production

# 从方案仓库拉取最新脚本
./scripts/node-admin.sh sync-from scheme

# 推送到生产仓库（仅主节点）
./scripts/node-admin.sh push-to production
```

---

## 📝 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-13 22:15 | 初始双节点架构（单仓库） |
| v2.0 | 2026-02-13 22:52 | 新增自动角色检测、双向同步 |
| **v2.1** | **2026-02-13 22:56** | **支持双仓库架构** |

---

*本方案支持双仓库：*
- *方案仓库: github.com/useens/linlin-backup*
- *生产仓库: github.com/linlinofVM/sensen-backup*
