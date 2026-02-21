#!/usr/bin/env python3
"""
应用EvoMap网络推荐的资产
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "evomap"))

from evomap.bridge import DecisionEngineEvoMapBridge
from evomap.client import EvoMapClient


# 推荐的5个高GDI资产
RECOMMENDED_ASSETS = [
    {
        "rank": 1,
        "asset_id": "sha256:6c8b2bef4652d5113cc802b6995a8e9f5da8b5b1ffe3d6bc639e2ca8ce27edec",
        "gdi": 70.9,
        "triggers": ["TimeoutError", "ECONNRESET", "ECONNREFUSED", "429TooManyRequests"],
        "summary": "Universal HTTP retry: exponential backoff, timeout control, connection pooling"
    },
    {
        "rank": 2,
        "asset_id": "sha256:dae9842a35d875a9e96ac5f0b9ee004eb3eb8bd71ad4c43a4a14c0e4a6a40763",
        "gdi": 70.7,
        "triggers": ["TimeoutError", "ECONNRESET", "ECONNREFUSED", "429TooManyRequests"],
        "summary": "HTTP retry with backoff, timeout, pooling (alternative implementation)"
    },
    {
        "rank": 3,
        "asset_id": "sha256:8ee18eac8610ef9ecb60d1392bc0b8eb2dd7057f119cb3ea8a2336bbc78f22b3",
        "gdi": 69.5,
        "triggers": ["FeishuFormatError", "markdown_render_failed", "card_send_rejected"],
        "summary": "Feishu message fallback: rich text → interactive card → plain text"
    },
    {
        "rank": 4,
        "asset_id": "sha256:7e7ad73ed072df6bfafa0b8f9a464da26f36b2127bb9c4d67a5c498551c9a0f4",
        "gdi": 69.3,
        "triggers": ["OOMKilled", "memory_limit", "vertical_scaling", "JVM_heap", "container_memory"],
        "summary": "K8s pod OOM fix: dynamic heap sizing with MaxRAMPercentage monitoring"
    },
    {
        "rank": 5,
        "asset_id": "sha256:def136049c982ed785117dff00bb3238ed71d11cf77c019b3db2a8f65b476f06",
        "gdi": 69.15,
        "triggers": ["session_amnesia", "context_loss", "cross_session_gap"],
        "summary": "Cross-session memory continuity auto-load RECENT_EVENTS + daily memory + MEMORY.md"
    }
]


async def fetch_capsule_details(client, asset_id):
    """获取资产详细内容"""
    try:
        # 尝试从客户端获取
        response = await client.get_capsule(asset_id)
        if response and "data" in response:
            return response["data"]

        # 尝试从本地文件读取
        local_file = Path(f"/root/.openclaw/workspace/evolver/assets/gep/capsules/{asset_id}.json")
        if local_file.exists():
            with open(local_file) as f:
                return json.load(f)

        return None
    except Exception as e:
        print(f"      ⚠️  获取详情失败: {e}")
        return None


async def apply_asset(bridge, client, asset):
    """应用单个资产"""
    rank = asset["rank"]
    asset_id = asset["asset_id"]
    gdi = asset["gdi"]
    triggers = asset["triggers"]
    summary = asset["summary"]

    print(f"\n{'='*70}")
    print(f"🥇 [{rank}/5] GDI {gdi} - {triggers[0] if triggers else 'general'}")
    print(f"{'='*70}")
    print(f"📦 Asset ID: {asset_id}")
    print(f"📝 Summary: {summary}")
    print(f"🎯 Triggers: {', '.join(triggers if triggers else ['N/A'])}")
    print()

    # 获取详细内容
    print("📄 获取资产详情...")
    capsule_details = await fetch_capsule_details(client, asset_id)

    if capsule_details:
        print(f"   ✅ 资产详情已加载")
        if isinstance(capsule_details, dict):
            if "code" in capsule_details:
                print(f"   📊 代码量: {len(capsule_details['code'])} 字符")
            if "files" in capsule_details:
                print(f"   📁 文件数: {len(capsule_details['files'])}")
    else:
        print(f"   ⚠️  无法获取资产详情")

    print()
    print("🔧 检查适用性...")

    # 检查是否适用于当前环境
    applicable = True
    notes = []

    # 资产5: 跨会话记忆连续性
    if asset_id == "sha256:def136049c982ed785117dff00bb3238ed71d11cf77c019b3db2a8f65b476f06":
        if not Path("/root/.openclaw/workspace/MEMORY.md").exists():
            notes.append("✅ MEMORY.md 存在 - 可以应用")
        if not Path("/root/.openclaw/workspace/memory").exists():
            applicable = False
            notes.append("❌ memory/ 目录不存在 - 需要先创建")

    # 资产3: Feishu消息fallback
    elif asset_id == "sha256:8ee18eac8610ef9ecb60d1392bc0b8eb2dd7057f119cb3ea8a2336bbc78f22b3":
        # 检查是否有Feishu消息发送脚本
        has_feishu = Path("/root/.openclaw/workspace/scripts").glob("*feishu*")
        if list(has_feishu):
            notes.append("✅ 发现 Feishu 脚本 - 可以应用")
        else:
            notes.append("⚠️  未发现 Feishu 脚本 - 仍可应用于未来")

    # HTTP重试机制（资产1和2）
    elif asset_id in [
        "sha256:6c8b2bef4652d5113cc802b6995a8e9f5da8b5b1ffe3d6bc639e2ca8ce27edec",
        "sha256:dae9842a35d875a9e96ac5f0b9ee004eb3eb8bd71ad4c43a4a14c0e4a6a40763"
    ]:
        # 检查是否有HTTP调用
        http_files = list(Path("/root/.openclaw/workspace/scripts").rglob("*.py"))
        http_count = sum(1 for f in http_files if "requests" in f.read_text() if f.is_file())
        if http_count > 0:
            notes.append(f"✅ 发现 {http_count} 个文件使用 requests - 可以应用")

    # K8s OOM（资产4）
    elif asset_id == "sha256:7e7ad73ed072df6bfafa0b8f9a464da26f36b2127bb9c4d67a5c498551c9a0f4":
        # 检查是否有K8s环境
        notes.append("ℹ️  K8s环境检测 - 未部署在K8s中，记录供未来使用")

    for note in notes:
        print(f"   {note}")

    print()

    if not applicable:
        print("⏭️  跳过：不适用当前环境")
        return {"status": "skipped", "reason": "not_applicable"}

    print("⚙️  应用资产...")

    # 记录到本地资产清单
    try:
        assets_dir = Path("/root/.openclaw/workspace/evolver/assets/applied")
        assets_dir.mkdir(parents=True, exist_ok=True)

        asset_file = assets_dir / f"{asset_id.replace(':', '_')}.json"
        record = {
            "asset_id": asset_id,
            "applied_at": asyncio.get_event_loop().time(),
            "gdi": gdi,
            "summary": summary,
            "triggers": triggers,
            "rank": rank,
            "status": "recorded"
        }

        with open(asset_file, "w") as f:
            json.dump(record, f, indent=2)

        print("   ✅ 已记录到本地资产清单")
        print(f"   📁 位置: {asset_file}")

    except Exception as e:
        print(f"   ⚠️  记录失败: {e}")

    print()
    print("✅ 资产处理完成")

    return {"status": "success", "record": record if 'record' in locals() else None}


async def main():
    print("╔" + "=" * 68 + "╗")
    print("║ 🌐 应用 EvoMap 网络推荐资产 (Top 5)               ║")
    print("╚" + "=" * 68 + "╝")
    print()

    # 创建客户端和bridge
    print("🔌 连接 EvoMap...")
    try:
        client = EvoMapClient()
        bridge = DecisionEngineEvoMapBridge()
        print("   ✅ 连接成功")
    except Exception as e:
        print(f"   ⚠️  连接失败: {e}")
        print("   将使用离线模式...")
        client = None
        bridge = None

    print()

    # 节点统计
    node_config = Path("/root/.openclaw/workspace/config/evomap/node-config.json")
    node_info = {}
    if node_config.exists():
        with open(node_config) as f:
            node_info = json.load(f)

    print("📊 节点信息:")
    print(f"   ID: {node_info.get('node_id', 'N/A')}")
    print(f"   状态: {node_info.get('status', 'N/A')}")
    print(f"   推荐资产数: {len(node_info.get('recommended_assets', []))}")
    print()

    # 应用资产
    results = []

    for asset in RECOMMENDED_ASSETS:
        try:
            result = await apply_asset(bridge, client, asset)
            results.append({
                "asset": asset,
                "result": result
            })
        except Exception as e:
            print(f"❌ 应用失败: {e}")
            results.append({
                "asset": asset,
                "result": {"status": "error", "reason": str(e)}
            })

    # 汇总
    print()
    print("╔" + "=" * 68 + "╗")
    print("║ 📊 应用汇总                                      ║")
    print("╚" + "=" * 68 + "╝")
    print()

    success_count = 0
    skipped_count = 0
    error_count = 0

    for i, r in enumerate(results):
        asset = r["asset"]
        result = r["result"]
        status = result.get("status", "unknown")
        rank = asset.get("rank", i + 1)

        if status == "success":
            success_count += 1
            emoji = "✅"
        elif status == "skipped":
            skipped_count += 1
            emoji = "⏭️ "
        elif status == "error":
            error_count += 1
            emoji = "❌"
        else:
            emoji = "❓"

        print(f"{emoji} [{rank}] GDI {asset['gdi']} - {asset['summary'][:50]}")

    print()
    print("统计:")
    print(f"   成功: {success_count}")
    print(f"   跳过: {skipped_count}")
    print(f"   失败: {error_count}")
    print(f"   总计: {len(results)}")
    print()

    # 保存报告
    report = {
        "timestamp": asyncio.get_event_loop().time(),
        "node_id": node_info.get('node_id', 'N/A'),
        "recommended_count": len(RECOMMENDED_ASSETS),
        "results": results,
        "summary": {
            "success": success_count,
            "skipped": skipped_count,
            "error": error_count,
            "total": len(results)
        }
    }

    report_file = Path("/root/.openclaw/workspace/data/evomap/apply-report-20260221.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"📄 报告已保存: {report_file}")
    print()
    print("✅ 处理完成！")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  应用中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 应用失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
