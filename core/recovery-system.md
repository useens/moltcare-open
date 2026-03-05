# 恢复机制设计 (Recovery System Design)
# 从 Moltbook @Kapso 学习
# "Autonomy doesn't fail because agents can't act. It fails because they can't recover."

## 三大恢复原语

### 1️⃣ 可撤销操作 (Undoable Actions)
**原则**: 优先执行有逆向操作的动作

| 操作 | 逆向操作 | 我的实现 |
|------|----------|----------|
| 创建文件 | 删除文件 | ✅ 自动备份到 .trash/ |
| 修改文件 | 恢复原版本 | ✅ Git 版本控制 |
| 发送消息 | 撤回/更正 | ⚠️ 部分平台支持 |
| 写入数据库 | 回滚事务 | ⚠️ 需要设计 |
| 执行命令 | 反向命令 | ⚠️ 需要评估风险 |

### 2️⃣ 检查点+重放 (Checkpoint-and-Replay)
**触发条件**:
- 每完成一个重要子任务
- 用户明确说"保存进度"
- 进入高风险操作前

**检查点内容**:
```json
{
  "timestamp": "2026-03-05T09:45:00Z",
  "task_id": "task_001",
  "completed_steps": ["step1", "step2"],
  "current_state": "准备执行 step3",
  "files_modified": ["/path/to/file1"],
  "can_rollback_to": "checkpoint_002"
}
```

### 3️⃣ 幂等设计 (Idempotent Design)
**原则**: 同一操作执行多次，结果相同

**实践**:
- 文件写入：先写临时文件，再原子替换
- 数据库更新：使用 UPSERT 而非 INSERT
- API 调用：添加幂等键 (idempotency key)
- 消息发送：去重检查

## 恢复策略矩阵

| 失败场景 | 恢复策略 | 自动化程度 |
|----------|----------|------------|
| 文件写入失败 | 回滚到上一个 Git commit | 全自动 |
| API 调用超时 | 指数退避重试 3 次 | 全自动 |
| 用户纠正错误 | 记录到 correction-log.md | 半自动 |
| 任务中断 | 从检查点重放 | 手动确认 |
| 严重错误 | 暂停并通知用户 | 手动处理 |

## 实施计划

### 阶段 1 (今天)
- [x] Git 自动提交（已实现）
- [x] 文件修改备份（已实现）
- [ ] 检查点记录系统

### 阶段 2 (本周)
- [ ] 任务状态持久化
- [ ] 自动重试机制
- [ ] 恢复 UI/通知

### 阶段 3 (本月)
- [ ] 预测性故障检测
- [ ] 自动恢复决策
- [ ] 跨会话恢复能力

---

*创建时间: 2026-03-05*
*来源: Moltbook @Kapso "The real bottleneck in agent autonomy is recovery (undo, replay, rollback)"*
