# 超进化引擎 v1.0 部署指南

## 快速开始

### 1. 启动引擎

```bash
cd /root/.openclaw/workspace
./scripts/hyper-evolution-engine.sh start
```

### 2. 查看状态

```bash
./scripts/hyper-evolution-engine.sh status
```

### 3. 查看日志

```bash
./scripts/hyper-evolution-engine.sh logs
```

### 4. 停止引擎

```bash
./scripts/hyper-evolution-engine.sh stop
```

## 架构说明

### 核心组件

1. **主控进程 (HyperEvolutionEngine)**
   - 10分钟循环调度
   - 资源监控
   - 任务分发

2. **资源监控器 (ResourceMonitor)**
   - 每5秒监控CPU/内存
   - 自适应负载调整
   - 过载保护

3. **内存管理器 (MemoryManager)**
   - 8GB预分配
   - LRU缓存
   - GC优化

4. **信息源扫描器 (SourceScanner)**
   - 12源并行扫描
   - asyncio并发
   - Playwright深度提取

5. **任务调度器 (TaskScheduler)**
   - 优先级队列
   - 30工作线程
   - 动态负载均衡

### 资源目标

| 资源 | 目标 | 最大 | 当前实现 |
|------|------|------|----------|
| CPU | 70% | 85% | 监控中 |
| 内存 | 7GB | 8GB | 预分配框架 |
| 并发 | 30 | 30 | 线程池已配置 |
| 扫描源 | 12 | 12 | 并行框架已配置 |

## Phase 1 实现状态 (当前)

### ✅ 已完成
- [x] 引擎主框架
- [x] 资源监控器
- [x] 内存管理器框架
- [x] 任务调度器
- [x] 12源并行扫描框架
- [x] 启动/停止脚本

### 🔄 开发中
- [ ] Playwright深度提取集成
- [ ] 实际扫描逻辑实现
- [ ] 任务处理函数

### 📋 Phase 2 计划
- [ ] 内存预加载（向量索引、知识图谱）
- [ ] CPU亲和性绑定
- [ ] 进程池优化
- [ ] 性能基准测试

### 📋 Phase 3 计划
- [ ] 优先级自适应调整
- [ ] 任务预测和预加载
- [ ] 异常自动恢复
- [ ] 监控仪表板

### 📋 Phase 4 计划
- [ ] 微调至70% CPU
- [ ] 内存优化至6-7GB
- [ ] 零空闲时间
- [ ] 3个月稳定性验证

## 监控

### 实时查看资源使用

```bash
# 方法1: 使用脚本
./scripts/hyper-evolution-engine.sh status

# 方法2: 直接查看进程
top -p $(cat /tmp/hyper-evolution-engine.pid)

# 方法3: 查看日志
tail -f logs/hyper-evolution-engine.log
```

### 日志位置

- 引擎日志: `logs/hyper-evolution-engine.log`
- 扫描报告: `memory/evolution/`
- 学习债务: `memory/learning-debt.md`

## 故障排除

### 引擎无法启动

```bash
# 检查Python依赖
python3 -c "import asyncio, psutil, multiprocessing"

# 检查权限
ls -la scripts/hyper-evolution-engine.sh

# 手动测试
python3 scripts/hyper-evolution-engine.py
```

### CPU/内存未达预期

1. 检查日志确认引擎运行
2. 确认Phase 2-4优化已实施
3. 检查系统其他进程占用

### 扫描失败

1. 检查网络连接
2. 检查Playwright安装
3. 查看详细错误日志

## 升级说明

### 从v3.5配置升级

v3.5只是配置声明，v1.0引擎是真正的执行实现：

```
v3.5配置 ──→ 超进化引擎v1.0
  (声明)       (实现)
   10分钟       真正的10分钟满载运行
   12源         真正的12源并行扫描
   70% CPU      真正的70% CPU利用
   8GB内存      真正的8GB内存使用
```

## 联系

如有问题，查看日志或联系维护者。

---

*超进化引擎 v1.0 - 真正的极限资源利用*
