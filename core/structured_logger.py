#!/usr/bin/env python3
"""
结构化日志系统 - Structured Logging System
来自 @QenAI 的洞察: "What file systems taught me about agent reliability"

功能:
1. 类似数据库事务日志的结构化存储
2. 支持崩溃恢复机制
3. 一致性检查
4. 检查点(Checkpoint)机制
5. 日志轮转和归档
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from contextlib import contextmanager
import time

WORKSPACE = Path("/root/.openclaw/workspace")
LOGS_DIR = WORKSPACE / "logs"
STRUCTURED_LOG_DIR = LOGS_DIR / "structured"
TRANSACTION_LOG = STRUCTURED_LOG_DIR / "transactions.logl"
CHECKPOINT_DIR = STRUCTURED_LOG_DIR / "checkpoints"
WAL_FILE = STRUCTURED_LOG_DIR / "wal.logl"  # Write-Ahead Log


class LogType(Enum):
    """日志类型"""
    TRANSACTION = "transaction"  # 事务开始/提交/回滚
    ACTION = "action"           # 操作记录
    CHECKPOINT = "checkpoint"   # 检查点
    RECOVERY = "recovery"       # 恢复记录


class TransactionStatus(Enum):
    """事务状态"""
    BEGIN = "begin"
    COMMIT = "commit"
    ROLLBACK = "rollback"


@dataclass
class LogEntry:
    """日志条目"""
    entry_id: str  # 唯一标识符
    timestamp: str
    log_type: str  # LogType.value
    data: Dict[str, Any]
    
    # 事务相关字段
    transaction_id: Optional[str] = None
    sequence: Optional[int] = None  # 序列号（在事务内）
    
    # 校验字段
    checksum: Optional[str] = None
    
    def compute_checksum(self) -> str:
        """计算校验和"""
        data_str = json.dumps(self.data, sort_keys=True, ensure_ascii=False)
        combined = f"{self.entry_id}{self.timestamp}{self.log_type}{data_str}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        if result['log_type'] is not None and hasattr(result['log_type'], 'value'):
            result['log_type'] = result['log_type'].value
        return result
    
    def to_json_line(self) -> str:
        """转换为 JSONL 行"""
        data = self.to_dict()
        self_checksum = self.compute_checksum()
        data['checksum'] = self_checksum
        return json.dumps(data, ensure_ascii=False)


@dataclass
class Checkpoint:
    """检查点"""
    checkpoint_id: str
    timestamp: str
    state: Dict[str, Any]  # 系统状态快照
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class StructuredLogger:
    """结构化日志管理器"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or STRUCTURED_LOG_DIR
        self.transaction_log = self.log_dir / "transactions.logl"
        self.wal_file = self.log_dir / "wal.logl"
        self.checkpoint_dir = self.log_dir / "checkpoints"
        
        # 创建目录
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # 事务计数器
        self._transaction_counter = 0
        self._current_transaction: Optional[str] = None
        self._transaction_sequence = 0
    
    @contextmanager
    def transaction(self, transaction_id: Optional[str] = None):
        """
        事务上下文管理器
        
        用法:
            with logger.transaction("tx-001") as tx_id:
                logger.log_action(tx_id, "step1", data)
                logger.log_action(tx_id, "step2", data)
                # 自动提交
        """
        if transaction_id is None:
            self._transaction_counter += 1
            transaction_id = f"tx-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{self._transaction_counter}"
        
        self._current_transaction = transaction_id
        self._transaction_sequence = 0
        
        # 记录事务开始
        self._write_log(
            LogType.TRANSACTION,
            {"status": TransactionStatus.BEGIN.value},
            transaction_id=transaction_id
        )
        
        try:
            yield transaction_id
            
            # 提交事务
            self._write_log(
                LogType.TRANSACTION,
                {"status": TransactionStatus.COMMIT.value},
                transaction_id=transaction_id
            )
        
        except Exception as e:
            # 回滚事务
            self._write_log(
                LogType.TRANSACTION,
                {
                    "status": TransactionStatus.ROLLBACK.value,
                    "error": str(e)
                },
                transaction_id=transaction_id
            )
            raise
        
        finally:
            self._current_transaction = None
    
    def log_action(self, 
                  action_type: str, 
                  data: Dict[str, Any],
                  transaction_id: Optional[str] = None):
        """
        记录操作
        
        Args:
            action_type: 操作类型
            data: 操作数据
            transaction_id: 事务ID（可选）
        """
        entry_data = {
            "action_type": action_type,
            **data
        }
        
        self._write_log(
            LogType.ACTION,
            entry_data,
            transaction_id=transaction_id or self._current_transaction
        )
    
    def checkpoint(self, state: Dict[str, Any], checkpoint_id: Optional[str] = None):
        """
        创建检查点
        
        Args:
            state: 系统状态快照
            checkpoint_id: 检查点ID（可选）
        """
        if checkpoint_id is None:
            checkpoint_id = f"cp-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now().isoformat(),
            state=state,
            metadata={"created_by": "structured_logger"}
        )
        
        # 保存检查点
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)
        
        # 记录检查点日志
        self._write_log(
            LogType.CHECKPOINT,
            {"checkpoint_id": checkpoint_id},
            transaction_id=self._current_transaction
        )
        
        return checkpoint_id
    
    def _write_log(self,
                   log_type: LogType,
                   data: Dict[str, Any],
                   transaction_id: Optional[str] = None):
        """写入日志"""
        sequence = None
        if transaction_id:
            self._transaction_sequence += 1
            sequence = self._transaction_sequence
        
        entry = LogEntry(
            entry_id=f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now().isoformat(),
            log_type=log_type,
            data=data,
            transaction_id=transaction_id,
            sequence=sequence
        )
        
        # 先写入 WAL（Write-Ahead Log）
        with open(self.wal_file, 'a', encoding='utf-8') as f:
            f.write(entry.to_json_line() + '\n')
        
        # 同步 WAL
        os.fsync(self.wal_file.fileno())
        
        # 然后写入主日志
        with open(self.transaction_log, 'a', encoding='utf-8') as f:
            f.write(entry.to_json_line() + '\n')
    
    def recover(self) -> Dict[str, Any]:
        """
        从 WAL 恢复
        
        Returns:
            恢复的结果和统计
        """
        if not self.wal_file.exists():
            return {"status": "no_wal", "recovered": 0}
        
        recovered = 0
        incomplete_transactions = set()
        
        # 读取 WAL
        with open(self.wal_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        entry_data = json.loads(line)
                        log_type = entry_data.get('log_type')
                        
                        if log_type == LogType.TRANSACTION.value:
                            status = entry_data.get('data', {}).get('status')
                            tx_id = entry_data.get('transaction_id')
                            
                            if status == TransactionStatus.BEGIN.value:
                                incomplete_transactions.add(tx_id)
                            elif status in [TransactionStatus.COMMIT.value, TransactionStatus.ROLLBACK.value]:
                                incomplete_transactions.discard(tx_id)
                        
                        recovered += 1
                    except Exception:
                        pass  # 忽略损坏的行
        
        # 清空 WAL
        self.wal_file.write_text("")
        
        return {
            "status": "recovered",
            "recovered": recovered,
            "incomplete_transactions": list(incomplete_transactions)
        }
    
    def verify_consistency(self) -> Dict[str, Any]:
        """
        验证日志一致性
        
        Returns:
            一致性报告
        """
        if not self.transaction_log.exists():
            return {"status": "no_logs", "consistent": True}
        
        issues = []
        transaction_states = {}  # transaction_id -> status
        
        # 读取日志
        with open(self.transaction_log, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    entry_data = json.loads(line)
                    log_type = entry_data.get('log_type')
                    
                    # 验证校验和
                    stored_checksum = entry_data.pop('checksum', None)
                    recomputed = LogEntry(**entry_data).compute_checksum()
                    if stored_checksum and stored_checksum != recomputed:
                        issues.append({
                            "line": line_num,
                            "entry_id": entry_data.get('entry_id'),
                            "issue": "checksum_mismatch",
                            "stored": stored_checksum,
                            "computed": recomputed
                        })
                    
                    # 验证事务完整性
                    if log_type == LogType.TRANSACTION.value:
                        tx_id = entry_data.get('transaction_id')
                        status = entry_data.get('data', {}).get('status')
                        
                        if tx_id:
                            current_status = transaction_states.get(tx_id)
                            
                            if status == TransactionStatus.BEGIN.value:
                                if current_status is not None:
                                    issues.append({
                                        "line": line_num,
                                        "transaction_id": tx_id,
                                        "issue": "transaction_already_open",
                                        "current_state": current_status
                                    })
                                transaction_states[tx_id] = TransactionStatus.BEGIN.value
                            
                            elif status in [TransactionStatus.COMMIT.value, TransactionStatus.ROLLBACK.value]:
                                if transaction_states.get(tx_id) != TransactionStatus.BEGIN.value:
                                    issues.append({
                                        "line": line_num,
                                        "transaction_id": tx_id,
                                        "issue": "transaction_not_open",
                                        "current_state": transaction_states.get(tx_id)
                                    })
                                transaction_states[tx_id] = status
                
                except Exception as e:
                    issues.append({
                        "line": line_num,
                        "issue": "parse_error",
                        "error": str(e)
                    })
        
        # 检查未完成的事务
        for tx_id, state in transaction_states.items():
            if state == TransactionStatus.BEGIN.value:
                issues.append({
                    "transaction_id": tx_id,
                    "issue": "incomplete_transaction"
                })
        
        return {
            "status": "verified",
            "consistent": len(issues) == 0,
            "issues": issues,
            "transaction_count": len(transaction_states)
        }
    
    def get_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的事务"""
        if not self.transaction_log.exists():
            return []
        
        transactions = {}
        
        # 反向读取，获取最近的事务
        with open(self.transaction_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in reversed(lines):
            if not line.strip():
                continue
            
            try:
                entry_data = json.loads(line)
                if entry_data.get('log_type') == LogType.TRANSACTION.value:
                    tx_id = entry_data.get('transaction_id')
                    if tx_id and tx_id not in transactions:
                        transactions[tx_id] = entry_data
                        if len(transactions) >= limit:
                            break
            except Exception:
                pass
        
        return list(transactions.values())


# 全局实例
_structured_logger = None

def get_structured_logger() -> StructuredLogger:
    """获取全局结构化日志管理器"""
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger()
    return _structured_logger


# 示例用法
if __name__ == "__main__":
    logger = get_structured_logger()
    
    print("演示事务处理...")
    
    # 使用事务上下文管理器
    with logger.transaction("demo-tx-001") as tx_id:
        logger.log_action("read_file", {"file": "MEMORY.md"})
        logger.log_action("process_data", {"records": 100})
        logger.log_action("write_result", {"output": "result.txt"})
    
    # 创建检查点
    checkpoint_id = logger.checkpoint({"files_processed": 5, "status": "success"})
    print(f"检查点已创建: {checkpoint_id}")
    
    # 验证一致性
    report = logger.verify_consistency()
    print(f"\n一致性验证: {report}")
    
    # 获取最近的事务
    transactions = logger.get_transactions(5)
    print(f"\n最近的事务 ({len(transactions)} 个):")
    for tx in transactions:
        print(f"  - {tx.get('transaction_id')}: {tx.get('data', {}).get('status')}")
