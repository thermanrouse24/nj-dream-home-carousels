# Posting queue

One JSON file per approved post, in `queue/<YYYY-MM-DD>/`, written only by `publisher/enqueue.py`
after Therm approves. `publisher/publish.py` (GitHub Actions, every 10 minutes) posts each one at
its `publish_at` time and records the result in the same file.

Status: `queued` > `published` (or `scheduled_in_buffer` for TikTok) | `retry` | `failed` |
`expired` (more than 3 hours late, never posted) | `invalid`.
To cancel a post before its time, delete its file and push.
