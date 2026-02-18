# TOOLS.md - 本地工具与环境

> 🔧 **用途**: 记录环境特定的工具配置  
> **原则**: Skills定义"怎么做"，这里记录"用什么"

---

## 🏠 工作环境

**主机**: 云端节点 (ARM64)  
**OpenClaw版本**: v2.x  
**模型**: kimi-coding/k2p5  
**工作目录**: `/root/.openclaw/workspace`

---

## 🔌 常用连接

### SSH
```
# 暂无配置
```

### API Keys
- Brave API: 待配置（用于外部搜索）
- GitHub Token: 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 (已配置)
- GitHub Repo: https://github.com/linlinofVM/sensen-backup
- GLM-5 (zai): 已配置
- 飞书 App ID: cli_a906761bf2789bd3 (已配置)
- 飞书 App Secret: GqdUWwF3xbNNlI8PTf6YjrrJtajqXZfa (已配置)

---

## 🛠️ 自定义脚本

| 脚本 | 用途 | 位置 |
|------|------|------|
| unified-monitor.py | 统一系统监控 | scripts/ |
| moltbook-unified.py | Moltbook扫描 | scripts/ |
| evolution-unified.py | 进化引擎 | scripts/ |
| skill-audit.py | 技能审计 | scripts/ |
| unified-maintenance.sh | 日常维护 | scripts/ |
| conditional-git-sync.sh | 条件Git同步 | scripts/ |

---

## 📊 监控配置

### 磁盘阈值
- 警告: 80%
- 严重: 90%

### 日志保留
- 活跃日志: 7天
- 归档日志: 30天

### 备份策略
- 自动备份: 每天03:00
- 保留数量: 5个

---

## 📝 备注

- 使用 `low` thinking模式进行常规检查
- 全自主运行模式已启用
- 技能审计已完成：22个全部在用

---

*环境配置 | 2026-02-15*
