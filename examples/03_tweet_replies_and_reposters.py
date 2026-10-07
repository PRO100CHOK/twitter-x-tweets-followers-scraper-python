"""Audit one X post: its reply thread plus everyone who reposted it.

Two runs against the same post URL - Post + replies, then Post engagement
(reposters) - so you can see both what people said and who amplified it.

Actor: https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python
"""
import os
import sys
from collections import Counter

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

POST_URL = "https://x.com/apify/status/2087572956683567110"
ACTOR = "pro100chok/x-twitter-all-in-one-scraper"

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

try:
    replies_run = client.actor(ACTOR).call(run_input={
        "scrapeType": "postDetail",
        "targets": [POST_URL],
        "includeReplies": True,
        "maxItems": 300,
    })
    reposters_run = client.actor(ACTOR).call(run_input={
        "scrapeType": "postEngagement",
        "targets": [POST_URL],
        "engagementType": "reposters",
        "maxItems": 300,
    })
except ApifyApiError as exc:
    sys.exit(f"Run failed: {exc}")

thread = list(client.dataset(replies_run["defaultDatasetId"]).iterate_items())
replies = [p for p in thread if p.get("isReply")]
print(f"{len(replies)} replies")
for p in sorted(replies, key=lambda p: -(p.get("likeCount") or 0))[:5]:
    print(f"  {p.get('likeCount') or 0:>5} likes  @{(p.get('author') or {}).get('username')}: "
          f"{(p.get('text') or '')[:90]}")

reposters = list(client.dataset(reposters_run["defaultDatasetId"]).iterate_items())
reach = sum(u.get("followers") or 0 for u in reposters)
print(f"\n{len(reposters)} reposters, combined audience {reach:,}")
for u in sorted(reposters, key=lambda u: -(u.get("followers") or 0))[:5]:
    print(f"  @{u.get('username') or '':<20} {u.get('followers') or 0:>9,} followers")

langs = Counter(p.get("lang") for p in replies)
print("\nReply languages:", dict(langs.most_common(5)))
