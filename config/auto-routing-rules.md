# 自动路由配置
# 基于用户配置：默认 step，复杂任务用 k2p5

## 路由规则

### 1. 代码任务 → k2p5 (Kimi K2.5)
触发关键词：
- 代码、编程、函数、类、模块、开发
- bug、调试、报错、修复、exception
- 算法、架构、设计、重构、优化
- Python、JavaScript、Java、Go、Rust、C++
- API、接口、数据库、SQL、Redis
- 前端、后端、全栈、devops

自动执行：
1. 切换到 `k2p5` (kimi-coding/k2p5)
2. 运行智能分级脚本（L1-L5）
3. 设置对应 thinking 模式

### 2. 图片/图像任务 → kimi (Kimi K2.5)
触发关键词：
- 图片、截图、照片、图像、图片分析
- 视觉、识别、OCR、图表、流程图
- 长文档、pdf、文档分析

自动执行：
1. 切换到 `nvidia-kimi` (nvidia-build/moonshotai/kimi-k2.5)
2. 自动开启多模态支持
3. reasoning on

### 3. 中文优化 → step (Step 3.5 Flash)
触发关键词：
- 中文、翻译、文案、本地化
- 快速响应、轻量级、简单任务

自动执行：
1. 切换到 `step` (nvidia-build/stepfun-ai/step-3.5-flash)
2. reasoning on

### 4. 默认 → step
其他所有任务：
1. 切换到 `step` (nvidia-build/stepfun-ai/step-3.5-flash)
2. reasoning on

## 子代理难度判断

子代理启动前自动评估任务难度：
- **L1-L2（简单）** → step
- **L3-L4（中等/困难）** → k2p5
- **L5（极难）** → 强制 k2p5 + stream thinking

⚠️ **危险操作强制L5**：
包含以下关键词的任务 **必须** 视为 L5 并强制使用 **k2p5**（最高安全级别）：
- 系统修复、紧急修复、故障排除、生产环境变更
- 配置更改、修改配置、配置文件调整
- 网关重启、cron 修改、系统ctl命令
- 备份回滚、沙箱测试、验证执行
- self-upgrade、hyper-evolution、evolution 相关
- 涉及 root/管理员权限的操作

这是为了确保系统级操作的精确性和安全性。

## 路由优先级

1. 最高：用户明确指定模型（`/status model=xxx`）
2. 🔥 超高：危险/系统操作 → **强制 k2p5 + stream** (L5)
3. 高：图片/文档 → nvidia-kimi
4. 中：代码 → k2p5
5. 低：中文 → step
6. 默认：step

**危险操作定义**（任何一项即触发 L5 强制 k2p5）：
- 系统维护：修复、故障排除、紧急处理、生产环境变更
- 配置管理：修改配置、调整参数、文件编辑
- 服务控制：重启、重装、reload、systemctl/cron
- 进化引擎：hyper-evolution、self-upgrade、evolution 相关
- 权限操作：root、sudo、管理员、backup/rollback

## 用户确认机制

自动路由建议后，等待用户确认：
- 用户说 "y/是/确认/ok" → 执行切换
- 用户说 "n/否/不用/no" → 保持当前模型
- 用户沉默 5 秒 → 默认执行建议

## 与智能分级系统集成

代码任务触发 k2p5 后，自动运行 `config/k2p5-difficulty-rules.md` 中的分级规则，动态调整 thinking 模式。

## 模型别名清单

| 别名 | 模型 | 用途 |
|------|------|------|
| `step` | stepfun-ai/step-3.5-flash | 默认、中文、常规 |
| `k2p5` | kimi-coding/k2p5 | 代码、复杂任务 |
| `nvidia-kimi` | moonshotai/kimi-k2.5 | 图像、长文档 |
| `nvidia-glm` | glm4.7 | 备用 |
| `nvidia-ds` | deepseek-v3.2 | 备用 |
| `nvidia-qwen` | qwen3.5 | 备用 |

---

*配置版本：v2.0 | 2026-02-18 | 基于 nvidia-build 模型集*
