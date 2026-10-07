"""Turn a competitor's X followers into a lead list with e-mails.

Scrapes the followers of an account with the e-mail finder on (bio + the
website each profile links to), keeps accounts with a real audience and
saves the ones that expose a contact address.

Actor: https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python
"""
import csv
import os
import sys

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

COMPETITOR = "https://x.com/vercel"
MAX_FOLLOWERS = 1000
MIN_AUDIENCE = 500

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

try:
    run = client.actor("pro100chok/x-twitter-all-in-one-scraper").call(run_input={
        "scrapeType": "connections",
        "targets": [COMPETITOR],
        "connectionType": "followers",
        "maxItems": MAX_FOLLOWERS,
        "findEmails": True,
        "includeAbout": False,
    }, timeout_secs=3600)
except ApifyApiError as exc:
    sys.exit(f"Run failed: {exc}")

leads = [
    u for u in client.dataset(run["defaultDatasetId"]).iterate_items()
    if u.get("emails") and (u.get("followers") or 0) >= MIN_AUDIENCE
]
leads.sort(key=lambda u: -(u.get("followers") or 0))

with open("followers_leads.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["username", "name", "followers", "location", "website", "emails"])
    for u in leads:
        w.writerow([u.get("username"), u.get("name"), u.get("followers"),
                    u.get("location"), u.get("website"), ", ".join(u["emails"])])

print(f"{len(leads)} followers with an e-mail and {MIN_AUDIENCE}+ followers -> followers_leads.csv")
