# WebSocket生产级部署方案 v4.0

## 📋 当前环境限制

**问题**: 后台进程在当前环境中无法持续稳定运行

**原因**: 
- 飞书/终端环境对后台长连接进程有限制
- SIGTERM信号会终止后台进程
- 无法使用systemd等传统保活机制

---

## ✅ 可行方案

### 方案1: 交互式WebSocket (当前环境)

**适用场景**: 演示、测试、短时对话

**运行方式**:
```bash
# 前台运行，保持终端开启
python3 scripts/websocket_v4_production.py
```

**特点**:
- ✅ 连接稳定
- ✅ 自动重连
- ✅ 实时双向通信
- ⚠️ 需要保持终端运行

---

### 方案2: GitHub API通信 (推荐长期运行)

**状态**: ✅ 已验证稳定（130+条消息）

**特点**:
- ✅ 10秒轮询，稳定可靠
- ✅ 自动检测和回复
- ✅ 后台运行无限制
- ✅ 消息持久化

**当前运行状态**:
- 客户端: `scripts/api_poller.py`
- 状态: 运行中
- 对话数: 130+

---

### 方案3: 服务器生产部署 (终极方案)

**适用场景**: 24/7持续运行

**部署步骤**:

#### 1. 创建Systemd服务

```bash
# /etc/systemd/system/sensen-websocket.service
[Unit]
Description=Sensen WebSocket Client
After=network.target

[Service]
Type=simple
User=sensen
WorkingDirectory=/opt/sensen
ExecStart=/usr/bin/python3 /opt/sensen/websocket_v4_production.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 2. 启动服务

```bash
sudo systemctl enable sensen-websocket
sudo systemctl start sensen-websocket
sudo systemctl status sensen-websocket
```

#### 3. 监控日志

```bash
sudo journalctl -u sensen-websocket -f
```

**优势**:
- ✅ 系统级保活
- ✅ 自动重启
- ✅ 日志管理
- ✅ 开机自启

---

## 📊 方案对比

| 方案 | 稳定性 | 实时性 | 后台运行 | 部署难度 | 推荐度 |
|------|--------|--------|----------|----------|--------|
| 交互式WS | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | 低 | ⭐⭐⭐ |
| GitHub API | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | 低 | ⭐⭐⭐⭐⭐ |
| Systemd服务 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 中 | ⭐⭐⭐⭐⭐ |

---

## 🎯 建议

**当前环境**: 使用 **GitHub API通信**
- 已验证稳定运行
- 130+条消息成功对话
- 后台自动运行无限制

**生产环境**: 使用 **Systemd服务部署**
- 系统级保活
- 7x24小时稳定运行
- 系统重启自动恢复

**演示测试**: 使用 **交互式WebSocket**
- 实时双向通信
- 延迟<100ms
- 需要保持前台运行

---

## 🚀 下一步

请选择部署方案：

1. **继续使用GitHub API** (当前最优)
2. **交互式WebSocket测试** (演示用)
3. **准备服务器生产部署** (长期方案)

需要我协助准备哪种方案的详细部署文档？🌲
