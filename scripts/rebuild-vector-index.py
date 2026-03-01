#!/usr/bin/env python3
"""
向量索引重建脚本 - 从长期记忆JSON迁移到Lance向量库
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

# 添加工作目录到路径
WORKSPACE = Path("/root/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def rebuild_vector_index():
    """重建Lance向量索引"""
    
    # 路径配置
    long_term_file = WORKSPACE / "memory" / "vector" / "long_term_memories.json"
    lance_dir = WORKSPACE / "memory" / "vector" / "production" / "memories.lance"
    
    logger.info("="*60)
    logger.info("🔄 Lance向量索引重建")
    logger.info("="*60)
    
    # 1. 检查长期记忆文件
    if not long_term_file.exists():
        logger.error(f"❌ 长期记忆文件不存在: {long_term_file}")
        return False
    
    # 2. 加载长期记忆
    try:
        with open(long_term_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                memories = list(data.values())
            else:
                memories = data
        logger.info(f"📂 已加载 {len(memories)} 条长期记忆")
    except Exception as e:
        logger.error(f"❌ 加载长期记忆失败: {e}")
        return False
    
    # 3. 备份现有Lance目录（如果存在）
    if lance_dir.exists():
        backup_dir = WORKSPACE / "memory" / "vector" / f"production/memories.lance.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.move(str(lance_dir), str(backup_dir))
            logger.info(f"💾 已备份旧索引到: {backup_dir}")
        except Exception as e:
            logger.warning(f"⚠️ 备份失败: {e}")
    
    # 4. 尝试导入必要的库
    try:
        import lancedb
        import pyarrow as pa
        import numpy as np
        from sentence_transformers import SentenceTransformer
        logger.info("✅ 依赖库检查通过")
    except ImportError as e:
        logger.error(f"❌ 缺少依赖: {e}")
        logger.error("请运行: pip install pylance lancedb sentence-transformers pyarrow")
        return False
    
    # 5. 初始化嵌入模型
    try:
        logger.info("🤖 加载嵌入模型 (all-MiniLM-L6-v2)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ 模型加载完成")
    except Exception as e:
        logger.error(f"❌ 模型加载失败: {e}")
        return False
    
    # 6. 准备数据
    logger.info("📊 准备向量数据...")
    
    # 过滤有效记忆
    valid_memories = []
    for m in memories:
        content = m.get("content", "")
        if content and len(content) > 10:  # 过滤太短的
            valid_memories.append(m)
    
    logger.info(f"✅ 有效记忆: {len(valid_memories)} 条")
    
    if len(valid_memories) == 0:
        logger.error("❌ 没有有效记忆可索引")
        return False
    
    # 7. 生成向量嵌入
    logger.info("🔢 生成向量嵌入...")
    try:
        texts = [m.get("content", "")[:512] for m in valid_memories]  # 截断到512字符
        embeddings = model.encode(texts, show_progress_bar=True)
        logger.info(f"✅ 生成 {len(embeddings)} 个向量 (维度: {embeddings.shape[1]})")
    except Exception as e:
        logger.error(f"❌ 向量生成失败: {e}")
        return False
    
    # 8. 创建Lance表
    logger.info("💾 创建Lance向量表...")
    try:
        # 准备数据
        import pandas as pd
        
        df_data = {
            "id": [m.get("id", f"mem_{i}") for i, m in enumerate(valid_memories)],
            "content": [m.get("content", "")[:1024] for m in valid_memories],
            "source": [m.get("source", "") for m in valid_memories],
            "type": [m.get("type", "general") for m in valid_memories],
            "importance": [m.get("importance", 5) for m in valid_memories],
            "tags": [json.dumps(m.get("tags", [])) for m in valid_memories],
            "created_at": [m.get("created_at", datetime.now().isoformat()) for m in valid_memories],
            "access_count": [m.get("access_count", 0) for m in valid_memories],
            "vector": embeddings.tolist()
        }
        
        df = pd.DataFrame(df_data)
        
        # 创建LanceDB连接
        db = lancedb.connect(str(WORKSPACE / "memory" / "vector" / "production"))
        
        # 创建表
        table = db.create_table(
            "memories",
            data=df,
            mode="overwrite"
        )
        
        # 创建向量索引（如果数据足够）
        num_rows = table.count_rows()
        if num_rows >= 256:
            table.create_index(
                metric="cosine",
                vector_column_name="vector",
                index_type="IVF_PQ"
            )
            logger.info(f"✅ Lance表创建成功: {num_rows} 条记录 (带IVF_PQ索引)")
        else:
            logger.info(f"✅ Lance表创建成功: {num_rows} 条记录 (数据不足256条，暂不创建PQ索引)")
            logger.info("   💡 提示: 添加更多记忆后可手动创建索引")
        
    except Exception as e:
        logger.error(f"❌ Lance表创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    except Exception as e:
        logger.error(f"❌ Lance表创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 9. 验证
    logger.info("🔍 验证索引...")
    try:
        # 测试搜索
        test_query = model.encode(["记忆系统"])[0]
        results = table.search(test_query).limit(3).to_pandas()
        logger.info(f"✅ 搜索测试成功: 找到 {len(results)} 条结果")
        logger.info(f"   示例: {results['content'].iloc[0][:50]}...")
    except Exception as e:
        logger.warning(f"⚠️ 搜索测试失败: {e}")
    
    logger.info("="*60)
    logger.info("🎉 Lance向量索引重建完成")
    logger.info("="*60)
    return True


if __name__ == "__main__":
    success = rebuild_vector_index()
    sys.exit(0 if success else 1)
