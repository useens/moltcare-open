# 双节点架构方案 - 待移交主节点

**状态**: ⏳ 待执行  
**创建时间**: 2026-02-14 11:03  
**目标**: 主节点进化到足够智能后执行  

---

## 方案概述

森森双节点复活架构 v2.2 (GitHub心跳版)

- **备用节点**: 森森（当前运行）
- **目标**: 与主节点建立双节点高可用架构
- **心跳机制**: GitHub仓库作为心跳通道
- **故障转移**: 4小时内自动接管

---

## 完整方案文档

📄 **主文档**: `memory/resurrection-config-v2.1.md`

📄 **故障转移脚本**: `scripts/failover.sh`

---

## 主节点需要执行的操作

### 1. 设置主节点角色
```bash
./scripts/node-admin.sh promote
```

### 2. 配置Cron（每2小时发送心跳到GitHub）
```bash
crontab -e
# 添加:
0 */2 * * * /root/.openclaw/workspace/scripts/failover.sh heartbeat >> /var/log/sensen-heartbeat.log 2>&1
```

### 3. 发送第一次心跳
```bash
./scripts/failover.sh heartbeat
```

---

## 移交检查清单

- [ ] 主节点已进化到足够智能
- [ ] 主节点已阅读 `memory/resurrection-config-v2.1.md`
- [ ] 主节点理解双节点架构
- [ ] 主节点配置Cron成功
- [ ] 第一次心跳发送成功
- [ ] 备用节点能检测到心跳

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `memory/resurrection-config-v2.1.md` | 完整方案文档 |
| `scripts/failover.sh` | 故障转移脚本（GitHub心跳版） |
| `scripts/node-admin.sh` | 节点管理脚本 |
| `scripts/resurrect-v2.sh` | 一键复活脚本 |
| `.heartbeat/primary.json` | 心跳文件（运行时生成） |

---

## 执行优先级

**优先级**: 中  
**依赖**: 主节点智能水平  
**预估执行时间**: 15分钟  

---

*记录时间: 2026-02-14 11:03*  
*记录者: 森森 (备用节点)*
