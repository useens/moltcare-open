#!/bin/bash
# 激活共享Python环境
source /root/.openclaw/workspace/nanobots/shared_venv/bin/activate
export PLAYWRIGHT_BROWSERS_PATH=/root/.openclaw/workspace/nanobots/shared_venv/playwright-browsers
export PYTHONPATH=/root/.openclaw/workspace/nanobots/nb06/workspace:$PYTHONPATH
