# 316脚本深度审计报告
# 生成时间: 2026-03-06 20:47
# 执行者: 神经中枢 (Nanobot未响应，直接执行)

## 📊 执行摘要

- **总脚本数**: 316个
- **安全删除**: 49个 (15.5%)
- **归档移动**: 15个 (4.7%)
- **保留**: 252个 (79.7%)

**清理后预计**: 267个脚本 (减少49个)

---

## 🗑️ 安全删除清单 (49个)

### 1. Moltbook旧版本 (14个)
```
moltbook_social_v7.py
moltbook_social_v8.py
moltbook_social_v21.py
moltbook_social_v30.py
moltbook_social_v31.py
moltbook_social_v32.py
moltbook_social_v32_clean.py
moltbook_social_v33.py
moltbook_social_v34.py
moltbook_social_v40.py
moltbook_social_v41.py
moltbook_social_v50.py
moltbook_social_v51.py
moltbook_social_v62.py (v61的bug修复版，可删)
```
**保留**: v60, v61, v71 (3个)

### 2. 临时修复脚本 (7个)
```
fix-and-run.py
fix_import_optimized.py
fix_import_standalone.py
fix_import_v2.py
fix_memory_import.py
verify-fix.py
verify_logger.py
```

### 3. 重复命名脚本 (2个)
```
token_optimizer_v10.py (下划线版本，保留横线版本)
state-snapshot-drift-v1-backup-20260216.py (备份文件)
```

### 4. 其他可删除 (14个)
```
fetch_moltbook.py (旧版，已被新版替代)
fetch_moltbook_v2.py (旧版)
fetch-moltbook-simple.py (功能重复)
fetch-moltbook-spa.py (功能重复)
moltbook_process.py (旧版)
moltbook_process_v72.py (中间版本，保留v61)
moltbook_generate_v61.py (中间版本)
moltbook_sender_v60.py (中间版本)
moltbook_scanner_v60.py (中间版本)
browser-automation-demo.py (演示脚本)
ai-consulting-service.py (空壳)
random_numbers.py (无用)
execute_full_learning_cycle.py (功能已合并)
fetch_silicon_zoo.py (旧版，保留v2)
```

### 5. 测试脚本移动 (13个 → tests/)
```
test-30-sources-concurrent.py
test-adaptive-frequency.py
test-daemon.py
test_memory_service.py
test-moltbook-insights.py
test-moltbook-integration.py
test-moltbook-round2.py
test-multi-round-chat.py
test_nanobot_nodes.py
test_uuid_fix.py
test_vector_integration.py
test_vector_queries.py
test_ws_realtime.py
```

---

## 📦 归档清单 (15个)

### 能力突破实验 (15个)
```
capability-breakthrough-exp-01.py ~ exp-15.py
```
**归档位置**: `scripts/.archive/capability-experiments/`

---

## ✅ 保留核心脚本 (252个)

### 1. Nanobot系统 (核心)
- `projects/nanobot/` 目录下所有文件

### 2. 神经中枢P0任务
- `deadman-switch-v2.sh`
- `unified-monitor.py`
- `autonomous-decision-engine.py`

### 3. Moltbook核心 (精简后3个)
- `moltbook_social_v60.py`
- `moltbook_social_v61.py`
- `moltbook_social_v71.py`

### 4. EvoMap核心 (精简后)
- `evomap-periodic-sync.py`
- `evomap-resolver.py`
- `evomap-task-hunter.py` (暂停但保留)

### 5. Polymarket核心 (精简后)
- `polymarket_monitor.py` (已移交给nanobot-1)
- `polymarket_reporter.py`

### 6. 记忆系统核心
- `init-vector-memory-full.py`
- `vector-memory-search.py`
- `rebuild-vector-index.py`

### 7. 自我优化核心
- `self-audit.py`
- `pruning-daemon.py`
- `intelligence-upgrade-daemon.py`

---

## ⚠️ 依赖检查结果

### 被引用的脚本 (不能删除)
- `moltbook_cli.py` - 被多个脚本导入
- `route.py` - 核心路由
- `cc.py` - 核心协调

### 无依赖的脚本 (可安全删除)
- 大部分旧版本Moltbook脚本
- 所有临时修复脚本
- 所有能力突破实验

---

## 📈 清理效果预估

| 指标 | 当前 | 清理后 | 变化 |
|------|------|--------|------|
| 脚本总数 | 316 | 267 | -49 (-15.5%) |
| 根目录脚本 | 316 | 252 | -64 (-20.3%) |
| tests/目录 | 0 | 13 | +13 |
| .archive/目录 | 少量 | 15+ | +15 |

---

## 🚀 执行建议

### 阶段1: 安全删除 (推荐立即执行)
- 临时修复脚本 (7个)
- 重复命名脚本 (2个)
- 明显无用的脚本 (4个)
**小计**: 13个，0风险

### 阶段2: Moltbook版本清理 (需要验证)
- 旧版本社交脚本 (14个)
- 旧版提取器 (5个)
**小计**: 19个，低风险

### 阶段3: 归档 (可逆操作)
- 能力突破实验 (15个)
- 测试脚本移动 (13个)
**小计**: 28个，可恢复

---

## ✅ 最终建议

**执行阶段1+2+3**: 安全清理49个脚本，从316减少到267个。

**风险等级**: 低 (已验证依赖关系)

**是否执行?** 等待用户确认。

---
*深度审计报告完成 - 神经中枢执行*
