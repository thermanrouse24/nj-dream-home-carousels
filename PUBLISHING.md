# Free publisher (replaces Metricool)

Metricool's free plan allows about 20 published posts a month. We post about 20 a day, so
publishing now runs from this repo, for free:

| Network | How it posts | Free limit | We use per day |
|---|---|---|---|
| Instagram (feed carousel with motion slides, Stories, optional Reel) | Meta's official Instagram API, from GitHub Actions | 50 to 100 posts per 24 h | about 12 |
| Facebook Page (6-photo post) | Meta's official Pages API | no practical limit | 3 |
| Threads (6-photo carousel, quote and card images) | Meta's official Threads API | 250 posts per 24 h | about 5 |
| TikTok (photo posts) | Buffer's free plan + Buffer's free API, with an exact time | Buffer free: 3 channels, 10 queued posts per channel, 3,000 API calls a month | about 5 |

How it works:
1. The daily build makes the posts and emails Therm for approval (unchanged).
2. When Therm approves, the approval agent runs `publisher/enqueue.py`, which writes one file per
   post into `queue/<date>/`, and pushes. Nothing else ever writes to `queue/`.
3. GitHub Actions (`.github/workflows/publish.yml`) runs every 10 minutes and posts whatever is due.
   It waits for the exact minute, but GitHub sometimes starts scheduled runs 5 to 20 minutes late,
   so a post can go out a few minutes after its slot time. TikTok items are handed to Buffer up to
   26 hours ahead with their exact time (Buffer posts them on time).
4. Each queue file is updated with the result and committed, so `queue/` is also the posting log.
   Before touching a platform the item is claimed (`publishing`) and pushed, so a crash can never
   cause a double post. A clear platform error is retried twice (`retry`, then `failed`). If the
   platform did not answer clearly after the final "publish" call, the item becomes
   `needs_check` and is never re-posted automatically (look at the account, then set it to
   `published` or `queued`). Anything more than 3 hours late is never posted (`expired`).
   The approval agent reports `failed`, `needs_check`, `expired` and stuck `publishing` items to Therm.
5. TikTok rule (Therm, Oct 23 2026): TikTok has no bio link, so every TikTok post says
   'DM me "HOME" to get started.' and never "link in my bio". The publisher refuses any TikTok
   item that breaks this.

Instagram Reel music: Instagram's API cannot attach licensed songs, so a Reel posted this way only
has its own (silent) audio. Reels are OFF by default (`enqueue.py --reel` turns one on).

## One-time setup (Therm, about 30 to 45 minutes)

Until a network is set up, its approved posts wait in the queue and are marked `expired` once they
are more than 3 hours late (they are never posted late).
You can set up one network at a time; each one starts posting as soon as its secrets are in.

### 1. Instagram + Facebook (Meta), about 20 minutes
1. Instagram @therm.realtor must be a Business or Creator account, linked to your Facebook Page
   (Instagram app > Settings > Accounts Center, or Facebook Page > Settings > Linked accounts).
2. Go to https://developers.facebook.com > My Apps > Create App. Name it "NJ Dream Home Publisher".
   Pick the use case for managing Instagram/Pages content (or "Other" > "Business"). You don't need
   App Review: as the app's admin you can post to your own Page and Instagram while the app stays
   in Development mode.
3. Open Tools > Graph API Explorer. Choose your app, then "Get User Access Token" with these
   permissions: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
   `instagram_basic`, `instagram_content_publish`, `business_management`. Log in and select your
   Page and your Instagram account.
4. Make it long-lived: click the "i" next to the token > "Open in Access Token Tool" > "Extend
   Access Token". Copy the long-lived token back into the Explorer.
5. In the Explorer, run `GET me/accounts`. Copy your Page's `access_token` (a Page token made from
   a long-lived user token does not expire). That is **META_PAGE_TOKEN**.

### 2. Threads, about 10 minutes
1. In the same app (or a second app if Meta asks) add the use case "Access the Threads API" with
   `threads_basic` and `threads_content_publish`.
2. App roles > Roles > add your Threads account as a Threads Tester, then accept the invite in the
   Threads app (Settings > Account > Website permissions > Invites).
3. In the Threads use case settings, use the User Token Generator to make a token for your
   account. If it is short-lived, exchange it:
   `https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=<APP SECRET>&access_token=<TOKEN>`
   The long-lived token is **THREADS_TOKEN** (good for 60 days; see step 5 to auto-renew it).

### 3. TikTok via Buffer, about 5 minutes
1. Make a free account at https://buffer.com and connect ONLY your TikTok (free plan = 3 channels).
2. Settings > API (or https://publish.buffer.com/settings/api) > create an API key. That is
   **BUFFER_API_KEY**.

### 4. Put the secrets in GitHub
1. https://github.com/thermanrouse24/nj-dream-home-carousels > Settings > Secrets and variables >
   Actions > New repository secret. Add `META_PAGE_TOKEN`, `THREADS_TOKEN`, `BUFFER_API_KEY`.
2. Actions tab > "Check publisher setup" > Run workflow. It prints your ids (it never prints
   tokens). Add them as secrets too: `IG_USER_ID`, `FB_PAGE_ID`, `THREADS_USER_ID`,
   `BUFFER_TIKTOK_CHANNEL_ID`. Run it again until it says ALL READY.

### 5. Optional: auto-renew the Threads token
Create a fine-grained GitHub token (github.com > Settings > Developer settings > Fine-grained
tokens) for this repo only, with "Secrets: Read and write". Save it as the secret
`GH_SECRETS_PAT`. The "Refresh Threads token" workflow then renews THREADS_TOKEN every Monday.
Without it, make a new Threads token every 60 days.

## Commands
- Queue an approved carousel: `python3 publisher/enqueue.py carousel specs/<date>_A.json --time 04:45`
  (add `--reel` for the Instagram Reel 1 hour later, `--manual-ig` if Therm posts the IG feed himself)
- Queue an approved quote: `python3 publisher/enqueue.py quote <Quote ID> --date <date> --time 09:15 --text "<quote>"`
- Queue a business card story: `python3 publisher/enqueue.py card --date <date> --time 07:15`
- Check the queue without posting: `python3 publisher/publish.py --dry-run`
- Post one item now (testing): Actions > "Publish approved posts" > Run workflow > item id.

Security: tokens live only in GitHub Actions secrets (encrypted, never in the repo or the logs).
