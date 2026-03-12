# MoltCare v2.0 集成说明

## 当前集成状态

### ✅ 已实现：文件层面集成

MoltCare v2.0 已成功实现与 OpenClaw 的**文件层面集成**：

1. **配置同步** - 自动将配置写入 `~/.openclaw/workspace/`
2. **模板应用** - 智能合并 SOUL.md、AGENTS.md 等文件
3. **Hooks 安装** - 生成 pre_message.py、heartbeat.py 等钩子文件
4. **运行时配置** - 生成 `.moltcare-runtime.yaml` 配置文件

### ⚠️ 待实现：运行时集成

以下功能**需要 OpenClaw 本体支持**才能完全生效：

1. **Hooks 调用** - OpenClaw 需要在消息处理前后调用 hook 脚本
2. **自动触发** - 触发词检测需要 OpenClaw 在运行时执行
3. **记忆捕获** - 需要 OpenClaw 在回复后调用 post_message hook
4. **心跳任务** - 需要 OpenClaw 定时执行 heartbeat hook

## 如何使用当前功能

### 1. 查看运行时配置

```bash
cat ~/.openclaw/workspace/.moltcare-runtime.yaml
```

### 2. 测试触发词（手动）

```bash
echo "多专家讨论: 如何设计这个系统？" | ~/.moltcare/hooks/pre_message.py
```

### 3. 手动触发多专家模式

在消息前添加触发词：
```
多专家讨论: 如何评估这个方案？
```

## 推荐搭配使用的 OpenClaw 技能

| 技能 | 用途 | 安装命令 |
|------|------|----------|
| **vestige** | FSRS-6 记忆系统 | `openclaw skills install vestige` |
| **clawdo** | 任务队列管理 | `openclaw skills install clawdo` |
| **healthcheck** | 系统健康检查 | `openclaw skills install healthcheck` |

## 故障排除

### Hooks 未生效

**原因**：OpenClaw 本体尚未调用 hooks
**解决**：手动在消息前添加 "多专家讨论:"

### 版本不匹配

```bash
rm -rf ~/.moltcare ~/.local/bin/moltcare
git clone https://github.com/useens/moltcare-open.git ~/.moltcare
cp ~/.moltcare/moltcare ~/.local/bin/moltcare
chmod +x ~/.local/bin/moltcare
moltcare init --force
```
