#!/usr/bin/env python3
"""
Moltbook Rate Limiter
Ensures compliance with API rate limits
"""

import time
import json
from datetime import datetime, timedelta
from pathlib import Path

class MoltbookRateLimiter:
    def __init__(self, log_file="/root/.openclaw/workspace/logs/moltbook_api_calls.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Rate limits
        self.MIN_REPLY_INTERVAL = 30  # seconds between replies
        self.MAX_REPLIES_PER_5MIN = 5  # max 5 replies in 5 minutes
        self.COOLDOWN_ON_429 = 60  # seconds to wait after rate limit error
        
    def log_call(self, action, post_id=None, status="success"):
        """Log an API call with timestamp"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "post_id": post_id,
            "status": status
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_recent_calls(self, action=None, seconds=300):
        """Get recent API calls within time window"""
        if not self.log_file.exists():
            return []
        
        cutoff = datetime.now() - timedelta(seconds=seconds)
        calls = []
        
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        if entry_time > cutoff:
                            if action is None or entry.get("action") == action:
                                calls.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except FileNotFoundError:
            pass
        
        return calls
    
    def can_reply(self):
        """Check if we can send a reply now"""
        recent_replies = self.get_recent_calls(action="reply", seconds=300)
        
        # Check: max 5 replies in 5 minutes
        if len(recent_replies) >= self.MAX_REPLIES_PER_5MIN:
            oldest_in_window = datetime.fromisoformat(recent_replies[0]["timestamp"])
            wait_time = 300 - (datetime.now() - oldest_in_window).total_seconds()
            return False, f"Rate limit: Max {self.MAX_REPLIES_PER_5MIN} replies per 5 min. Wait {int(wait_time)}s"
        
        # Check: min 30 seconds between replies
        if recent_replies:
            last_reply_time = datetime.fromisoformat(recent_replies[-1]["timestamp"])
            elapsed = (datetime.now() - last_reply_time).total_seconds()
            if elapsed < self.MIN_REPLY_INTERVAL:
                wait_time = self.MIN_REPLY_INTERVAL - elapsed
                return False, f"Rate limit: Min {self.MIN_REPLY_INTERVAL}s between replies. Wait {int(wait_time)}s"
        
        return True, "OK"
    
    def wait_for_reply_slot(self, max_wait=300):
        """Wait until we can send a reply"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            can_reply, message = self.can_reply()
            if can_reply:
                return True
            
            # Extract wait time from message or default to 10s
            try:
                wait_seconds = int(message.split("Wait ")[1].split("s")[0])
            except (IndexError, ValueError):
                wait_seconds = 10
            
            print(f"Rate limit: {message}. Waiting...")
            time.sleep(min(wait_seconds, 30))  # Max 30s sleep intervals
        
        return False
    
    def record_429_error(self):
        """Record a rate limit error and wait"""
        self.log_call("error", status="429_rate_limited")
        print(f"Received 429 error. Cooling down for {self.COOLDOWN_ON_429} seconds...")
        time.sleep(self.COOLDOWN_ON_429)

# Usage example
if __name__ == "__main__":
    limiter = MoltbookRateLimiter()
    
    # Check if we can reply
    can_reply, message = limiter.can_reply()
    print(f"Can reply: {can_reply}, Message: {message}")
    
    # Show recent activity
    recent = limiter.get_recent_calls(seconds=300)
    print(f"Recent calls in last 5 min: {len(recent)}")
