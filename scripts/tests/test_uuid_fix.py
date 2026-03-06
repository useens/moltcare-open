#!/usr/bin/env python3
"""
验证 Moltbook ID 修复效果
测试 moltbook_cli.py 和 moltbook-unified-scan.py 是否正确处理UUID
"""

import subprocess
import re
import sys
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")

def test_cli_output():
    """测试 moltbook_cli.py 输出是否包含完整UUID"""
    print("=" * 60)
    print("🧪 测试 1: moltbook_cli.py 输出格式")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["python3", str(WORKSPACE / "scripts/moltbook_cli.py"), "hot", "3"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode != 0:
            print(f"   ❌ CLI执行失败: {result.stderr}")
            return False
        
        lines = result.stdout.strip().split('\n')
        posts_found = 0
        valid_uuid_count = 0
        short_id_count = 0
        
        for line in lines:
            # 匹配帖子格式
            match = re.search(r'\[([a-f0-9-]+)\]', line)
            if match:
                posts_found += 1
                post_id = match.group(1)
                
                # 检查UUID格式
                if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', post_id.lower()):
                    valid_uuid_count += 1
                    print(f"   ✅ 完整UUID: {post_id}")
                elif len(post_id) == 8:
                    short_id_count += 1
                    print(f"   ❌ 短ID: {post_id}")
                else:
                    print(f"   ⚠️ 未知格式: {post_id}")
        
        print(f"\n   统计: 找到 {posts_found} 个帖子")
        print(f"         ✅ 完整UUID: {valid_uuid_count}")
        print(f"         ❌ 短ID: {short_id_count}")
        
        if short_id_count > 0:
            print(f"   ❌ 测试失败: 检测到短ID，修复未生效")
            return False
        elif valid_uuid_count > 0:
            print(f"   ✅ 测试通过: 所有ID都是完整UUID")
            return True
        else:
            print(f"   ⚠️ 未找到帖子，无法验证")
            return None
            
    except Exception as e:
        print(f"   ❌ 测试错误: {e}")
        return False

def test_parse_function():
    """测试 parse_posts 函数是否正确解析UUID"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: parse_posts 函数UUID解析")
    print("=" * 60)
    
    # 模拟包含完整UUID的输入
    test_input = """
🔥 热门帖子 (3个):

  [cbd6474f-8478-4894-95f1-7b104a73bcd5] Skill供应链攻击 - @eudaemon_0 (↑4951 💬113027)
  [562faad7-f9cc-49a3-8520-2bdf362606bb] The Nightly Build - @Ronin (↑3185 💬41921)
  [94fc8fda-a6a9-4177-8d6b-e499adb9d675] The good Samaritan - @m0ther (↑1929 💬45645)
"""
    
    # 导入并测试 parse_posts
    sys.path.insert(0, str(WORKSPACE / "scripts"))
    try:
        # 动态导入带连字符的文件名
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "moltbook_unified_scan", 
            WORKSPACE / "scripts" / "moltbook-unified-scan.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["moltbook_unified_scan"] = module
        spec.loader.exec_module(module)
        
        parse_posts = module.parse_posts
        validate_uuid = module.validate_uuid
        
        posts = parse_posts(test_input)
        
        print(f"   解析到 {len(posts)} 个帖子")
        
        all_valid = True
        for post in posts:
            post_id = post.get('id', '')
            is_valid = validate_uuid(post_id)
            
            if is_valid:
                print(f"   ✅ {post['title'][:40]}...: {post_id}")
            else:
                print(f"   ❌ {post['title'][:40]}...: {post_id} (无效UUID)")
                all_valid = False
        
        if all_valid and len(posts) == 3:
            print(f"\n   ✅ 测试通过: 所有UUID格式正确")
            return True
        else:
            print(f"\n   ❌ 测试失败: 部分UUID格式错误")
            return False
            
    except Exception as e:
        print(f"   ❌ 导入/执行错误: {e}")
        return False

def test_validation_functions():
    """测试验证函数"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: UUID验证函数")
    print("=" * 60)
    
    sys.path.insert(0, str(WORKSPACE / "scripts"))
    try:
        # 动态导入带连字符的文件名
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "moltbook_unified_scan", 
            WORKSPACE / "scripts" / "moltbook-unified-scan.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["moltbook_unified_scan"] = module
        spec.loader.exec_module(module)
        
        validate_uuid = module.validate_uuid
        validate_post_data = module.validate_post_data
        
        # 测试 validate_uuid
        test_cases = [
            ("cbd6474f-8478-4894-95f1-7b104a73bcd5", True, "完整UUID"),
            ("562faad7-f9cc-49a3-8520-2bdf362606bb", True, "完整UUID"),
            ("cbd6474f", False, "短ID"),
            ("abc123", False, "无效格式"),
            ("", False, "空字符串"),
        ]
        
        all_passed = True
        for test_id, expected, desc in test_cases:
            result = validate_uuid(test_id)
            status = "✅" if result == expected else "❌"
            if result != expected:
                all_passed = False
            print(f"   {status} {desc}: '{test_id[:20]}...' -> {result}")
        
        # 测试 validate_post_data
        print(f"\n   测试 validate_post_data:")
        valid_post = {
            "id": "cbd6474f-8478-4894-95f1-7b104a73bcd5",
            "title": "测试帖子",
            "url": "https://www.moltbook.com/post/cbd6474f-8478-4894-95f1-7b104a73bcd5"
        }
        is_valid, error = validate_post_data(valid_post)
        print(f"   {'✅' if is_valid else '❌'} 有效帖子: {error if error else '通过'}")
        
        invalid_post = {
            "id": "cbd6474f",
            "title": "测试帖子",
            "url": "https://www.moltbook.com/post/cbd6474f"
        }
        is_valid, error = validate_post_data(invalid_post)
        print(f"   {'✅' if not is_valid else '❌'} 无效帖子(短ID): {error}")
        
        if all_passed:
            print(f"\n   ✅ 测试通过: 验证函数工作正常")
            return True
        else:
            print(f"\n   ❌ 测试失败: 部分验证错误")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔬 Moltbook UUID 修复验证测试\n")
    
    results = []
    
    # 测试1: CLI输出 (需要API凭证，可能失败)
    result1 = test_cli_output()
    results.append(("CLI输出格式", result1))
    
    # 测试2: parse_posts函数
    result2 = test_parse_function()
    results.append(("parse_posts函数", result2))
    
    # 测试3: 验证函数
    result3 = test_validation_functions()
    results.append(("UUID验证函数", result3))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    unknown = sum(1 for _, r in results if r is None)
    
    for name, result in results:
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️ 未知"
        print(f"   {status}: {name}")
    
    print(f"\n总计: ✅ {passed} 通过 | ❌ {failed} 失败 | ⚠️ {unknown} 未知")
    
    if failed == 0:
        print(f"\n🎉 所有测试通过! UUID修复已生效")
        return 0
    else:
        print(f"\n⚠️ 部分测试失败，请检查修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())
