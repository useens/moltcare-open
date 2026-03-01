#!/usr/bin/env python3
"""
内存优化器 - 提升内存利用率至80%
"""
import json
import psutil
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"

def optimize_memory():
    """优化内存使用"""
    memory = psutil.virtual_memory()
    
    print(f"内存状态:")
    print(f"  总内存: {memory.total/1024**3:.1f}GB")
    print(f"  已使用: {memory.used/1024**3:.1f}GB ({memory.percent}%)")
    print(f"  可用: {memory.available/1024**3:.1f}GB")
    
    # 计算可以使用的额外内存 (目标80%)
    target_usage = memory.total * 0.8
    available_for_cache = target_usage - memory.used
    
    if available_for_cache > 0:
        print(f"\n可分配额外缓存: {available_for_cache/1024**3:.1f}GB")
        
        # 配置大内存缓存
        cache_config = {
            "timestamp": datetime.now().isoformat(),
            "target_memory_usage": 80,
            "allocated_cache_mb": available_for_cache / 1024**2,
            "cache_strategy": "vector_memory_preload",
            "optimizations": [
                "preload_frequent_memories",
                "increase_embedding_cache",
                "batch_processing_buffers"
            ]
        }
        
        # 保存配置
        config_file = MEMORY_DIR / "self-upgrade" / "memory-optimized.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(cache_config, indent=2))
        
        # 创建预加载脚本
        preload_script = WORKSPACE / "scripts" / "preload-memory-cache.py"
        preload_content = '''#!/usr/bin/env python3
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
'''
        preload_script.write_text(preload_content)
        preload_script.chmod(0o755)
        
        print(f"✅ 内存优化配置已保存: {config_file}")
        print(f"✅ 预加载脚本已创建: {preload_script}")
        
        return True
    else:
        print("⚠️ 内存已接近目标使用率")
        return False

if __name__ == "__main__":
    optimize_memory()
