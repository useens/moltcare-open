# Phase 2 测试计划
# 云+本地VM混合模式测试

> **版本**: v2.0  
> **目标**: 验证云节点故障时，本地VM能在2分钟内完成接管  
> **测试时间**: 用户回来后执行  
> **预计总耗时**: 30-45分钟

---

## 一、测试环境准备

### 1.1 云节点（当前环境）

```bash
# 检查清单
- [ ] OpenClaw Gateway 运行正常
- [ ] GitHub仓库可写 (linlin-backup)
- [ ] 心跳脚本已部署
- [ ] 通知渠道配置完成 (Telegram/飞书)
```

### 1.2 本地VM准备

```bash
# 必备条件
- [ ] 可访问GitHub的Linux VM (Ubuntu/Debian)
- [ ] 已安装Git
- [ ] 磁盘空间 > 2GB
- [ ] 内存 > 2GB
- [ ] 已配置GitHub Token
- [ ] 已安装OpenClaw (可选，测试中可能安装)
```

### 1.3 配置部署

在云节点执行：
```bash
cd ~/.openclaw/workspace/scripts

# 1. 配置云节点心跳
./cloud-heartbeat.sh --setup
# 输入:
# - GitHub仓库: useens/linlin-backup
# - 心跳间隔: 60 (秒)

# 2. 启动心跳守护进程
./cloud-heartbeat.sh --daemon &

# 3. 验证心跳写入
curl -s https://api.github.com/repos/useens/linlin-backup/contents/status/cloud-status.json?ref=heartbeat | \
  python3 -c "import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())"
```

在本地VM执行：
```bash
# 1. 下载复活脚本
curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/local-resurrect-optimized.sh -o ~/resurrect.sh
chmod +x ~/resurrect.sh

# 2. 配置
./resurrect.sh --setup
# 输入:
# - GitHub仓库: useens/linlin-backup
# - 云节点主机: [云节点IP/域名]
# - Telegram Token/Chat ID (用于接收通知)

# 3. 预拉取备份
./resurrect.sh --prefetch
```

---

## 二、测试场景

### 场景1: 基础心跳检测测试 ⏱️ 5分钟

**目的**: 验证云节点能正确写入心跳，本地VM能正确读取

```bash
# 在云节点执行
./scripts/cloud-heartbeat.sh --test

# 预期结果:
# ✅ 心跳发送成功 [healthy]

# 在本地VM执行
./resurrect.sh --status

# 预期结果:
# 显示云节点状态为 healthy
# 显示上次心跳时间在60秒内
```

**通过标准**:
- [ ] 心跳文件写入GitHub
- [ ] 本地能正确解析心跳数据
- [ ] 时间戳显示正确

---

### 场景2: 模拟云节点网络故障 ⏱️ 5分钟

**目的**: 验证本地VM能检测到云节点失联

```bash
# 在云节点 - 临时阻止心跳写入
# 方法1: 暂停心跳进程
kill -STOP [heartbeat-pid]

# 方法2: 断开网络 (慎用)
sudo iptables -A OUTPUT -d api.github.com -j DROP

# 等待2分钟

# 在本地VM检查
./resurrect.sh --status

# 预期结果:
# 显示云节点状态异常
# 显示心跳超时
```

**恢复**:
```bash
# 在云节点
kill -CONT [heartbeat-pid]
# 或
sudo iptables -F
```

**通过标准**:
- [ ] 本地VM正确识别心跳超时
- [ ] 检测到云节点故障
- [ ] 网络检测同步失败

---

### 场景3: 本地VM预拉取测试 ⏱️ 5分钟

**目的**: 验证预拉取能缩短复活时间

```bash
# 在本地VM执行
./resurrect.sh --prefetch

# 检查缓存
du -sh ~/.openclaw/.resurrection-cache
ls -la ~/.openclaw/.resurrection-cache

# 再次执行，验证增量更新
time ./resurrect.sh --prefetch
```

**通过标准**:
- [ ] 首次拉取成功
- [ ] 缓存目录创建
- [ ] 增量更新比全量更快

---

### 场景4: 完整故障转移测试 ⏱️ 10分钟

**目的**: 模拟完整故障转移流程，验证2分钟目标

```bash
# 前置条件: 云节点正常运行

# 步骤1: 在云节点启动对话 (用于验证连续性)
# 发送一条测试消息给用户

# 步骤2: 模拟云节点完全故障
# 方法A: 停止OpenClaw
openclaw gateway stop

# 方法B: 模拟更严重的故障 (云节点关机)
# 仅在测试环境中使用

# 步骤3: 在本地VM立即执行复活
./resurrect.sh --now

# 记录输出时间
```

**预期流程**:
```
[预检] 并行执行多项检查...
[拉取] 获取最新备份... (使用缓存)
[恢复] 执行快速复活...
  [1/5] 停止现有服务...
  [2/5] 备份当前工作区...
  [3/5] 恢复备份到工作区...
  [4/5] 恢复API凭证...
  [5/5] 启动OpenClaw...
[验证] 检查复活状态...
通知已发送
总耗时: XX秒
```

**通过标准**:
- [ ] 总耗时 < 120秒
- [ ] 所有验证通过
- [ ] 收到Telegram/飞书通知
- [ ] 能响应新的消息

---

### 场景5: 对话连续性验证 ⏱️ 5分钟

**目的**: 验证故障转移后对话不丢失

