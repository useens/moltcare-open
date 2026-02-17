# Staging 系统 - 影子副本

> 🔄 安全修改核心文件的工作流

## 结构

```
staging/
├── AGENTS.md          ← 副本（开发环境）
├── SOUL.md
├── USER.md
├── IDENTITY.md
├── TOOLS.md
├── HEARTBEAT.md
├── MEMORY.md
├── backups/           ← 自动备份
│   └── 20260217_185800/
├── scripts/
│   ├── stage-validate.sh   ← 验证
│   ├── stage-deploy.sh     ← 部署
│   └── stage-rollback.sh   ← 回滚
└── README.md          ← 本文件
```

## 工作流

### 1. 修改副本
在 `staging/*.md` 中随意修改，不影响主系统。

### 2. 验证
```bash
cd ~/.openclaw/workspace
./staging/scripts/stage-validate.sh        # 验证全部
./staging/scripts/stage-validate.sh AGENTS.md  # 验证单个
```

### 3. 部署
```bash
./staging/scripts/stage-deploy.sh            # 部署全部
./staging/scripts/stage-deploy.sh AGENTS.md   # 部署单个
```

自动备份到 `staging/backups/YYYYMMDD_HHMMSS/`

### 4. 验证效果
- 检查 OpenClaw 是否正常响应
- 测试修改是否生效

### 5. 回滚（如需）
```bash
./staging/scripts/stage-rollback.sh          # 回滚最新
./staging/scripts/stage-rollback.sh 1        # 回滚指定备份
```

## 初始状态

文件已复制于: 2026-02-17 18:58

---
**警告**: 部署前务必验证回滚路径可用
