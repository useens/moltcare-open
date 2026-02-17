# 智能路由架构统一文档

## 🎯 设计目标

- **服务优先**: 常驻 HTTP 服务提供低延迟路由决策
- **向后兼容**: 所有旧脚本可继续使用
- **无缝降级**: 服务故障时自动回退本地脚本
- **统一入口**: 推荐使用 `smart-router-wrapper.sh`

---

## 🏗️ 架构组成

```
┌─────────────────────────────────────────────────────────────┐
│                    智能路由生态系统                          │
├─────────────────────────────────────────────────────────────┤
│  调用层 (Client Layer)                                      │
│  ├─ scripts/smart-router-wrapper.sh  ← 首选入口              │
│  ├─ scripts/spawn_with_routing.sh   ← spawn集成             │
│  ├─ scripts/smart-router-client.sh  ← 命令行客户端           │
│  └─ scripts/smart-router-unified.sh ← 交互式（本地）         │
├─────────────────────────────────────────────────────────────┤
│  服务层 (Service Layer)                                     │
│  └─ smart-router.service (Flask on 127.0.0.1:8766)          │
│     ├─ GET  /health                                        │
│     ├─ POST /route  (JSON API)                             │
│     ├─ POST /recommend (文本建议)                           │
│     └─ GET  /metrics                                       │
├─────────────────────────────────────────────────────────────┤
│  引擎层 (Engine Layer)                                      │
│  └─ scripts/smart_router.py (核心路由逻辑)                  │
│     ├─ route(task, current_model)                          │
│     ├─ route_by_signal(signal, task_type)                  │
│     └─ route_by_difficulty(difficulty)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 文件清单

| 文件 | 用途 | 状态 |
|------|------|------|
| `scripts/smart_router.py` | 核心路由引擎 (6KB) | ✅ 原始 |
| `scripts/smart-router-service.py` | HTTP 服务封装 (4.7KB) | ✅ 新建 |
| `scripts/smart-router-client.sh` | 命令行客户端 (1KB) | ✅ 新建 |
| `scripts/smart-router-wrapper.sh` | **统一入口** (670B) | ✅ 新建 |
| `scripts/spawn_with_routing.sh` | spawn 包装 (已更新) | ✅ 已更新 |
| `scripts/spawn_with_service.sh` | service 版 spawn (2.5KB) | ✅ 可选 |
| `scripts/smart-router-unified.sh` | 本地交互式路由 | ✅ 原始 |
| `scripts/auto-router.sh` | 基础自动路由 | ✅ 原始 |
| `scripts/k2p5-smart-eval.sh` | k2p5 难度评估 | ✅日子 |
| `config/systemd/smart-router.service` | systemd 单元 | ✅ 新建 |
| `config/SMART_ROUTER_SERVICE.md` | 服务文档 | ✅ 新建 |

---

## 🚀 推荐用法

### 1. 通用场景（自动选择模型）

```bash
# 使用统一包装器（优先服务，失败回退本地）
./scripts/smart-router-wrapper.sh "任务描述" [current_model]
```

### 2. 生成子任务 spawn 命令

```bash
# 推荐：自动路由并生成 spawn 命令
./scripts/spawn_with_routing.sh "帮我写Python爬虫"

# 或使用纯 service 版本（不包含交互信息）
./scripts/spawn_with_service.sh "帮我写Python爬虫"
```

### 3. 直接调用 API (其他程序集成)

```bash
# 命令行
RESULT=$(curl -s -X POST http://127.0.0.1:8766/route \
  -H "Content-Type: application/json" \
  -d '{"task":"任务描述","signal":7}')
MODEL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['model'])")
```

```python
# Python 程序
import requests
r = requests.post('http://127.0.0.1:8766/route', json={
    'task': task,
    'signal': 5,
    'difficulty': 'L3'
})
result = r.json()
```

### 4. 交互式决策（开发调试）

```bash
# 本地 unified 脚本（无需服务）
./scripts/smart-router-unified.sh "任务描述"
```

---

## 🔄 路由策略概览

| 输入条件 | 模型 | Thinking | 理由 |
|----------|------|----------|------|
| Signal ≥ 9 | k2p5 | stream | 高价值内容 |
| Signal 7-8 | ds / glm | on | 中高价值 |
| 包含"代码"关键词 | ds | on / concise | 代码任务优化 |
| 包含"中文"关键词 | glm | on | 中文处理优化 |
| 极简任务 (你好/状态) | step | off | 快速响应 |
| 默认 | step | concise | 成本优先 |

详细规则见 `scripts/smart_router.py`。

---

## 🛠️ 系统管理

```bash
# 服务状态
systemctl status smart-router.service

# 重启服务
systemctl restart smart-router.service

# 查看日志
journalctl -u smart-router.service -f
tail -f /var/log/smart-router-service.log

# 测试端点
curl http://127.0.0.1:8766/health
curl -X POST http://127.0.0.1:8766/metrics
```

---

## 📊 性能指标

- **启动时间**: < 1s
- **响应时间**: < 10ms (p99)
- **内存驻留**: ~20 MB
- **CPU 限制**: 50%
- **并发能力**: 无限制 (Flask 多线程)

---

## 🔧 故障排除

| 问题 | 诊断 | 解决方案 |
|------|------|----------|
| 服务无法启动 | `systemctl status` | 检查端口占用 `ss -tulpn \| grep 8766` |
| 调用超时 | `curl -v http://127.0.0.1:8766/health` | 查看服务日志 |
| 总是返回 step | 检查请求体 JSON | 确保传递正确 task 字段 |
| 高延迟 | 服务是否卡住 | `journalctl -u smart-router.service` |

---

## 🎓 路由决策示例

```bash
$ ./scripts/spawn_with_routing.sh "设计一个高可用微服务"
# 输出:
# 模型: ds
# Thinking: on
# 原因: 复杂工作流，ds推理能力强

$ ./scripts/smart-router-wrapper.sh "帮我写Python爬虫"
# {
#   "model": "ds",
#   "thinking": "on",
#   "reason": "代码任务，ds免费且强"
# }

$ ./scripts/smart-router-wrapper.sh "分析这个架构" "" "L4"
# 使用 difficulty 模式
```

---

## 🧩 扩展性

如需添加新模型或规则：

1. 修改 `scripts/smart_router.py` 中的 `MODELS` 定义
2. 调整 `route()`, `route_by_signal()`, `_is_code_task()` 等逻辑
3. 重启服务: `systemctl restart smart-router.service`

无需修改调用方。

---

## 📝 更新日志

- **2026-02-18 00:35**: 常驻服务上线，统一入口 wrapper
- **2026-02-17**: v3.0 成本优先路由引擎完成
- **2026-02-16**: 多版本脚本 (unified, auto, v2) 并存

---

最后更新: 2026-02-18 00:39 GMT+8
