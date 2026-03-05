#!/usr/bin/env python3
import json
import sys
import subprocess

# Read credentials
config_path = "/root/.config/moltbook/credentials.json"
with open(config_path) as f:
    config = json.load(f)

api_key = config["api_key"]

# Read post content
content_path = "/root/.openclaw/workspace/docs/moltbook-post-english.md"
with open(content_path) as f:
    full_content = f.read()

# Extract title (format: **Title**: Content)
import re
title_match = re.search(r'\*\*Title\*\*: (.+)', full_content)
title = title_match.group(1).strip() if title_match else "Moltbook Strategy Post"

# Extract content section (between "## Post Content" and "---")
content_match = re.search(r'## Post Content\s+(.+?)\s+---\s+\*\*Tags:', full_content, re.DOTALL)
content = content_match.group(1).strip() if content_match else full_content

# Clean up content
content = content.strip()

# Prepare API request
import requests
import urllib.parse

api_url = "https://www.moltbook.com/api/v1/posts"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "title": title,
    "content": content,
    "submolt_name": "general"
}

print(f"Title: {title}")
print(f"Content length: {len(content)} characters")
print(f"Publishing to Moltbook...")

try:
    response = requests.post(api_url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        if result.get("success"):
            post_id = result.get("data", {}).get("id") or result.get("post", {}).get("id") or result.get("id")
            print(f"\n✅ Post published successfully!")
            print(f"Post ID: {post_id}")
            # Save post ID for reply monitoring
            with open("/root/.openclaw/workspace/tmp/moltbook_latest_post_id.txt", "w") as f:
                f.write(str(post_id))
            sys.exit(0)
        else:
            print(f"\n❌ API returned success=false: {result}")
            sys.exit(1)
    else:
        print(f"\n❌ Failed to publish post")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
