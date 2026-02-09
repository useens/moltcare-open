#!/usr/bin/env python3
"""
Whisper Transcription Queue Manager
支持并发请求、模型缓存、错误重试的队列管理系统
"""

import asyncio
import hashlib
import json
import logging
import os
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from functools import lru_cache
import threading

warnings.filterwarnings("ignore")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("whisper-queue")


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class TranscriptionTask:
    """转录任务"""
    task_id: str
    audio_file: str
    model: str = "base"
    language: Optional[str] = None
    timestamps: bool = False
    as_json: bool = False
    priority: int = 5  # 1-10, 数字越小优先级越高
    max_retries: int = 3
    retry_count: int = 0
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    callback: Optional[Callable] = None

    @property
    def duration(self) -> float:
        """获取任务持续时间"""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        if self.started_at:
            return time.time() - self.started_at
        return 0.0


class ModelCache:
    """
    模型缓存管理器
    使用LRU缓存避免重复加载模型，支持多模型同时缓存
    """
    
    def __init__(self, max_models: int = 2, device: str = "cpu"):
        self.max_models = max_models
        self.device = device
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._last_used: Dict[str, float] = {}
        self._load_count: Dict[str, int] = {}
        
    def get_model(self, model_name: str) -> Any:
        """获取模型，如果不存在则加载"""
        with self._lock:
            if model_name in self._cache:
                self._last_used[model_name] = time.time()
                logger.debug(f"Model '{model_name}' loaded from cache")
                return self._cache[model_name]
            
            # 如果缓存已满，移除最久未使用的模型
            if len(self._cache) >= self.max_models:
                self._evict_lru()
            
            # 加载新模型
            logger.info(f"Loading model: {model_name}...")
            start_time = time.time()
            
            try:
                import whisper
                model = whisper.load_model(model_name, device=self.device)
                self._cache[model_name] = model
                self._last_used[model_name] = time.time()
                self._load_count[model_name] = self._load_count.get(model_name, 0) + 1
                
                load_time = time.time() - start_time
                logger.info(f"Model '{model_name}' loaded in {load_time:.2f}s (cache size: {len(self._cache)})")
                return model
                
            except Exception as e:
                logger.error(f"Failed to load model '{model_name}': {e}")
                raise
    
    def _evict_lru(self):
        """移除最久未使用的模型"""
        if not self._last_used:
            return
        
        lru_model = min(self._last_used, key=self._last_used.get)
        logger.info(f"Evicting model from cache: {lru_model}")
        del self._cache[lru_model]
        del self._last_used[lru_model]
    
    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            logger.info(f"Clearing model cache ({len(self._cache)} models)")
            self._cache.clear()
            self._last_used.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            return {
                "cached_models": list(self._cache.keys()),
                "cache_size": len(self._cache),
                "max_models": self.max_models,
                "load_counts": self._load_count.copy()
            }


