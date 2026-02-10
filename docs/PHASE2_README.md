# Phase 2 架构 - 云+本地VM混合模式

## 📁 文件清单

### 核心脚本

| 文件 | 大小 | 说明 |
|------|------|------|
| `scripts/cloud-heartbeat.sh` | 18KB | 云节点心跳广播服务 |
| `scripts/local-resurrect-optimized.sh` | 23KB | 本地VM优化复活脚本 |
| `scripts/systemd/cloud-heartbeat@.service` | 586B | 云心跳systemd服务 |
| `scripts/systemd/local-resurrect@.service` | 596B | 本地复活systemd服务 |

### 文档

| 文件 | 大小 | 说明 |
|------|------|------|
| `docs/phase2-test-plan.md` | 9KB | Phase 2完整测试计划 |
| `docs/phase2-test-checklist.md` | 8KB | 测试检查清单（可打印） |
| `docs/phase2-deployment-guide.md` | 10KB | 部署指南 |
| `docs/PHASE2_README.md` | 本文件 | 快速参考 |

---

## 🚀 快速开始

### 云节点（5分钟部署）

```bash
# 1. 配置Token
echo "ghp_xxx" > ~/.config/linlin/github-token
chmod 600 ~/.config/linlin/github-token

# 2. 运行配置向导
./scripts/cloud-heartbeat.sh --setup

# 3. 启动心跳
./scripts/cloud-heartbeat.sh --daemon
```

### 本地VM（5分钟部署）

```bash
# 1. 下载脚本
curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/local-resurrect-optimized.sh -o ~/resurrect.sh
chmod +x ~/resurrect.sh

# 2. 配置
./resurrect.sh --setup

# 3. 预拉取备份
./resurrect.sh --prefetch

# 4. 添加到crontab
(crontab -l 2>/dev/null; echo "*/10 * * * * $HOME/resurrect.sh --prefetch") | crontab -
```

---

## 📊 架构对比

| 特性 | Phase 1 (基础) | Phase 2 (本版) |
|------|----------------|----------------|
| 故障检测 | 手动 | 自动 (心跳+网络) |
| RTO目标 | 15-30分钟 | **2分钟** |
| 备份拉取 | 完整克隆 | 增量更新 |
| 预拉取 | 无 | 有 (缓存机制) |
| 并行处理 | 无 | 有 |
| 状态广播 | 无 | GitHub心跳 |
| 自恢复 | 无 | 有 |

---

## ⚡ 性能目标

```
故障检测:    < 10秒  (心跳间隔60秒 + 超时阈值)
备份拉取:    < 60秒  (增量更新 < 10秒)
服务启动:    < 30秒
验证流程:    < 10秒
通知发送:    < 5秒
─────────────────────────────
总RTO目标:   < 120秒 (2分钟)
```

---

## 🔄 工作流程

### 正常运行
```
云节点 ◄──心跳──► GitHub (每60秒)
         
本地VM ◄──预拉取──► GitHub (每10分钟)
```

### 故障转移
```
云节点故障
    │
    ▼
本地VM检测到心跳超时 (120秒)
    │
    ▼
本地VM执行复活流程
    │
    ▼
本地VM接管服务 (< 2分钟)
    │
    ▼
发送通知给用户
```

### 恢复回切
```
云节点修复完成
    │
    ▼
云节点恢复心跳
    │
    ▼
用户手动执行回切
    │
    ▼
数据同步
    │
    ▼
云节点重新接管
```

---

## 🧪 测试检查项

- [ ] 心跳正常写入GitHub
- [ ] 本地VM能检测到故障
- [ ] 预拉取缓存有效
- [ ] 复活总耗时 < 2分钟
- [ ] 通知正常发送
- [ ] 数据无丢失
- [ ] 回切流程正常

---

## 📈 监控指标

### 云节点
```bash
# 查看心跳日志
tail -f ~/.openclaw/logs/cloud-heartbeat.log

# 查看最新状态
./scripts/cloud-heartbeat.sh --status

# 检查GitHub
./scripts/cloud-heartbeat.sh --status
```

### 本地VM
```bash
# 查看状态
./resurrect.sh --status

# 查看日志
tail -f ~/.openclaw/logs/local-resurrect.log

# 检查缓存
du -sh ~/.openclaw/.resurrection-cache
```

---

## 🆘 故障排除

### 问题1: 心跳未写入
```bash
# 检查Token
cat ~/.config/linlin/github-token

# 测试API
curl -H "Authorization: token $(cat ~/.config/linlin/github-token)" \
  https://api.github.com/user

# 手动发送心跳
./scripts/cloud-heartbeat.sh --test
```

### 问题2: 本地VM无法检测故障
```bash
# 检查配置
cat ~/.config/linlin/resurrection.conf

# 检查时区
date
timedatectl status

# 手动检查
./resurrect.sh --status
```

### 问题3: 复活失败
```bash
# 查看详细日志
tail -n 100 ~/.openclaw/logs/local-resurrect.log

# 检查磁盘空间
df -h

# 检查网络
ping github.com
```

---

## 📝 重要文件路径

| 用途 | 路径 |
|------|------|
| GitHub Token | `~/.config/linlin/github-token` |
| 配置文件 | `~/.config/linlin/resurrection.conf` |
| 备份缓存 | `~/.openclaw/.resurrection-cache` |
| 复活日志 | `~/.openclaw/logs/local-resurrect.log` |
| 心跳日志 | `~/.openclaw/logs/cloud-heartbeat.log` |
| 凭证目录 | `~/.openclaw/credentials/` |
| 工作目录 | `~/.openclaw/workspace/` |

---

## 🎯 Phase 3 规划

- [ ] 多本地VM支持 (主备模式)
- [ ] 智能路由选择
- [ ] WebSocket实时同步
- [ ] 自动故障演练
- [ ] RTO目标: < 1分钟

---

**完成时间**: 2026-02-11 00:40 GMT+8  
**版本**: v2.0 Phase 2  
**状态**: 已就绪，等待测试
