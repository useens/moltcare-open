# 分支策略变更记录

## 2026-02-12 分支策略变更

### 变更内容

**废弃 master 分支，只保留 main 分支**

### 变更原因

1. **冗余**: main 和 master 内容相同，但 main 更活跃（领先 38 个提交）
2. **一致性**: GitHub 默认分支为 main，符合现代 Git 实践
3. **简化**: 避免双分支维护的复杂性
4. **关键内容丢失**: master 缺少超进化模式所有代码 (7小时差距)

### 执行操作

**本地变更** (已完成):
- ✅ 删除本地 master 分支
- ✅ 当前只保留 main 分支
- ✅ 所有开发工作都在 main 进行

**远程变更** (需要手动):
- ⏳ 需要在 GitHub 设置中更改默认分支为 main
- ⏳ 然后才能删除远程 master 分支

### GitHub 设置步骤

1. 访问 https://github.com/useens/linlin-backup/settings
2. 找到 "Default branch" 设置
3. 点击切换图标，选择 "main"
4. 确认更改
5. 然后可以删除 master 分支

### 当前状态

```
本地分支:
  * main

远程分支:
    remotes/origin/main
    remotes/origin/master  (等待删除)

HEAD branch: master  (需要改为 main)
```

### 影响

- 所有新克隆默认会获取 main 分支
- 旧克隆可能需要手动切换: `git checkout main`
- 超进化模式只在 main 分支可用

### 备份信息

- 变更时间: 2026-02-12 16:42
- 执行者: 森森 (完全自主模式)
- 授权: 用户明确指令 "废弃 master，只用 main"
