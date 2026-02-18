# 智能模型路由系统 - 配置完成

> ✅ 已根据用户需求配置：step 默认，复杂/代码/图像/子代理任务自动路由到 k2p5 或相应的最优模型。

---

## 📋 配置概览

### 1. 模型集
| 别名 | 完整模型ID | 用途 |
|------|------------|------|
| `step` (默认) | `nvidia-build/stepfun-ai/step-3.5-flash` | 常规任务、中文、简单任务 |
| `k2p5` | `kimi-coding/k2p5` | 复杂任务、代码开发、L3-L5 |
| `nvidia-kimi` | `nvidia-build/moonshotai/kimi-k2.5` | 图片/文档分析、视觉任务 |
| `nvidia-glm` | `nvidia-build/z-ai/glm4.7` | 备用（中文优化） |
| `nvidia-ds` | `nvidia-build/deepseek-ai/deepseek-v3.2` | 备用（推理） |
| `nvidia-qwen` | `nvidia-build/qwen/qwen3.5-397b-a17b` | 备用 |

**环境变量**：`NVIDIA_API_KEY` 已设置，安全存储 API Key。

**网关重启**：已完成，配置已生效。

---

## 🧠 智能路由规则

### 自动切换逻辑

| 任务类型 | 触发关键词 | 目标模型 | Thinking模式 | 说明 |
|---------|-----------|----------|-------------|------|
| **图片/视觉** | 图片、截图、OCR、图表 | `nvidia-kimi` | `on` | Kimi 支持多模态+256k上下文 |
| **代码任务** | 代码、编程、算法、调试 | `k2p5` | `auto` (L2:concise, L3+:on) | k2p5 最强代码能力 |
| **中文/快速** | 中文、翻译、简单、快速 | `step` | `on` | Step 快速响应 |
| **默认** | 其他 | `step` | `on` | 通用任务 |

### 难度分级（L1-L5）

| 级别 | 难度 | Thinking | 适用模型 | 触发特征 |
|------|------|----------|----------|----------|
| L1 | 极简 | `off` | step | "你好"、"状态"、短确认 |
| L2 | 简单 | `concise` | step/k2p5 | 语法修复、简单问题、<20行代码 |
| L3 | 中等 | `on` | k2p5/step | 函数、模块、常规调试、20-100行代码 |
| L4 | 困难 | `on` | k2p5 | 架构、设计、复杂算法、100+行代码 |
| L5 | 极难 | `stream` | k2p5 | 系统重构、高可用、大规模、疑难问题 |

---

## 🚀 使用方式

### 1. 普通对话
正常发送消息，系统默认使用 **step** 模型。

如果检测到自动路由规则匹配，系统会**建议**切换模型并等待确认（5秒超时）。

手动切换：`/status model=k2p5` 或 `/status model=nvidia-kimi`

### 2. 子代理任务
当启动子代理（sessions spawn）时，系统自动评估任务难度并选择模型。

**示例**：
```bash
openclaw sessions spawn --task="帮我设计一个分布式数据库分片方案" --agent=main
```
自动路由决策：
- 难度：L5
- 模型：k2p5
- Thinking：stream

### 3. 手动评估难度
```bash
python3 scripts/assess-difficulty.py "你的任务描述"
```
输出：难度级别、推荐模型、Thinking模式、原因。

---

## 📁 文件清单

| 文件 | 用途 |
|------|------|
| `/root/.openclaw/openclaw.json` | 主配置（已更新 models.providers） |
| `/root/.openclaw/workspace/config/auto-routing-rules.md` | 路由规则文档 |
| `/root/.openclaw/workspace/config/model-routing.yaml` | YAML路由配置（备用） |
| `/root/.openclaw/workspace/scripts/assess-difficulty.py` | 难度评估脚本 |
| `/root/.openclaw/workspace/scripts/smart-router-unified.sh` | 统一智能路由（供spawn调用） |
| `/root/.openclaw/workspace/scripts/spawn_with_routing.sh` | 子代理智能路由包装器 |
| `/root/.openclaw/workspace/scripts/auto-model-router.py` | 自动模型路由器（建议集成） |

---

## ⚙️ 自动化任务

已安装的 cron 任务（`crontab -l`）：
- `*/5 * * * * .../auto-model-router.py --scan` - 定期检查路由（可选）

**注意**：当前自动路由建议仅在子代理启动时自动应用。普通会话需要用户确认或手动切换。

如需全自动（无确认），可修改 `auto-routing-rules.md` 中的 `confirmation.enabled` 或调整脚本参数。

---

## 🎯 测试验证

### 测试 1：复杂任务
```bash
/root/.openclaw/workspace/scripts/spawn_with_routing.sh "设计一个高可用的微服务架构，包含服务发现、配置中心、熔断降级" main
```
✅ 应路由到 `k2p5` + `stream`

### 测试 2：图片任务
```bash
/root/.openclaw/workspace/scripts/spawn_with_routing.sh "分析这张架构图，识别所有组件和它们之间的关系" main
```
✅ 应路由到 `nvidia-kimi` + `on`

### 测试 3：简单任务
```bash
/root/.openclaw/workspace/scripts/spawn_with_routing.sh "你好" main
```
✅ 应路由到 `step` + `off`

### 测试 4：代码任务
```bash
/root/.openclaw/workspace/scripts/spawn_with_routing.sh "帮我写一个Python的快速排序函数" main
```
✅ 应路由到 `k2p5` + `on`

---

## 🔧 调整规则

如需修改路由逻辑，编辑以下文件：

1. **难度关键词**：`scripts/assess-difficulty.py` 中的 `l5_patterns`、`l4_patterns` 等
2. **路由映射**：`scripts/assess-difficulty.py` 中的 `get_model_for_difficulty()` 函数
3. **模型别名**：`openclaw.json` 中的 `agents.defaults.models` 和 `agents.defaults.model.primary`

修改后**无需重启**网关，新任务将使用新规则。

---

## 📊 监控与统计

模型使用统计：`scripts/analyze-model-usage.py`（可选）

 Cron 每小时运行一次，记录模型使用情况用于优化。

---

## ❓ 问题排查

| 问题 | 可能原因 | 解决 |
|------|----------|------|
| NVIDIA API Key 无效 | 环境变量未设置或过期 | `echo $NVIDIA_API_KEY` 检查，更新 `~/.bashrc` |
| 模型切换不生效 | Gateway 未重启 | 执行 `openclaw gateway restart` |
| 子代理未自动选模型 | spawn 脚本未使用包装器 | 确保使用 `spawn_with_routing.sh` 而不是直接调用 `openclaw sessions spawn` |
| Thinking 模式不对 | 难度评估错误 | 检查 `assess-difficulty.py` 中的规则，或手动指定 `/status thinking=on` |

---

## ✅ 完成清单

- [x] 添加 nvidia-build 提供商配置到 `openclaw.json`
- [x] 设置 `NVIDIA_API_KEY` 环境变量
- [x] 设置默认模型为 `step`
- [x] 创建智能路由规则（文档+YAML）
- [x] 实现难度评估脚本
- [x] 实现统一路由脚本
- [x] 实现子代理包装器
- [x] 测试各场景路由
- [x] 安装 cron 自动化任务
- [x] 编写使用指南

**状态**：✅ 智能模型路由系统已全面配置完成

---

*配置时间：2026-02-18 13:49 GMT+8*
