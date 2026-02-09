#!/usr/bin/env python3
"""生成测试音频文件"""

import numpy as np

# 尝试使用不同的音频库
try:
    import wave
    import struct
    
    # 生成一个 5 秒的测试音频 (16kHz, 16bit, mono)
    sample_rate = 16000
    duration = 5  # 秒
    
    # 生成正弦波（用于测试）
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 创建一个简单的频率变化（模拟语音）
    frequency = 200 + 100 * np.sin(2 * np.pi * 2 * t)  # 200Hz 基础频率，有变化
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    
    # 转换为 16-bit 整数
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # 保存为 WAV
    with wave.open('/tmp/test_synthetic.wav', 'w') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print("✓ 合成测试音频已生成: /tmp/test_synthetic.wav")
    
except Exception as e:
    print(f"生成合成音频失败: {e}")
    
# 也尝试下载一个公开的测试音频
import urllib.request
try:
    # 下载一个公开的中文测试音频
    url = "https://github.com/openai/whisper/raw/main/tests/jfk.flac"
    output_path = "/tmp/test_jfk.flac"
    
    print(f"下载测试音频: {url}")
    urllib.request.urlretrieve(url, output_path)
    print(f"✓ 测试音频已下载: {output_path}")
except Exception as e:
    print(f"下载测试音频失败: {e}")
