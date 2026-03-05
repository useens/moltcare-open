#!/usr/bin/env python3
"""
重新生成10个AI nanobot的nanobot.py文件
"""

from pathlib import Path
import re

SOURCE_FILE = Path("/root/.openclaw/workspace/nanobot/nanobot.py")
CONFIGS = {}

# 读取原始文件
if not SOURCE_FILE.exists():
    print(f"源文件不存在: {SOURCE_FILE}")
    exit(1)

source_content = SOURCE_FILE.read_text()

for i in range(1, 11):
    nb_id = f"nanobot-{i}"
    target_dir = Path(f"/root/.openclaw/workspace/ai-nanobots/{nb_id}")
    target_file = target_dir / "nanobot.py"

    # 读取身份配置
    identity_file = target_dir / "identity.json"
    if identity_file.exists():
        import json
        identity = json.loads(identity_file.read_text())
        name = identity.get('name', nb_id)
    else:
        name = nb_id

    # 创建新内容
    new_content = source_content

    # 替换NANOBOT_DIR
    new_content = new_content.replace(
        'Path("/root/.openclaw/workspace/nanobot")',
        f'Path("/root/.openclaw/workspace/ai-nanobots/{nb_id}")'
    )

    # 替换LOG_FILE
    new_content = new_content.replace(
        'LOG_FILE = NANOBOT_DIR / "nanobot.log"',
        f'LOG_FILE = NANOBOT_DIR / "{nb_id}.log"'
    )

    # 替换SESSION_FILE
    new_content = new_content.replace(
        'SESSION_FILE = NANOBOT_DIR / "session.json"',
        f'SESSION_FILE = NANOBOT_DIR / "session.json"'
    )

    # 替换名称
    new_content = new_content.replace(
        'self.name = "虾米派派 (Nanobot)"',
        f'self.name = "{name}"'
    )

    # 替换版本
    new_content = new_content.replace(
        'self.version = "2.3"',
        f'self.version = "3.0"'
    )

    # 替换from标识
    new_content = new_content.replace(
        '"from": "nanobot"',
        f'"from": "{nb_id}"'
    )

    # 替换轮询端点
    new_content = new_content.replace(
        '/poll/nanobot")',
        f'/poll/{nb_id}")'
    )

    # 写入文件
    target_file.write_text(new_content)
    print(f"✅ {nb_id} 已生成")

print("\n验证语法...")
# 验证语法
for i in range(1, 11):
    nb_id = f"nanobot-{i}"
    target_file = Path(f"/root/.openclaw/workspace/ai-nanobots/{nb_id}/nanobot.py")
    try:
        import py_compile
        py_compile.compile(str(target_file), doraise=True)
        print(f"✅ {nb_id} 语法正确")
    except Exception as e:
        print(f"❌ {nb_id} 语法错误: {e}")

print("\n完成！")
