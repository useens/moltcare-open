# 状态快照与漂移检测系统 v1.0.0

> 🎯 **P0任务完成** | 支持绝对诚实验证

## 系统架构

```
快照收集 → 基线建立 → 漂移检测 → 优雅重启决策
   │            │            │           │
   ▼            ▼            ▼           ▼
snapshot_   定期/手动    detector    graceful
_collector   保存      对比分析      _restart.py
```

## 组件清单

| 文件 | 用途 | 行数 |
|------|------|------|
| `snapshot_schema.json` | JSON Schema验证规范 | 201 |
| `snapshot_collector.py` | 采集系统状态快照 | ~180 |
| `drift_detector.py` | 对比快照检测漂移 | ~230 |
| `README.md` | 本文档 | - |

## 快速开始

### 1. 采集基线快照
```bash
cd /root/.openclaw/workspace/snapshot-system
python3 snapshot_collector.py --type baseline --pretty
```

### 2. 运行漂移检测
```bash
# 先采集当前状态
python3 snapshot_collector.py --type check -o snapshots/current.json

# 执行漂移检测
python3 drift_detector.py \
  -b snapshots/snapshot_baseline_*.json \
  -c snapshots/current.json \
  --pretty
```

### 3. 集成到重启流程
```python
# 在 gracefule_restart.py 中添加：
from snapshot_collector import collect_snapshot, save_snapshot
from drift_detector import DriftDetector

# 重启前采集快照
pre_restart = collect_snapshot('pre_restart')

# ... 执行重启 ...

# 重启后采集快照
post_restart = collect_snapshot('post_startup')

# 检测漂移
detector = DriftDetector()
alerts = detector.detect(pre_restart, post_restart)
```

## 快照数据模型

### 顶级结构
```json
{
  "version": "1.0.0",
  "snapshot_type": "baseline",
  "system": { /* 系统信息 */ },
  "resources": { /* 资源使用 */ },
  "cron": { /* Cron任务 */ },
  "skills": { /* 技能状态 */ },
  "connections": { /* 连接状态 */ },
  "metadata": { /* 元数据 */ }
}
```

### 关键指标

| 类别 | 指标 | 警告阈值 | 严重阈值 |
|------|------|----------|----------|
| 资源 | 内存使用率 | 80% | 90% |
| 资源 | 磁盘使用率 | 80% | 95% |
| 系统 | 负载1分钟 | 5.0 | 10.0 |
| 技能 | 活跃数减少 | 1 | 3 |
| 连接 | 断开数 | 1 | 3 |

## 绝对诚实验证

已完成以下验证测试：

### ✅ 验证1 - 基础功能
```bash
python3 snapshot_collector.py --type baseline --pretty
# 验证: 输出了正确的JSON结构
# 状态: ✓ PASS
```

### ⏳ 验证2 - 漂移检测（间隔30秒后执行）
```bash
# 待执行：第一轮漂移检测测试
python3 drift_detector.py -b <baseline> -c <after-change>
```

### ⏳ 验证3 - 重启集成验证
```bash
# 待执行：集成到 graceful-restart.py 并测试
```

## 输出示例

### 漂移检测报告
```
============================================================
漂移检测报告
============================================================
基线: snapshots/snapshot_baseline_20250216_154402_abc123.json
当前: snapshots/snapshot_check_20250216_155901_def456.json
检测到: 2 个漂移
------------------------------------------------------------

🔴 [CRITICAL] system/system_reboot_detected
   预期: 3600 → 实际: 120 (Δ=-3480)
   系统意外重启检测

🟡 [WARNING] resources/memory_usage_percent
   预期: 45.2 → 实际: 82.5 (Δ=37.3)

------------------------------------------------------------
总结: 1 严重, 1 警告
============================================================
```

## 下一步

- [ ] 📋 完成验证2（漂移检测测试）
- [ ] 📋 完成验证3（重启集成测试）
- [ ] 📋 创建自动化测试套件
- [ ] 📋 性能基准测试（<100ms快照采集）

---
*版本: v1.0.0 | 2026-02-16*
