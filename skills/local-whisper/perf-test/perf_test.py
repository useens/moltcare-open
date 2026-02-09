#!/usr/bin/env python3
"""
Local Whisper 性能测试脚本

测试项目:
1. 不同长度音频测试 (5s, 10s, 20s, 60s)
2. 不同模型测试 (tiny, base, small, turbo)
3. 并发测试 (1, 2, 4, 8 并发)
4. CPU/内存占用监控
5. 长时间运行稳定性测试
"""

import os
import sys
import time
import json
import subprocess
import threading
import psutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import tempfile
import signal

# 测试配置
TEST_DIR = Path(__file__).parent
SAMPLES_DIR = TEST_DIR / "samples"
RESULTS_DIR = TEST_DIR / "results"
SKILL_DIR = Path(__file__).parent.parent
TRANSCRIBE_SCRIPT = SKILL_DIR / "scripts" / "transcribe.py"

# 测试音频长度 (秒)
AUDIO_LENGTHS = [5, 10, 20, 60]

# 测试模型
MODELS = ["tiny", "base", "small", "turbo"]

# 并发级别
CONCURRENCY_LEVELS = [1, 2, 4]

# 长时间测试的迭代次数
STABILITY_ITERATIONS = 50


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    audio_file: str
    model: str
    duration: float  # 处理耗时(秒)
    audio_length: float  # 音频长度(秒)
    cpu_percent: float = 0.0  # 平均 CPU 使用率
    memory_mb: float = 0.0  # 峰值内存使用(MB)
    rtf: float = 0.0  # Real-Time Factor (处理时间/音频时长)
    success: bool = True
    error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.cpu_readings: List[float] = []
        self.memory_readings: List[float] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.process: Optional[psutil.Process] = None
        
    def start(self, pid: Optional[int] = None):
        """开始监控"""
        self.cpu_readings = []
        self.memory_readings = []
        self._stop_event.clear()
        
        if pid:
            try:
                self.process = psutil.Process(pid)
            except psutil.NoSuchProcess:
                pass
        
        self._thread = threading.Thread(target=self._monitor)
        self._thread.start()
        
    def _monitor(self):
        """监控循环"""
        while not self._stop_event.is_set():
            try:
                if self.process and self.process.is_running():
                    # 监控特定进程
                    cpu = self.process.cpu_percent()
                    mem = self.process.memory_info().rss / 1024 / 1024  # MB
                    self.cpu_readings.append(cpu)
                    self.memory_readings.append(mem)
                else:
                    # 监控整个系统
                    cpu = psutil.cpu_percent()
                    mem = psutil.virtual_memory().used / 1024 / 1024  # MB
                    self.cpu_readings.append(cpu)
                    self.memory_readings.append(mem)
            except Exception:
                pass
            time.sleep(self.interval)
    
    def stop(self):
        """停止监控"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
    
    def get_avg_cpu(self) -> float:
        """获取平均 CPU 使用率"""
        return sum(self.cpu_readings) / len(self.cpu_readings) if self.cpu_readings else 0
    
    def get_peak_memory(self) -> float:
        """获取峰值内存使用"""
        return max(self.memory_readings) if self.memory_readings else 0


def generate_test_audio(duration: int, output_path: Path) -> bool:
    """生成测试音频文件 (使用 sine wave)"""
    try:
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"sine=frequency=1000:duration={duration}",
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"生成音频失败 ({duration}s): {e}")
        return False


def run_transcription(audio_file: Path, model: str = "base", quiet: bool = True) -> tuple:
    """
    运行转录并返回结果和耗时
    返回: (success: bool, text: str, duration: float)
    """
    start_time = time.time()
    try:
        cmd = [
            sys.executable, str(TRANSCRIBE_SCRIPT),
            str(audio_file), "--model", model
        ]
        if quiet:
            cmd.append("--quiet")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            return True, result.stdout.strip(), duration
        else:
            return False, result.stderr, duration
            
    except subprocess.TimeoutExpired:
        return False, "Timeout", time.time() - start_time
    except Exception as e:
        return False, str(e), time.time() - start_time


def test_single_file(audio_file: Path, model: str = "base") -> TestResult:
    """测试单个文件"""
    result = TestResult(
        test_name="single_file",
        audio_file=audio_file.name,
        model=model,
        duration=0,
        audio_length=get_audio_duration(audio_file)
    )
    
    # 启动资源监控
    monitor = ResourceMonitor(interval=0.2)
    
    try:
        monitor.start()
        success, text, duration = run_transcription(audio_file, model)
        monitor.stop()
        
        result.duration = duration
        result.success = success
        result.cpu_percent = monitor.get_avg_cpu()
        result.memory_mb = monitor.get_peak_memory()
        result.rtf = duration / result.audio_length if result.audio_length > 0 else 0
        
        if not success:
            result.error = text
            
    except Exception as e:
        monitor.stop()
        result.success = False
        result.error = str(e)
    
    return result


def get_audio_duration(audio_file: Path) -> float:
    """获取音频时长"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except:
        return 0


