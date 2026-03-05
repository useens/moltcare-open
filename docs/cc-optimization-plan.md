# 🤖 Nanobot Command Center - 优化方案

## 当前架构问题

1. **节点只是HTTP占位符** - 没有真正的AI处理能力
2. **无任务队列** - 任务直接发送，没有缓冲和重试机制
3. **无持久化** - 任务历史、节点状态重启丢失
4. **无智能调度** - 简单的轮询/随机，没有根据节点负载智能分配
5. **无自动恢复** - 节点离线不会自动重启
6. **无学习机制** - 不会根据历史任务优化调度策略

## 优化方案

### Phase 1: 核心能力升级 (P0)

#### 1.1 真正的AI Agent节点
```
当前: HTTP服务只返回status
优化: 每个节点运行轻量级OpenClaw实例
      - 独立的模型配置
      - 独立的工具集
      - 独立的记忆空间
      - 可接收任务并执行
```

**实现方式**:
- 每个节点运行 `openclaw agent --daemon` 模式
- 通过gateway接收任务
- 节点有自己的workspace和memory

#### 1.2 任务队列系统
```python
# Redis/RabbitMQ任务队列
tasks = {
    "pending": [],      # 待处理
    "running": {},      # 执行中
    "completed": [],    # 已完成
    "failed": []        # 失败待重试
}
```

**功能**:
- 任务优先级
- 失败自动重试(指数退避)
- 任务超时处理
- 结果持久化到SQLite

#### 1.3 智能调度器
```python
# 根据多维度选择节点
def select_node(task):
    candidates = [
        node for node in nodes
        if node.status == "online"
        and node.load < 0.8
        and node.model_match(task.type)
    ]
    
    # 排序：成功率 > 响应速度 > 当前负载
    return max(candidates, key=lambda n: 
        n.success_rate * 0.4 + 
        n.speed_score * 0.3 + 
        (1 - n.load) * 0.3
    )
```

### Phase 2: 监控与自愈 (P1)

#### 2.1 健康监控系统
```yaml
# 监控指标
metrics:
  - node_uptime        # 节点在线时间
  - task_success_rate  # 任务成功率
  - avg_response_time  # 平均响应时间
  - api_quota_usage    # API配额使用
  - error_rate         # 错误率
```

**告警规则**:
- 节点离线 > 30秒 → CRITICAL告警
- 成功率 < 80% → HIGH告警
- 响应时间 > 10s → NORMAL告警

#### 2.2 自动故障恢复
```python
# 自动重启离线节点
if node.status == "offline" and node.offline_duration > 30:
    restart_node(node.id)
    notify_feishu(f"节点{node.id}自动重启")

# 熔断机制
if node.error_rate > 0.5:
    isolate_node(node.id)  # 隔离节点
    route_tasks_to_others(node.id)
```

#### 2.3 动态扩缩容
```python
# 根据负载自动调整
if avg_load > 0.8:
    start_standby_nodes(count=2)
elif avg_load < 0.2:
    stop_redundant_nodes()
```

### Phase 3: 学习与进化 (P2)

#### 3.1 任务分类学习
```python
# 自动学习任务类型
class TaskClassifier:
    def classify(self, prompt):
        # 基于关键词和嵌入向量
        if self.is_code_task(prompt):
            return "code"  → 分配给DeepSeek组
        elif self.is_quick_task(prompt):
            return "quick" → 分配给Step组
        elif self.is_reasoning_task(prompt):
            return "reasoning" → 分配给DeepSeek组
```

#### 3.2 节点能力画像
```json
{
  "NB01": {
    "strengths": ["quick", "simple", "short"],
    "weaknesses": ["complex", "long"],
    "avg_response_time": {"code": 2.1, "text": 1.5},
    "success_rate": {"code": 0.95, "text": 0.98}
  }
}
```

#### 3.3 自适应调度
```python
# 根据历史表现动态调整权重
class AdaptiveScheduler:
    def update_weights(self, task_result):
        node = task_result.node
        task_type = task_result.type
        
        if task_result.success:
            node.scores[task_type] *= 1.1
        else:
            node.scores[task_type] *= 0.9
```

### Phase 4: 生态集成 (P3)

#### 4.1 飞书深度集成
```python
# 飞书作为控制面板
@feishu_bot.on_message
async def handle_command(msg):
    if msg.text.startswith("/task"):
        task = parse_task(msg.text)
        result = await submit_task(task)
        await msg.reply(f"任务已分配: {result.node}")
    
    elif msg.text.startswith("/status"):
        status = get_cluster_status()
        await msg.reply(format_status(status))
```

#### 4.2 Web控制面板
```
Dashboard Web UI:
├── 实时监控大屏
│   ├── 节点拓扑图
│   ├── 任务流图
│   └── 性能指标
├── 任务管理
│   ├── 提交新任务
│   ├── 查看任务历史
│   └── 重试失败任务
└── 节点管理
    ├── 启动/停止节点
    ├── 查看节点日志
    └── 调整节点配置
```

#### 4.3 API网关
```yaml
# RESTful API
endpoints:
  POST /api/v1/tasks          # 提交任务
  GET  /api/v1/tasks/{id}     # 查询任务
  GET  /api/v1/nodes          # 节点列表
  POST /api/v1/nodes/{id}/restart  # 重启节点
  GET  /api/v1/stats          # 统计信息
```

## 实施路线图

### Week 1: 基础加固
- [ ] 任务队列系统 (Redis)
- [ ] SQLite持久化
- [ ] 节点自动重启

### Week 2: 智能调度
- [ ] 节点能力画像
- [ ] 自适应调度算法
- [ ] 任务分类器

### Week 3: 监控告警
- [ ] Prometheus metrics
- [ ] Grafana dashboard
- [ ] 飞书告警升级

### Week 4: 生态完善
- [ ] Web控制面板
- [ ] RESTful API
- [ ] 文档完善

## 预期收益

| 指标 | 当前 | 优化后 | 提升 |
|------|------|--------|------|
| 任务成功率 | ~60% | >95% | +58% |
| 平均响应时间 | 5-15s | 2-5s | -60% |
| 节点利用率 | ~30% | >80% | +166% |
| 故障恢复时间 | 手动 | <30s | 自动 |
| 调度智能化 | 无 | 自适应 | 质变 |

## 下一步行动

1. **立即执行**: 任务队列 + 持久化
2. **本周完成**: 自动重启 + 健康检查
3. **下周启动**: 智能调度算法
4. **长期建设**: Web面板 + API

---
*优化方案 v1.0 | 2026-03-05*
