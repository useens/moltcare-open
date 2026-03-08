#!/usr/bin/env python3
"""
决策引擎缓存增强补丁
添加任务处理历史缓存，避免重复处理相同内容

使用方法:
    python3 autonomous-decision-engine-with-cache.py --cycle

本脚本会自动加载原始的autonomous-decision-engine.py并注入缓存逻辑
"""

import sys
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
PROCESSED_CACHE_FILE = DATA_DIR / "processed-tasks-cache.json"


class TaskCache:
    """任务内容缓存"""

    def __init__(self, max_age_hours=24, max_entries=200):
        self.cache_file = PROCESSED_CACHE_FILE
        self.max_age_hours = max_age_hours
        self.max_entries = max_entries
        self.cache = self._load_cache()

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {"entries": {}}
        return {"entries": {}}

    def _save_cache(self):
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存缓存失败: {e}")

    def _cleanup(self):
        now = datetime.now()
        cutoff = now - timedelta(hours=self.max_age_hours)

        # 清理过期条目
        expired = [k for k, v in self.cache["entries"].items()
                   if datetime.fromisoformat(v.get('processed_at', '')) < cutoff]
        for k in expired:
            del self.cache["entries"][k]

        # 清理过量条目
        if len(self.cache["entries"]) > self.max_entries:
            sorted_items = sorted(
                self.cache["entries"].items(),
                key=lambda x: datetime.fromisoformat(x[1].get('processed_at', ''))
            )
            for k, _ in sorted_items[:len(self.cache["entries"]) - self.max_entries]:
                del self.cache["entries"][k]

    def _key(self, topic, source):
        content = f"{topic}|{source}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def is_processed(self, topic, source):
        return self._key(topic, source) in self.cache["entries"]

    def mark_processed(self, topic, source, task_id, risk_level, outcome="completed"):
        k = self._key(topic, source)
        self.cache["entries"][k] = {
            "topic": topic[:100],
            "source": source,
            "task_id": task_id,
            "risk_level": risk_level,
            "outcome": outcome,
            "processed_at": datetime.now().isoformat()
        }
        self._cleanup()
        self._save_cache()

    def get_info(self, topic, source):
        k = self._key(topic, source)
        return self.cache["entries"].get(k)

    def get_stats(self):
        now = datetime.now()
        cutoff = now - timedelta(hours=self.max_age_hours)
        active = sum(1 for v in self.cache["entries"].values()
                     if datetime.fromisoformat(v.get('processed_at', '')) >= cutoff)
        return {
            "total": len(self.cache["entries"]),
            "active": active,
            "expired": len(self.cache["entries"]) - active
        }


