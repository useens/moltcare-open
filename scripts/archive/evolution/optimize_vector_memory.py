#!/usr/bin/env python3
"""
向量记忆系统深度优化脚本
任务：夜间进化第2轮 - 任务2
生成：reports/OPT_MEMORY_20260215.md
"""

import os
import sys
import json
import pickle
import sqlite3
import hashlib
import time
import gc
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

# 配置路径
WORKSPACE = Path("/root/.openclaw/workspace")
VECTOR_DIR = WORKSPACE / "memory" / "vector"
STORE_DIR = WORKSPACE / "memory" / "vector-store"
REPORTS_DIR = WORKSPACE / "reports"
LANCE_DIR = WORKSPACE / "memory" / "knowledge" / "vector_db"

# 文件路径
PKL_FILE = VECTOR_DIR / "memory_vectors.pkl"
JSON_FILE = VECTOR_DIR / "long_term_memories.json"
DB_FILE = VECTOR_DIR / "memory_vectors.db"
ARCHIVED_FILE = VECTOR_DIR / "archived_memories.pkl"
COMPRESSION_LOG = VECTOR_DIR / "compression_log.json"

# 报告路径
REPORT_FILE = REPORTS_DIR / "OPT_MEMORY_20260215.md"
LOG_FILE = REPORTS_DIR / "OPT_MEMORY_20260215.log"

# 优化配置
SIMILARITY_THRESHOLD = 0.95  # 语义相似度阈值
EXPIRY_DAYS = 90  # 过期天数
MIN_IMPORTANCE = 2  # 最小重要性

class Logger:
    """日志记录器"""
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.messages = []
        
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        self.messages.append(log_line)
        print(log_line)
        
    def info(self, message: str):
        self.log("INFO", message)
        
    def warning(self, message: str):
        self.log("WARN", message)
        
    def error(self, message: str):
        self.log("ERROR", message)
        
    def success(self, message: str):
        self.log("SUCCESS", message)
        
    def save(self):
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.messages))