```bash
# 步骤1: 云节点正常运行时
# 记录当前MEMORY.md的SHA
cd ~/.openclaw/workspace
git rev-parse HEAD:MEMORY.md

# 步骤2: 故障转移后
# 在本地VM检查MEMORY.md
# 确认内容一致

diff <(git show HEAD:MEMORY.md) ~/.openclaw/workspace/MEMORY.md
```

**通过标准**:
- [ ] 记忆文件完整
- [ ] 最近的对话记录保留
- [ ] 无数据丢失

---

### 场景6: 云节点恢复后的回切测试 ⏱️ 10分钟

**目的**: 验证云节点恢复后能重新接管

```bash
# 假设已完成场景4，本地VM正在运行

# 步骤1: 重新启动云节点
openclaw gateway start
./scripts/cloud-heartbeat.sh --daemon &

# 步骤2: 等待心跳恢复
sleep 120

# 步骤3: 在云节点拉取本地VM的更新
git pull origin main
git merge local-vm-updates  # 如果有冲突需要处理

# 步骤4: 验证云节点接管
# 停止本地VM的OpenClaw
# 确认云节点响应正常
```

**通过标准**:
- [ ] 心跳恢复正常
- [ ] 数据同步无冲突
- [ ] 云节点能正常响应

---

### 场景7: 边界条件测试 ⏱️ 5分钟

#### 测试7.1: 网络抖动
```bash
# 模拟间歇性网络故障
for i in {1..5}; do
  sudo iptables -A OUTPUT -d api.github.com -j DROP
  sleep 30
  sudo iptables -F
  sleep 30
done
```

**通过标准**:
- [ ] 心跳系统在恢复后能继续工作
- [ ] 不会误判为故障

#### 测试7.2: 磁盘空间不足
```bash
# 在本地VM模拟磁盘满
# 预期: 复活前检测失败，给出明确提示
```

**通过标准**:
- [ ] 提前检测磁盘空间
- [ ] 给出清晰的错误信息

#### 测试7.3: GitHub API限流
```bash
# 模拟频繁请求触发限流
# 预期: 优雅降级，等待后重试
```

---

## 三、数据同步策略验证

### 3.1 实时同步机制

```bash
# 测试自动同步脚本
# 在云节点修改文件，观察同步

echo "$(date): 测试修改" >> ~/.openclaw/workspace/memory/test-sync.md

# 30秒后检查GitHub
sleep 30
git log --oneline -1

# 在本地VM拉取验证
git fetch origin
git diff HEAD origin/main
```

### 3.2 冲突解决

```bash
# 模拟双向修改
# 云节点修改文件A
# 本地VM修改同一文件

# 验证冲突检测和提示
```

### 3.3 回滚测试

```bash
# 在本地VM执行
# 恢复到指定版本

cd ~/.openclaw/workspace
git log --oneline -10
git checkout [commit-hash]

# 验证功能正常
```

---

## 四、性能基准测试

### 4.1 各项操作耗时统计

| 操作 | 目标耗时 | 实测耗时 | 状态 |
|------|----------|----------|------|
| 心跳检测 | < 5s | | |
| 备份拉取 (完整) | < 60s | | |
| 备份拉取 (增量) | < 10s | | |
| 服务启动 | < 30s | | |
| 验证流程 | < 10s | | |
| **总故障转移** | **< 120s** | | |

### 4.2 资源占用

```bash
# 监控资源使用
# 在云节点执行心跳时
top -p [heartbeat-pid]

# 在本地VM执行复活时
vmstat 1
iostat 1
```

---

## 五、故障排除指南

### 常见问题

#### Q1: 心跳写入失败
```bash
# 检查GitHub Token
cat ~/.config/linlin/github-token

# 测试API访问
curl -H "Authorization: token $(cat ~/.config/linlin/github-token)" \
  https://api.github.com/user

# 检查分支是否存在
curl -H "Authorization: token $(cat ~/.config/linlin/github-token)" \
  https://api.github.com/repos/useens/linlin-backup/git/refs/heads/heartbeat
```

#### Q2: 本地VM无法检测到故障
```bash
# 检查配置
cat ~/.config/linlin/resurrection.conf

# 手动测试心跳检查
./resurrect.sh --status

# 检查时间同步
date
timedatectl status
```

#### Q3: 复活后OpenClaw无法启动
```bash
# 检查日志
tail -f ~/.openclaw/logs/*.log

# 检查端口占用
lsof -i :18789

# 手动启动看错误
openclaw gateway start --verbose
```

#### Q4: 通知未收到
```bash
# 测试Telegram
curl -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "text=测试消息"

# 测试飞书
curl -X POST "${WEBHOOK}" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"测试消息"}}'
```

---

## 六、测试完成 checklist

- [ ] 所有测试场景通过
- [ ] 2分钟目标达成
- [ ] 文档已更新
- [ ] 回滚方案验证
- [ ] 通知渠道确认
- [ ] 性能基准记录
- [ ] 用户已培训 (如何触发/监控)

---

## 七、后续优化方向

### Phase 3 规划
- [ ] 多本地VM支持 (主备模式)
- [ ] 智能路由 (根据延迟选择节点)
- [ ] 状态同步优化 (WebSocket替代轮询)
- [ ] 自动化故障演练

---

**测试负责人**: [用户]  
**测试时间**: [待执行]  
**测试结果**: [待填写]
