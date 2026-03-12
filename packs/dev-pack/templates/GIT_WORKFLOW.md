# Git 工作流指南

> MoltCare dev-pack 自动生成

## 🌿 分支策略 (Git Flow 简化版)

```
main        - 生产分支，永远可部署
  ↓
develop     - 开发分支，集成测试通过
  ↓
feature/*   - 功能分支，从 develop 创建
bugfix/*    - 修复分支，从 develop 创建
hotfix/*    - 紧急修复，从 main 创建
```

## 📋 日常 workflow

### 1. 开始新功能

```bash
# 确保 develop 是最新的
git checkout develop
git pull origin develop

# 创建功能分支
git checkout -b feature/user-authentication

# 开发完成后
git add .
git commit -m "feat(auth): 实现用户登录"
git push -u origin feature/user-authentication
```

### 2. 提交 PR

```bash
# 创建 PR（使用 gh CLI）
gh pr create --title "feat(auth): 实现用户登录" \
             --body "## 变更\n- 添加登录接口\n- 添加 JWT 验证"
```

### 3. 代码审查后合并

```bash
# 使用 squash 合并，保持历史整洁
git checkout develop
git merge --squash feature/user-authentication
git commit -m "feat(auth): 实现用户登录"
git push origin develop

# 删除功能分支
git branch -d feature/user-authentication
git push origin --delete feature/user-authentication
```

## 🔄 同步上游变更

```bash
# 当 main/develop 更新后，同步到当前分支
git fetch origin
git rebase origin/develop

# 如果有冲突
git status  # 查看冲突文件
# 编辑解决冲突
git add .
git rebase --continue
```

## 🏷️ 版本发布流程

```bash
# 1. 从 main 创建发布分支
git checkout -b release/v1.2.0 main

# 2. 更新版本号，修复最后问题
# 编辑 version.py, CHANGELOG.md

git add .
git commit -m "chore(release): 准备 v1.2.0"

# 3. 合并到 main
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags

# 4. 合并回 develop
git checkout develop
git merge --no-ff release/v1.2.0
git push origin develop

# 5. 删除发布分支
git branch -d release/v1.2.0
```

## 🆘 常见场景

### 场景 1: 提交到错误分支

```bash
# 假设你在 main 上提交了不该提交的代码
git checkout main
git log  # 找到要移动的 commit hash: abc123

# 创建正确分支并移动
git checkout -b feature/correct-branch
git checkout main
git reset --hard HEAD~1  # 回退 main
git checkout feature/correct-branch
# 现在代码在正确的分支了
```

### 场景 2: 撤销已推送的提交

```bash
# 撤销最后一次提交，但保留更改
git reset --soft HEAD~1
git reset HEAD .  # 取消 add
# 现在更改在工作区，可以重新提交

# 如果已推送到远程（慎用！）
git revert abc123  # 创建反向提交
```

### 场景 3: 临时保存工作

```bash
# stash 保存
git stash push -m "WIP: 登录功能"

# 切换分支做其他事
git checkout hotfix/critical-bug

# 完成后恢复
git checkout feature/login
git stash pop
```

## 🔒 安全最佳实践

- ✅ **永远不要**提交敏感信息（密码、API key）
- ✅ 使用 `.gitignore` 忽略配置文件
- ✅ 定期审查仓库，清理敏感历史
- ✅ 启用分支保护规则

## 📊 提交统计

```bash
# 查看个人提交统计
git log --author="你的名字" --pretty=tformat: --numstat | \
  awk '{ add += $1; subs += $2; loc += $1 - $2 } END { printf "添加: %s, 删除: %s, 净增: %s\n", add, subs, loc }'

# 查看提交历史图表
git log --graph --oneline --all --decorate
```

---

*此指南由 MoltCare dev-pack 自动生成*
