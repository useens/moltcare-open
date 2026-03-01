import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone
import numpy as np

# 会话数据 (从 sessions_list 获取)
sessions = [
    {"name": "Health Monitor", "tokens": 13393, "time": "07:55"},
    {"name": "GitHub Backup", "tokens": 13847, "time": "06:00"},
    {"name": "Monthly Archive", "tokens": 13940, "time": "04:00"},
    {"name": "Hourly Backup", "tokens": 14041, "time": "03:00"},
    {"name": "Autonomous Evolution", "tokens": 35428, "time": "02:55"},
    {"name": "AI Intel Collection", "tokens": 49304, "time": "02:20"},
    {"name": "Health Monitor", "tokens": 14269, "time": "01:55"},
    {"name": "Health Report (8AM)", "tokens": 14982, "time": "08:00"},
    {"name": "Influencer Monitoring", "tokens": 27924, "time": "08:00"},
    {"name": "Main Session", "tokens": 13997, "time": "08:04"},
]

# 反转顺序使其按时间排序
sessions = sessions[::-1]

# 创建时间序列
now = datetime.now()
times = [now.replace(hour=int(s["time"].split(":")[0]), 
                    minute=int(s["time"].split(":")[1])) for s in sessions]
tokens = [s["tokens"] for s in sessions]

# 创建图表
fig, ax = plt.subplots(figsize=(12, 6))

# 绘制折线图
ax.plot(range(len(sessions)), tokens, marker='o', linewidth=2, markersize=8, 
        color='#3B82F6', markerfacecolor='#60A5FA', markeredgecolor='#1D4ED8', markeredgewidth=2)

# 填充区域
ax.fill_between(range(len(sessions)), tokens, alpha=0.2, color='#3B82F6')

# 设置标签
ax.set_xlabel('Session', fontsize=11, fontweight='bold')
ax.set_ylabel('Total Tokens', fontsize=11, fontweight='bold')
ax.set_title('📊 Token Usage Timeline - 2026-02-09', fontsize=14, fontweight='bold', pad=20)

# 设置x轴标签
session_labels = [f"{s['name']}\n{s['time']}" for s in sessions]
ax.set_xticks(range(len(sessions)))
ax.set_xticklabels(session_labels, rotation=45, ha='right', fontsize=9)

# 添加数值标签
for i, (token, label) in enumerate(zip(tokens, session_labels)):
    ax.annotate(f'{token:,}', (i, token), textcoords="offset points", 
                xytext=(0, 10), ha='center', fontsize=9, fontweight='bold', color='#1D4ED8')

# 添加平均线
avg_tokens = np.mean(tokens)
ax.axhline(y=avg_tokens, color='#EF4444', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Average: {avg_tokens:,.0f}')

# 样式优化
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(loc='upper left')

# 格式化y轴
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

# 紧凑布局
plt.tight_layout()

# 保存图表
plt.savefig('/root/.openclaw/workspace/token_usage_chart.png', dpi=150, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
plt.close()

print("Chart saved to token_usage_chart.png")
print(f"Total tokens used today: {sum(tokens):,}")
print(f"Average per session: {avg_tokens:,.0f}")
print(f"Peak session: AI Intel Collection ({max(tokens):,} tokens)")
