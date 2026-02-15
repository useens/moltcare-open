#!/usr/bin/env python3
"""
Predictive Monitor v5.0
预测性故障检测模块

功能：
1. 基于趋势预测磁盘满、内存不足
2. 预测GitHub同步延迟问题
3. 预测API限流风险
4. 资源趋势分析和预警
"""

import json
import time
import asyncio
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from collections import deque
from pathlib import Path
import logging
import math

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/predictive_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PredictiveMonitor')


@dataclass
class PredictionResult:
    """预测结果数据类"""
    timestamp: str
    metric_name: str
    current_value: float
    predicted_value: float
    prediction_time: datetime  # 预测时间点
    confidence: float  # 预测置信度 0-1
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    time_to_threshold: Optional[float]  # 到达阈值的时间（小时）
    recommendation: str


@dataclass
class TrendData:
    """趋势数据类"""
    timestamps: List[datetime]
    values: List[float]
    slope: float  # 趋势线斜率
    intercept: float  # 截距
    r_squared: float  # R²拟合度
    trend_direction: str  # 'increasing', 'decreasing', 'stable'


class LinearRegressionPredictor:
    """线性回归预测器"""
    
    def __init__(self, min_data_points: int = 10):
        self.min_data_points = min_data_points
    
    def fit(self, timestamps: List[datetime], values: List[float]) -> TrendData:
        """拟合趋势线"""
        n = len(values)
        if n < self.min_data_points:
            raise ValueError(f"Need at least {self.min_data_points} data points")
        
        # 将时间转换为小时（相对于第一个点）
        base_time = timestamps[0]
        x = [(t - base_time).total_seconds() / 3600 for t in timestamps]
        
        # 计算均值
        mean_x = sum(x) / n
        mean_y = sum(values) / n
        
        # 计算斜率和截距
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, values))
        denominator = sum((xi - mean_x) ** 2 for xi in x)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = mean_y - slope * mean_x
        
        # 计算R²
        ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, values))
        ss_tot = sum((yi - mean_y) ** 2 for yi in values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # 确定趋势方向
        if slope > 0.01:
            trend_direction = 'increasing'
        elif slope < -0.01:
            trend_direction = 'decreasing'
        else:
            trend_direction = 'stable'
        
        return TrendData(
            timestamps=timestamps,
            values=values,
            slope=slope,
            intercept=intercept,
            r_squared=r_squared,
            trend_direction=trend_direction
        )
    
    def predict(self, trend: TrendData, hours_ahead: float) -> Tuple[float, float]:
        """
        预测未来值
        
        Returns:
            Tuple[预测值, 置信度]
        """
        # 基于趋势线的预测
        last_x = (trend.timestamps[-1] - trend.timestamps[0]).total_seconds() / 3600
        future_x = last_x + hours_ahead
        predicted_value = trend.slope * future_x + trend.intercept
        
        # 置信度基于R²和预测时间距离
        base_confidence = max(0, min(1, trend.r_squared))
        time_decay = math.exp(-hours_ahead / 24)  # 24小时后置信度大幅下降
        confidence = base_confidence * time_decay
        
        return predicted_value, confidence
    
    def predict_crossing(self, trend: TrendData, threshold: float) -> Optional[float]:
        """
        预测何时会超过阈值
        
        Returns:
            到达阈值的小时数，如果不会到达则返回None
        """
        if trend.slope <= 0:
            return None
        
        last_x = (trend.timestamps[-1] - trend.timestamps[0]).total_seconds() / 3600
        last_value = trend.values[-1]
        
        # 计算还需增加多少
        remaining = threshold - last_value
        if remaining <= 0:
            return 0
        
        # 计算时间
        hours_needed = remaining / trend.slope
        return hours_needed if hours_needed > 0 else None


class DiskSpacePredictor:
    """磁盘空间预测器"""
    
    def __init__(self, history_size: int = 168):  # 7天，每小时一个点
        self.history: deque = deque(maxlen=history_size)
        self.predictor = LinearRegressionPredictor(min_data_points=6)
        self.thresholds = {
            'warning': 80,  # 80%使用率警告
            'critical': 90,  # 90%使用率危险
            'full': 95  # 95%使用率几乎满
        }
    
    def record(self, path: str = '/'):
        """记录磁盘使用情况"""
        try:
            usage = psutil.disk_usage(path)
            percent_used = usage.percent
            
            self.history.append({
                'timestamp': datetime.now(),
                'path': path,
                'percent_used': percent_used,
                'free_gb': usage.free / (1024**3),
                'total_gb': usage.total / (1024**3)
            })
        except Exception as e:
            logger.error(f"Failed to record disk usage: {e}")
    
    def predict(self, path: str = '/') -> Optional[PredictionResult]:
        """预测磁盘空间"""
        if len(self.history) < self.predictor.min_data_points:
            return None
        
        # 筛选特定路径的数据
        path_data = [h for h in self.history if h['path'] == path]
        if len(path_data) < self.predictor.min_data_points:
            return None
        
        timestamps = [h['timestamp'] for h in path_data]
        values = [h['percent_used'] for h in path_data]
        
        try:
            trend = self.predictor.fit(timestamps, values)
            current_value = values[-1]
            
            # 预测24小时后
            predicted_value, confidence = self.predictor.predict(trend, 24)
            
            # 确定风险等级
            risk_level = self._assess_risk(current_value, predicted_value)
            
            # 计算到达阈值的时间
            time_to_critical = self.predictor.predict_crossing(trend, self.thresholds['critical'])
            
            # 生成建议
            recommendation = self._generate_recommendation(
                current_value, predicted_value, time_to_critical, trend.trend_direction
            )
            
            return PredictionResult(
                timestamp=datetime.now().isoformat(),
                metric_name=f'disk_usage_{path}',
                current_value=round(current_value, 2),
                predicted_value=round(predicted_value, 2),
                prediction_time=datetime.now() + timedelta(hours=24),
                confidence=round(confidence, 3),
                risk_level=risk_level,
                time_to_threshold=round(time_to_critical, 2) if time_to_critical else None,
                recommendation=recommendation
            )
        except Exception as e:
            logger.error(f"Failed to predict disk usage: {e}")
            return None
    
    def _assess_risk(self, current: float, predicted: float) -> str:
        """评估风险等级"""
        if predicted >= self.thresholds['full'] or current >= self.thresholds['critical']:
            return 'critical'
        elif predicted >= self.thresholds['critical'] or current >= self.thresholds['warning']:
            return 'high'
        elif predicted >= self.thresholds['warning']:
            return 'medium'
        return 'low'
    
    def _generate_recommendation(self, current: float, predicted: float,
                                  time_to_critical: Optional[float],
                                  trend: str) -> str:
        """生成建议"""
        if current >= self.thresholds['critical']:
            return f"磁盘空间严重不足！当前{current:.1f}%，请立即清理"
        
        if time_to_critical and time_to_critical < 24:
            return f"预计{time_to_critical:.1f}小时后磁盘将达到临界状态，建议立即清理"
        
        if time_to_critical and time_to_critical < 72:
            return f"预计{time_to_critical:.1f}小时后磁盘空间将不足，建议规划清理"
        
        if predicted > self.thresholds['warning']:
            return f"磁盘使用率呈{trend}趋势，建议关注空间使用情况"
        
        return "磁盘空间充足，保持监控"
    
    def get_cleanup_candidates(self) -> List[Dict]:
        """获取可清理的文件候选"""
        candidates = []
        
        # 常见大文件目录
        cleanup_paths = [
            '/tmp',
            '/var/log',
            '/var/cache',
            str(Path.home() / '.cache'),
            str(Path.home() / 'logs'),
        ]
        
        for path_str in cleanup_paths:
            path = Path(path_str)
            if path.exists():
                try:
                    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    candidates.append({
                        'path': str(path),
                        'size_gb': round(total_size / (1024**3), 2)
                    })
                except Exception as e:
                    logger.warning(f"Cannot scan {path}: {e}")
        
        return sorted(candidates, key=lambda x: x['size_gb'], reverse=True)[:5]


class MemoryPredictor:
    """内存使用预测器"""
    
    def __init__(self, history_size: int = 168):
        self.history: deque = deque(maxlen=history_size)
        self.predictor = LinearRegressionPredictor(min_data_points=6)
        self.thresholds = {
            'warning': 75,
            'critical': 85,
            'oom': 95  # 可能触发OOM
        }
        self.process_history: Dict[int, deque] = {}  # 进程内存历史
    
    def record(self):
        """记录内存使用情况"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # 记录系统内存
            self.history.append({
                'timestamp': datetime.now(),
                'percent_used': mem.percent,
                'available_gb': mem.available / (1024**3),
                'swap_percent': swap.percent,
                'top_processes': self._get_top_memory_processes(5)
            })
            
            # 记录各进程内存
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    pid = proc.info['pid']
                    if pid not in self.process_history:
                        self.process_history[pid] = deque(maxlen=48)  # 2天
                    
                    self.process_history[pid].append({
                        'timestamp': datetime.now(),
                        'memory_percent': proc.info['memory_percent'] or 0,
                        'name': proc.info['name']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.error(f"Failed to record memory usage: {e}")
    
    def _get_top_memory_processes(self, n: int) -> List[Dict]:
        """获取内存使用最多的进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
            try:
                info = proc.info
                if info['memory_percent'] > 0.1:  # 只关注使用超过0.1%的进程
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'memory_percent': round(info['memory_percent'], 2),
                        'memory_mb': round(info['memory_info'].rss / (1024**2), 2)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:n]
    
    def predict(self) -> Optional[PredictionResult]:
        """预测内存使用情况"""
        if len(self.history) < self.predictor.min_data_points:
            return None
        
        timestamps = [h['timestamp'] for h in self.history]
        values = [h['percent_used'] for h in self.history]
        
        try:
            trend = self.predictor.fit(timestamps, values)
            current_value = values[-1]
            
            # 预测12小时后（内存变化更快）
            predicted_value, confidence = self.predictor.predict(trend, 12)
            
            # 考虑内存泄漏检测
            leak_detected, leak_processes = self._detect_memory_leak()
            if leak_detected:
                confidence *= 0.8  # 有内存泄漏时降低置信度
            
            # 确定风险等级
            risk_level = self._assess_risk(current_value, predicted_value, leak_detected)
            
            # 计算到达阈值的时间
            time_to_critical = self.predictor.predict_crossing(trend, self.thresholds['critical'])
            
            # 生成建议
            recommendation = self._generate_recommendation(
                current_value, predicted_value, time_to_critical,
                leak_detected, leak_processes
            )
            
            return PredictionResult(
                timestamp=datetime.now().isoformat(),
                metric_name='memory_usage',
                current_value=round(current_value, 2),
                predicted_value=round(predicted_value, 2),
                prediction_time=datetime.now() + timedelta(hours=12),
                confidence=round(confidence, 3),
                risk_level=risk_level,
                time_to_threshold=round(time_to_critical, 2) if time_to_critical else None,
                recommendation=recommendation
            )
        except Exception as e:
            logger.error(f"Failed to predict memory usage: {e}")
            return None
    
    def _detect_memory_leak(self) -> Tuple[bool, List[Dict]]:
        """检测内存泄漏"""
        suspicious_processes = []
        
        for pid, history in self.process_history.items():
            if len(history) < 12:  # 至少需要12个点
                continue
            
            values = [h['memory_percent'] for h in history]
            timestamps = [h['timestamp'] for h in history]
            
            try:
                trend = self.predictor.fit(timestamps, values)
                
                # 如果斜率显著为正且R²较高，可能存在内存泄漏
                if trend.slope > 0.05 and trend.r_squared > 0.7:
                    # 内存持续增长
                    growth_rate = (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
                    if growth_rate > 0.5:  # 增长超过50%
                        suspicious_processes.append({
                            'pid': pid,
                            'name': history[-1]['name'],
                            'growth_rate': round(growth_rate, 2),
                            'current_memory_percent': round(values[-1], 2)
                        })
            except:
                continue
        
        return len(suspicious_processes) > 0, suspicious_processes
    
    def _assess_risk(self, current: float, predicted: float, leak_detected: bool) -> str:
        """评估风险等级"""
        if current >= self.thresholds['oom'] or (predicted >= self.thresholds['oom'] and leak_detected):
            return 'critical'
        elif current >= self.thresholds['critical'] or predicted >= self.thresholds['critical']:
            return 'high'
        elif current >= self.thresholds['warning'] or predicted >= self.thresholds['warning'] or leak_detected:
            return 'medium'
        return 'low'
    
    def _generate_recommendation(self, current: float, predicted: float,
                                  time_to_critical: Optional[float],
                                  leak_detected: bool, leak_processes: List[Dict]) -> str:
        """生成建议"""
        if current >= self.thresholds['critical']:
            return f"内存严重不足！当前{current:.1f}%，请立即释放内存或重启服务"
        
        if leak_detected and leak_processes:
            procs = ', '.join([p['name'] for p in leak_processes[:3]])
            return f"检测到内存泄漏：{procs}，建议检查相关进程"
        
        if time_to_critical and time_to_critical < 6:
            return f"预计{time_to_critical:.1f}小时后内存将不足，建议准备扩容或优化"
        
        if predicted > self.thresholds['warning']:
            return "内存使用呈上升趋势，建议关注内存优化"
        
        return "内存使用正常，继续监控"


class GitHubSyncPredictor:
    """GitHub同步延迟预测器"""
    
    def __init__(self, history_size: int = 168):
        self.history: deque = deque(maxlen=history_size)
        self.predictor = LinearRegressionPredictor(min_data_points=5)
        self.latency_thresholds = {
            'warning': 5000,  # 5秒
            'critical': 10000,  # 10秒
            'unusable': 30000  # 30秒
        }
    
    def record_sync(self, duration_ms: float, success: bool, operation: str):
        """记录同步操作"""
        self.history.append({
            'timestamp': datetime.now(),
            'duration_ms': duration_ms,
            'success': success,
            'operation': operation
        })
    
    async def test_latency(self) -> Optional[float]:
        """测试GitHub连接延迟"""
        try:
            start = time.time()
            proc = await asyncio.create_subprocess_exec(
                'curl', '-s', '-o', '/dev/null', '-w', '%{time_total}',
                'https://api.github.com',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            
            if proc.returncode == 0:
                latency_ms = float(stdout.decode().strip()) * 1000
                return latency_ms
            return None
        except Exception as e:
            logger.warning(f"Failed to test GitHub latency: {e}")
            return None
    
    def predict(self) -> Optional[PredictionResult]:
        """预测同步延迟"""
        if len(self.history) < self.predictor.min_data_points:
            return None
        
        # 只使用成功的操作
        successful_ops = [h for h in self.history if h['success']]
        if len(successful_ops) < self.predictor.min_data_points:
            return None
        
        timestamps = [h['timestamp'] for h in successful_ops]
        values = [h['duration_ms'] for h in successful_ops]
        
        try:
            trend = self.predictor.fit(timestamps, values)
            current_value = values[-1]
            
            # 预测未来延迟
            predicted_value, confidence = self.predictor.predict(trend, 6)  # 6小时
            
            # 计算成功率趋势
            recent = list(self.history)[-20:]
            success_rate = sum(1 for h in recent if h['success']) / len(recent)
            
            # 调整置信度
            confidence *= success_rate
            
            # 确定风险等级
            risk_level = self._assess_risk(current_value, predicted_value, success_rate)
            
            # 生成建议
            recommendation = self._generate_recommendation(
                current_value, predicted_value, success_rate, trend.trend_direction
            )
            
            return PredictionResult(
                timestamp=datetime.now().isoformat(),
                metric_name='github_sync_latency',
                current_value=round(current_value, 2),
                predicted_value=round(predicted_value, 2),
                prediction_time=datetime.now() + timedelta(hours=6),
                confidence=round(confidence, 3),
                risk_level=risk_level,
                time_to_threshold=None,
                recommendation=recommendation
            )
        except Exception as e:
            logger.error(f"Failed to predict GitHub latency: {e}")
            return None
    
    def _assess_risk(self, current: float, predicted: float, success_rate: float) -> str:
        """评估风险等级"""
        if success_rate < 0.5 or current >= self.latency_thresholds['unusable']:
            return 'critical'
        elif success_rate < 0.8 or predicted >= self.latency_thresholds['critical']:
            return 'high'
        elif success_rate < 0.95 or predicted >= self.latency_thresholds['warning']:
            return 'medium'
        return 'low'
    
    def _generate_recommendation(self, current: float, predicted: float,
                                  success_rate: float, trend: str) -> str:
        """生成建议"""
        if success_rate < 0.5:
            return f"GitHub同步成功率极低({success_rate*100:.1f}%)，建议检查网络连接"
        
        if current >= self.latency_thresholds['unusable']:
            return "GitHub连接延迟过高，建议切换到离线模式或使用代理"
        
        if predicted >= self.latency_thresholds['critical']:
            return f"预计GitHub延迟将恶化，当前趋势：{trend}，建议准备应急方案"
        
        if success_rate < 0.9:
            return f"GitHub同步成功率偏低({success_rate*100:.1f}%)，建议排查失败原因"
        
        return "GitHub同步状态良好"


class APIRateLimitPredictor:
    """API限流风险预测器"""
    
    def __init__(self):
        self.api_calls: Dict[str, deque] = {}  # API端点 -> 调用历史
        self.rate_limits: Dict[str, Dict] = {}  # API端点 -> 限流配置
        self.error_history: deque = deque(maxlen=100)
        
        # 默认限流配置
        self.default_limits = {
            'github_api': {'requests_per_hour': 5000, 'burst': 100},
            'openai_api': {'requests_per_minute': 60, 'burst': 10},
            'feishu_api': {'requests_per_second': 20, 'burst': 5},
        }
    
    def record_call(self, api_name: str, endpoint: str, status_code: int,
                    response_headers: Optional[Dict] = None):
        """记录API调用"""
        key = f"{api_name}:{endpoint}"
        
        if key not in self.api_calls:
            self.api_calls[key] = deque(maxlen=1000)
        
        call_record = {
            'timestamp': datetime.now(),
            'status_code': status_code,
            'api_name': api_name,
            'endpoint': endpoint
        }
        
        # 解析限流头信息
        if response_headers:
            rate_limit_info = self._parse_rate_limit_headers(response_headers)
            call_record['rate_limit_info'] = rate_limit_info
            
            # 更新限流配置
            if rate_limit_info:
                self.rate_limits[key] = rate_limit_info
        
        self.api_calls[key].append(call_record)
        
        # 记录错误
        if status_code in [429, 403]:
            self.error_history.append({
                'timestamp': datetime.now(),
                'api': key,
                'status_code': status_code
            })
    
    def _parse_rate_limit_headers(self, headers: Dict) -> Optional[Dict]:
        """解析限流相关的HTTP头"""
        info = {}
        
        # GitHub风格的限流头
        if 'X-RateLimit-Limit' in headers:
            info['limit'] = int(headers.get('X-RateLimit-Limit', 0))
            info['remaining'] = int(headers.get('X-RateLimit-Remaining', 0))
            info['reset_time'] = int(headers.get('X-RateLimit-Reset', 0))
        
        # 通用的Retry-After
        if 'Retry-After' in headers:
            info['retry_after'] = int(headers.get('Retry-After', 0))
        
        return info if info else None
    
    def predict(self, api_name: str, endpoint: str) -> Optional[PredictionResult]:
        """预测API限流风险"""
        key = f"{api_name}:{endpoint}"
        
        if key not in self.api_calls or len(self.api_calls[key]) < 10:
            return None
        
        calls = list(self.api_calls[key])
        
        # 计算当前使用速率
        now = datetime.now()
        recent_calls = [c for c in calls if (now - c['timestamp']).total_seconds() < 3600]
        
        if not recent_calls:
            return None
        
        # 获取限流配置
        limit_info = self.rate_limits.get(key, self.default_limits.get(api_name, {}))
        limit = limit_info.get('limit', 1000)
        remaining = limit_info.get('remaining', limit - len(recent_calls))
        
        # 计算消耗速率
        time_span_hours = max(1, (recent_calls[-1]['timestamp'] - recent_calls[0]['timestamp']).total_seconds() / 3600)
        consumption_rate = len(recent_calls) / time_span_hours
        
        # 预测剩余时间
        if consumption_rate > 0:
            hours_remaining = remaining / consumption_rate
        else:
            hours_remaining = float('inf')
        
        # 计算风险等级
        usage_percent = (limit - remaining) / limit * 100 if limit > 0 else 0
        
        if hours_remaining < 0.5 or usage_percent > 95:
            risk_level = 'critical'
        elif hours_remaining < 2 or usage_percent > 80:
            risk_level = 'high'
        elif hours_remaining < 6 or usage_percent > 60:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # 生成建议
        recommendation = self._generate_api_recommendation(
            api_name, usage_percent, hours_remaining, consumption_rate
        )
        
        return PredictionResult(
            timestamp=datetime.now().isoformat(),
            metric_name=f'api_rate_limit_{key}',
            current_value=round(usage_percent, 2),
            predicted_value=round(min(100, usage_percent + consumption_rate), 2),
            prediction_time=now + timedelta(hours=1),
            confidence=0.7 if limit_info else 0.5,
            risk_level=risk_level,
            time_to_threshold=round(hours_remaining, 2) if hours_remaining != float('inf') else None,
            recommendation=recommendation
        )
    
    def _generate_api_recommendation(self, api_name: str, usage_percent: float,
                                      hours_remaining: float, rate: float) -> str:
        """生成API限流建议"""
        if usage_percent > 95:
            return f"{api_name} API配额即将耗尽({usage_percent:.1f}%)，请立即停止调用"
        
        if hours_remaining < 1:
            return f"{api_name} API预计1小时内达到限流，当前速率：{rate:.1f}/小时"
        
        if usage_percent > 80:
            return f"{api_name} API使用率较高({usage_percent:.1f}%)，建议降低调用频率"
        
        if rate > 100:
            return f"{api_name} API调用频率较高({rate:.1f}/小时)，建议启用缓存"
        
        return f"{api_name} API使用情况正常"
    
    def get_all_predictions(self) -> List[PredictionResult]:
        """获取所有API的预测"""
        predictions = []
        
        # 按API名称分组
        api_endpoints: Dict[str, List[str]] = {}
        for key in self.api_calls.keys():
            api_name = key.split(':')[0]
            if api_name not in api_endpoints:
                api_endpoints[api_name] = []
            api_endpoints[api_name].append(key)
        
        # 为每个API生成聚合预测
        for api_name, endpoints in api_endpoints.items():
            total_calls = sum(len(self.api_calls[e]) for e in endpoints)
            if total_calls > 0:
                # 使用主要端点的预测
                main_endpoint = max(endpoints, key=lambda e: len(self.api_calls[e]))
                pred = self.predict(api_name, main_endpoint.split(':', 1)[1])
                if pred:
                    predictions.append(pred)
        
        return predictions


class PredictiveMonitor:
    """预测性监控主类"""
    
    def __init__(self, data_dir: str = '/root/.openclaw/workspace/data/diagnosis'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.disk_predictor = DiskSpacePredictor()
        self.memory_predictor = MemoryPredictor()
        self.github_predictor = GitHubSyncPredictor()
        self.api_predictor = APIRateLimitPredictor()
        
        self.running = False
        self.interval_minutes = 10
        
        # 告警回调
        self.alert_callbacks: List[Callable] = []
    
    def register_alert_callback(self, callback: Callable):
        """注册告警回调"""
        self.alert_callbacks.append(callback)
    
    async def collect_metrics(self):
        """收集指标"""
        # 磁盘
        self.disk_predictor.record('/')
        self.disk_predictor.record('/root')
        
        # 内存
        self.memory_predictor.record()
        
        # GitHub延迟（异步）
        latency = await self.github_predictor.test_latency()
        if latency:
            self.github_predictor.record_sync(latency, True, 'latency_test')
    
    def generate_predictions(self) -> List[PredictionResult]:
        """生成所有预测"""
        predictions = []
        
        # 磁盘预测
        disk_pred = self.disk_predictor.predict('/')
        if disk_pred:
            predictions.append(disk_pred)
        
        # 内存预测
        mem_pred = self.memory_predictor.predict()
        if mem_pred:
            predictions.append(mem_pred)
        
        # GitHub预测
        github_pred = self.github_predictor.predict()
        if github_pred:
            predictions.append(github_pred)
        
        # API预测
        api_preds = self.api_predictor.get_all_predictions()
        predictions.extend(api_preds)
        
        return predictions
    
    def check_alerts(self, predictions: List[PredictionResult]):
        """检查是否需要告警"""
        alerts = []
        
        for pred in predictions:
            if pred.risk_level in ['high', 'critical']:
                alerts.append({
                    'level': pred.risk_level,
                    'metric': pred.metric_name,
                    'message': pred.recommendation,
                    'predicted_value': pred.predicted_value,
                    'time_to_threshold': pred.time_to_threshold
                })
        
        # 触发回调
        for callback in self.alert_callbacks:
            try:
                callback(alerts)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        return alerts
    
    def save_state(self):
        """保存状态"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'disk_history': list(self.disk_predictor.history),
            'memory_history': list(self.memory_predictor.history),
            'github_history': list(self.github_predictor.history)
        }
        
        # 转换datetime为字符串
        for key in ['disk_history', 'memory_history', 'github_history']:
            for item in state[key]:
                if isinstance(item.get('timestamp'), datetime):
                    item['timestamp'] = item['timestamp'].isoformat()
        
        state_file = self.data_dir / 'predictor_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, default=str, indent=2)
    
    def load_state(self):
        """加载状态"""
        state_file = self.data_dir / 'predictor_state.json'
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # 恢复历史数据
                for item in state.get('disk_history', []):
                    self.disk_predictor.history.append(item)
                
                for item in state.get('memory_history', []):
                    self.memory_predictor.history.append(item)
                
                for item in state.get('github_history', []):
                    self.github_predictor.history.append(item)
                
                logger.info("Predictor state loaded")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    async def run_cycle(self):
        """运行一个监控周期"""
        # 收集指标
        await self.collect_metrics()
        
        # 生成预测
        predictions = self.generate_predictions()
        
        # 检查告警
        alerts = self.check_alerts(predictions)
        
        # 保存状态
        self.save_state()
        
        # 记录预测
        for pred in predictions:
            logger.info(f"Prediction: {pred.metric_name}="
                       f"{pred.current_value:.2f} -> {pred.predicted_value:.2f} "
                       f"({pred.risk_level})")
        
        return predictions, alerts
    
    async def run(self):
        """主运行循环"""
        self.running = True
        self.load_state()
        
        logger.info("Predictive monitor started")
        
        while self.running:
            try:
                await self.run_cycle()
                await asyncio.sleep(self.interval_minutes * 60)
            except Exception as e:
                logger.error(f"Monitor cycle failed: {e}")
                await asyncio.sleep(60)
        
        logger.info("Predictive monitor stopped")
    
    def stop(self):
        """停止监控"""
        self.running = False
    
    def get_status(self) -> Dict:
        """获取监控状态"""
        return {
            'running': self.running,
            'interval_minutes': self.interval_minutes,
            'disk_data_points': len(self.disk_predictor.history),
            'memory_data_points': len(self.memory_predictor.history),
            'github_data_points': len(self.github_predictor.history),
            'api_endpoints_monitored': len(self.api_predictor.api_calls),
            'last_prediction_time': datetime.now().isoformat()
        }


# 便捷函数
async def run_prediction_check() -> Tuple[List[PredictionResult], List[Dict]]:
    """运行一次预测检查"""
    monitor = PredictiveMonitor()
    monitor.load_state()
    return await monitor.run_cycle()


def get_current_predictions() -> List[Dict]:
    """获取当前预测（同步版本）"""
    monitor = PredictiveMonitor()
    monitor.load_state()
    
    # 收集当前指标
    monitor.disk_predictor.record('/')
    monitor.memory_predictor.record()
    
    # 生成预测
    predictions = monitor.generate_predictions()
    
    return [asdict(p) for p in predictions]


# CLI接口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Predictive Monitor')
    parser.add_argument('--run', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--status', action='store_true', help='Show status')
    
    args = parser.parse_args()
    
    if args.run:
        monitor = PredictiveMonitor()
        try:
            asyncio.run(monitor.run())
        except KeyboardInterrupt:
            monitor.stop()
    elif args.once:
        predictions, alerts = asyncio.run(run_prediction_check())
        print(json.dumps({
            'predictions': [asdict(p) for p in predictions],
            'alerts': alerts
        }, indent=2))
    elif args.status:
        monitor = PredictiveMonitor()
        print(json.dumps(monitor.get_status(), indent=2))
    else:
        # 默认显示当前预测
        preds = get_current_predictions()
        print(json.dumps(preds, indent=2))
