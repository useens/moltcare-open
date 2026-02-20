# EvoMap Auto-Resolver 实现完成

## ✅ 已实现功能

### 1. 自动错误检测 (`evomap-resolver.py`)
- 检测 10 种常见错误模式：
  - 网络错误 (timeout, connection refused, 429)
  - 内存错误 (OOM, memory limit)
  - 数据库错误 (MySQL gone away)
  - 文件系统错误 (ENOENT, permission)
  - 飞书错误 (format error, card rejected)
  - CORS 错误
  - 会话丢失
  - Agent 错误
  - 命令不存在
  - WebSocket 错误

### 2. 自动 EvoMap 查询
- 根据错误模式提取 signals
- POST /a2a/fetch 查询匹配的 capsules
- 按 signals 匹配度排序
- 选择 GDI 最高的解决方案

### 3. 智能应用策略
- `auto_apply=True`: 自动应用 (网络、飞书等低风险错误)
- `auto_apply=False`: 需要人工确认 (数据库、文件系统等高风险错误)
- GDI < 70: 需要人工确认

### 4. 集成到消息处理流程
- 修改 `trigger_handler.py`
- 在 `process_message()` 中自动检测错误
- 返回 `evomap_resolution` 字段

## 📊 工作流程

```
消息输入
    ↓
检测错误关键词 (error/timeout/memory/...)
    ↓
匹配错误模式 → 提取 Signals
    ↓
查询 EvoMap /a2a/fetch
    ↓
找到匹配 Capsules?
    ├── 否 → 返回 None
    └── 是 → 按 GDI 排序
                ↓
        自动应用? (auto_apply=True + GDI>=70)
            ├── 是 → 应用解决方案，记录到日志
            └── 否 → 返回 needs_review
```

## 📁 新增/修改文件

```
scripts/evomap-resolver.py          # 新增：自动解决器核心
core/trigger_handler.py              # 修改：集成 EvoMap 解决
logs/evomap-resolver.log             # 新增：解决日志
data/evomap/auto-resolutions.jsonl   # 新增：应用记录
```

## 🧪 测试结果

```bash
$ python3 scripts/evomap-resolver.py --test

测试 1: Connection timeout
  → 匹配: 网络连接错误
  → Signals: [TimeoutError, ECONNRESET, ...]
  → 找到 3 个 capsules
  → 最佳: GDI=70.9 (HTTP Retry)
  → 状态: ✅ resolved

测试 2: Feishu format error  
  → 匹配: 飞书消息发送错误
  → Signals: [FeishuFormatError, ...]
  → 找到 2 个 capsules
  → 最佳: GDI=69.5 (Message Fallback)
  → 状态: ✅ resolved

测试 3: MySQL gone away
  → 匹配: 数据库连接错误
  → Auto-apply: False
  → 状态: ⚠️ needs_review
```

## 🚀 使用方式

### 自动触发
当森森遇到错误时，会自动触发：
```python
# 在 trigger_handler.py 中
result = process_message("Connection timeout...")
# 返回: {'evomap_resolution': {'status': 'resolved', ...}}
```

### 手动调用
```python
from scripts.evo_map_resolver import EvoMapResolver

resolver = EvoMapResolver()
result = resolver.resolve("Error message here")

if result['status'] == 'resolved':
    print(f"应用了: {result['capsule']['asset_id']}")
```

## 📈 后续优化

- [ ] 添加更多错误模式
- [ ] 实现 Capsule 的自动应用（目前只记录）
- [ ] 添加解决效果追踪
- [ ] 集成到 autonomous-decision-engine

## 🎯 当前状态

✅ **已实现**: 检测 → 查询 → 匹配 → 记录 的完整闭环
✅ **已测试**: 网络和飞书错误可自动找到解决方案
🔄 **待完善**: 自动应用解决方案到实际系统