def test_different_lengths() -> List[TestResult]:
    """测试不同长度的音频"""
    print("\n" + "="*60)
    print("测试 1: 不同长度音频测试")
    print("="*60)
    
    results = []
    
    for length in AUDIO_LENGTHS:
        audio_file = SAMPLES_DIR / f"test_{length}s.wav"
        
        # 确保音频文件存在
        if not audio_file.exists():
            print(f"  生成 {length}s 测试音频...")
            if not generate_test_audio(length, audio_file):
                continue
        
        print(f"\n  测试 {length}s 音频 (model=base):")
        
        # 预热
        run_transcription(audio_file, "base", quiet=True)
        
        # 正式测试（运行3次取平均）
        for i in range(3):
            result = test_single_file(audio_file, "base")
            if result.success:
                print(f"    运行 {i+1}: {result.duration:.2f}s (RTF: {result.rtf:.2f}x)")
            else:
                print(f"    运行 {i+1}: 失败 - {result.error}")
            results.append(result)
    
    return results


def test_different_models() -> List[TestResult]:
    """测试不同模型"""
    print("\n" + "="*60)
    print("测试 2: 不同模型测试")
    print("="*60)
    
    results = []
    test_file = SAMPLES_DIR / "test_20s.wav"
    
    if not test_file.exists():
        generate_test_audio(20, test_file)
    
    for model in MODELS:
        print(f"\n  测试模型: {model}")
        
        # 预热
        run_transcription(test_file, model, quiet=True)
        
        # 正式测试
        for i in range(3):
            result = test_single_file(test_file, model)
            result.test_name = "model_comparison"
            if result.success:
                print(f"    运行 {i+1}: {result.duration:.2f}s (RTF: {result.rtf:.2f}x)")
            else:
                print(f"    运行 {i+1}: 失败 - {result.error}")
            results.append(result)
    
    return results


def test_concurrent() -> List[TestResult]:
    """并发测试"""
    print("\n" + "="*60)
    print("测试 3: 并发测试")
    print("="*60)
    
    results = []
    test_file = SAMPLES_DIR / "test_10s.wav"
    
    if not test_file.exists():
        generate_test_audio(10, test_file)
    
    for concurrency in CONCURRENCY_LEVELS:
        print(f"\n  并发级别: {concurrency}")
        
        files = [test_file] * concurrency
        start_time = time.time()
        
        # 启动系统级资源监控
        monitor = ResourceMonitor(interval=0.2)
        monitor.start()
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(run_transcription, f, "base", True)
                for f in files
            ]
            
            completed = 0
            failed = 0
            for future in as_completed(futures):
                success, text, _ = future.result()
                if success:
                    completed += 1
                else:
                    failed += 1
        
        total_time = time.time() - start_time
        monitor.stop()
        
        result = TestResult(
            test_name="concurrent",
            audio_file=f"{concurrency}x {test_file.name}",
            model="base",
            duration=total_time,
            audio_length=10 * concurrency,
            cpu_percent=monitor.get_avg_cpu(),
            memory_mb=monitor.get_peak_memory(),
            rtf=total_time / 10,  # 单个文件RTF
            success=(failed == 0)
        )
        
        print(f"    总耗时: {total_time:.2f}s")
        print(f"    完成: {completed}, 失败: {failed}")
        print(f"    平均CPU: {result.cpu_percent:.1f}%, 峰值内存: {result.memory_mb:.1f}MB")
        
        results.append(result)
    
    return results


