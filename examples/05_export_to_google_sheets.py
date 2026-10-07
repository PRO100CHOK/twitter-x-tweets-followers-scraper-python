"""Push today's X (Twitter) trends into a Google Sheet.

Pulls worldwide, news and sports trends and writes them to a worksheet
with gspread. Needs a Google service account JSON file shared with the
sheet (see https://docs.gspread.org/en/latest/oauth2.html).

Actor: https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python
"""
import os
from datetime import datetime, timezone

import gspread
from apify_client import ApifyClient
from dotenv import load_dotenv

SHEET_NAME = "X trends tracker"
SERVICE_ACCOUNT_FILE = "service_account.json"

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/x-twitter-all-in-one-scraper").call(run_input={
    "scrapeType": "trends",
    "targets": ["worldwide", "news", "sports"],
    "maxItems": 30,
})
trends = list(client.dataset(run["defaultDatasetId"]).iterate_items())

stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
rows = [[stamp, t.get("location"), t.get("rank"), t.get("name"),
         t.get("category"), t.get("postCount"), t.get("url")] for t in trends]

gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
ws = gc.open(SHEET_NAME).sheet1
if not ws.get_all_values():
    ws.append_row(["scrapedAt", "location", "rank", "trend", "category", "postCount", "url"])
ws.append_rows(rows, value_input_option="USER_ENTERED")
print(f"Appended {len(rows)} trends to '{SHEET_NAME}'")
