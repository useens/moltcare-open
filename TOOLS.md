# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

---

## ⭐ Output Verification Checklist (第7.1项)

**Before sending ANY response:**

| Check | Question | Fix If Failed |
|-------|----------|---------------|
| 数据真实性 | 基于真实数据还是估算？ | 用exec/read获取实际数据 |
| 信息时效性 | 是最新数据还是缓存？ | 重新读取文件/执行命令 |
| 逻辑合理性 | 推理自洽无矛盾？ | 重新推理，找矛盾点 |
| 来源可追溯 | 关键结论有来源？ | 添加数据来源引用 |
| 安全合规性 | 无敏感信息泄露？ | 删除/脱敏敏感内容 |

**流程**: 生成 → 自检 → 发现问题 → 十大原则修复 → 再验证 → ✅输出
