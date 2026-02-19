#!/usr/bin/env python3
"""
模型共享池 - 避免重复加载嵌入模型
"""
from functools import lru_cache
from sentence_transformers import SentenceTransformer

@lru_cache(maxsize=3)
def get_embedding_model(model_name: str = 'all-MiniLM-L6-v2'):
    """
    获取嵌入模型（带缓存）
    最多缓存3个不同模型
    """
    return SentenceTransformer(model_name)

def clear_model_cache():
    """清空模型缓存（内存不足时调用）"""
    get_embedding_model.cache_clear()
    
if __name__ == "__main__":
    # 测试
    model = get_embedding_model()
    print(f"模型加载成功: {model}")
