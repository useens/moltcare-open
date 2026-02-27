#!/bin/bash
# evomap-retry-publish.sh - 自动重试发布死手开关资产到 EvoMap

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/evomap-retry.log"
ASSETS_DIR="$WORKSPACE/.evomap_assets"

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log() {
    echo "[$(timestamp)] $1" | tee -a "$LOG_FILE"
}

# 检查 EvoMap API 状态
check_evomap_status() {
    local status=$(curl -s -o /dev/null -w "%{http_code}" https://evomap.ai/a2a/publish 2>/dev/null)
    echo "$status"
}

# 发布资产到 EvoMap
publish_assets() {
    log "🚀 尝试发布死手开关 v2.0 资产到 EvoMap..."
    
    cd "$WORKSPACE"
    
    # 使用 Python 发布
    python3 -c "
import json
import hashlib
import requests
from datetime import datetime

HUB_URL = 'https://evomap.ai'
NODE_ID = 'node_e8d73f59'

def compute_asset_id(asset_obj):
    obj_copy = {k: v for k, v in asset_obj.items() if k != 'asset_id'}
    canonical = json.dumps(obj_copy, sort_keys=True, separators=(',', ':'))
    return f'sha256:{hashlib.sha256(canonical.encode()).hexdigest()}'

def build_envelope(message_type, payload):
    timestamp = datetime.utcnow().isoformat() + 'Z'
    message_id = f'msg_{int(datetime.utcnow().timestamp() * 1000)}'
    return {
        'protocol': 'gep-a2a',
        'protocol_version': '1.0.0',
        'message_type': message_type,
        'message_id': message_id,
        'sender_id': NODE_ID,
        'timestamp': timestamp,
        'payload': payload
    }

try:
    # Load assets
    with open('.evomap_assets/deadman-v2-gene.json') as f:
        gene = json.load(f)
    with open('.evomap_assets/deadman-v2-capsule.json') as f:
        capsule = json.load(f)
    with open('.evomap_assets/deadman-v2-event.json') as f:
        event = json.load(f)
    
    # Publish
    payload = {'assets': [gene, capsule, event]}
    envelope = build_envelope('publish', payload)
    
    response = requests.post(
        f'{HUB_URL}/a2a/publish',
        json=envelope,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print('SUCCESS')
        print(json.dumps(result, indent=2))
    else:
        print(f'FAILED: {response.status_code}')
        print(response.text[:500])
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1
}

# 主流程
main() {
    log "═══════════════════════════════════════"
    log "EvoMap 自动重试发布 - 死手开关 v2.0"
    log "═══════════════════════════════════════"
    
    # 检查资产是否存在
    if [ ! -f "$ASSETS_DIR/deadman-v2-gene.json" ]; then
        log "❌ 资产文件不存在，跳过"
        exit 1
    fi
    
    # 检查 API 状态
    log "🔍 检查 EvoMap API 状态..."
    API_STATUS=$(check_evomap_status)
    log "   API 状态码: $API_STATUS"
    
    if [ "$API_STATUS" = "502" ] || [ "$API_STATUS" = "503" ]; then
        log "⚠️  EvoMap 服务暂时不可用 (HTTP $API_STATUS)"
        log "⏰ 将在下次定时任务时重试"
        exit 0
    fi
    
    # 尝试发布
    RESULT=$(publish_assets)
    
    if echo "$RESULT" | grep -q "SUCCESS"; then
        log "✅ 发布成功！"
        log "📋 响应:"
        echo "$RESULT" | tail -n +2 | while read line; do
            log "   $line"
        done
        
        # 发送通知
        echo "🎉 死手开关 v2.0 已成功发布到 EvoMap！" > "$WORKSPACE/.state/evomap_publish_success.txt"
        
        # 禁用后续的自动重试
        log "🔒 禁用自动重试任务（发布成功）"
        crontab -l 2>/dev/null | grep -v "evomap-retry-publish" | crontab -
    else
        log "❌ 发布失败"
        log "📋 错误信息:"
        echo "$RESULT" | while read line; do
            log "   $line"
        done
    fi
    
    log "═══════════════════════════════════════"
}

main "$@"
