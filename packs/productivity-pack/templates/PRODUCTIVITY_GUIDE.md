# 生产力提升指南

> MoltCare productivity-pack 自动生成

## 🎯 任务管理

### 1. 任务分类法（Eisenhower Matrix）

```
          紧急              不紧急
     ┌──────────────┬──────────────┐
重要 │   立即做      │   计划做      │
     │  (Do First)  │  (Schedule)  │
     ├──────────────┼──────────────┤
不重要│   委托做      │   不做/少做   │
     │  (Delegate)  │  (Eliminate) │
     └──────────────┴──────────────┘
```

### 2. 每日任务模板

```markdown
# {{date}} 任务清单

## 🎯 今日三大目标
1. [ ] 目标 1（最重要的任务）
2. [ ] 目标 2
3. [ ] 目标 3

## 📋 任务列表

### 紧急且重要
- [ ] 任务 A - 截止 {{time}}
- [ ] 任务 B

### 重要不紧急
- [ ] 任务 C
- [ ] 任务 D

### 紧急不重要
- [ ] 任务 E（考虑委托）

### 不紧急不重要
- [ ] 任务 F（考虑删除）

## 📊 时间块

| 时间 | 活动 | 状态 |
|------|------|------|
| 09:00-11:00 | 深度工作 | ⬜ |
| 11:00-12:00 | 会议/沟通 | ⬜ |
| 14:00-16:00 | 深度工作 | ⬜ |
| 16:00-17:00 | 复盘/计划 | ⬜ |

## 📝 今日复盘

完成：
未完成：
原因：
改进：
```

## ⏰ 时间管理技巧

### Pomodoro 番茄工作法

```
工作 25 分钟 → 休息 5 分钟
×4 次 → 长休息 15-30 分钟
```

### 深度工作时间

```
🌅 早晨 (9:00-11:00)
  - 大脑最清醒
  - 处理复杂任务
  - 避免会议

🌞 下午 (14:00-16:00)  
  - 第二黄金时段
  - 专注编程/写作
  - 关闭通知

🌙 晚上 (可选)
  - 轻度工作
  - 学习/阅读
  - 计划明天
```

### 两分钟规则

```
如果任务能在 2 分钟内完成，立即做！

示例：
✓ 回复简单邮件
✓ 添加待办事项
✓ 更新状态
✓ 简单修复

不要：添加到待办清单
```

## 🛠️ 效率工具配置

### 命令行效率工具

#### 快捷别名（.bashrc/.zshrc）

```bash
# 导航
alias ..='cd ..'
alias ...='cd ../..'
alias ~='cd ~'
alias pr='cd ~/projects'

# 列表
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Git
alias g='git'
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline'

# Python
alias py='python3'
alias venv='python3 -m venv'
alias activate='source venv/bin/activate'

# 效率
alias c='clear'
alias h='history'
alias today='date +"%Y-%m-%d"'
alias now='date +"%H:%M:%S"'
```

#### 函数工具

```bash
# 创建项目目录并进入
mkcd() {
    mkdir -p "$1" && cd "$1"
}

# 备份文件
backup() {
    cp "$1" "${1}.backup.$(date +%Y%m%d_%H%M%S)"
}

# 快速任务计时
timer() {
    local minutes=${1:-25}
    echo "开始计时 $minutes 分钟..."
    sleep "${minutes}m" && echo "⏰ 时间到！" && notify-send "时间到！"
}

# 今日任务
today() {
    local task_file="~/tasks/$(date +%Y-%m-%d).md"
    if [ ! -f "$task_file" ]; then
        mkdir -p ~/tasks
        cat > "$task_file" << EOF
# $(date +%Y-%m-%d) 任务清单

## 🎯 今日三大目标
1. [ ]
2. [ ]
3. [ ]

## 📋 任务列表
- [ ]

## 📝 复盘
EOF
    fi
    ${EDITOR:-vim} "$task_file"
}
```

