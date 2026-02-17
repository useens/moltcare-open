# Smart Router Service 配置文档

## 概述

智能路由常驻服务，为 OpenClaw 系统提供实时的模型与 thinking 模式决策。

## 服务详情

- **服务名**: `smart-router.service`
- **端口**: `8766` (仅 localhost)
- **Socket**: HTTP REST API
- **状态**: ✅ 已启用并自动启动

## API 端点

### `GET /health`
健康检查，返回服务状态。

### `POST /route`
执行路由决策。

**请求体**:
```json
{
  "task": "任务描述",
  "signal": 5,           // 可选 1-10
  "difficulty": "L3",    // 可选 L1-L5
  "current_model": "ds"  // 可选
}
```

**响应**:
```json
{
  "model": "ds",
  "full_model": "nvidia-build/deepseek-ai/deepseek-v3.2",
  "thinking": "on",
  "reason": "...",
  "tier": "free_fast",
  "cost": "免费",
  "success": true
}
```

### `POST /recommend`
获取人类可读的路由建议文本。

响应:
```json
{
  "text": "💎 路由建议\n模型: k2p5\n..."
}
```

### `GET /metrics`
服务指标。

## 客户端工具

### `scripts/smart-router-client.sh`
命令行客户端，快速调用服务。

```bash
./scripts/smart-router-client.sh "帮我写Python脚本"
./scripts/smart-router-client.sh "重要任务" 9
```

### `scripts/spawn_with_service.sh`
生成 `sessions_spawn` 命令，集成到工作流。

```bash
# 输出 spawn 命令
./scripts/spawn_with_service.sh "帮我设计微服务架构"

# 直接执行 (eval)
eval $(./scripts/spawn_with_service.sh "写一个爬虫")
```

### 原有脚本保留
- `scripts/spawn_with_routing.sh` (本地脚本模式)
- `scripts/smart-router-unified.sh`
- `scripts/auto-router.sh`
- `scripts/smart_router.py`

## 系统管理

```bash
# 查看状态
systemctl status smart-router.service

# 查看日志
journalctl -u smart-router.service -f

# 重启服务
systemctl restart smart-router.service

# 停止并禁用
systemctl stop smart-router.service
systemctl disable smart-router.service
```

## 资源限制

- Memory: 512M
- CPU: 50%
- 自动重启: on-failure

## 集成建议

在需要路由决策的地方，使用 HTTP 调用：

```bash
RESULT=$(curl -s -X POST http://127.0.0.1:8766/route \
  -H "Content-Type: application/json" \
  -d '{"task":"用户输入","signal":7}')
MODEL=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['model'])")
```

或在 Python 中：

```python
import requests
resp = requests.post('http://127.0.0.1:8766/route', json={'task': task, 'signal': signal})
result = resp.json()
model = result['model']
thinking = result['thinking']
```

## 故障排除

1. 服务无法启动: 检查端口占用 `ss -tulpn | grep 8766`
2. 连接失败: 确认服务状态 `systemctl status`
3. 调用缓慢: 查看日志 `journalctl -u smart-router.service`

---

最后更新: 2026-02-18 00:35 GMT+8
