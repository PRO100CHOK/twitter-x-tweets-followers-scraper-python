"""Minimal example: search X (Twitter) posts for a keyword and print them.

Actor: https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python
"""
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/x-twitter-all-in-one-scraper").call(run_input={
    "scrapeType": "search",
    "targets": ["web scraping"],
    "searchType": "latest",
    "maxItems": 20,
})

for post in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(post.get("likeCount"), post.get("url"), (post.get("text") or "")[:80])
