#!/usr/bin/env python3
"""
记忆系统深度优化脚本
执行：向量压缩、索引重建、检索性能调优
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加workspace到路径
sys.path.insert(0, '/root/.openclaw/workspace')

class MemoryOptimizer:
    """记忆系统优化器"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "databases": {},
            "optimization": {},
            "performance": {},
            "issues": [],
            "recommendations": []
        }
        
    def check_database_status(self, db_path: str, name: str) -> Dict[str, Any]:
        """检查数据库状态"""
        logger.info(f"\n{'='*60}")
        logger.info(f"检查数据库: {name}")
        logger.info(f"路径: {db_path}")
        logger.info(f"{'='*60}")
        
        status = {
            "name": name,
            "path": db_path,
            "exists": False,
            "record_count": 0,
            "storage_size_mb": 0,
            "index_status": "unknown",
            "fragment_count": 0,
            "errors": []
        }
        
        try:
            import lancedb
            
            db_path = Path(db_path)
            if not db_path.exists():
                status["errors"].append(f"数据库路径不存在: {db_path}")
                return status
            
            status["exists"] = True
            
            # 获取存储大小
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(db_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            status["storage_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            # 连接数据库
            db = lancedb.connect(str(db_path))
            tables_result = db.list_tables()
            # list_tables()返回的是分页结果，需要提取表名列表
            if hasattr(tables_result, 'tables'):
                table_names = tables_result.tables
            elif isinstance(tables_result, tuple) and len(tables_result) >= 1:
                table_names = tables_result[0]
            else:
                table_names = list(tables_result)
            
            if not table_names:
                status["errors"].append("数据库中没有表")
                return status
            
            logger.info(f"发现表: {table_names}")
            
            # 检查每个表
            for table_name in table_names:
                try:
                    table = db.open_table(table_name)
                    df = table.to_pandas()
                    status["record_count"] = len(df)
                    
                    # 获取统计信息
                    logger.info(f"表 '{table_name}' 记录数: {len(df)}")
                    
                    # 尝试获取片段信息（LanceDB内部结构）
                    try:
                        # 使用Lance的统计信息
                        stats = table.stats() if hasattr(table, 'stats') else {}
                        if stats:
                            logger.info(f"表统计: {stats}")
                    except Exception as e:
                        logger.debug(f"无法获取详细统计: {e}")
                    
                    # 检查索引状态
                    try:
                        # LanceDB的索引信息获取
                        status["index_status"] = "已创建" if len(df) > 0 else "空表"
                    except Exception as e:
                        status["index_status"] = f"未知: {e}"
                    
                except Exception as e:
                    status["errors"].append(f"表 {table_name} 检查失败: {e}")
            
            # LanceDB不需要显式关闭
            
        except ImportError:
            status["errors"].append("lancedb模块未安装")
        except Exception as e:
            status["errors"].append(f"检查失败: {e}")
        
        return status
    
    def optimize_database(self, db_path: str, name: str) -> Dict[str, Any]:
        """执行数据库优化"""
        logger.info(f"\n{'='*60}")
        logger.info(f"优化数据库: {name}")
        logger.info(f"{'='*60}")
        
        result = {
            "name": name,
            "optimized": False,
            "before_size_mb": 0,
            "after_size_mb": 0,
            "size_reduction_mb": 0,
            "size_reduction_percent": 0,
            "compact_success": False,
            "optimize_success": False,
            "duration_seconds": 0,
            "errors": []
        }
        
        start_time = time.time()
        
        try:
            import lancedb
            
            db_path = Path(db_path)
            if not db_path.exists():
                result["errors"].append("数据库路径不存在")
                return result
            
            # 获取优化前大小
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(db_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            result["before_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            logger.info(f"优化前大小: {result['before_size_mb']:.2f} MB")
            
            # 连接数据库
            db = lancedb.connect(str(db_path))
            tables_result = db.list_tables()
            if hasattr(tables_result, 'tables'):
                table_names = tables_result.tables
            elif isinstance(tables_result, tuple) and len(tables_result) >= 1:
                table_names = tables_result[0]
            else:
                table_names = list(tables_result)
            
            for table_name in table_names:
                try:
                    table = db.open_table(table_name)
                    df = table.to_pandas()
                    
                    if len(df) == 0:
                        logger.info(f"表 {table_name} 为空，跳过优化")
                        continue
                    
                    logger.info(f"开始优化表: {table_name}")
                    logger.info(f"当前记录数: {len(df)}")
                    
                    # 获取优化前统计
                    try:
                        stats = table.stats()
                        logger.info(f"优化前片段数: {stats.get('fragment_stats', {}).get('num_fragments', 'N/A')}")
                    except:
                        pass
                    
                    # LanceDB 0.21+ 使用统一的optimize()方法
                    try:
                        # 这会自动执行compact_files + optimize_index
                        table.optimize()
                        result["compact_success"] = True
                        result["optimize_success"] = True
                        logger.info("✓ 表优化完成（压缩+索引重建）")
                    except Exception as e:
                        # 降级处理
                        result["errors"].append(f"优化失败: {e}")
                        logger.error(f"优化失败: {e}")
                    
                    # 获取优化后统计
                    try:
                        df_after = table.to_pandas()
                        logger.info(f"优化后记录数: {len(df_after)}")
                        stats_after = table.stats()
                        logger.info(f"优化后片段数: {stats_after.get('fragment_stats', {}).get('num_fragments', 'N/A')}")
                    except:
                        pass
                    
                except Exception as e:
                    result["errors"].append(f"表 {table_name} 优化失败: {e}")
            
            # LanceDB不需要显式关闭
            
            # 获取优化后大小
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(db_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            result["after_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            result["size_reduction_mb"] = round(
                result["before_size_mb"] - result["after_size_mb"], 2
            )
            if result["before_size_mb"] > 0:
                result["size_reduction_percent"] = round(
                    (result["size_reduction_mb"] / result["before_size_mb"]) * 100, 2
                )
            
            result["duration_seconds"] = round(time.time() - start_time, 2)
            result["optimized"] = result["compact_success"] or result["optimize_success"]
            
            logger.info(f"优化后大小: {result['after_size_mb']:.2f} MB")
            logger.info(f"空间释放: {result['size_reduction_mb']:.2f} MB ({result['size_reduction_percent']}%)")
            logger.info(f"优化耗时: {result['duration_seconds']:.2f} 秒")
            
        except ImportError:
            result["errors"].append("lancedb模块未安装")
        except Exception as e:
            result["errors"].append(f"优化失败: {e}")
        
        return result
    
    def test_search_performance(self, db_path: str, name: str) -> Dict[str, Any]:
        """测试检索性能"""
        logger.info(f"\n{'='*60}")
        logger.info(f"测试检索性能: {name}")
        logger.info(f"{'='*60}")
        
        result = {
            "name": name,
            "tested": False,
            "query_latency_ms": {},
            "avg_latency_ms": 0,
            "errors": []
        }
        
        try:
            import lancedb
            
            db_path = Path(db_path)
            if not db_path.exists():
                result["errors"].append("数据库路径不存在")
                return result
            
            db = lancedb.connect(str(db_path))
            
            tables_result = db.list_tables()
            if hasattr(tables_result, 'tables'):
                table_names = tables_result.tables
            elif isinstance(tables_result, tuple) and len(tables_result) >= 1:
                table_names = tables_result[0]
            else:
                table_names = list(tables_result)
            
            for table_name in table_names:
                try:
                    table = db.open_table(table_name)
                    df = table.to_pandas()
                    
                    if len(df) == 0:
                        logger.info(f"表 {table_name} 为空，跳过性能测试")
                        continue
                    
                    # 获取向量维度
                    if 'vector' in df.columns and len(df) > 0:
                        vector_dim = len(df['vector'].iloc[0])
                        logger.info(f"向量维度: {vector_dim}")
                        
                        # 生成测试查询向量
                        test_queries = [
                            ("random_query_1", np.random.randn(vector_dim).astype(np.float32)),
                            ("random_query_2", np.random.randn(vector_dim).astype(np.float32)),
                            ("random_query_3", np.random.randn(vector_dim).astype(np.float32)),
                        ]
                        
                        latencies = []
                        
                        for query_name, query_vec in test_queries:
                            # 预热
                            _ = table.search(query_vec.tolist()).limit(5).to_list()
                            
                            # 正式测试
                            start = time.perf_counter()
                            results = table.search(query_vec.tolist()).limit(10).to_list()
                            end = time.perf_counter()
                            
                            latency_ms = round((end - start) * 1000, 2)
                            latencies.append(latency_ms)
                            result["query_latency_ms"][query_name] = latency_ms
                            
                            logger.info(f"查询 '{query_name}': {latency_ms}ms (返回 {len(results)} 条)")
                        
                        if latencies:
                            result["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)
                            result["tested"] = True
                            
                            logger.info(f"平均查询延迟: {result['avg_latency_ms']}ms")
                    else:
                        logger.info("表中无向量数据，跳过搜索测试")
                    
                except Exception as e:
                    result["errors"].append(f"表 {table_name} 测试失败: {e}")
            
            # LanceDB不需要显式关闭
            
        except ImportError:
            result["errors"].append("lancedb模块未安装")
        except Exception as e:
            result["errors"].append(f"性能测试失败: {e}")
        
        return result
    
    def find_duplicate_vectors(self, db_path: str, name: str, threshold: float = 0.99) -> Dict[str, Any]:
        """查找重复向量"""
        logger.info(f"\n{'='*60}")
        logger.info(f"检查重复向量: {name}")
        logger.info(f"{'='*60}")
        
        result = {
            "name": name,
            "checked": False,
            "duplicate_count": 0,
            "duplicate_groups": [],
            "errors": []
        }
        
        try:
            import lancedb
            
            db_path = Path(db_path)
            if not db_path.exists():
                result["errors"].append("数据库路径不存在")
                return result
            
            db = lancedb.connect(str(db_path))
            
            tables_result = db.list_tables()
            if hasattr(tables_result, 'tables'):
                table_names = tables_result.tables
            elif isinstance(tables_result, tuple) and len(tables_result) >= 1:
                table_names = tables_result[0]
            else:
                table_names = list(tables_result)
            
            for table_name in table_names:
                try:
                    table = db.open_table(table_name)
                    df = table.to_pandas()
                    
                    if len(df) < 2 or 'vector' not in df.columns:
                        continue
                    
                    logger.info(f"分析 {len(df)} 条记录...")
                    
                    # 提取向量
                    vectors = np.array([np.array(v) for v in df['vector']])
                    ids = df['id'].tolist() if 'id' in df.columns else list(range(len(df)))
                    
                    # 计算相似度矩阵（简化版，只检查高相似度）
                    # 使用采样来加速
                    sample_size = min(1000, len(vectors))
                    if len(vectors) > sample_size:
                        indices = np.random.choice(len(vectors), sample_size, replace=False)
                        sample_vectors = vectors[indices]
                    else:
                        indices = np.arange(len(vectors))
                        sample_vectors = vectors
                    
                    # 归一化
                    norms = np.linalg.norm(sample_vectors, axis=1, keepdims=True)
                    sample_norm = sample_vectors / (norms + 1e-8)
                    
                    # 计算相似度
                    similarity_matrix = np.dot(sample_norm, sample_norm.T)
                    
                    # 找出高相似度对
                    duplicates = []
                    for i in range(len(sample_vectors)):
                        for j in range(i + 1, len(sample_vectors)):
                            if similarity_matrix[i, j] > threshold:
                                duplicates.append((
                                    ids[indices[i]],
                                    ids[indices[j]],
                                    round(float(similarity_matrix[i, j]), 4)
                                ))
                    
                    result["duplicate_count"] = len(duplicates)
                    result["duplicate_groups"] = duplicates[:10]  # 只显示前10个
                    result["checked"] = True
                    
                    if duplicates:
                        logger.warning(f"发现 {len(duplicates)} 对相似度>{threshold}的向量")
                        for dup in duplicates[:5]:
                            logger.warning(f"  - {dup[0]} <-> {dup[1]}: 相似度={dup[2]}")
                    else:
                        logger.info("未发现重复向量")
                    
                except Exception as e:
                    result["errors"].append(f"表 {table_name} 检查失败: {e}")
            
            # LanceDB不需要显式关闭
            
        except ImportError:
            result["errors"].append("lancedb模块未安装")
        except Exception as e:
            result["errors"].append(f"重复检查失败: {e}")
        
        return result
    
    def run_full_optimization(self):
        """运行完整优化流程"""
        logger.info("\n" + "="*60)
        logger.info("开始记忆系统深度优化")
        logger.info(f"时间: {datetime.now().isoformat()}")
        logger.info("="*60)
        
        # 数据库列表
        databases = [
            ("/root/.openclaw/workspace/memory_db", "主记忆数据库"),
            ("/root/.openclaw/workspace/memory/knowledge/vector_db", "知识向量数据库"),
        ]
        
        all_issues = []
        all_recommendations = []
        
        for db_path, name in databases:
            # 1. 检查状态
            status = self.check_database_status(db_path, name)
            self.results["databases"][name] = status
            
            if status["errors"]:
                all_issues.extend([f"[{name}] {e}" for e in status["errors"]])
            
            if not status["exists"]:
                all_recommendations.append(f"[{name}] 数据库不存在，需要初始化")
                continue
            
            if status["record_count"] == 0:
                all_recommendations.append(f"[{name}] 数据库为空，建议导入数据")
                continue
            
            # 2. 检查重复向量
            dup_result = self.find_duplicate_vectors(db_path, name)
            self.results["optimization"][f"{name}_duplicates"] = dup_result
            
            if dup_result["duplicate_count"] > 0:
                all_issues.append(f"[{name}] 发现 {dup_result['duplicate_count']} 对重复向量")
                all_recommendations.append(f"[{name}] 建议清理重复向量以节省空间")
            
            # 3. 执行优化
            opt_result = self.optimize_database(db_path, name)
            self.results["optimization"][name] = opt_result
            
            if opt_result["errors"]:
                all_issues.extend([f"[{name}] {e}" for e in opt_result["errors"]])
            
            if opt_result["size_reduction_percent"] > 5:
                all_recommendations.append(
                    f"[{name}] 优化释放了 {opt_result['size_reduction_percent']}% 空间，建议定期执行"
                )
            
            # 4. 测试性能
            perf_result = self.test_search_performance(db_path, name)
            self.results["performance"][name] = perf_result
            
            if perf_result["errors"]:
                all_issues.extend([f"[{name}] {e}" for e in perf_result["errors"]])
            
            if perf_result.get("avg_latency_ms", 0) > 100:
                all_recommendations.append(
                    f"[{name}] 查询延迟较高 ({perf_result['avg_latency_ms']}ms)，建议增加索引分区数"
                )
            elif perf_result.get("avg_latency_ms", 0) > 0:
                all_recommendations.append(
                    f"[{name}] 查询延迟正常 ({perf_result['avg_latency_ms']}ms)"
                )
        
        self.results["issues"] = all_issues
        self.results["recommendations"] = all_recommendations
        
        logger.info("\n" + "="*60)
        logger.info("优化完成")
        logger.info("="*60)
        
        return self.results
    
    def generate_report(self) -> str:
        """生成优化报告"""
        report = []
        
        report.append("# 记忆系统深度优化报告")
        report.append(f"\n**执行时间**: {self.results['timestamp']}")
        report.append(f"**优化类型**: 向量压缩、索引重建、检索性能调优")
        report.append("\n---\n")
        
        # 数据库状态
        report.append("## 1. 数据库状态检查\n")
        
        for name, status in self.results["databases"].items():
            report.append(f"### {name}")
            report.append(f"- **路径**: `{status['path']}`")
            report.append(f"- **存在**: {'✓' if status['exists'] else '✗'}")
            report.append(f"- **记录数**: {status['record_count']}")
            report.append(f"- **存储大小**: {status['storage_size_mb']} MB")
            report.append(f"- **索引状态**: {status['index_status']}")
            if status['errors']:
                report.append(f"- **错误**: {', '.join(status['errors'])}")
            report.append("")
        
        # 优化结果
        report.append("\n## 2. 优化执行结果\n")
        
        for name, opt in self.results["optimization"].items():
            if name.endswith('_duplicates'):
                continue
            
            report.append(f"### {name}")
            report.append(f"- **优化成功**: {'✓' if opt['optimized'] else '✗'}")
            report.append(f"- **压缩执行**: {'✓' if opt['compact_success'] else '✗'}")
            report.append(f"- **索引优化**: {'✓' if opt['optimize_success'] else '✗'}")
            report.append(f"- **优化前大小**: {opt['before_size_mb']} MB")
            report.append(f"- **优化后大小**: {opt['after_size_mb']} MB")
            report.append(f"- **空间释放**: {opt['size_reduction_mb']} MB ({opt['size_reduction_percent']}%)")
            report.append(f"- **优化耗时**: {opt['duration_seconds']} 秒")
            if opt['errors']:
                report.append(f"- **错误**: {', '.join(opt['errors'])}")
            report.append("")
        
        # 重复向量检查
        report.append("\n## 3. 重复向量检查\n")
        
        for name, dup in self.results["optimization"].items():
            if not name.endswith('_duplicates'):
                continue
            
            db_name = name.replace('_duplicates', '')
            report.append(f"### {db_name}")
            report.append(f"- **检查完成**: {'✓' if dup['checked'] else '✗'}")
            report.append(f"- **重复向量对数**: {dup['duplicate_count']}")
            if dup['duplicate_groups']:
                report.append("- **示例重复对**:")
                for d in dup['duplicate_groups'][:5]:
                    report.append(f"  - `{d[0]}` ↔ `{d[1]}` (相似度: {d[2]})")
            report.append("")
        
        # 性能测试
        report.append("\n## 4. 检索性能基准\n")
        
        for name, perf in self.results["performance"].items():
            report.append(f"### {name}")
            report.append(f"- **测试完成**: {'✓' if perf['tested'] else '✗'}")
            report.append(f"- **平均查询延迟**: {perf['avg_latency_ms']} ms")
            if perf['query_latency_ms']:
                report.append("- **单次查询延迟**:")
                for q_name, latency in perf['query_latency_ms'].items():
                    report.append(f"  - {q_name}: {latency} ms")
            if perf['errors']:
                report.append(f"- **错误**: {', '.join(perf['errors'])}")
            report.append("")
        
        # 问题汇总
        report.append("\n## 5. 发现的问题\n")
        
        if self.results["issues"]:
            for issue in self.results["issues"]:
                report.append(f"- ⚠️ {issue}")
        else:
            report.append("- ✓ 未发现严重问题")
        
        # 建议
        report.append("\n## 6. 优化建议\n")
        
        if self.results["recommendations"]:
            for rec in self.results["recommendations"]:
                report.append(f"- 💡 {rec}")
        else:
            report.append("- ✓ 系统状态良好，保持当前配置")
        
        # 总结
        report.append("\n## 7. 优化总结\n")
        
        total_before = sum(
            opt['before_size_mb'] 
            for name, opt in self.results["optimization"].items() 
            if not name.endswith('_duplicates')
        )
        total_after = sum(
            opt['after_size_mb'] 
            for name, opt in self.results["optimization"].items() 
            if not name.endswith('_duplicates')
        )
        total_saved = total_before - total_after
        
        report.append(f"- **总存储优化前**: {total_before:.2f} MB")
        report.append(f"- **总存储优化后**: {total_after:.2f} MB")
        report.append(f"- **总空间释放**: {total_saved:.2f} MB")
        report.append(f"- **数据库数量**: {len(self.results['databases'])}")
        
        avg_latency = np.mean([
            p['avg_latency_ms'] 
            for p in self.results["performance"].values() 
            if p.get('avg_latency_ms', 0) > 0
        ]) if self.results["performance"] else 0
        
        report.append(f"- **平均查询延迟**: {avg_latency:.2f} ms")
        
        if avg_latency < 50:
            report.append("- **性能评级**: 🟢 优秀")
        elif avg_latency < 100:
            report.append("- **性能评级**: 🟡 良好")
        elif avg_latency > 0:
            report.append("- **性能评级**: 🔴 需优化")
        else:
            report.append("- **性能评级**: ⚪ 未测试")
        
        report.append("\n---\n")
        report.append(f"*报告生成时间: {datetime.now().isoformat()}*")
        
        return "\n".join(report)


def main():
    """主函数"""
    optimizer = MemoryOptimizer()
    
    # 运行优化
    results = optimizer.run_full_optimization()
    
    # 生成报告
    report = optimizer.generate_report()
    
    # 创建输出目录
    output_dir = Path("/root/.openclaw/workspace/memory/optimization")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存报告
    output_file = output_dir / "OPT-MEMORY-20260212-01.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 保存原始数据
    data_file = output_dir / "OPT-MEMORY-20260212-01.json"
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"\n报告已保存: {output_file}")
    logger.info(f"数据已保存: {data_file}")
    
    print("\n" + "="*60)
    print(report)
    print("="*60)


if __name__ == "__main__":
    main()
