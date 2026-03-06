# NVIDIA API配置对照检查
# 时间: 2026-03-06

## 📄 配置文档要求

### 1. Provider
- **要求**: nvidia-build

### 2. Base URL
- **要求**: https://integrate.api.nvidia.com/v1

### 3. API Keys (10个)
```
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
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
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
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
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
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
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
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
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
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
```

### 4. API Type
- **要求**: openai-completions

### 5. 可用模型 (4个)
```json
{
  "models": [
    {"id": "moonshotai/kimi-k2.5", "name": "Kimi K2.5"},
    {"id": "z-ai/glm4.7", "name": "GLM 4.7"},
    {"id": "deepseek-ai/deepseek-v3.2", "name": "DeepSeek V3.2"},
    {"id": "stepfun-ai/step-3.5-flash", "name": "Step 3.5 Flash"}
  ],
  "priority": ["stepfun-ai/step-3.5-flash", "deepseek-ai/deepseek-v3.2"]
}
```

---

## 🔍 当前Nanobot配置检查

需要检查:
- [ ] 每个nanobot的.env文件
- [ ] agent.py中的API调用配置
- [ ] 模型ID是否正确

## ⚠️ 已知问题

当前API返回403错误，可能原因:
1. API Key不正确或已过期
2. 模型ID格式错误 (应该是 `nvidia-build/xxx/xxx` 还是直接使用?)
3. API调用方式错误 (需要 openai-completions 格式)
4. 缺少必要的请求头