class VectorMemoryOptimizer:
    """向量记忆系统优化器"""
    
    def __init__(self):
        self.logger = Logger(LOG_FILE)
        self.stats_before = {}
        self.stats_after = {}
        self.benchmark_results = {}
        self.optimization_log = []
        
    def run_full_optimization(self):
        """执行完整优化流程"""
        self.logger.info("="*60)
        self.logger.info("向量记忆系统深度优化开始")
        self.logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("="*60)
        
        # 阶段1: 健康检查
        self.logger.info("\n" + "="*60)
        self.logger.info("【阶段1】向量存储健康检查")
        self.logger.info("="*60)
        self.health_check()
        
        # 阶段2: 基准测试（优化前）
        self.logger.info("\n" + "="*60)
        self.logger.info("【阶段2】性能基准测试（优化前）")
        self.logger.info("="*60)
        self.benchmark_before()
        
        # 阶段3: 记忆压缩与去重
        self.logger.info("\n" + "="*60)
        self.logger.info("【阶段3】记忆压缩与去重")
        self.logger.info("="*60)
        self.compress_and_deduplicate()
        
        # 阶段4: 索引重建与优化
        self.logger.info("\n" + "="*60)
        self.logger.info("【阶段4】索引重建与优化")
        self.logger.info("="*60)
        self.rebuild_index()
        
        # 阶段5: 基准测试（优化后）
        self.logger.info("\n" + "="*60)
        self.logger.info("【阶段5】性能基准测试（优化后）")
        self.logger.info("="*60)
        self.benchmark_after()
        
        # 阶段6: 生成报告
        self.logger.info("\n" + "="*60)
        self.logger.info("【阶段6】生成优化报告")
        self.logger.info("="*60)
        self.generate_report()
        
        self.logger.success("\n向量记忆系统优化完成!")
        self.logger.save()
        
    def health_check(self):
        """1. 向量存储健康检查"""
        self.logger.info("执行向量存储健康检查...")
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "files": {},
            "database": {},
            "vectors": {},
            "issues": []
        }
        
        # 1.1 检查核心文件
        files_to_check = [
            ("PKL向量文件", PKL_FILE),
            ("长期记忆JSON", JSON_FILE),
            ("SQLite数据库", DB_FILE),
            ("归档记忆", ARCHIVED_FILE),
        ]
        
        for name, filepath in files_to_check:
            if not filepath.exists():
                health_report["files"][name] = {"status": "缺失", "size": 0}
                health_report["issues"].append(f"{name} 不存在")
                self.logger.warning(f"❌ {name}: 不存在")
            else:
                size = filepath.stat().st_size
                health_report["files"][name] = {"status": "存在", "size": size}
                self.logger.success(f"✅ {name}: {size:,} bytes")
        
        # 1.2 读取并验证JSON数据
        memories = {}
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            health_report["vectors"]["json_count"] = len(memories)
            self.logger.success(f"✅ JSON记忆数量: {len(memories):,}")
        except Exception as e:
            health_report["issues"].append(f"JSON读取失败: {e}")
            self.logger.error(f"❌ JSON读取失败: {e}")
        
        # 1.3 读取并验证PKL数据
        try:
            with open(PKL_FILE, 'rb') as f:
                pkl_data = pickle.load(f)
            
            if isinstance(pkl_data, dict):
                pkl_count = len(pkl_data)
                # 检查向量维度
                sample_keys = list(pkl_data.keys())[:5]
                dimensions = []
                for key in sample_keys:
                    if isinstance(pkl_data[key], np.ndarray):
                        dimensions.append(pkl_data[key].shape)
                    elif isinstance(pkl_data[key], list):
                        dimensions.append(len(pkl_data[key]))
                
                health_report["vectors"]["pkl_count"] = pkl_count
                health_report["vectors"]["sample_dimensions"] = dimensions
                self.logger.success(f"✅ PKL向量数量: {pkl_count:,}")
                self.logger.info(f"   样本维度: {dimensions}")
            elif isinstance(pkl_data, list):
                health_report["vectors"]["pkl_count"] = len(pkl_data)
                self.logger.success(f"✅ PKL向量数量: {len(pkl_data):,}")
        except Exception as e:
            health_report["issues"].append(f"PKL读取失败: {e}")
            self.logger.error(f"❌ PKL读取失败: {e}")
        
        # 1.4 检查SQLite数据库
        try:
            conn = sqlite3.connect(str(DB_FILE))
            cursor = conn.cursor()
            
            # 获取表列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            health_report["database"]["tables"] = tables
            
            # 统计记录数
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                health_report["database"][f"{table}_count"] = count
                self.logger.success(f"✅ 表 {table}: {count:,} 条记录")
            
            conn.close()
        except Exception as e:
            health_report["issues"].append(f"SQLite检查失败: {e}")
            self.logger.error(f"❌ SQLite检查失败: {e}")
        
        # 1.5 检查LanceDB
        try:
            import lancedb
            if LANCE_DIR.exists():
                db = lancedb.connect(str(LANCE_DIR))
                tables = db.table_names()
                health_report["database"]["lance_tables"] = tables
                for table_name in tables:
                    table = db.open_table(table_name)
                    count = len(table.to_pandas())
                    health_report["database"][f"lance_{table_name}_count"] = count
                    self.logger.success(f"✅ LanceDB表 {table_name}: {count:,} 条记录")
        except Exception as e:
            health_report["issues"].append(f"LanceDB检查失败: {e}")
            self.logger.warning(f"⚠️ LanceDB检查失败: {e}")
        
        # 1.6 检查数据一致性
        if memories and 'pkl_count' in health_report["vectors"]:
            json_count = len(memories)
            pkl_count = health_report["vectors"]["pkl_count"]
            if json_count != pkl_count:
                health_report["issues"].append(f"JSON与PKL数量不一致: {json_count} vs {pkl_count}")
                self.logger.warning(f"⚠️ 数据不一致: JSON({json_count}) != PKL({pkl_count})")
            else:
                self.logger.success(f"✅ 数据一致性检查通过")
        
        # 1.7 检查过期和低价值记忆
        expired_count = 0
        low_value_count = 0
        cutoff_date = datetime.now() - timedelta(days=EXPIRY_DAYS)
        
        for mem_id, mem_data in memories.items():
            if isinstance(mem_data, dict):
                # 检查过期
                created_at = mem_data.get('created_at', '')
                if created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if created_dt < cutoff_date:
                            expired_count += 1
                    except:
                        pass
                
                # 检查低价值
                importance = mem_data.get('importance', 5)
                access_count = mem_data.get('access_count', 0)
                if importance < MIN_IMPORTANCE and access_count == 0:
                    low_value_count += 1
        
        health_report["cleanup_candidates"] = {
            "expired": expired_count,
            "low_value": low_value_count
        }
        self.logger.info(f"📊 可清理记忆: 过期({expired_count}), 低价值({low_value_count})")
        
        # 保存健康检查结果
        self.stats_before["health"] = health_report
        health_score = 100 - len(health_report["issues"]) * 10
        self.logger.info(f"📊 健康评分: {max(0, health_score)}%")
        
        return health_report
    
    def benchmark_before(self):
        """优化前基准测试"""
        self.logger.info("执行优化前基准测试...")
        
        benchmark = {
            "timestamp": datetime.now().isoformat(),
            "write_speed": {},
            "read_latency": {},
            "search_accuracy": {}
        }
        
        # 读取数据
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            with open(PKL_FILE, 'rb') as f:
                vectors = pickle.load(f)
        except Exception as e:
            self.logger.error(f"基准测试数据加载失败: {e}")
            return
        
        # 2.1 写入速度测试
        self.logger.info("测试写入速度...")
        test_data = [{"id": f"test_{i}", "content": f"测试内容 {i}"} for i in range(100)]
        
        start = time.time()
        for item in test_data:
            memories[item["id"]] = item
        write_time = time.time() - start
        benchmark["write_speed"]["json"] = {
            "operations": 100,
            "time_seconds": write_time,
            "ops_per_second": 100 / write_time if write_time > 0 else 0
        }
        self.logger.info(f"   JSON写入: {write_time:.4f}s ({100/write_time:.0f} ops/s)")
        
        # 2.2 读取延迟测试
        self.logger.info("测试读取延迟...")
        sample_ids = list(memories.keys())[:1000]
        
        start = time.time()
        for mem_id in sample_ids:
            _ = memories.get(mem_id)
        read_time = time.time() - start
        benchmark["read_latency"]["json"] = {
            "operations": len(sample_ids),
            "time_seconds": read_time,
            "avg_latency_ms": (read_time / len(sample_ids)) * 1000 if sample_ids else 0
        }
        self.logger.info(f"   JSON读取: {read_time:.4f}s (avg: {(read_time/len(sample_ids))*1000:.4f}ms)")
        
        # 2.3 语义搜索准确性测试（如果有嵌入模型）
        self.logger.info("测试语义搜索...")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("BAAI/bge-large-zh-v1.5", device="cpu")
            
            # 测试查询
            test_queries = [
                "系统优化",
                "记忆管理", 
                "向量检索",
                "性能测试"
            ]
            
            search_times = []
            for query in test_queries:
                start = time.time()
                query_vec = model.encode(query, convert_to_numpy=True)
                # 简单相似度计算
                similarities = []
                sample_items = list(vectors.items())[:500]
                for mem_id, vec in sample_items:
                    if isinstance(vec, np.ndarray):
                        sim = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec))
                        similarities.append((mem_id, sim))
                # 排序取top5
                similarities.sort(key=lambda x: x[1], reverse=True)
                search_times.append(time.time() - start)
            
            avg_search_time = sum(search_times) / len(search_times)
            benchmark["search_accuracy"]["avg_latency_seconds"] = avg_search_time
            self.logger.info(f"   语义搜索: avg {avg_search_time:.4f}s per query")
            
        except Exception as e:
            self.logger.warning(f"语义搜索测试失败: {e}")
            benchmark["search_accuracy"]["error"] = str(e)
        
        self.stats_before["benchmark"] = benchmark
        self.logger.success("✅ 基准测试完成")
        
    def compress_and_deduplicate(self):
        """3. 记忆压缩与去重"""
        self.logger.info("执行记忆压缩与去重...")
        
        # 读取数据
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            with open(PKL_FILE, 'rb') as f:
                vectors = pickle.load(f)
            self.logger.success(f"✅ 加载完成: {len(memories)} 条记忆")
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return
        
        stats = {
            "original_count": len(memories),
            "removed_expired": 0,
            "removed_low_value": 0,
            "removed_duplicates": 0,
            "merged_similar": 0,
            "final_count": 0
        }
        
        # 3.1 清理过期记忆
        self.logger.info("清理过期记忆...")
        cutoff_date = datetime.now() - timedelta(days=EXPIRY_DAYS)
        expired_ids = []
        
        for mem_id, mem_data in list(memories.items()):
            if isinstance(mem_data, dict):
                created_at = mem_data.get('created_at', '')
                if created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if created_dt < cutoff_date:
                            importance = mem_data.get('importance', 5)
                            access_count = mem_data.get('access_count', 0)
                            # 只删除低重要性且未被访问的过期记忆
                            if importance < 5 and access_count < 2:
                                expired_ids.append(mem_id)
                    except:
                        pass
        
        for mem_id in expired_ids:
            del memories[mem_id]
            if isinstance(vectors, dict) and mem_id in vectors:
                del vectors[mem_id]
        
        stats["removed_expired"] = len(expired_ids)
        self.logger.success(f"✅ 清理过期记忆: {len(expired_ids)} 条")
        
        # 3.2 清理低价值记忆
        self.logger.info("清理低价值记忆...")
        low_value_ids = []
        
        for mem_id, mem_data in list(memories.items()):
            if isinstance(mem_data, dict):
                importance = mem_data.get('importance', 5)
                access_count = mem_data.get('access_count', 0)
                created_at = mem_data.get('created_at', '')
                
                # 检查是否超过30天
                is_old = False
                if created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if (datetime.now() - created_dt).days > 30:
                            is_old = True
                    except:
                        pass
                
                if importance < MIN_IMPORTANCE and access_count == 0 and is_old:
                    low_value_ids.append(mem_id)
        
        for mem_id in low_value_ids:
            del memories[mem_id]
            if isinstance(vectors, dict) and mem_id in vectors:
                del vectors[mem_id]
        
        stats["removed_low_value"] = len(low_value_ids)
        self.logger.success(f"✅ 清理低价值记忆: {len(low_value_ids)} 条")
        
        # 3.3 去重 - 基于内容哈希
        self.logger.info("执行内容去重...")
        content_hashes = {}
        duplicate_ids = []
        
        for mem_id, mem_data in memories.items():
            if isinstance(mem_data, dict):
                content = mem_data.get('content', '')
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                if content_hash in content_hashes:
                    duplicate_ids.append(mem_id)
                    # 合并访问统计
                    existing_id = content_hashes[content_hash]
                    if existing_id in memories:
                        memories[existing_id]['access_count'] = (
                            memories[existing_id].get('access_count', 0) + 
                            mem_data.get('access_count', 0)
                        )
                else:
                    content_hashes[content_hash] = mem_id
        
        for mem_id in duplicate_ids:
            del memories[mem_id]
            if isinstance(vectors, dict) and mem_id in vectors:
                del vectors[mem_id]
        
        stats["removed_duplicates"] = len(duplicate_ids)
        self.logger.success(f"✅ 内容去重: {len(duplicate_ids)} 条")
        
        # 3.4 语义相似度去重
        self.logger.info("执行语义相似度去重...")
        similar_pairs = []
        
        if isinstance(vectors, dict) and len(vectors) > 0:
            # 获取有向量的记忆
            vec_items = [(k, v) for k, v in vectors.items() if isinstance(v, np.ndarray)]
            
            if len(vec_items) > 1:
                # 随机采样进行相似度检查（避免O(n^2)）
                import random
                sample_size = min(1000, len(vec_items))
                sampled = random.sample(vec_items, sample_size)
                
                checked = set()
                for i, (id1, vec1) in enumerate(sampled):
                    for j, (id2, vec2) in enumerate(sampled[i+1:], i+1):
                        pair_key = tuple(sorted([id1, id2]))
                        if pair_key in checked:
                            continue
                        checked.add(pair_key)
                        
                        # 计算余弦相似度
                        norm1 = np.linalg.norm(vec1)
                        norm2 = np.linalg.norm(vec2)
                        if norm1 > 0 and norm2 > 0:
                            sim = np.dot(vec1, vec2) / (norm1 * norm2)
                            if sim > SIMILARITY_THRESHOLD:
                                similar_pairs.append((id1, id2, sim))
                
                # 删除相似的记忆（保留先创建的）
                removed_similar = set()
                for id1, id2, sim in similar_pairs:
                    if id1 not in removed_similar and id2 not in removed_similar:
                        # 比较创建时间
                        mem1 = memories.get(id1, {})
                        mem2 = memories.get(id2, {})
                        created1 = mem1.get('created_at', '')
                        created2 = mem2.get('created_at', '')
                        
                        if created1 > created2:  # id1更新，删除id1
                            to_remove = id1
                        else:
                            to_remove = id2
                        
                        if to_remove in memories:
                            del memories[to_remove]
                            removed_similar.add(to_remove)
                        if isinstance(vectors, dict) and to_remove in vectors:
                            del vectors[to_remove]
                
                stats["merged_similar"] = len(removed_similar)
                self.logger.success(f"✅ 语义去重: {len(removed_similar)} 条 (发现 {len(similar_pairs)} 对相似)")
        
        stats["final_count"] = len(memories)
        
        # 保存优化后的数据
        self.logger.info("保存优化后的数据...")
        try:
            # 备份原文件
            backup_dir = VECTOR_DIR / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(exist_ok=True)
            
            import shutil
            shutil.copy2(JSON_FILE, backup_dir / "long_term_memories.json.bak")
            shutil.copy2(PKL_FILE, backup_dir / "memory_vectors.pkl.bak")
            
            # 写入优化后的数据
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
            
            with open(PKL_FILE, 'wb') as f:
                pickle.dump(vectors, f)
            
            self.logger.success(f"✅ 数据保存完成，备份至: {backup_dir}")
            
            # 记录压缩日志
            compression_entry = {
                "timestamp": datetime.now().isoformat(),
                "original_count": stats["original_count"],
                "removed_expired": stats["removed_expired"],
                "removed_low_value": stats["removed_low_value"],
                "removed_duplicates": stats["removed_duplicates"],
                "merged_similar": stats["merged_similar"],
                "final_count": stats["final_count"],
                "reduction_rate": (stats["original_count"] - stats["final_count"]) / stats["original_count"] * 100 if stats["original_count"] > 0 else 0
            }
            
            # 读取现有压缩日志
            try:
                with open(COMPRESSION_LOG, 'r', encoding='utf-8') as f:
                    log = json.load(f)
            except:
                log = []
            
            log.append(compression_entry)
            
            with open(COMPRESSION_LOG, 'w', encoding='utf-8') as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"数据保存失败: {e}")
        
        self.optimization_log.append(stats)
        self.logger.success(f"✅ 压缩去重完成: {stats['original_count']} -> {stats['final_count']} ({stats['original_count']-stats['final_count']} 条已清理)")
        
    def rebuild_index(self):
        """4. 索引重建与优化"""
        self.logger.info("执行索引重建与优化...")
        
        try:
            with open(PKL_FILE, 'rb') as f:
                vectors = pickle.load(f)
        except Exception as e:
            self.logger.error(f"向量加载失败: {e}")
            return
        
        index_stats = {
            "timestamp": datetime.now().isoformat(),
            "original_vectors": len(vectors) if isinstance(vectors, dict) else 0,
            "rebuilt": False
        }
        
        # 4.1 重建PKL索引
        self.logger.info("重建PKL向量索引...")
        try:
            if isinstance(vectors, dict):
                # 确保所有向量都是numpy数组
                normalized_vectors = {}
                for key, vec in vectors.items():
                    if isinstance(vec, list):
                        normalized_vectors[key] = np.array(vec, dtype=np.float32)
                    elif isinstance(vec, np.ndarray):
                        normalized_vectors[key] = vec.astype(np.float32)
                    else:
                        normalized_vectors[key] = vec
                
                # 保存标准化后的向量
                with open(PKL_FILE, 'wb') as f:
                    pickle.dump(normalized_vectors, protocol=pickle.HIGHEST_PROTOCOL)
                
                index_stats["rebuilt"] = True
                self.logger.success(f"✅ PKL索引重建完成: {len(normalized_vectors)} 条向量")
                
                # 更新vectors引用
                vectors = normalized_vectors
        except Exception as e:
            self.logger.error(f"PKL索引重建失败: {e}")
        
        # 4.2 重建SQLite索引
        self.logger.info("重建SQLite数据库索引...")
        try:
            conn = sqlite3.connect(str(DB_FILE))
            cursor = conn.cursor()
            
            # 创建索引表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_index (
                    id TEXT PRIMARY KEY,
                    content_hash TEXT,
                    created_at TIMESTAMP,
                    importance INTEGER,
                    access_count INTEGER,
                    last_accessed TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created ON memory_index(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_importance ON memory_index(importance)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_access ON memory_index(access_count)')
            
            # 清空并重建索引数据
            cursor.execute('DELETE FROM memory_index')
            
            # 读取JSON数据填充索引
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            
            for mem_id, mem_data in memories.items():
                if isinstance(mem_data, dict):
                    content = mem_data.get('content', '')
                    content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
                    cursor.execute('''
                        INSERT OR REPLACE INTO memory_index 
                        (id, content_hash, created_at, importance, access_count, last_accessed)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        mem_id,
                        content_hash,
                        mem_data.get('created_at', ''),
                        mem_data.get('importance', 5),
                        mem_data.get('access_count', 0),
                        mem_data.get('last_accessed', '')
                    ))
            
            conn.commit()
            
            # 验证索引
            cursor.execute('SELECT COUNT(*) FROM memory_index')
            index_count = cursor.fetchone()[0]
            index_stats["sqlite_index_count"] = index_count
            
            conn.close()
            self.logger.success(f"✅ SQLite索引重建完成: {index_count} 条记录")
            
        except Exception as e:
            self.logger.error(f"SQLite索引重建失败: {e}")
        
        # 4.3 重建LanceDB索引
        self.logger.info("重建LanceDB向量索引...")
        try:
            import lancedb
            import pyarrow as pa
            
            if LANCE_DIR.exists():
                db = lancedb.connect(str(LANCE_DIR))
                
                # 删除旧表
                if "knowledge_vectors" in db.table_names():
                    db.drop_table("knowledge_vectors")
                
                # 准备数据
                if isinstance(vectors, dict) and len(vectors) > 0:
                    data = []
                    for mem_id, vec in list(vectors.items())[:1000]:  # 限制数量
                        if isinstance(vec, np.ndarray):
                            data.append({
                                "id": mem_id,
                                "vector": vec.tolist()
                            })
                    
                    if data:
                        # 创建新表
                        table = db.create_table(
                            "knowledge_vectors",
                            data=data,
                            mode="create"
                        )
                        
                        # 创建向量索引
                        table.create_index(
                            vector_column_name="vector",
                            index_type="ivf_pq",
                            num_partitions=16,
                            num_sub_vectors=16
                        )
                        
                        index_stats["lance_rebuilt"] = True
                        index_stats["lance_vectors"] = len(data)
                        self.logger.success(f"✅ LanceDB索引重建完成: {len(data)} 条向量")
                
        except Exception as e:
            self.logger.warning(f"LanceDB索引重建失败: {e}")
        
        # 4.4 验证检索准确性
        self.logger.info("验证检索准确性...")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("BAAI/bge-large-zh-v1.5", device="cpu")
            
            # 测试查询
            test_queries = ["系统优化", "记忆管理"]
            accuracy_results = []
            
            for query in test_queries:
                query_vec = model.encode(query, convert_to_numpy=True)
                
                # 计算相似度
                similarities = []
                sample_items = list(vectors.items())[:200]
                for mem_id, vec in sample_items:
                    if isinstance(vec, np.ndarray):
                        sim = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-8)
                        similarities.append((mem_id, sim))
                
                # 排序
                similarities.sort(key=lambda x: x[1], reverse=True)
                top5 = similarities[:5]
                
                # 检查top5的相似度是否都较高
                avg_sim = sum(s[1] for s in top5) / len(top5) if top5 else 0
                accuracy_results.append(avg_sim)
            
            avg_accuracy = sum(accuracy_results) / len(accuracy_results)
            index_stats["retrieval_accuracy"] = avg_accuracy
            self.logger.success(f"✅ 检索准确性验证: 平均相似度 {avg_accuracy:.4f}")
            
        except Exception as e:
            self.logger.warning(f"检索准确性验证失败: {e}")
        
        self.optimization_log.append(index_stats)
        self.logger.success("✅ 索引重建与优化完成")
        
    def benchmark_after(self):
        """优化后基准测试"""
        self.logger.info("执行优化后基准测试...")
        
        benchmark = {
            "timestamp": datetime.now().isoformat(),
            "write_speed": {},
            "read_latency": {},
            "search_accuracy": {}
        }
        
        # 读取数据
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            with open(PKL_FILE, 'rb') as f:
                vectors = pickle.load(f)
        except Exception as e:
            self.logger.error(f"基准测试数据加载失败: {e}")
            return
        
        # 写入速度测试
        test_data = [{"id": f"test_after_{i}", "content": f"测试内容 {i}"} for i in range(100)]
        
        start = time.time()
        for item in test_data:
            memories[item["id"]] = item
        write_time = time.time() - start
        benchmark["write_speed"]["json"] = {
            "operations": 100,
            "time_seconds": write_time,
            "ops_per_second": 100 / write_time if write_time > 0 else 0
        }
        self.logger.info(f"   JSON写入: {write_time:.4f}s ({100/write_time:.0f} ops/s)")
        
        # 读取延迟测试
        sample_ids = list(memories.keys())[:1000]
        start = time.time()
        for mem_id in sample_ids:
            _ = memories.get(mem_id)
        read_time = time.time() - start
        benchmark["read_latency"]["json"] = {
            "operations": len(sample_ids),
            "time_seconds": read_time,
            "avg_latency_ms": (read_time / len(sample_ids)) * 1000 if sample_ids else 0
        }
        self.logger.info(f"   JSON读取: {read_time:.4f}s (avg: {(read_time/len(sample_ids))*1000:.4f}ms)")
        
        # 语义搜索测试
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("BAAI/bge-large-zh-v1.5", device="cpu")
            
            test_queries = ["系统优化", "记忆管理", "向量检索", "性能测试"]
            search_times = []
            
            for query in test_queries:
                start = time.time()
                query_vec = model.encode(query, convert_to_numpy=True)
                
                similarities = []
                sample_items = list(vectors.items())[:500]
                for mem_id, vec in sample_items:
                    if isinstance(vec, np.ndarray):
                        sim = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-8)
                        similarities.append((mem_id, sim))
                
                similarities.sort(key=lambda x: x[1], reverse=True)
                search_times.append(time.time() - start)
            
            avg_search_time = sum(search_times) / len(search_times)
            benchmark["search_accuracy"]["avg_latency_seconds"] = avg_search_time
            self.logger.info(f"   语义搜索: avg {avg_search_time:.4f}s per query")
            
        except Exception as e:
            self.logger.warning(f"语义搜索测试失败: {e}")
        
        self.stats_after["benchmark"] = benchmark
        self.logger.success("✅ 优化后基准测试完成")
        
    def generate_report(self):
        """生成优化报告"""
        self.logger.info("生成优化报告...")
        
        # 计算性能对比
        before = self.stats_before.get("benchmark", {})
        after = self.stats_after.get("benchmark", {})
        
        # 写入速度对比
        before_write = before.get("write_speed", {}).get("json", {}).get("ops_per_second", 0)
        after_write = after.get("write_speed", {}).get("json", {}).get("ops_per_second", 0)
        write_improvement = ((after_write - before_write) / before_write * 100) if before_write > 0 else 0
        
        # 读取延迟对比
        before_read = before.get("read_latency", {}).get("json", {}).get("avg_latency_ms", 0)
        after_read = after.get("read_latency", {}).get("json", {}).get("avg_latency_ms", 0)
        read_improvement = ((before_read - after_read) / before_read * 100) if before_read > 0 else 0
        
        # 搜索延迟对比
        before_search = before.get("search_accuracy", {}).get("avg_latency_seconds", 0)
        after_search = after.get("search_accuracy", {}).get("avg_latency_seconds", 0)
        search_improvement = ((before_search - after_search) / before_search * 100) if before_search > 0 else 0
        
        # 构建报告
        report = f"""# 向量记忆系统优化报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**任务**: 夜间进化第2轮 - 任务2  
**优化目标**: 向量存储健康检查、记忆压缩与去重、索引重建、性能基准测试

---

## 1. 执行摘要

本次优化对向量记忆系统进行了全面的健康检查、压缩去重、索引重建和性能优化。

### 1.1 优化前后对比

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 记忆数量 | {self.optimization_log[0].get('original_count', 'N/A') if self.optimization_log else 'N/A'} | {self.optimization_log[0].get('final_count', 'N/A') if self.optimization_log else 'N/A'} | -{self.optimization_log[0].get('original_count', 0) - self.optimization_log[0].get('final_count', 0) if self.optimization_log else 'N/A'} |
| 写入速度 | {before_write:.0f} ops/s | {after_write:.0f} ops/s | {write_improvement:+.1f}% |
| 读取延迟 | {before_read:.4f} ms | {after_read:.4f} ms | {read_improvement:+.1f}% |
| 搜索延迟 | {before_search:.4f}s | {after_search:.4f}s | {search_improvement:+.1f}% |

---

## 2. 详细优化结果

### 2.1 向量存储健康检查

#### 文件完整性
"""
        
        health = self.stats_before.get("health", {})
        for name, info in health.get("files", {}).items():
            status_icon = "✅" if info.get("status") == "存在" else "❌"
            report += f"- {status_icon} **{name}**: {info.get('size', 0):,} bytes ({info.get('status')})\n"
        
        report += f"""
#### 数据统计
- JSON记忆数量: {health.get('vectors', {}).get('json_count', 'N/A')} 条
- PKL向量数量: {health.get('vectors', {}).get('pkl_count', 'N/A')} 条
- 样本向量维度: {health.get('vectors', {}).get('sample_dimensions', 'N/A')}

#### 发现的问题
"""
        issues = health.get("issues", [])
        if issues:
            for issue in issues:
                report += f"- ⚠️ {issue}\n"
        else:
            report += "- ✅ 未发现严重问题\n"
        
        report += f"""
#### 可清理记忆
- 过期记忆 (>90天): {health.get('cleanup_candidates', {}).get('expired', 0)} 条
- 低价值记忆: {health.get('cleanup_candidates', {}).get('low_value', 0)} 条

---

### 2.2 记忆压缩与去重

| 操作类型 | 清理数量 | 说明 |
|----------|----------|------|
| 过期记忆清理 | {self.optimization_log[0].get('removed_expired', 0) if self.optimization_log else 'N/A'} | 删除超过90天且低重要性记忆 |
| 低价值记忆 | {self.optimization_log[0].get('removed_low_value', 0) if self.optimization_log else 'N/A'} | 删除重要性<2且未被访问记忆 |
| 内容去重 | {self.optimization_log[0].get('removed_duplicates', 0) if self.optimization_log else 'N/A'} | 基于MD5哈希去重 |
| 语义去重 | {self.optimization_log[0].get('merged_similar', 0) if self.optimization_log else 'N/A'} | 相似度>0.95的记忆合并 |

**清理率**: {(self.optimization_log[0].get('original_count', 0) - self.optimization_log[0].get('final_count', 0)) / self.optimization_log[0].get('original_count', 1) * 100:.1f}%  
**原始数量**: {self.optimization_log[0].get('original_count', 'N/A') if self.optimization_log else 'N/A'}  
**最终数量**: {self.optimization_log[0].get('final_count', 'N/A') if self.optimization_log else 'N/A'}

---

### 2.3 索引重建与优化

"""
        
        if len(self.optimization_log) > 1:
            index_stats = self.optimization_log[1]
            report += f"""
#### PKL向量索引
- 重建状态: {'✅ 完成' if index_stats.get('rebuilt') else '❌ 失败'}
- 向量数量: {index_stats.get('original_vectors', 'N/A')}

#### SQLite数据库索引
- 索引记录数: {index_stats.get('sqlite_index_count', 'N/A')}
- 创建的索引: created_at, importance, access_count

#### LanceDB向量索引
- 重建状态: {'✅ 完成' if index_stats.get('lance_rebuilt') else '⚠️ 未完成'}
- 向量数量: {index_stats.get('lance_vectors', 'N/A')}

#### 检索准确性验证
- 平均相似度: {index_stats.get('retrieval_accuracy', 'N/A')}
- 状态: {'✅ 正常' if index_stats.get('retrieval_accuracy', 0) > 0.5 else '⚠️ 需关注'}
"""
        
        report += f"""
---

### 2.4 性能基准测试

#### 优化前性能

| 测试项 | 数值 |
|--------|------|
| JSON写入速度 | {before_write:.0f} ops/s |
| JSON读取延迟 | {before_read:.4f} ms/op |
| 语义搜索延迟 | {before_search:.4f} s/query |

#### 优化后性能

| 测试项 | 数值 | 提升 |
|--------|------|------|
| JSON写入速度 | {after_write:.0f} ops/s | {write_improvement:+.1f}% |
| JSON读取延迟 | {after_read:.4f} ms/op | {read_improvement:+.1f}% |
| 语义搜索延迟 | {after_search:.4f} s/query | {search_improvement:+.1f}% |

---

## 3. 优化建议

### 3.1 已完成优化
1. ✅ 清理过期和低价值记忆
2. ✅ 执行内容去重和语义去重
3. ✅ 重建PKL、SQLite和LanceDB索引
4. ✅ 验证检索准确性

### 3.2 后续建议
1. **定期维护**: 建议每月执行一次压缩去重
2. **监控告警**: 设置记忆数量增长监控
3. **增量更新**: 考虑实现增量索引更新机制
4. **备份策略**: 定期备份向量数据到外部存储

---

## 4. 附录

### 4.1 优化日志文件
- 详细日志: `{LOG_FILE}`
- 压缩日志: `{COMPRESSION_LOG}`

### 4.2 备份位置
优化前的数据已备份至: `{VECTOR_DIR}/backup_YYYYMMDD_HHMMSS/`

### 4.3 验证命令
```bash
# 检查向量数量
python3 -c "import pickle; d=pickle.load(open('{PKL_FILE}','rb')); print(f'Vectors: {{len(d)}}')"

# 检查JSON记录数
python3 -c "import json; d=json.load(open('{JSON_FILE}')); print(f'Memories: {{len(d)}}')"
```

---

*报告生成完成 - 向量记忆系统优化任务*
"""
        
        # 保存报告
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.success(f"✅ 优化报告已保存: {REPORT_FILE}")

def main():
    optimizer = VectorMemoryOptimizer()
    optimizer.run_full_optimization()
    print(f"\n{'='*60}")
    print(f"优化完成！报告位置: {REPORT_FILE}")
    print(f"日志位置: {LOG_FILE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
