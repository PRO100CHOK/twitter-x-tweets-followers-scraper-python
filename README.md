# X (Twitter) Tweets, Followers & Profile Scraper in Python

> Pull tweets, replies, followers, following lists, reposters, list members, trends and profile e-mails from X (Twitter) with a few lines of Python — no X developer account, no OAuth keys, no $5-per-1,000-reads bill.

[![Apify Actor](https://img.shields.io/badge/Apify-Actor-blue)](https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

This repository is a working Python client project for the [X (Twitter) All-in-One Scraper](https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python) on Apify. Clone it, add an API token, and run scripts for brand monitoring, follower lead lists, reply analysis, timeline exports and a trends sheet.

## What this does

The official X API now charges per post read, and followers, likers and trends are missing or locked behind higher plans.

The actor behind this repo is an unofficial X API: you send it keywords, handles, post links or list URLs, it returns the same structured JSON a signed-in user sees on x.com. It runs on a pool of logged-in sessions managed by the actor itself, so **you never paste cookies** (you can, optionally, if you prefer your own session). The Python code here simply calls it through the official `apify-client` package and post-processes the results.

One input field — `targets` — takes everything. What it means depends on `scrapeType`:

| `scrapeType` | Put in `targets` | You get back |
|---|---|---|
| `search` | keywords or raw X search queries | matching posts (latest, top, media) or accounts |
| `profile` | `@handle`, `handle` or profile URL | one row per account, bio, counts, e-mails |
| `userPosts` | handles or profile URLs | posts, replies, media, likes, highlights or articles tab |
| `postDetail` | post URLs or ids | the post plus its reply thread |
| `postEngagement` | post URLs or ids | reposters, likers or quote posts |
| `connections` | handles or profile URLs | followers, following, verified followers, mutuals, subscribers |
| `list` | `https://x.com/i/lists/<id>` | the list's posts or its members |
| `community` | `https://x.com/i/communities/<id>` | community posts or members |
| `trends` | `worldwide`, `news`, `sports`… or nothing | trending topics with rank, category and post volume |

## Use cases

- **Brand and competitor monitoring** — track every mention of a product with a likes floor, language and date window, and rank who drives the conversation (`main.py`).
- **Audience-based lead generation** — export a competitor's followers with the e-mail finder on, then keep only accounts with a real audience and a contact address.
- **Influencer research** — build a shortlist from the members of a curated X list or the reposters of a viral post, sorted by follower count.
- **Customer feedback mining** — scrape the full reply thread under a launch announcement and read what people actually said.
- **Content benchmarking** — pull a profile's last few hundred posts and find which formats (media vs text) earn the most views.
- **Trend tracking** — log worldwide, news and sports trends into a spreadsheet on a schedule.

## Requirements

- Python **3.10+**
- A free [Apify account](https://console.apify.com/sign-up) — the $5 monthly free credit covers roughly 24,000 results at free-plan prices
- **No** X account, developer key or cookies

## Quick start

```bash
git clone https://github.com/pro100chok/twitter-x-tweets-followers-scraper-python.git
cd twitter-x-tweets-followers-scraper-python
pip install -r requirements.txt
cp .env.example .env
# paste your APIFY_API_TOKEN into .env
python main.py
```

The smallest possible call looks like this:

```python
import os
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_API_TOKEN"])
run = client.actor("pro100chok/x-twitter-all-in-one-scraper").call(run_input={
    "scrapeType": "search",
    "targets": ["\"web scraping\" min_faves:10"],
    "searchType": "latest",
    "maxItems": 100,
})
for post in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(post["url"], post.get("likeCount"))
```

## How `main.py` works

`main.py` is a two-step brand-mention monitor:

1. **Search** — runs `scrapeType: "search"` for the brand keywords over the last 7 days, English only, no replies or reposts, at least 3 likes. The `start` date is computed at runtime and turned into a `since:` operator by the actor.
2. **Rank** — groups posts by author and scores them on likes, reposts, quotes and replies.
3. **Enrich** — sends the top 25 handles back to the actor in `profile` mode with `findEmails` and `includeAbout` on, which adds follower counts, website, the country the account is based in and any e-mail found in the bio or on the linked website.
4. **Save** — writes `output.json` and `output.csv` with one row per author, including their best post of the week.

Change `QUERIES`, `DAYS_BACK` and `TOP_AUTHORS` at the top of the file to point it at your own brand.

## Advanced search without memorising operators

Search mode accepts X's raw query language, but form fields compile into it for you:

| Field | Becomes |
|---|---|
| `fromUsers` / `toUsers` / `mentioningUsers` | `from:` / `to:` / `@` |
| `start` / `end` | `since:` / `until:` |
| `tweetLanguage` | `lang:` |
| `minLikes` / `minRetweets` / `minReplies` | `min_faves:` / `min_retweets:` / `min_replies:` |
| `onlyVerifiedUsers`, `onlyMedia`, `onlyVideo`, `onlyLinks`, `onlyQuote` | `filter:` operators |
| `excludeReplies` / `excludeReposts` | `-filter:replies` / `-filter:nativeretweets` |
| `geoNear` + `geoWithin` | `near:` + `within:` |

Operators you type yourself are kept, so mixing both styles is fine.

## Example output

A post row (trimmed):

```json
{
  "type": "post",
  "url": "https://x.com/apify/status/2087572956683567110",
  "text": "Full post text, long posts included…",
  "lang": "en",
  "createdAt": "2026-09-18T18:37:20Z",
  "likeCount": 41,
  "repostCount": 9,
  "replyCount": 4,
  "quoteCount": 2,
  "bookmarkCount": 6,
  "viewCount": 5120,
  "hashtags": ["webscraping"],
  "media": [{"type": "video", "videoUrl": "https://video.twimg.com/…mp4"}],
  "author": {"username": "apify", "name": "Apify", "followers": 15862}
}
```

A profile row from `profile` or `connections` mode carries `username`, `name`, `description`, `location`, `website`, `descriptionLinks`, `emails`, `followers`, `following`, `postsCount`, `verifiedType`, `createdAt` and an `about` block with `accountBasedIn`, `connectedVia` and `usernameChanges`. Trend rows have `name`, `rank`, `category`, `postCount`, `location` and `url`.

## Input parameters

| Parameter | Type | Description |
|---|---|---|
| `scrapeType` | string | `search`, `profile`, `userPosts`, `postDetail`, `postEngagement`, `connections`, `list`, `community`, `trends` |
| `targets` | array | Keywords, handles, profile/post URLs, list or community URLs, trend locations |
| `maxItems` | integer | Max results **per entry** (per keyword / profile / post); `0` = no limit |
| `searchType` | string | `latest`, `top`, `media`, `people` |
| `postsFrom` | string | Profile tab: `posts`, `replies`, `media`, `likes`, `highlights`, `articles` |
| `connectionType` | string | `followers`, `following`, `verifiedFollowers`, `mutuals`, `subscribers` |
| `engagementType` | string | `reposters`, `likers`, `quotes` |
| `listContent` / `communityContent` | string | `posts` or `members` |
| `start` / `end` | string | Date window, `YYYY-MM-DD` |
| `tweetLanguage` | string | Language code, e.g. `en`, `de`, `ja` |
| `minLikes` / `minRetweets` / `minReplies` | integer | Engagement floors |
| `findEmails` | boolean | Read e-mails from bios and linked websites (default on) |
| `includeAbout` | boolean | Add the "About this account" panel (default on) |
| `includeReplies` | boolean | For `postDetail`: include the reply thread |
| `useOurAccounts` / `cookies` | boolean / string | Use the actor's session pool (default) or your own cookies |

## More examples

| File | What it shows |
|---|---|
| [`examples/01_basic_usage.py`](examples/01_basic_usage.py) | Minimal keyword search, printed to the terminal |
| [`examples/02_followers_to_leads.py`](examples/02_followers_to_leads.py) | A competitor's followers filtered to accounts with e-mails and 500+ followers |
| [`examples/03_tweet_replies_and_reposters.py`](examples/03_tweet_replies_and_reposters.py) | Reply thread plus reposters of one post, with combined reach |
| [`examples/04_export_to_csv.py`](examples/04_export_to_csv.py) | Profile timeline to CSV with pandas, top posts by views |
| [`examples/05_export_to_google_sheets.py`](examples/05_export_to_google_sheets.py) | Today's trends appended to a Google Sheet |

## Pricing

The actor is pay-per-result. Posts, profiles, trends and e-mails found on linked websites cost **$0.20 per 1,000 on the free plan** and **from $0.14 per 1,000 on paid Apify plans**, plus a tiny per-run start fee. E-mails already visible in a bio are not charged separately, and inputs that return nothing are not charged at all. Compare that with $5.00 per 1,000 post reads on X's own pay-per-use API.

## FAQ

**Do I need an X developer account or API key?**
No. The [actor](https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python) runs on its own pool of logged-in sessions. You only need an Apify token.

**Is `maxItems` per run or per input?**
Per entry. Three keywords at `maxItems: 100` can return up to 300 rows.

**Can I get likers of someone else's post?**
X shows likers only to the post's author, so `likers` comes back empty for other people's posts. Use `reposters` or `quotes` instead.

**How far back can a profile timeline go?**
X stops profile timelines at roughly the last 3,200 posts. For older posts, use `search` with `from:handle` and a `start`/`end` window.

**Where do the e-mails come from?**
From the bio, display name and expanded bio links, and from one visit to the website the profile links to. Obfuscated spellings like `name (at) domain (dot) com` are recognised.

## Related actors

- [Threads Scraper — posts, profiles and replies](https://apify.com/pro100chok/threads-scraper-usage?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python) — the same workflow for Meta's Threads.
- [Instagram Scraper — profiles, posts, reels, comments](https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python)
- [Reddit Scraper — posts, comments, users, emails](https://apify.com/pro100chok/reddit-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python)
- [YouTube Scraper — videos, comments, transcripts, channel emails](https://apify.com/pro100chok/youtube-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python)
- [TikTok Profile Scraper with contacts and emails](https://apify.com/pro100chok/tiktok-profile-pro?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python)

## License

MIT — see [LICENSE](LICENSE). Collect public data only and respect GDPR when storing e-mails.

---

Built by [pro100chok](https://apify.com/pro100chok/x-twitter-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=twitter-x-tweets-followers-scraper-python) on Apify.
