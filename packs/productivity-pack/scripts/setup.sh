#!/bin/bash
# productivity-pack 安装脚本

echo "🚀 配置生产力工具环境..."

# 创建任务目录
mkdir -p tasks
echo "✓ 创建 tasks/ 目录"

# 创建今日任务模板
cat > tasks/template.md << 'EOF'
# {{date}} 任务清单

## 🎯 今日三大目标
1. [ ]
2. [ ]
3. [ ]

## 📋 任务列表

### 紧急且重要
- [ ]

### 重要不紧急
- [ ]

### 紧急不重要
- [ ]

### 不紧急不重要
- [ ]

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
EOF
echo "✓ 创建任务模板"

# 创建快捷命令脚本
cat > scripts/productivity.sh << 'EOF'
#!/bin/bash
# 生产力工具脚本

TASKS_DIR="${HOME}/tasks"
mkdir -p "$TASKS_DIR"

today_file() {
    echo "${TASKS_DIR}/$(date +%Y-%m-%d).md"
}

case "$1" in
    today|t)
        file=$(today_file)
        if [ ! -f "$file" ]; then
            sed "s/{{date}}/$(date +%Y-%m-%d)/g" tasks/template.md > "$file"
        fi
        ${EDITOR:-vim} "$file"
        ;;
    
    timer|tm)
        minutes=${2:-25}
        echo "开始计时 $minutes 分钟..."
        sleep "${minutes}m" && echo "⏰ 时间到！"
        ;;
    
    track|tr)
        if [ -z "$2" ]; then
            echo "用法: track '<activity>'"
            exit 1
        fi
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "$timestamp,$2" >> "$TASKS_DIR/timetracking.csv"
        echo "✓ 已记录: $2"
        ;;
    
    analyze|a)
        if [ -f "$TASKS_DIR/timetracking.csv" ]; then
            echo "时间分布:"
            cut -d',' -f2 "$TASKS_DIR/timetracking.csv" | sort | uniq -c | sort -rn
        else
            echo "暂无记录"
        fi
        ;;
    
    focus|f)
        echo "🎯 启用专注模式 (25分钟)..."
        echo "提示: 关闭通知，开始深度工作"
        sleep 25m
        echo "⏰ 时间到！休息 5 分钟"
        ;;
    
    list|ls)
        echo "最近任务文件:"
        ls -t "$TASKS_DIR"/*.md 2>/dev/null | head -5
        ;;
    
    *)
        echo "生产力工具"
        echo ""
        echo "用法: ./scripts/productivity.sh [命令]"
        echo ""
        echo "命令:"
        echo "  today, t          打开今日任务清单"
        echo "  timer, tm [分钟]  启动番茄钟计时"
        echo "  track, tr <活动>  记录活动"
        echo "  analyze, a        分析时间分布"
        echo "  focus, f          专注模式 (25分钟)"
        echo "  list, ls          列出最近任务"
        echo ""
        echo "示例:"
        echo "  ./scripts/productivity.sh today"
        echo "  ./scripts/productivity.sh timer 30"
        echo "  ./scripts/productivity.sh track '开始编码'"
        ;;
esac
EOF
chmod +x scripts/productivity.sh
echo "✓ 创建 scripts/productivity.sh"

# 创建 shell 别名配置
cat > .productivity-aliases << 'EOF'
# 生产力工具别名 (添加到 .bashrc 或 .zshrc)
# source .productivity-aliases

# 导航
alias ..='cd ..'
alias ...='cd ../..'
alias ~='cd ~'

# 列表
alias ll='ls -alF'
alias la='ls -A'

# Git
alias g='git'
alias gs='git status'
alias ga='git add'
alias gc='git commit -m'
alias gp='git push'
alias gl='git log --oneline'

# Python
alias py='python3'
alias venv='python3 -m venv venv'
alias activate='source venv/bin/activate'

# 效率
alias c='clear'
alias h='history'
alias today='date +"%Y-%m-%d"'
alias now='date +"%H:%M:%S"'

# 函数
mkcd() { mkdir -p "$1" && cd "$1"; }
backup() { cp "$1" "${1}.backup.$(date +%Y%m%d_%H%M%S)"; }
EOF
echo "✓ 创建 .productivity-aliases"

# 创建 tmux 配置
cat > .tmux.conf.local << 'EOF'
# 本地 tmux 配置 (合并到 ~/.tmux.conf)

# 鼠标支持
set -g mouse on

# 快捷键前缀 (如果 C-b 不习惯)
# set -g prefix C-a
# bind C-a send-prefix

# 窗口索引从 1 开始
set -g base-index 1
setw -g pane-base-index 1

# 快速切换窗口
bind -n M-1 select-window -t 1
bind -n M-2 select-window -t 2
bind -n M-3 select-window -t 3
bind -n M-4 select-window -t 4

# 状态栏
set -g status-right '#(date +"%H:%M") %d-%b'
set -g status-interval 5

# 历史记录
set -g history-limit 10000
EOF
echo "✓ 创建 .tmux.conf.local"

# 创建启动脚本
cat > scripts/start-dev.sh << 'EOF'
#!/bin/bash
# 启动开发环境

echo "🚀 启动开发环境..."

# 检查 tmux
if ! command -v tmux &> /dev/null; then
    echo "⚠️  tmux 未安装"
    exit 1
fi

# 创建或连接 tmux 会话
SESSION="dev"

tmux has-session -t $SESSION 2>/dev/null
if [ $? != 0 ]; then
    tmux new-session -d -s $SESSION
    tmux rename-window -t $SESSION:1 'code'
    tmux send-keys -t $SESSION:1 '${EDITOR:-vim}' C-m
    
    tmux new-window -t $SESSION:2 -n 'server'
    tmux new-window -t $SESSION:3 -n 'shell'
    
    echo "✓ 创建新的 tmux 会话: $SESSION"
else
    echo "✓ 连接到现有会话: $SESSION"
fi

# 打开今日任务
echo "📋 打开今日任务..."
./scripts/productivity.sh today &

echo ""
echo "✅ 开发环境已启动"
echo ""
echo "连接到: tmux attach -t $SESSION"
echo "快捷操作:"
echo "  Ctrl+b 1/2/3  - 切换窗口"
echo "  Ctrl+b d      - 分离会话"
echo "  ./scripts/productivity.sh timer 25  - 启动番茄钟"
EOF
chmod +x scripts/start-dev.sh
echo "✓ 创建 scripts/start-dev.sh"

echo ""
echo "🎉 productivity-pack 配置完成!"
echo ""
echo "已创建:"
echo "  📁 tasks/              - 任务目录"
echo "  📄 tasks/template.md   - 任务模板"
echo "  📄 .productivity-aliases - Shell 别名"
echo "  📄 .tmux.conf.local    - Tmux 配置"
echo ""
echo "快捷命令:"
echo "  ./scripts/productivity.sh today     # 今日任务"
echo "  ./scripts/productivity.sh timer 25  # 番茄钟"
echo "  ./scripts/productivity.sh track     # 记录活动"
echo "  ./scripts/start-dev.sh              # 启动开发环境"
echo ""
echo "添加到 shell 配置:"
echo "  echo 'source $(pwd)/.productivity-aliases' >> ~/.bashrc"
echo ""
echo "查看指南:"
echo "  cat PRODUCTIVITY_GUIDE.md"
