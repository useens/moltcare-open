#!/usr/bin/env python3
import json
from pathlib import Path

# 预加载频繁访问的记忆到内存
cache_dir = Path("/root/.openclaw/workspace/memory/vector")
if cache_dir.exists():
    # 加载长期记忆到内存缓存
    long_term = cache_dir / "long_term_memories.json"
    if long_term.exists():
        data = json.loads(long_term.read_text())
        print(f"预加载 {len(data)} 条记忆到缓存")