class TranscriptionQueue:
    """
    转录队列管理器
    支持优先级队列、并发处理、错误重试
    """
    
    def __init__(
        self,
        max_workers: int = 2,
        max_models: int = 2,
        device: str = "cpu",
        default_model: str = "base"
    ):
        self.max_workers = max_workers
        self.device = device
        self.default_model = default_model
        
        # 模型缓存
        self.model_cache = ModelCache(max_models=max_models, device=device)
        
        # 任务队列
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: Dict[str, TranscriptionTask] = {}
        self._task_lock = asyncio.Lock()
        
        # 执行器
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._semaphore = asyncio.Semaphore(max_workers)
        
        # 运行状态
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        
        # 统计
        self._stats = {
            "total_processed": 0,
            "total_failed": 0,
            "total_retried": 0,
            "start_time": None
        }
        
        logger.info(f"TranscriptionQueue initialized (workers={max_workers}, max_models={max_models})")
    
    def generate_task_id(self, audio_file: str) -> str:
        """生成任务ID"""
        content = f"{audio_file}:{time.time()}:{os.urandom(8).hex()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def submit(
        self,
        audio_file: str,
        model: Optional[str] = None,
        language: Optional[str] = None,
        timestamps: bool = False,
        as_json: bool = False,
        priority: int = 5,
        max_retries: int = 3,
        callback: Optional[Callable] = None
    ) -> str:
        """提交转录任务"""
        task_id = self.generate_task_id(audio_file)
        
        task = TranscriptionTask(
            task_id=task_id,
            audio_file=audio_file,
            model=model or self.default_model,
            language=language,
            timestamps=timestamps,
            as_json=as_json,
            priority=priority,
            max_retries=max_retries,
            callback=callback
        )
        
        async with self._task_lock:
            self._tasks[task_id] = task
        
        # 优先级队列: (优先级, 创建时间, 任务ID, 任务)
        await self._queue.put((priority, task.created_at, task_id, task))
        
        logger.info(f"Task {task_id} submitted (priority={priority}, model={task.model})")
        
        # 如果队列未运行，自动启动
        if not self._running:
            await self.start()
        
        return task_id
    
    async def start(self):
        """启动队列处理"""
        if self._running:
            return
        
        self._running = True
        self._stats["start_time"] = time.time()
        self._worker_task = asyncio.create_task(self._process_queue())
        logger.info("Queue processing started")
    
    async def stop(self):
        """停止队列处理"""
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        self._executor.shutdown(wait=True)
        logger.info("Queue processing stopped")
    
    async def _process_queue(self):
        """处理队列的主循环"""
        while self._running:
            try:
                # 使用超时以便检查_running状态
                priority, created_at, task_id, task = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
                
                # 使用信号量限制并发
                async with self._semaphore:
                    await self._process_task(task)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
    
    async def _process_task(self, task: TranscriptionTask):
        """处理单个任务"""
        task.status = TaskStatus.PROCESSING
        task.started_at = time.time()
        
        logger.info(f"Processing task {task.task_id} (model={task.model})")
        
        try:
            # 在线程池中执行转录（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._transcribe_sync,
                task
            )
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            self._stats["total_processed"] += 1
            
            logger.info(f"Task {task.task_id} completed in {task.duration:.2f}s")
            
            # 调用回调
            if task.callback:
                try:
                    if asyncio.iscoroutinefunction(task.callback):
                        await task.callback(task)
                    else:
                        task.callback(task)
                except Exception as e:
                    logger.error(f"Callback error for task {task.task_id}: {e}")
            
        except Exception as e:
            await self._handle_task_error(task, str(e))
    
    def _transcribe_sync(self, task: TranscriptionTask) -> Dict[str, Any]:
        """同步执行转录（在线程池中运行）"""
        # 获取缓存的模型
        model = self.model_cache.get_model(task.model)
        
        # 执行转录
        result = model.transcribe(
            task.audio_file,
            language=task.language,
            word_timestamps=task.timestamps,
            verbose=False
        )
        
        # 格式化结果
        output = {
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "task_id": task.task_id
        }
        
        if task.timestamps and "segments" in result:
            output["segments"] = [
                {
                    "start": s["start"],
                    "end": s["end"],
                    "text": s["text"],
                    **({"words": s["words"]} if "words" in s else {})
                }
                for s in result["segments"]
            ]
        
        return output
    
    async def _handle_task_error(self, task: TranscriptionTask, error: str):
        """处理任务错误，支持重试"""
        task.error = error
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # 重试任务
            task.status = TaskStatus.RETRYING
            self._stats["total_retried"] += 1
            
            # 指数退避
            delay = min(2 ** task.retry_count, 30)  # 最大30秒
            logger.warning(
                f"Task {task.task_id} failed (attempt {task.retry_count}), "
                f"retrying in {delay}s: {error}"
            )
            
            await asyncio.sleep(delay)
            
            # 重新提交到队列（降低优先级）
            task.status = TaskStatus.PENDING
            await self._queue.put((task.priority + 1, time.time(), task.task_id, task))
        else:
            # 重试次数用尽
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            self._stats["total_failed"] += 1
            
            logger.error(f"Task {task.task_id} failed after {task.retry_count} retries: {error}")
            
            # 调用回调（即使失败）
            if task.callback:
                try:
                    if asyncio.iscoroutinefunction(task.callback):
                        await task.callback(task)
                    else:
                        task.callback(task)
                except Exception as e:
                    logger.error(f"Error callback error for task {task.task_id}: {e}")
    
    async def get_task(self, task_id: str) -> Optional[TranscriptionTask]:
        """获取任务状态"""
        async with self._task_lock:
            return self._tasks.get(task_id)
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[TranscriptionTask]:
        """等待任务完成"""
        start_time = time.time()
        
        while True:
            task = await self.get_task(task_id)
            if not task:
                return None
            
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                return task
            
            if timeout and (time.time() - start_time) > timeout:
                return None
            
            await asyncio.sleep(0.1)
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        async with self._task_lock:
            status_counts = {}
            for task in self._tasks.values():
                status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1
            
            return {
                **self._stats,
                "running": self._running,
                "queue_size": self._queue.qsize(),
                "total_tasks": len(self._tasks),
                "status_counts": status_counts,
                "model_cache": self.model_cache.get_stats(),
                "uptime": time.time() - self._stats["start_time"] if self._stats["start_time"] else 0
            }
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消待处理的任务"""
        async with self._task_lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.FAILED
                task.error = "Cancelled by user"
                return True
            return False
    
    async def clear_completed(self):
        """清理已完成的任务"""
        async with self._task_lock:
            to_remove = [
                task_id for task_id, task in self._tasks.items()
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            ]
            for task_id in to_remove:
                del self._tasks[task_id]
            logger.info(f"Cleared {len(to_remove)} completed tasks")
            return len(to_remove)


# 全局队列实例（单例模式）
_queue_instance: Optional[TranscriptionQueue] = None
_queue_lock = asyncio.Lock()


async def get_queue(
    max_workers: int = 2,
    max_models: int = 2,
    device: str = "cpu"
) -> TranscriptionQueue:
    """获取全局队列实例"""
    global _queue_instance
    
    if _queue_instance is None:
        async with _queue_lock:
            if _queue_instance is None:
                _queue_instance = TranscriptionQueue(
                    max_workers=max_workers,
                    max_models=max_models,
                    device=device
                )
    
    return _queue_instance


def reset_queue():
    """重置全局队列实例（主要用于测试）"""
    global _queue_instance
    _queue_instance = None


if __name__ == "__main__":
    # 简单测试
    async def test():
        queue = await get_queue(max_workers=2, max_models=2)
        await queue.start()
        
        # 提交测试任务
        task_id = await queue.submit(
            audio_file="test.wav",
            model="base",
            priority=1
        )
        
        print(f"Submitted task: {task_id}")
        
        # 等待一段时间
        await asyncio.sleep(2)
        
        stats = await queue.get_stats()
        print(f"Stats: {json.dumps(stats, indent=2)}")
        
        await queue.stop()
    
    asyncio.run(test())
