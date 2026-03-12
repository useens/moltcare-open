# MoltCare v2.0 集成说明

## 集成状态

### ✅ 文件层面集成（已实现）
- 配置同步到 OpenClaw workspace
- 智能合并 SOUL.md 等文件
- 生成 Hooks 文件
- 生成运行时配置

### ⚠️ 运行时集成（需 OpenClaw 支持）
- Hooks 自动调用
- 触发词实时检测
- 自动记忆捕获
- 心跳任务执行

## 使用方式

### 手动测试触发词
```bash
echo "多专家讨论: 测试" | ~/.moltcare/hooks/pre_message.py
```

### 手动触发多专家模式
在消息前添加：
```
多专家讨论: 你的问题
```

## 推荐搭配技能
- **vestige** - 记忆系统
- **clawdo** - 任务队列
- **healthcheck** - 健康检查
