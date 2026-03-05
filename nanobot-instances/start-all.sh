#!/bin/bash
/root/.openclaw/workspace/nanobot-instances/nanobot-1/start.sh &
/root/.openclaw/workspace/nanobot-instances/nanobot-2/start.sh &
/root/.openclaw/workspace/nanobot-instances/nanobot-3/start.sh &
/root/.openclaw/workspace/nanobot-instances/nanobot-4/start.sh &
/root/.openclaw/workspace/nanobot-instances/nanobot-5/start.sh &
/root/.openclaw/workspace/nanobot-instances/nanobot-6/start.sh &
/root/.openclaw/workspace/nanobot-instances/nanobot-7/start.sh &
/root/.openclaw/workspace/nanobot-instances/nanobot-8/start.sh &
/root/.openclaw/workspace/nanobot-instances/nanobot-9/start.sh &
/root/.openclaw/workspace/nanobot-instances/nanobot-10/start.sh &
sleep 5
echo '10个nanobot已启动'
ps aux | grep nanobot-gateway | grep -v grep | wc -l