def test_stability() -> List[TestResult]:
    """长时间运行稳定性测试"""
    print("\n" + "="*60)
    print("测试 4: 长时间运行稳定性测试")
    print("="*60)
    
    results = []
    test_file = SAMPLES_DIR / "test_10s.wav"
    
    if not test_file.exists():
        generate_test_audio(10, test_file)
    
    print(f"  运行 {STABILITY_ITERATIONS} 次转录...")
    
    durations = []
    for i in range(STABILITY_ITERATIONS):
        success, text, duration = run_transcription(test_file, "base", quiet=True)
        
        if success:
            durations.append(duration)
            
        if (i + 1) % 10 == 0:
            avg = sum(durations[-10:]) / len(durations[-10:])
            print(f"    进度: {i+1}/{STABILITY_ITERATIONS}, 最近10次平均: {avg:.2f}s")
        
        result = TestResult(
            test_name="stability",
            audio_file=test_file.name,
            model="base",
            duration=duration,
            audio_length=10,
            rtf=duration / 10,
            success=success
        )
        results.append(result)
    
    # 统计分析
    if durations:
        avg = sum(durations) / len(durations)
        min_d = min(durations)
        max_d = max(durations)
        variance = sum((d - avg) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5
        
        print(f"\n  统计结果:")
        print(f"    平均耗时: {avg:.2f}s")
        print(f"    最小耗时: {min_d:.2f}s")
        print(f"    最大耗时: {max_d:.2f}s")
        print(f"    标准差: {std_dev:.2f}s")
        print(f"    波动范围: {((max_d - min_d) / avg * 100):.1f}%")
    
    return results


def generate_report(all_results: List[TestResult]):
    """生成测试报告"""
    report_path = RESULTS_DIR / "perf_report.md"
    json_path = RESULTS_DIR / "results.json"
    
    # 保存 JSON 数据
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump([asdict(r) for r in all_results], f, indent=2, ensure_ascii=False)
    
    # 生成 Markdown 报告
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Local Whisper 性能测试报告\n\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试环境: {os.uname().sysname} {os.uname().machine}\n")
        f.write(f"CPU: {os.cpu_count()} 核\n")
        
        # 内存信息
        mem = psutil.virtual_memory()
        f.write(f"内存: {mem.total / 1024 / 1024 / 1024:.1f} GB\n\n")
        
        # 1. 不同长度音频测试结果
        f.write("## 1. 不同长度音频测试结果\n\n")
        f.write("| 音频长度 | 模型 | 平均耗时 | RTF | 平均CPU | 峰值内存 |\n")
        f.write("|---------|------|---------|-----|---------|----------|\n")
        
        length_results = [r for r in all_results if r.test_name == "single_file"]
        for length in AUDIO_LENGTHS:
            rs = [r for r in length_results if r.audio_length == length and r.success]
            if rs:
                avg_time = sum(r.duration for r in rs) / len(rs)
                avg_rtf = sum(r.rtf for r in rs) / len(rs)
                avg_cpu = sum(r.cpu_percent for r in rs) / len(rs)
                max_mem = max(r.memory_mb for r in rs)
                f.write(f"| {length}s | base | {avg_time:.2f}s | {avg_rtf:.2f}x | {avg_cpu:.1f}% | {max_mem:.1f}MB |\n")
        
        # 2. 不同模型对比
        f.write("\n## 2. 不同模型性能对比\n\n")
        f.write("| 模型 | 平均耗时 | RTF | 平均CPU | 峰值内存 |\n")
        f.write("|------|---------|-----|---------|----------|\n")
        
        model_results = [r for r in all_results if r.test_name == "model_comparison"]
        for model in MODELS:
            rs = [r for r in model_results if r.model == model and r.success]
            if rs:
                avg_time = sum(r.duration for r in rs) / len(rs)
                avg_rtf = sum(r.rtf for r in rs) / len(rs)
                avg_cpu = sum(r.cpu_percent for r in rs) / len(rs)
                max_mem = max(r.memory_mb for r in rs)
                f.write(f"| {model} | {avg_time:.2f}s | {avg_rtf:.2f}x | {avg_cpu:.1f}% | {max_mem:.1f}MB |\n")
        
        # 3. 并发测试结果
        f.write("\n## 3. 并发测试结果\n\n")
        f.write("| 并发数 | 总耗时 | 平均CPU | 峰值内存 |\n")
        f.write("|--------|--------|---------|----------|\n")
        
        concurrent_results = [r for r in all_results if r.test_name == "concurrent"]
        for r in concurrent_results:
            if r.success:
                f.write(f"| {r.audio_file.split('x')[0]} | {r.duration:.2f}s | {r.cpu_percent:.1f}% | {r.memory_mb:.1f}MB |\n")
        
        # 4. 稳定性测试结果
        f.write("\n## 4. 长时间运行稳定性测试\n\n")
        stability_results = [r for r in all_results if r.test_name == "stability" and r.success]
        if stability_results:
            durations = [r.duration for r in stability_results]
            avg = sum(durations) / len(durations)
            min_d = min(durations)
            max_d = max(durations)
            variance = sum((d - avg) ** 2 for d in durations) / len(durations)
            std_dev = variance ** 0.5
            
            f.write(f"- 测试次数: {len(stability_results)}\n")
            f.write(f"- 平均耗时: {avg:.2f}s\n")
            f.write(f"- 最小耗时: {min_d:.2f}s\n")
            f.write(f"- 最大耗时: {max_d:.2f}s\n")
            f.write(f"- 标准差: {std_dev:.2f}s\n")
            f.write(f"- 波动范围: {((max_d - min_d) / avg * 100):.1f}%\n\n")
            
            if std_dev / avg < 0.1:
                f.write("**稳定性评估**: ✅ 优秀 (标准差 < 10%)\n")
            elif std_dev / avg < 0.2:
                f.write("**稳定性评估**: ⚠️ 良好 (标准差 10-20%)\n")
            else:
                f.write("**稳定性评估**: ❌ 需优化 (标准差 > 20%)\n")
        
        # 瓶颈分析
        f.write("\n## 5. 瓶颈分析\n\n")
        
        # 分析 CPU 瓶颈
        all_cpu = [r.cpu_percent for r in all_results if r.success]
        if all_cpu:
            avg_cpu = sum(all_cpu) / len(all_cpu)
            if avg_cpu > 300:  # 4核系统中超过300%表示接近满载
                f.write("1. **CPU 瓶颈**: ⚠️ 高CPU占用，多核利用率良好\n")
            elif avg_cpu > 100:
                f.write("1. **CPU 瓶颈**: 中等CPU占用，仍有优化空间\n")
            else:
                f.write("1. **CPU 瓶颈**: 低CPU占用，CPU不是瓶颈\n")
        
        # 分析内存瓶颈
        all_mem = [r.memory_mb for r in all_results if r.success]
        if all_mem:
            max_mem = max(all_mem)
            f.write(f"2. **内存使用**: 峰值 {max_mem:.1f}MB，")
            if max_mem > 4000:
                f.write("⚠️ 内存占用较高\n")
            else:
                f.write("✅ 内存使用合理\n")
        
        # 分析并发效率
        concurrent = [r for r in all_results if r.test_name == "concurrent"]
        if len(concurrent) >= 2:
            f.write("3. **并发效率**: ")
            # 计算加速比
            if concurrent[0].duration > 0:
                speedup = concurrent[0].duration * len(concurrent) / concurrent[-1].duration
                efficiency = speedup / len(concurrent) * 100
                f.write(f"并发加速比 {speedup:.2f}x，效率 {efficiency:.1f}%\n")
        
        # 优化建议
        f.write("\n## 6. 优化建议\n\n")
        
        # 根据测试结果给出建议
        tiny_results = [r for r in model_results if r.model == "tiny" and r.success]
        turbo_results = [r for r in model_results if r.model == "turbo" and r.success]
        
        if tiny_results and turbo_results:
            tiny_time = sum(r.duration for r in tiny_results) / len(tiny_results)
            turbo_time = sum(r.duration for r in turbo_results) / len(turbo_results)
            
            f.write(f"1. **模型选择**:\n")
            f.write(f"   - 追求速度: 使用 `tiny` 模型 ({tiny_time:.2f}s)\n")
            f.write(f"   - 追求质量: 使用 `turbo` 模型 ({turbo_time:.2f}s)\n")
            f.write(f"   - 速度差: {turbo_time/tiny_time:.1f}x\n\n")
        
        f.write("2. **性能优化建议**:\n")
        
        # 检查 RTF
        all_rtf = [r.rtf for r in all_results if r.success and r.rtf > 0]
        if all_rtf:
            avg_rtf = sum(all_rtf) / len(all_rtf)
            if avg_rtf > 0.5:
                f.write(f"   - ⚠️ 平均RTF为{avg_rtf:.2f}，建议考虑更快的模型或硬件加速\n")
            else:
                f.write(f"   - ✅ 平均RTF为{avg_rtf:.2f}，处理速度良好\n")
        
        f.write("   - 考虑使用 GPU 加速 (CUDA/MPS) 以获得更好的性能\n")
        f.write("   - 对于批量处理，建议使用队列和进程池\n")
        f.write("   - 预热模型可以减少首次调用延迟\n")
    
    print(f"\n报告已生成: {report_path}")
    return report_path


def main():
    """主函数"""
    print("="*60)
    print("Local Whisper 性能测试")
    print("="*60)
    
    # 创建目录
    SAMPLES_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # 检查转录脚本
    if not TRANSCRIBE_SCRIPT.exists():
        print(f"错误: 找不到转录脚本 {TRANSCRIBE_SCRIPT}")
        sys.exit(1)
    
    all_results = []
    
    try:
        # 运行测试
        all_results.extend(test_different_lengths())
        all_results.extend(test_different_models())
        all_results.extend(test_concurrent())
        all_results.extend(test_stability())
        
        # 生成报告
        report_path = generate_report(all_results)
        
        # 打印摘要
        print("\n" + "="*60)
        print("测试完成!")
        print("="*60)
        print(f"结果文件: {RESULTS_DIR}")
        print(f"报告文件: {report_path}")
        
    except KeyboardInterrupt:
        print("\n测试被中断")
        sys.exit(1)


if __name__ == "__main__":
    main()
