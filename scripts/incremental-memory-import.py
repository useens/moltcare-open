#!/usr/bin/env python3
"""
增量记忆入库脚本
自动扫描新增/修改的记忆文件，编码入库到向量数据库
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# 路径配置
WORKSPACE = Path.home() / ".openclaw/workspace"
MEMORY_DIR = WORKSPACE / "memory"
DB_PATH = MEMORY_DIR / "vector/production"
IMPORT_STATE_FILE = DB_PATH / ".import_state.json"

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_file_hash(file_path):
    """计算文件哈希"""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def load_import_state():
    """加载导入状态"""
    if IMPORT_STATE_FILE.exists():
        try:
            with open(IMPORT_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log(f"⚠️ 加载导入状态失败: {e}")
    return {}

def save_import_state(state):
    """保存导入状态"""
    try:
        os.makedirs(DB_PATH, exist_ok=True)
        with open(IMPORT_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"⚠️ 保存导入状态失败: {e}")

def scan_memory_files():
    """扫描需要导入的记忆文件"""
    state = load_import_state()
    files_to_import = []
    
    # 扫描目录
    scan_dirs = [
        MEMORY_DIR / "daily",
        MEMORY_DIR / "modules",
        MEMORY_DIR / "evolution/2026-02",
    ]
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
            
        for file_path in scan_dir.rglob("*.md"):
            file_key = str(file_path.resolve())
            current_mtime = file_path.stat().st_mtime
            current_hash = get_file_hash(file_path)
            
            # 检查是否需要导入
            if file_key not in state:
                # 新文件
                files_to_import.append((file_path, current_hash))
            elif state[file_key].get("hash") != current_hash:
                # 文件已修改
                files_to_import.append((file_path, current_hash))
    
    return files_to_import, state

def import_file_to_vector(file_path, memory_adapter):
    """将单个文件导入向量数据库"""
    try:
        content = file_path.read_text(encoding='utf-8')
        if not content.strip():
            return False
        
        # 分段处理（简单分段，每1000字符）
        chunk_size = 1000
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            chunks.append(chunk)
        
        # 导入每个分段
        imported_count = 0
        for idx, chunk in enumerate(chunks):
            metadata = {
                "source": str(file_path.relative_to(WORKSPACE)),
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "imported_at": datetime.now().isoformat()
            }
            memory_adapter.add_memory(chunk, metadata)
            imported_count += 1
        
        return imported_count
    except Exception as e:
        log(f"  ⚠️ 导入失败 {file_path}: {e}")
        return 0

def incremental_import():
    """执行增量导入"""
    log("🔄 开始增量记忆导入...")
    
    # 导入适配器
    sys.path.insert(0, str(WORKSPACE))
    from memory_adapter import get_memory_adapter
    
    adapter = get_memory_adapter()
    if adapter._memory is None:
        log("❌ 向量记忆系统未初始化")
        return 0
    
    # 扫描文件
    files_to_import, state = scan_memory_files()
    
    if not files_to_import:
        log("✅ 没有新文件需要导入")
        return 0
    
    log(f"📁 发现 {len(files_to_import)} 个新/修改文件")
    
    # 导入文件
    total_imported = 0
    for file_path, file_hash in files_to_import:
        log(f"  📄 导入: {file_path.name}")
        imported = import_file_to_vector(file_path, adapter)
        total_imported += imported
        
        # 更新状态
        state[str(file_path.resolve())] = {
            "mtime": file_path.stat().st_mtime,
            "hash": file_hash,
            "imported_at": datetime.now().isoformat(),
            "chunks": imported
        }
    
    # 保存状态
    save_import_state(state)
    
    log(f"✅ 增量导入完成: {len(files_to_import)} 个文件, {total_imported} 个文本块")
    return total_imported

if __name__ == "__main__":
    try:
        count = incremental_import()
        sys.exit(0 if count >= 0 else 1)
    except Exception as e:
        log(f"❌ 增量导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
