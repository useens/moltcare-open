# 🚀 超进化模式使用指南

## 快速开始

### 启动超进化模式

```bash
# 方式1: 直到用户说结束
python3 scripts/hyper-evolution.py start

# 方式2: 持续指定时长
python3 scripts/hyper-evolution.py start --duration 48  # 48小时

# 方式3: 直到达成里程碑
python3 scripts/hyper-evolution.py start --milestone version-release
```

或者直接对我说：
- `开始超进化`
- `开始超进化，持续2天`
- `开始超进化，直到更新一个大版本`

### 停止超进化模式

```bash
python3 scripts/hyper-evolution.py stop
```

或对我说：`结束超进化`

### 查看状态

```bash
python3 scripts/hyper-evolution.py status
```

## 超进化 vs 正常模式

| 维度 | 正常模式 | 超进化模式 |
|------|----------|------------|
| **扫描频率** | 每2-6小时 | 每30分钟 |
| **Signal阈值** | ≥7 | ≥6 (更积极) |
| **深度提取量** | 每源3条 | 每源10条 |
| **活跃信息源** | 3个 | 8+个 |
| **CPU使用** | 30% | 80% |
| **知识内化** | 每日 | 每4小时 |
| **应用检验** | 可选 | 强制 |

## 执行流程

```
用户: 开始超进化
    ↓
🟢 激活超进化状态
    ↓
每30分钟自动循环:
  ├─ 📡 高强度情报收集 (8+源)
  ├─ 📚 学习债务处理
  ├─ 🧠 知识内化 → MEMORY.md
  ├─ ✅ 应用检验 → 验证效果
  └─ 🔍 检查结束条件
    ↓
达成条件 → 📊 生成进化报告 → 退出
```

## 核心文件

| 文件 | 作用 |
|------|------|
| `config/hyper-evolution.yaml` | 超进化配置 |
| `scripts/hyper-evolution.py` | 模式控制器 |
| `scripts/hyper-evolution-loop.sh` | 执行循环 |
| `memory/hyper-evolution-state.json` | 实时状态 |
| `memory/evolution-log.md` | 进化历史 |

## 安全保护

即使处于超进化模式，以下情况会自动触发保护：
- 系统负载超过90%
- 内存使用超过4GB
- 连续5次任务失败
- 用户发送任何指令

---

*超进化模式 v1.0.0 - 代号 Hyperion*
