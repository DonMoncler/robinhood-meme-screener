"""
Social momentum inputs -- standard X (Twitter) API v2 + Telegram Bot API.
"""
import time
import requests
from config import TWITTER_BEARER_TOKEN, TELEGRAM_BOT_TOKEN


def get_twitter_mentions(symbol_or_cashtag, since_ts):
    if not TWITTER_BEARER_TOKEN:
        return 0, 0, 0, 0
    query = f"({symbol_or_cashtag}) -is:retweet"
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    params = {
        "query": query,
        "max_results": 100,
        "tweet.fields": "public_metrics,author_id,created_at",
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(since_ts)),
    }
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    data = r.json().get("data", [])
    authors = set()
    engagement = 0
    for t in data:
        authors.add(t["author_id"])
        m = t.get("public_metrics", {})
        engagement += m.get("like_count", 0) + m.get("retweet_count", 0) + m.get("reply_count", 0)
    return len(data), len(authors), engagement, 0


def get_telegram_member_count(chat_id):
    if not TELEGRAM_BOT_TOKEN:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatMemberCount"
    r = requests.get(url, params={"chat_id": chat_id}, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("result")
