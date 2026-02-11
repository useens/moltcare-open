#!/bin/bash
#
# VM状态检测脚本
# 检测VM工作节点是否在线
#

VM_HOST="localhost"
VM_PORT="4444"
VM_KEY="/tmp/linlin_cloud_key"
MAX_RETRY=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRY ]; do
    if ssh -p $VM_PORT -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i $VM_KEY root@$VM_HOST "echo 'pong'" 2>/dev/null | grep -q "pong"; then
        echo "ONLINE"
        exit 0
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 2
done

echo "OFFLINE"
exit 1