if __name__ == "__main__":
    import argparse
    import subprocess

    parser = argparse.ArgumentParser()
    parser.add_argument("--test-cache", action="store_true", help="测试缓存功能")
    parser.add_argument("--stats", action="store_true", help="显示缓存统计")
    parser.add_argument("--clear", action="store_true", help="清空缓存")
    args, unknown = parser.parse_known_args()

    # 处理缓存命令
    if args.test_cache:
        cache = TaskCache()
        topic = "测试任务"
        print(f"测试: {topic}")
        print(f"  缓存前: {cache.is_processed(topic, 'test')}")
        cache.mark_processed(topic, 'test', 'test-001', 'L3')
        print(f"  缓存后: {cache.is_processed(topic, 'test')}")
        sys.exit(0)

    if args.stats:
        cache = TaskCache()
        stats = cache.get_stats()
        print(f"缓存统计: {json.dumps(stats, indent=2)}")
        sys.exit(0)

    if args.clear:
        cache = TaskCache()
        cache.cache = {"entries": {}}
        cache._save_cache()
        print("✅ 缓存已清空")
        sys.exit(0)

    # 修改原始脚本，注入缓存逻辑
    original_script = Path(__file__).parent / "autonomous-decision-engine.py"

    if not original_script.exists():
        print(f"❌ 找不到原始脚本: {original_script}")
        sys.exit(1)

    # 读取原始脚本
    original_code = original_script.read_text(encoding='utf-8')

    # 注入缓存初始化代码（在DecisionEngine类初始化之前）
    cache_init_code = '''
# 注入: 任务内容缓存
PROCESSED_CACHE_FILE = WORKSPACE / "data" / "processed-tasks-cache.json"
'''

    # 找到合适的位置注入
    inject_pos = original_code.find("REPORTS_DIR = WORKSPACE / \"reports\"")
    if inject_pos > 0:
        inject_end = original_code.find("\\n", inject_pos)
        original_code = original_code[:inject_end] + "\\n" + cache_init_code + original_code[inject_end:]

    # 注入检查方法到DecisionEngine类（在scan_learning_debts方法前）
    cache_check_method = '''
    def _check_task_cache(self, topic: str, source: str) -> Optional[Dict]:
        """检查任务是否已处理过"""
        import json
        import hashlib
        from datetime import datetime, timedelta

        if not PROCESSED_CACHE_FILE.exists():
            return None

        try:
            with open(PROCESSED_CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except Exception:
            return None

        content_key = hashlib.md5(f"{topic}|{source}".encode()).hexdigest()[:16]

        if content_key in cache.get("entries", {}):
            entry = cache["entries"][content_key]
            # 检查是否过期（24小时内）
            entry_time = datetime.fromisoformat(entry.get("processed_at", ""))
            if (datetime.now() - entry_time) < timedelta(hours=24):
                return entry
        return None

    def _add_to_cache(self, topic: str, source: str, task_id: str,
                      risk_level: str, outcome: str = "completed"):
        """将任务添加到缓存"""
        import json
        import hashlib

        cache = {"entries": {}}
        if PROCESSED_CACHE_FILE.exists():
            try:
                with open(PROCESSED_CACHE_FILE, 'r') as f:
                    cache = json.load(f)
            except Exception:
                pass

        # 清理过期条目
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(hours=24)
        cache["entries"] = {
            k: v for k, v in cache["entries"].items()
            if datetime.fromisoformat(v.get("processed_at", "")) >= cutoff
        }

        # 添加新条目
        content_key = hashlib.md5(f"{topic}|{source}".encode()).hexdigest()[:16]
        cache["entries"][content_key] = {
            "topic": topic[:100],
            "source": source,
            "task_id": task_id,
            "risk_level": risk_level,
            "outcome": outcome,
            "processed_at": datetime.now().isoformat()
        }

        # 保存
        try:
            PROCESSED_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PROCESSED_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass  # 静默失败

'''

    # 注入方法（在scan_learning_debts方法前）
    scan_pos = original_code.find("def scan_learning_debts(self)")
    if scan_pos > 0:
        original_code = original_code[:scan_pos] + cache_check_method + original_code[scan_pos:]

    # 修改scan_learning_debts方法，添加缓存检查逻辑
    # 在"contexts.append(context)"之前添加缓存检查
    cache_check_inject = '''
                    # 检查缓存
                    cache_entry = self._check_task_cache(topic)
                    if cache_entry:
                        logger.info(f"  ⏭️  已跳过: {topic[:40]}... (上次处理: {cache_entry['task_id']})")
                        continue

'''

    # 在两个append位置注入
    original_code = original_code.replace(
        "contexts.append(context)\\n\\n        logger.info(f\"扫描到 {len(contexts)} 个高Signal学习债务\")",
        cache_check_inject + "contexts.append(context)\\n                            # 标记为已处理\\n                            self._add_to_cache(topic, 'learning-debt-scan', context.task_id, str(risk_level))\\n\\n        logger.info(f\"扫描到 {len(contexts)} 个高Signal学习债务\")"
    )

    # 创建临时修改后的脚本
    temp_script = Path(__file__).parent / f".autonomous-decision-engine-injected-{sys.argv[0]}.py"
    temp_script.write_text(original_code, encoding='utf-8')

    # 执行原始命令
    cmd = ["python3", str(temp_script)] + unknown
    print(f"🚀 执行决策引擎（带缓存增强）...")
    result = subprocess.run(cmd, cwd=WORKSPACE)

    # 清理临时文件
    try:
        temp_script.unlink()
    except Exception:
        pass

    sys.exit(result.returncode)
