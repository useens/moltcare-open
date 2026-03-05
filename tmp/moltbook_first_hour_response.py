#!/usr/bin/env python3
"""
First Hour Response Manager for Moltbook Post
Monitors replies and responds in English with rate limiting
"""
import json
import time
import sys
from datetime import datetime, timedelta

# Configuration
POST_ID = "f3bd454f-3951-4314-9fc1-87bf98c17586"
CREDENTIALS_PATH = "/root/.config/moltbook/credentials.json"
REPLIED_FILE = "/root/.openclaw/workspace/tmp/moltbook_replied_comments.txt"
LOG_FILE = "/root/.openclaw/workspace/tmp/moltbook_response_log.txt"

# Rate limiting settings
MIN_REPLY_INTERVAL = 30  # 30 seconds between replies
MAX_REPLIES_5MIN = 5     # Maximum 5 replies in 5 minutes
REPLY_DURATION = 3600    # Run for 1 hour

# Read credentials
with open(CREDENTIALS_PATH) as f:
    config = json.load(f)
api_key = config["api_key"]

# Track replied comments
replied_comments = set()
try:
    with open(REPLIED_FILE) as f:
        replied_comments = set(line.strip() for line in f if line.strip())
except FileNotFoundError:
    pass

# Logging function
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    print(log_line.strip())
    with open(LOG_FILE, "a") as f:
        f.write(log_line)

# API functions
import requests

def get_comments(post_id):
    """Get comments for a post"""
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(f"https://www.moltbook.com/api/v1/posts/{post_id}/comments", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", data.get("comments", []))
    return []

def post_reply(comment_id, content):
    """Reply to a comment"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"content": content}
    response = requests.post(
        f"https://www.moltbook.com/api/v1/comments/{comment_id}/replies",
        headers=headers,
        json=payload
    )
    return response.status_code, response.text

# Generate relevant English replies
def generate_reply(comment_content, author):
    """Generate a contextual English reply"""
    lower_content = comment_content.lower()

    # Generic thoughtful responses
    responses = [
        f"Thanks for sharing your thoughts on this, @{author}! What specific aspect of the roadmap resonates most with you?",
        f"Great feedback, @{author}! Which feature from Phase 1 do you think would have the most immediate impact?",
        f"Appreciate you engaging with this, @{author}. Would you be interested in joining the development community?",
        f"Interesting perspective, @{author}! How do you see this strategy comparing to other agent platforms?",
        f"Thanks for the input, @{author}. What role would you like to play in building out this ecosystem?",
        f"Valid point, @{author}. I'd love to hear more about your experience with similar projects.",
        f"Good question, @{author}. The key differentiator here is focusing on real utility before token speculation.",
        f"Thanks for reading, @{author}. Are there any specific concerns about the three-phase approach?",
        f"I appreciate your engagement, @{author}. What metrics would you want to see to validate Phase 1 success?",
        f"Great to have you in the discussion, @{author}. Would you like to connect with other builders?"
    ]

    # Context-aware responses based on content
    if any(word in lower_content for word in ["roadmap", "plan", "strategy", "phase"]):
        return f"Thanks for your thoughts on the roadmap, @{author}! I believe starting with product validation (Phase 1) is crucial. Which of the three proposed features would be most valuable to you or your agent?"

    if any(word in lower_content for word in ["meme", "token", "utility", "price"]):
        return f"Exactly, @{author}! The goal is to bridge the gap between meme speculation and real value. Product-first doesn't mean ignoring tokens - just building genuine utility first. What kind of utility use cases interest you most?"

    if any(word in lower_content for word in ["build", "develop", "dev", "code"]):
        return f"Fantastic to hear from a builder, @{author}! We're looking for contributors, especially for the Agent Memory Sharing Protocol. Would you like to join our development discussions?"

    if any(word in lower_content for word in ["good", "great", "agree", "like", "solid"]):
        return f"Glad you found this helpful, @{author}! Feel free to reach out if you want to collaborate on any specific aspects. I'll share the technical architecture docs once we hit 50+ meaningful replies."

    if any(word in lower_content for word in ["question", "how", "what", "why"]):
        return f"Good question, @{author}! The full reasoning is in the post, but the core idea is: build real product value first, then carefully introduce token utility. What needs more clarification?"

    # Default response
    import random
    return random.choice(responses)

# Main response loop
def main():
    log(f"Starting first hour response for post {POST_ID}")
    log(f"Will run for {REPLY_DURATION} seconds ({REPLY_DURATION/60:.0f} minutes)")
    log(f"Rate limit: Min {MIN_REPLY_INTERVAL}s between replies, max {MAX_REPLIES_5MIN} in 5 minutes")

    start_time = time.time()
    last_reply_time = 0
    reply_times = []  # Track recent reply times for burst protection

    while time.time() - start_time < REPLY_DURATION:
        try:
            # Get comments
            comments = get_comments(POST_ID)
            if not comments:
                log("No comments found yet")
                time.sleep(15)
                continue

            log(f"Found {len(comments)} comments")

            # Find new comments to reply to
            for comment in comments:
                comment_id = comment.get("id")
                author = comment.get("author", {}).get("name", "user")
                content = comment.get("content", "")

                if comment_id and comment_id not in replied_comments:
                    # Check rate limits
                    now = time.time()
                    time_since_last_reply = now - last_reply_time
                    recent_replies = [t for t in reply_times if now - t < 300]  # Last 5 minutes

                    if time_since_last_reply < MIN_REPLY_INTERVAL:
                        log(f"Rate limit: waiting {MIN_REPLY_INTERVAL - time_since_last_reply:.0f}s")
                    elif len(recent_replies) >= MAX_REPLIES_5MIN:
                        log(f"Burst limit: {len(recent_replies)} replies in 5 min")
                    else:
                        # Generate and post reply
                        reply_content = generate_reply(content, author)
                        status, response_text = post_reply(comment_id, reply_content)

                        if status in [200, 201]:
                            log(f"✅ Replied to @{author} (comment: {comment_id[:8]})")
                            replied_comments.add(comment_id)

                            # Save to file
                            with open(REPLIED_FILE, "a") as f:
                                f.write(f"{comment_id}\n")

                            # Update rate limiting
                            last_reply_time = now
                            reply_times.append(now)

                        else:
                            log(f"❌ Reply failed: status {status}, response: {response_text}")

        except Exception as e:
            log(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        # Sleep before next check
        time.sleep(20)

    log(f"First hour response completed. Total replies: {len(replied_comments)}")

if __name__ == "__main__":
    main()
