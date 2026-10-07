"""X (Twitter) brand-mention monitor -> influencer contact list.

Use case: find who has been talking about a brand on X over the last week,
rank the posts by engagement, then enrich the loudest authors with their full
profile (followers, website, account country) and any e-mail address the actor
can find in their bio or on their linked website. You end up with a short,
ready-to-contact list of people who already care about the topic.

Run:
    pip install -r requirements.txt
    cp .env.example .env
    python main.py

Actor: https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

ACTOR_ID = "pro100chok/x-twitter-all-in-one-scraper"
QUERIES = ["notion", "\"notion ai\""]   # plain keywords or raw X search operators
DAYS_BACK = 7
MAX_POSTS_PER_QUERY = 300
TOP_AUTHORS = 25


def engagement(post: dict) -> int:
    return ((post.get("likeCount") or 0) + 2 * (post.get("repostCount") or 0)
            + 2 * (post.get("quoteCount") or 0) + (post.get("replyCount") or 0))


def main() -> int:
    load_dotenv()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN missing - copy .env.example to .env first.")

    client = ApifyClient(token)
    out = Path(__file__).parent
    since = (date.today() - timedelta(days=DAYS_BACK)).isoformat()

    # Step 1: every English, non-reply post mentioning the brand this week
    print(f"Step 1/2 - searching X for {QUERIES} since {since}")
    try:
        run = client.actor(ACTOR_ID).call(
            run_input={
                "scrapeType": "search",
                "targets": QUERIES,
                "searchType": "latest",
                "maxItems": MAX_POSTS_PER_QUERY,
                "start": since,
                "tweetLanguage": "en",
                "excludeReplies": True,
                "excludeReposts": True,
                "minLikes": 3,
                "includeSearchTerms": True,
            },
            timeout_secs=1800,
        )
    except ApifyApiError as exc:
        sys.exit(f"Search step failed: {exc}")

    posts = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"  {len(posts)} posts collected")
    if not posts:
        return 0

    by_author: dict[str, dict] = defaultdict(lambda: {"posts": 0, "engagement": 0, "best": None})
    for p in posts:
        username = (p.get("author") or {}).get("username")
        if not username:
            continue
        a = by_author[username]
        a["posts"] += 1
        a["engagement"] += engagement(p)
        if a["best"] is None or engagement(p) > engagement(a["best"]):
            a["best"] = p

    ranked = sorted(by_author.items(), key=lambda kv: -kv[1]["engagement"])[:TOP_AUTHORS]
    print("\n  Loudest voices this week:")
    for username, a in ranked[:10]:
        print(f"    @{username:<20} {a['posts']:>3} posts  {a['engagement']:>7} engagement")

    # Step 2: enrich the top authors with profile data and e-mails
    handles = [u for u, _ in ranked]
    print(f"\nStep 2/2 - enriching {len(handles)} profiles (bio, website, e-mails)")
    try:
        prof_run = client.actor(ACTOR_ID).call(
            run_input={
                "scrapeType": "profile",
                "targets": handles,
                "findEmails": True,
                "includeAbout": True,
            },
            timeout_secs=1800,
        )
    except ApifyApiError as exc:
        sys.exit(f"Profile step failed: {exc}")

    profiles = {p.get("username"): p
                for p in client.dataset(prof_run["defaultDatasetId"]).iterate_items()}

    rows = []
    for username, a in ranked:
        prof = profiles.get(username) or {}
        best = a["best"] or {}
        rows.append({
            "username": username,
            "name": prof.get("name"),
            "followers": prof.get("followers"),
            "verifiedType": prof.get("verifiedType"),
            "basedIn": (prof.get("about") or {}).get("accountBasedIn"),
            "website": prof.get("website"),
            "emails": ", ".join(prof.get("emails") or []),
            "postsThisWeek": a["posts"],
            "engagement": a["engagement"],
            "bestPostUrl": best.get("url"),
            "bestPostText": (best.get("text") or "").replace("\n", " ")[:200],
        })

    (out / "output.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False),
                                     encoding="utf-8")
    with (out / "output.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with_email = [r for r in rows if r["emails"]]
    print(f"\n  {len(rows)} authors saved to output.csv - {len(with_email)} with an e-mail")
    for r in with_email[:10]:
        print(f"    @{r['username']:<20} {str(r['followers'] or '-'):>8} followers  {r['emails']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
