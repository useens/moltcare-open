#!/bin/bash
# 自动密码保护脚本 - 防止日志泄露
# 触发条件: 检测到密码模式时自动执行

SENSITIVE_PATTERNS=(
    "password[:=]?\s*[a-zA-Z0-9]{8,}"
    "passwd[:=]?\s*[a-zA-Z0-9]{8,}"
    "pwd[:=]?\s*[a-zA-Z0-9]{8,}"
    "secret[:=]?\s*[a-zA-Z0-9]{8,}"
    "token[:=]?\s*[a-zA-Z0-9]{20,}"
    "key[:=]?\s*[a-zA-Z0-9]{20,}"
)

LOG_DIRS=(
    "$HOME/.openclaw/agents/main/sessions/"
    "/tmp/openclaw/"
)

auto_redact() {
    for dir in "${LOG_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            for pattern in "${SENSITIVE_PATTERNS[@]}"; do
                find "$dir" -type f -name "*.jsonl" -o -name "*.log" 2>/dev/null | \
                xargs grep -l -E "$pattern" 2>/dev/null | \
                while read file; do
                    # 替换敏感信息
                    sed -i -E "s/($pattern)/[REDACTED-SENSITIVE]/gi" "$file"
                    echo "$(date '+%Y-%m-%d %H:%M:%S') - 自动脱敏: $file" >> ~/.openclaw/workspace/logs/auto-redact.log
                done
            done
        fi
    done
}

# 每小时执行一次
auto_redact
