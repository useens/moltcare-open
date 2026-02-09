#!/usr/bin/env python3
"""Whisper Model Benchmark Tool - 测试不同模型的性能表现"""

import json
import sys
import time
import warnings
import psutil
import os
from pathlib import Path

warnings.filterwarnings("ignore")

# 测试配置
MODELS_TO_TEST = ["tiny", "base", "small"]
TEST_AUDIO = "/tmp/tts-mZNb7I/voice-1770623015386.mp3"
REFERENCE_TEXT = "这是一段用于测试语音识别模型的中文音频样本。我们将使用这段音频来比较不同大小模型的转录速度和准确率。人工智能技术正在快速发展。"


def get_memory_usage():
    """获取当前进程内存使用（MB）"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def calculate_cer(reference, hypothesis):
    """计算字符错误率 (CER) - 中文更适合用CER而非WER"""
    # 使用动态规划计算编辑距离
    m, n = len(reference), len(hypothesis)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if reference[i-1] == hypothesis[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j],      # 删除
                                  dp[i][j-1],      # 插入
                                  dp[i-1][j-1])    # 替换
    
    cer = dp[m][n] / max(m, 1)
    return cer


def calculate_accuracy(reference, hypothesis):
    """计算准确率（基于CER）"""
    cer = calculate_cer(reference, hypothesis)
    return max(0, (1 - cer) * 100)


def benchmark_model(model_name, audio_path):
    """测试单个模型的性能"""
    import whisper
    
    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"{'='*60}")
    
    results = {
        "model": model_name,
        "model_size_mb": None,  # 将在后面获取
    }
    
    # 测量模型加载时间
    mem_before = get_memory_usage()
    load_start = time.time()
    
    try:
        model = whisper.load_model(model_name)
        load_time = time.time() - load_start
        mem_after_load = get_memory_usage()
        
        results["load_time_sec"] = round(load_time, 2)
        results["memory_after_load_mb"] = round(mem_after_load - mem_before, 2)
        print(f"✓ 模型加载时间: {load_time:.2f}s")
        print(f"✓ 加载后内存增量: {mem_after_load - mem_before:.2f} MB")
        
    except Exception as e:
        print(f"✗ 模型加载失败: {e}")
        return None
    
    # 测量转录时间
    transcribe_start = time.time()
    
    try:
        result = model.transcribe(audio_path, language="zh", verbose=False)
        transcribe_time = time.time() - transcribe_start
        mem_after_transcribe = get_memory_usage()
        
        results["transcribe_time_sec"] = round(transcribe_time, 2)
        results["memory_after_transcribe_mb"] = round(mem_after_transcribe - mem_before, 2)
        results["peak_memory_mb"] = round(mem_after_transcribe - mem_before, 2)
        
        print(f"✓ 转录时间: {transcribe_time:.2f}s")
        print(f"✓ 转录后内存使用: {mem_after_transcribe - mem_before:.2f} MB")
        
    except Exception as e:
        print(f"✗ 转录失败: {e}")
        return None
    
    # 获取转录文本并计算准确率
    transcribed_text = result["text"].strip()
    results["transcribed_text"] = transcribed_text
    results["detected_language"] = result.get("language", "unknown")
    
    accuracy = calculate_accuracy(REFERENCE_TEXT, transcribed_text)
    results["accuracy_percent"] = round(accuracy, 2)
    
    print(f"\n📄 转录结果:")
    print(f"   {transcribed_text}")
    print(f"\n🎯 准确率: {accuracy:.1f}%")
    
    return results


def get_model_file_size(model_name):
    """获取模型文件大小"""
    import whisper
    
    # Whisper 模型存储在 ~/.cache/whisper/
    cache_dir = Path.home() / ".cache" / "whisper"
    
    # 模型文件名映射
    model_files = {
        "tiny": "tiny.pt",
        "base": "base.pt",
        "small": "small.pt",
    }
    
    if model_name in model_files:
        model_path = cache_dir / model_files[model_name]
        if model_path.exists():
            size_mb = model_path.stat().st_size / 1024 / 1024
            return round(size_mb, 1)
    
    return None


def generate_report(all_results):
    """生成 benchmark 报告"""
    print("\n" + "="*70)
    print("📊 WHISPER 模型 Benchmark 报告")
    print("="*70)
    
    # 表头
    print(f"\n{'模型':<10} {'大小(MB)':<10} {'加载时间':<10} {'转录时间':<10} {'内存占用':<10} {'准确率':<10}")
    print("-" * 70)
    
    for r in all_results:
        if r:
            size = r.get('model_size_mb', '-')
            load = r.get('load_time_sec', '-')
            trans = r.get('transcribe_time_sec', '-')
            mem = r.get('peak_memory_mb', '-')
            acc = r.get('accuracy_percent', '-')
            print(f"{r['model']:<10} {size:<10} {load:<10} {trans:<10} {mem:<10} {acc:<10}")
    
    print("\n" + "-" * 70)
    
    # 模型选择建议
    print("\n💡 模型选择建议:")
    print("-" * 40)
    
    # 找出各项指标最优的模型
    valid_results = [r for r in all_results if r]
    
    if valid_results:
        fastest_load = min(valid_results, key=lambda x: x['load_time_sec'])
        fastest_trans = min(valid_results, key=lambda x: x['transcribe_time_sec'])
        lowest_mem = min(valid_results, key=lambda x: x['peak_memory_mb'])
        highest_acc = max(valid_results, key=lambda x: x['accuracy_percent'])
        
        print(f"🚀 最快加载: {fastest_load['model']} ({fastest_load['load_time_sec']}s)")
        print(f"⚡ 最快转录: {fastest_trans['model']} ({fastest_trans['transcribe_time_sec']}s)")
        print(f"💾 最低内存: {lowest_mem['model']} ({lowest_mem['peak_memory_mb']} MB)")
        print(f"🎯 最高准确率: {highest_acc['model']} ({highest_acc['accuracy_percent']}%)")
    
    print("\n📋 推荐场景:")
    print("-" * 40)
    
    # tiny 推荐
    tiny_result = next((r for r in valid_results if r['model'] == 'tiny'), None)
    if tiny_result:
        print(f"\n🔹 tiny (39MB):")
        print(f"   - 适合: 实时性要求极高、资源受限场景")
        print(f"   - 准确率: {tiny_result['accuracy_percent']:.1f}%")
        print(f"   - 转录速度: {tiny_result['transcribe_time_sec']}s")
        if tiny_result['accuracy_percent'] < 70:
            print(f"   - ⚠️ 注意: 中文准确率偏低，适合英文或简单场景")
    
    # base 推荐
    base_result = next((r for r in valid_results if r['model'] == 'base'), None)
    if base_result:
        print(f"\n🔹 base (74MB):")
        print(f"   - 适合: 通用场景，平衡速度和准确率")
        print(f"   - 准确率: {base_result['accuracy_percent']:.1f}%")
        print(f"   - 转录速度: {base_result['transcribe_time_sec']}s")
        print(f"   - ✅ 推荐作为默认模型")
    
    # small 推荐
    small_result = next((r for r in valid_results if r['model'] == 'small'), None)
    if small_result:
        print(f"\n🔹 small (244MB):")
        print(f"   - 适合: 高质量转录场景，接受稍慢速度")
        print(f"   - 准确率: {small_result['accuracy_percent']:.1f}%")
        print(f"   - 转录速度: {small_result['transcribe_time_sec']}s")
        acc_diff = small_result['accuracy_percent'] - base_result['accuracy_percent'] if base_result else 0
        if acc_diff > 5:
            print(f"   - ✅ 比 base 准确率高 {acc_diff:.1f}%，值得用于高质量场景")
        elif acc_diff > 0:
            print(f"   - ⚠️ 比 base 仅高 {acc_diff:.1f}%，需权衡内存占用")
        else:
            print(f"   - ⚠️ 准确率提升不明显，不建议使用")
    
    print("\n" + "="*70)
    
    # 输出 JSON 报告
    report = {
        "reference_text": REFERENCE_TEXT,
        "test_audio": TEST_AUDIO,
        "results": valid_results
    }
    
    report_path = "/root/.openclaw/workspace/skills/local-whisper/benchmark_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 详细报告已保存: {report_path}")
    
    return report


def main():
    print("🎙️ Whisper 模型性能 Benchmark")
    print(f"测试音频: {TEST_AUDIO}")
    print(f"参考文本: {REFERENCE_TEXT}")
    
    # 检查测试音频是否存在
    if not os.path.exists(TEST_AUDIO):
        print(f"\n✗ 测试音频不存在: {TEST_AUDIO}")
        sys.exit(1)
    
    # 运行测试
    all_results = []
    for model in MODELS_TO_TEST:
        result = benchmark_model(model, TEST_AUDIO)
        if result:
            # 获取模型文件大小
            result["model_size_mb"] = get_model_file_size(model)
            all_results.append(result)
    
    # 生成报告
    generate_report(all_results)


if __name__ == "__main__":
    main()