### Tmux 工作流

```bash
# 开发会话
tmux new-session -d -s dev
tmux rename-window -t dev:1 'editor'
tmux new-window -t dev:2 -n 'server'
tmux new-window -t dev:3 -n 'terminal'
tmux attach-session -t dev
```

```conf
# .tmux.conf
# 鼠标支持
set -g mouse on

# 快捷键前缀
unbind C-b
set -g prefix C-a
bind C-a send-prefix

# 快速切换窗口
bind -n M-1 select-window -t 1
bind -n M-2 select-window -t 2
bind -n M-3 select-window -t 3

# 状态栏
set -g status-right '#(date +"%H:%M")'
```

## 📊 工作流自动化

### 开发启动脚本

```bash
#!/bin/bash
# start-dev.sh - 启动开发环境

echo "🚀 启动开发环境..."

# 启动 Tmux 会话
tmux has-session -t dev 2>/dev/null
if [ $? != 0 ]; then
    tmux new-session -d -s dev
    tmux rename-window -t dev:1 'code'
    tmux send-keys -t dev:1 'vim' C-m
    
    tmux new-window -t dev:2 -n 'server'
    tmux send-keys -t dev:2 'make dev' C-m
    
    tmux new-window -t dev:3 -n 'shell'
fi

# 启动浏览器
google-chrome http://localhost:3000 &

# 打开任务清单
today

echo "✅ 开发环境已启动"
echo "连接到: tmux attach -t dev"
```

### Git Hook 自动化

```bash
#!/bin/bash
# .git/hooks/pre-commit
# 提交前自动检查

echo "🔍 运行提交前检查..."

# 格式化
make format

# 检查
make lint
if [ $? -ne 0 ]; then
    echo "❌ 代码检查失败"
    exit 1
fi

# 测试
make test
if [ $? -ne 0 ]; then
    echo "❌ 测试失败"
    exit 1
fi

echo "✅ 检查通过"
```

## 🎯 专注模式

### 深度工作协议

1. **准备阶段 (5分钟)**
   - 关闭通知
   - 准备茶水
   - 清理桌面

2. **深度工作 (50分钟)**
   - 单一任务
   - 不切换上下文
   - 记录中断次数

3. **休息阶段 (10分钟)**
   - 离开座位
   - 眺望远方
   - 轻微活动

### 干扰管理

```bash
# 启用专注模式
focus-mode() {
    # 关闭通知
    gsettings set org.gnome.desktop.notifications show-banners false
    
    # 静音
    amixer -D pulse set Master mute
    
    # 启动番茄钟
    timer 25
    
    # 恢复
    gsettings set org.gnome.desktop.notifications show-banners true
    amixer -D pulse set Master unmute
}
```

## 📈 数据分析

### 时间追踪

```bash
# 记录活动
track() {
    local activity="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp,$activity" >> ~/.time-tracking.csv
}

# 示例
track "开始编码功能 A"
# ... 工作 ...
track "完成编码功能 A"

# 生成报告
analyze-time() {
    cat ~/.time-tracking.csv | cut -d',' -f2 | sort | uniq -c | sort -rn
}
```

## 🎖️ 习惯养成

### 每日习惯清单

```markdown
# 晨间习惯 (6:00-9:00)
- [ ] 起床整理
- [ ] 运动/冥想 15分钟
- [ ] 阅读 30分钟
- [ ] 规划今日任务

# 工作习惯 (9:00-18:00)
- [ ] 深度工作 4小时
- [ ] 每 50 分钟休息
- [ ] 下午 3 点站立办公
- [ ] 17:30 复盘

# 晚间习惯 (18:00-22:00)
- [ ] 运动
- [ ] 学习/阅读
- [ ] 准备明天
- [ ] 22:30 前睡觉
```

---

*此指南由 MoltCare productivity-pack 自动生成*
*效率不是做更多，而是做对的事*
