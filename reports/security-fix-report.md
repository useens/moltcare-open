# 🔒 安全审计执行报告
生成时间: 2026-03-06 10:06:11

## 发现的问题

找到 163 处硬编码凭证:

- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:7`
- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:8`
- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:9`
- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:10`
- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:11`
- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:12`
- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:13`
- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:14`
- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:15`
- **NVIDIA API Key**: `scripts/test_nanobot_chat.sh:16`
- **NVIDIA API Key**: `scripts/fix-config-and-start.sh:12`
- **NVIDIA API Key**: `scripts/update-to-step.py:24`
- **NVIDIA API Key**: `scripts/update-to-step.py:25`
- **NVIDIA API Key**: `scripts/update-to-step.py:26`
- **NVIDIA API Key**: `scripts/update-to-step.py:27`
- **NVIDIA API Key**: `scripts/update-to-step.py:28`
- **NVIDIA API Key**: `scripts/fix-and-run.py:8`
- **NVIDIA API Key**: `scripts/fix-and-run.py:9`
- **NVIDIA API Key**: `scripts/fix-and-run.py:10`
- **NVIDIA API Key**: `scripts/fix-and-run.py:11`
- **NVIDIA API Key**: `scripts/fix-and-run.py:12`
- **NVIDIA API Key**: `scripts/fix-and-run.py:13`
- **NVIDIA API Key**: `scripts/fix-and-run.py:14`
- **NVIDIA API Key**: `scripts/fix-and-run.py:15`
- **NVIDIA API Key**: `scripts/fix-and-run.py:16`
- **NVIDIA API Key**: `scripts/fix-and-run.py:17`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:5`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:6`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:7`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:8`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:9`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:10`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:11`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:12`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:13`
- **NVIDIA API Key**: `scripts/fix-all-configs.sh:14`
- **NVIDIA API Key**: `scripts/nb_relay.py:23`
- **NVIDIA API Key**: `scripts/nb_relay.py:24`
- **NVIDIA API Key**: `scripts/nb_relay.py:25`
- **NVIDIA API Key**: `scripts/nb_relay.py:26`
- **NVIDIA API Key**: `scripts/nb_relay.py:27`
- **NVIDIA API Key**: `scripts/nb_relay.py:28`
- **NVIDIA API Key**: `scripts/nb_relay.py:29`
- **NVIDIA API Key**: `scripts/nb_relay.py:30`
- **NVIDIA API Key**: `scripts/nb_relay.py:31`
- **NVIDIA API Key**: `scripts/nb_relay.py:32`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:12`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:13`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:14`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:15`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:16`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:17`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:18`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:19`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:20`
- **NVIDIA API Key**: `scripts/update-nanobot-config.py:21`
- **飞书Secret**: `scripts/feishu_sync.py:22`
- **GitHub Token**: `scripts/github-backup.sh:21`
- **NVIDIA API Key**: `scripts/cc.py:28`
- **NVIDIA API Key**: `scripts/cc.py:29`
- **NVIDIA API Key**: `scripts/cc.py:30`
- **NVIDIA API Key**: `scripts/cc.py:31`
- **NVIDIA API Key**: `scripts/cc.py:32`
- **NVIDIA API Key**: `scripts/cc.py:33`
- **NVIDIA API Key**: `scripts/cc.py:34`
- **NVIDIA API Key**: `scripts/cc.py:35`
- **NVIDIA API Key**: `scripts/cc.py:36`
- **NVIDIA API Key**: `scripts/cc.py:37`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:12`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:13`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:14`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:15`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:16`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:17`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:18`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:19`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:20`
- **NVIDIA API Key**: `scripts/test_nanobot_nodes.py:21`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:14`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:15`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:16`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:17`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:18`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:19`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:20`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:21`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:22`
- **NVIDIA API Key**: `scripts/setup-10-nanobots.sh:23`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:21`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:22`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:23`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:24`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:25`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:26`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:27`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:28`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:29`
- **NVIDIA API Key**: `scripts/nb_relay_v2.py:30`
- **飞书Secret**: `scripts/feishu-sync.py:22`
- **NVIDIA API Key**: `scripts/nb-relay.py:23`
- **NVIDIA API Key**: `scripts/nb-relay.py:24`
- **NVIDIA API Key**: `scripts/nb-relay.py:25`
- **NVIDIA API Key**: `scripts/nb-relay.py:26`
- **NVIDIA API Key**: `scripts/nb-relay.py:27`
- **NVIDIA API Key**: `scripts/nb-relay.py:28`
- **NVIDIA API Key**: `scripts/nb-relay.py:29`
- **NVIDIA API Key**: `scripts/nb-relay.py:30`
- **NVIDIA API Key**: `scripts/nb-relay.py:31`
- **NVIDIA API Key**: `scripts/nb-relay.py:32`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:23`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:24`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:25`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:26`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:27`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:28`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:29`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:30`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:31`
- **NVIDIA API Key**: `scripts/cc-node-manager.py:32`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:8`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:9`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:10`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:11`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:12`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:13`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:14`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:15`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:16`
- **NVIDIA API Key**: `scripts/enable-relay-channel.py:17`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:23`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:24`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:25`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:26`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:27`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:28`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:29`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:30`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:31`
- **NVIDIA API Key**: `scripts/cc_node_manager.py:32`
- **飞书Secret**: `scripts/archive/local-resurrect-optimized.sh:455`
- **飞书Secret**: `scripts/archive/auto-resurrect.sh:331`
- **飞书Secret**: `scripts/archive/resurrect.sh:159`
- **飞书Secret**: `scripts/archive/resurrect.sh:169`
- **NVIDIA API Key**: `nanobot-instances/nanobot-8/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-8/.nanobot/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-2/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-2/.nanobot/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-9/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-9/.nanobot/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-6/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-6/.nanobot/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-1/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-1/.nanobot/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-3/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-3/.nanobot/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-4/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-4/.nanobot/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-7/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-7/.nanobot/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-10/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-10/.nanobot/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-5/config.json:4`
- **NVIDIA API Key**: `nanobot-instances/nanobot-5/.nanobot/config.json:4`

## 已执行的修复

- [x] 文件权限修复 (.env, .moltbook_key, scripts)
- [ ] API Key轮换 (需要手动执行)
- [ ] Git历史清理 (需要手动执行)

## 建议操作

1. **立即撤销并重新生成以下API Key**:
   - GitHub Token
   - 飞书 App Secret
   - NVIDIA API Keys

2. **清理Git历史**:
   ```bash
   git filter-branch --force --index-filter      'git rm --cached --ignore-unmatch .env' HEAD
   ```

3. **启用pre-commit钩子**，防止未来提交敏感信息
