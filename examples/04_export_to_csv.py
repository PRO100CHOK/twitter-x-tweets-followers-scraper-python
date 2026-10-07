"""Export an X profile's timeline to CSV with pandas and find its best posts.

Pulls the Posts tab of a profile, flattens the engagement counters and
writes both the full timeline and a top-20 by views to CSV.

Actor: https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python
"""
import os

import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

PROFILE = "NASA"

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/x-twitter-all-in-one-scraper").call(run_input={
    "scrapeType": "userPosts",
    "targets": [PROFILE],
    "postsFrom": "posts",
    "maxItems": 500,
})

items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
df = pd.DataFrame(items)
if df.empty:
    raise SystemExit("No posts returned.")

cols = ["createdAt", "url", "text", "viewCount", "likeCount", "repostCount",
        "replyCount", "quoteCount", "bookmarkCount", "isRepost"]
df = df[[c for c in cols if c in df.columns]]
df["createdAt"] = pd.to_datetime(df["createdAt"], errors="coerce")
df["hasMedia"] = [bool(i.get("media")) for i in items]

is_repost = df["isRepost"].fillna(False).astype(bool) if "isRepost" in df else False
originals = df[~is_repost] if "isRepost" in df else df
originals.to_csv("output.csv", index=False)
originals.nlargest(20, "viewCount").to_csv("top_posts.csv", index=False)

print(f"{len(originals)} original posts -> output.csv")
print("Median views, media vs no media:")
print(originals.groupby("hasMedia")["viewCount"].median())
