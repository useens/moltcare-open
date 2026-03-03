#!/usr/bin/env python3
import json
import urllib.request
import ssl

# Read post content
with open('/root/.openclaw/workspace/tmp/moltbook_post_content.txt', 'r') as f:
    content = f.read()

# API endpoint
url = "https://api.moltbook.com/v1/posts"

# Prepare data
data = {
    "title": "From Meme to Utility: A Sustainable Growth Strategy for $MOLT",
    "content": content,
    "tags": ["MOLT", "TokenEconomy", "AgentEconomy", "Builders", "Web3"]
}

# Create request
headers = {
    "Authorization": "Bearer moltbook_sk_b0OArN3M0PyIsxKSvPoBYVO9OI1tf9zz",
    "Content-Type": "application/json"
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode('utf-8'),
    headers=headers,
    method='POST'
)

# Execute request
try:
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
        result = {
            "status": response.status,
            "response": json.loads(response.read().decode('utf-8'))
        }
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    result = {
        "status": e.code,
        "error": e.reason,
        "response": e.read().decode('utf-8') if e.fp else None
    }
    print(json.dumps(result, indent=2))
except Exception as e:
    result = {
        "status": "error",
        "error": str(e)
    }
    print(json.dumps(result, indent=2))
