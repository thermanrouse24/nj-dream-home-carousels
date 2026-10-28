#!/usr/bin/env python3
"""Free auto-publisher for NJ Dream Home (replaces Metricool).

Runs in GitHub Actions every 10 minutes (.github/workflows/publish.yml). It reads queue items
(queue/YYYY-MM-DD/*.json, written by publisher/enqueue.py after Therm approves) and posts each
one when its time comes, using the platforms' own free APIs:

  instagram  carousel (photos + motion MP4s), story (one story per frame), reel   Instagram Graph API
  facebook   multi-photo post                                                        Facebook Pages API
  threads    carousel or single image                                                Threads API
  tiktok     photo post, handed to Buffer's free API with an exact time              Buffer GraphQL API

Nothing is published unless it is in queue/ with status "queued", and only approved posts are
ever written to queue/. After each item, the item file is updated (status, post ids or the error)
and the workflow commits it back, so the queue is also the log.

Usage:
  python3 publisher/publish.py                 # publish everything due now (+ lookahead)
  python3 publisher/publish.py --dry-run       # validate the queue, publish nothing
  python3 publisher/publish.py --only <item id> --force   # publish one item now (testing)

Secrets (GitHub Actions secrets, see PUBLISHING.md):
  META_PAGE_TOKEN   Facebook Page access token with instagram_content_publish + pages_manage_posts
  IG_USER_ID        Instagram professional account id (linked to the Page)
  FB_PAGE_ID        Facebook Page id
  THREADS_TOKEN     Threads long-lived user token (threads_basic, threads_content_publish)
  THREADS_USER_ID   Threads user id
  BUFFER_API_KEY    Buffer API key (free plan)
  BUFFER_TIKTOK_CHANNEL_ID  Buffer channel id of the TikTok account
A platform whose secrets are missing is skipped (its items stay "queued") and reported.
"""
import argparse, datetime as dt, glob, json, os, subprocess, sys, time

try:
    import requests
except ImportError:  # pragma: no cover
    print("pip install requests"); raise

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
QUEUE = os.path.join(ROOT, "queue")
RAW_PREFIX = "https://raw.githubusercontent.com/thermanrouse24/nj-dream-home-carousels/main/"
GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v23.0")
THREADS = "https://graph.threads.net/v1.0"
BUFFER = "https://api.buffer.com"
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York")  # printing only; item times carry their own offset

LOOKAHEAD_MIN = int(os.environ.get("LOOKAHEAD_MIN", "11"))   # wait for items due before the next run
STALE_HOURS = float(os.environ.get("STALE_HOURS", "3"))      # never post something this late
MAX_ATTEMPTS = 3


class PublishError(Exception):
    """The platform answered with a clear error: nothing was posted, safe to retry."""


class UncertainError(PublishError):
    """No clear answer (network error, timeout): the post MAY have gone out. Never auto-retry."""


def now():
    return dt.datetime.now(dt.timezone.utc)


def parse(ts):
    return dt.datetime.fromisoformat(ts)


def env(name):
    v = os.environ.get(name, "").strip()
    return v or None


def platform_ready(p):
    need = {
        "instagram": ["META_PAGE_TOKEN", "IG_USER_ID"],
        "facebook": ["META_PAGE_TOKEN", "FB_PAGE_ID"],
        "threads": ["THREADS_TOKEN", "THREADS_USER_ID"],
        "tiktok": ["BUFFER_API_KEY", "BUFFER_TIKTOK_CHANNEL_ID"],
    }[p]
    missing = [n for n in need if not env(n)]
    return (not missing), missing


def local_path(url):
    """A local copy of a video for direct upload: the checked-out repo file for raw GitHub URLs,
    otherwise (e.g. home tour videos in the GitHub release) a downloaded temp file."""
    if url.startswith(RAW_PREFIX):
        p = os.path.join(ROOT, url[len(RAW_PREFIX):])
        if os.path.exists(p):
            return p
    if url.lower().endswith(".mp4"):
        import tempfile
        p = os.path.join(tempfile.mkdtemp(), "video.mp4")
        try:
            with requests.get(url, stream=True, timeout=300, allow_redirects=True) as r:
                r.raise_for_status()
                with open(p, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
        except requests.RequestException as e:
            raise PublishError(f"could not download video {url}: {type(e).__name__}")
        return p
    return None


def rupload(upload_url, token, path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        r = requests.post(upload_url, data=f.read(), timeout=600, headers={
            "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)})
    try:
        ok = r.status_code < 400 and r.json().get("success")
    except ValueError:
        ok = False
    if not ok:
        raise PublishError(redact(f"video upload failed {r.status_code}: {r.text[:400]}"))


SECRET_VALUES = [v for k, v in os.environ.items() if v and len(v) > 8 and k.endswith(("TOKEN", "KEY", "PAT"))]


def redact(text):
    text = str(text)
    for v in SECRET_VALUES:
        text = text.replace(v, "***")
    return text


def threads_len(text):
    """Threads counts characters outside the basic plane (emoji) as UTF-8 bytes."""
    return sum(len(c.encode()) if ord(c) > 0xFFFF else 1 for c in text)


def check_url(url):
    r = requests.head(url, timeout=30, allow_redirects=True)
    if r.status_code != 200:
        raise PublishError(f"media not reachable ({r.status_code}): {url}")


def api(method, url, token=None, **kw):
    """Token goes in the Authorization header (never in the URL), so errors can't leak it."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = requests.request(method, url, headers=headers, timeout=120, **kw)
    except requests.RequestException as e:
        raise UncertainError(redact(f"{method} {url.split('?')[0]} network error: {type(e).__name__}"))
    try:
        data = r.json()
    except ValueError:
        data = {"raw": r.text[:500]}
    if r.status_code >= 400 or (isinstance(data, dict) and "error" in data):
        err = data.get("error", data) if isinstance(data, dict) else data
        raise PublishError(redact(f"{method} {url.split('?')[0]} -> {r.status_code}: {json.dumps(err)[:600]}"))
    return data


# ---------------- Instagram ----------------

def _no_checkpoint(item):
    pass


CHECKPOINT = _no_checkpoint   # main() sets this: saves the item and pushes it BEFORE a final publish call


def mark_publishing(item, **info):
    """Record that we are about to make the call that makes a post public. If that call or the
    run dies afterwards, the item becomes "needs_check" instead of being posted again."""
    item["publish_called"] = True
    item.setdefault("result", {}).update(info)
    CHECKPOINT(item)


def ig_wait(container_id, token, timeout=300):
    t0 = time.time()
    while True:
        d = api("GET", f"{GRAPH}/{container_id}", token, params={"fields": "status_code,status"})
        code = d.get("status_code")
        if code in ("FINISHED", "PUBLISHED"):
            return
        if code in ("ERROR", "EXPIRED"):
            raise PublishError(f"Instagram container {container_id} {code}: {d.get('status')}")
        if time.time() - t0 > timeout:
            raise PublishError(f"Instagram container {container_id} still {code} after {timeout}s")
        time.sleep(15)


def ig_video_container(ig, token, url, media_type, extra):
    """Create a video container. Uploads the repo file directly (resumable upload), because
    raw.githubusercontent.com serves MP4s as application/octet-stream; falls back to video_url."""
    path = local_path(url)
    if path:
        d = api("POST", f"{GRAPH}/{ig}/media", token,
                data={"media_type": media_type, "upload_type": "resumable", **extra})
        cid, uri = d["id"], d.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{GRAPH.rsplit('/', 1)[1]}/{d['id']}"
        rupload(uri, token, path)
        return cid
    d = api("POST", f"{GRAPH}/{ig}/media", token,
            data={"media_type": media_type, "video_url": url, **extra})
    return d["id"]


def ig_publish(ig, token, creation_id, item, key="ig_creation_id"):
    mark_publishing(item, **{key: creation_id})
    d = api("POST", f"{GRAPH}/{ig}/media_publish", token, data={"creation_id": creation_id})
    return d["id"]


def instagram(item):
    token, ig = env("META_PAGE_TOKEN"), env("IG_USER_ID")
    kind, media = item["type"], item["media"]
    if kind == "carousel":
        if not 2 <= len(media) <= 10:
            raise PublishError("Instagram carousel needs 2 to 10 items")
        children = []
        for u in media:
            if u.lower().endswith(".mp4"):
                cid = ig_video_container(ig, token, u, "VIDEO", {"is_carousel_item": "true"})
            else:
                cid = api("POST", f"{GRAPH}/{ig}/media", token, data={
                    "image_url": u, "is_carousel_item": "true"})["id"]
            children.append(cid)
        for cid in children:
            ig_wait(cid, token)
        parent = api("POST", f"{GRAPH}/{ig}/media", token, data={
            "media_type": "CAROUSEL", "children": ",".join(children),
            "caption": item.get("caption", "")})["id"]
        ig_wait(parent, token)
        return {"ig_media_id": ig_publish(ig, token, parent, item)}
    if kind == "story":
        ids = item.setdefault("result", {}).setdefault("ig_story_ids", [])
        for i, u in enumerate(media):  # one story per frame, in order; resume after frames already up
            if i < len(ids):
                continue
            if u.lower().endswith(".mp4"):
                cid = ig_video_container(ig, token, u, "STORIES", {})
            else:
                cid = api("POST", f"{GRAPH}/{ig}/media", token, data={
                    "media_type": "STORIES", "image_url": u})["id"]
            ig_wait(cid, token)
            ids.append(ig_publish(ig, token, cid, item, key=f"ig_story_creation_{i + 1}"))
            item["publish_called"] = False      # this frame is confirmed; the next one starts clean
            CHECKPOINT(item)
            time.sleep(3)
        return {"ig_story_ids": ids}
    if kind == "reel":
        extra = {"caption": item.get("caption", "")}
        if item.get("ig_audio"):  # Instagram Audio API (May 2026): attach a licensed song to the Reel
            import ig_audio
            hit = ig_audio.resolve(token, ig, item["ig_audio"], item.get("ig_audio_backup"))
            if not hit:
                raise PublishError(f"Instagram audio not found for {item['ig_audio']!r} "
                                   f"(backup {item.get('ig_audio_backup')!r}); not posting a silent Reel")
            extra["audio_configuration"] = ig_audio.audio_configuration(
                hit["audio_id"], item.get("audio_volume"), item.get("video_volume"))
            item.setdefault("result", {})["ig_audio_used"] = f"{hit['title']} - {hit['artist']} ({hit['audio_id']})"
        cid = ig_video_container(ig, token, media[0], "REELS", extra)
        ig_wait(cid, token)
        return {"ig_media_id": ig_publish(ig, token, cid, item)}
    if kind == "image":
        cid = api("POST", f"{GRAPH}/{ig}/media", token, data={
            "image_url": media[0], "caption": item.get("caption", "")})["id"]
        ig_wait(cid, token)
        return {"ig_media_id": ig_publish(ig, token, cid, item)}
    raise PublishError(f"unknown Instagram type {kind}")


# ---------------- Facebook ----------------

def facebook_reel(item, token, page):
    """Facebook Reel (home tours): start, upload the file, then publish."""
    path = local_path(item["media"][0])
    d = api("POST", f"{GRAPH}/{page}/video_reels", token, data={"upload_phase": "start"})
    vid = d["video_id"]
    rupload(d.get("upload_url") or f"https://rupload.facebook.com/video-upload/{GRAPH.rsplit('/', 1)[1]}/{vid}", token, path)
    mark_publishing(item, fb_video_id=vid)
    api("POST", f"{GRAPH}/{page}/video_reels", token, data={
        "upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
        "description": item.get("caption", "")})
    return {"fb_reel_id": vid}


def facebook(item):
    token, page = env("META_PAGE_TOKEN"), env("FB_PAGE_ID")
    if item["type"] == "reel":
        return facebook_reel(item, token, page)
    photos = [u for u in item["media"] if not u.lower().endswith(".mp4")]
    if not photos:
        raise PublishError("Facebook post needs photos")
    ids = []
    for u in photos:
        d = api("POST", f"{GRAPH}/{page}/photos", token, data={"url": u, "published": "false"})
        ids.append(d["id"])
    data = {"message": item.get("caption", "")}
    for i, pid in enumerate(ids):
        data[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    mark_publishing(item)
    d = api("POST", f"{GRAPH}/{page}/feed", token, data=data)
    return {"fb_post_id": d["id"]}


# ---------------- Threads ----------------

def threads_wait(cid, token, timeout=300):
    t0 = time.time()
    while True:
        d = api("GET", f"{THREADS}/{cid}", token, params={"fields": "status,error_message"})
        st = d.get("status")
        if st in ("FINISHED", "PUBLISHED"):
            return
        if st in ("ERROR", "EXPIRED"):
            raise PublishError(f"Threads container {cid} {st}: {d.get('error_message')}")
        if time.time() - t0 > timeout:
            raise PublishError(f"Threads container {cid} still {st}")
        time.sleep(15)


def threads(item):
    token, uid = env("THREADS_TOKEN"), env("THREADS_USER_ID")
    text = item.get("caption", "")
    if threads_len(text) > 500:
        raise PublishError(f"Threads text is {threads_len(text)} characters (limit 500)")
    photos = [u for u in item["media"] if not u.lower().endswith(".mp4")]
    if len(photos) == 1:
        cid = api("POST", f"{THREADS}/{uid}/threads", token, data={
            "media_type": "IMAGE", "image_url": photos[0], "text": text})["id"]
    elif len(photos) >= 2:
        kids = []
        for u in photos[:20]:
            kids.append(api("POST", f"{THREADS}/{uid}/threads", token, data={
                "media_type": "IMAGE", "image_url": u, "is_carousel_item": "true"})["id"])
        for k in kids:
            threads_wait(k, token)
        cid = api("POST", f"{THREADS}/{uid}/threads", token, data={
            "media_type": "CAROUSEL", "children": ",".join(kids), "text": text})["id"]
    else:
        cid = api("POST", f"{THREADS}/{uid}/threads", token, data={
            "media_type": "TEXT", "text": text})["id"]
    threads_wait(cid, token)
    mark_publishing(item, threads_creation_id=cid)
    d = api("POST", f"{THREADS}/{uid}/threads_publish", token, data={"creation_id": cid})
    return {"threads_post_id": d["id"]}


# ---------------- TikTok via Buffer ----------------

ENUMS = {"schedulingType", "mode"}


def gql(v, key=None):
    """Python value -> GraphQL literal (inline, so we don't depend on Buffer's input type names)."""
    if isinstance(v, dict):
        return "{" + " ".join(f"{k}: {gql(x, k)}" for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(gql(x) for x in v) + "]"
    if key in ENUMS:
        return str(v)
    return json.dumps(v, ensure_ascii=False)


def tiktok(item):
    key, channel = env("BUFFER_API_KEY"), env("BUFFER_TIKTOK_CHANNEL_ID")
    due = max(parse(item["publish_at"]).astimezone(dt.timezone.utc), now() + dt.timedelta(minutes=3))
    assets = [{"video": {"url": u}} if u.lower().endswith(".mp4") else {"image": {"url": u}}
              for u in item["media"]]
    payload = {
        "text": item.get("caption", ""),
        "channelId": channel,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": due.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "assets": assets,
    }
    query = ("mutation { createPost(input: " + gql(payload) + ") { "
             "... on PostActionSuccess { post { id dueAt } } ... on MutationError { message } } }")
    mark_publishing(item)
    try:
        r = requests.post(BUFFER, json={"query": query}, timeout=120,
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    except requests.RequestException as e:
        raise UncertainError(f"Buffer network error: {type(e).__name__}")
    try:
        d = r.json()
    except ValueError:
        raise PublishError(redact(f"Buffer {r.status_code}: {r.text[:400]}"))
    if r.status_code >= 400 or d.get("errors"):
        raise PublishError(redact(f"Buffer {r.status_code}: {json.dumps(d.get('errors', d))[:600]}"))
    res = (d.get("data") or {}).get("createPost") or {}
    if "message" in res and "post" not in res:
        raise PublishError(f"Buffer: {res['message']}")
    return {"buffer_post_id": res.get("post", {}).get("id"), "buffer_due_at": res.get("post", {}).get("dueAt")}


HANDLERS = {"instagram": instagram, "facebook": facebook, "threads": threads, "tiktok": tiktok}


# ---------------- queue handling ----------------

def load_items():
    items = []
    for f in sorted(glob.glob(os.path.join(QUEUE, "*", "*.json"))):
        with open(f) as fh:
            it = json.load(fh)
        it["_file"] = f
        items.append(it)
    return items


def save(it):
    f = it.pop("_file")
    with open(f, "w") as fh:
        json.dump(it, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    it["_file"] = f


def git_commit(msg):
    """Commit and push queue/. Returns False if the push did not land (caller must stop)."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return True
    subprocess.run(["git", "add", "queue"], cwd=ROOT, check=False)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0:
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=ROOT, check=False)
    for _ in range(4):
        if subprocess.run(["git", "pull", "-q", "--rebase", "origin", "main"], cwd=ROOT).returncode != 0:
            subprocess.run(["git", "rebase", "--abort"], cwd=ROOT, check=False)
        if subprocess.run(["git", "push", "-q", "origin", "HEAD:main"], cwd=ROOT).returncode == 0:
            return True
        time.sleep(5)
    return False


def checkpoint(item):
    save(item)
    if not git_commit(f"publisher: {item['id']} {item.get('status')}"):
        raise SystemExit(f"STOP: could not push status of {item['id']}; stopping so nothing double-posts")


TIKTOK_CTA = 'DM me "HOME" to get started.'


def validate(it):
    problems = []
    for k in ("id", "platform", "type", "publish_at", "media", "status"):
        if k not in it:
            problems.append(f"missing {k}")
    if it.get("platform") not in HANDLERS:
        problems.append(f"bad platform {it.get('platform')}")
    try:
        if parse(it["publish_at"]).tzinfo is None:
            problems.append("publish_at needs a timezone offset")
    except Exception:
        problems.append("bad publish_at")
    cap = it.get("caption", "") or ""
    if it.get("platform") == "threads" and threads_len(cap) > 500:
        problems.append("Threads caption over 500 characters")
    if it.get("platform") == "instagram" and len(cap) > 2200:
        problems.append("Instagram caption over 2,200 characters")
    if it.get("platform") == "tiktok":  # Therm's rule: TikTok has no bio link, every post says DM HOME
        if "link in my bio" in cap.lower():
            problems.append("TikTok caption says 'link in my bio' (use DM me \"HOME\")")
        if TIKTOK_CTA not in cap:
            problems.append("TikTok caption must include: " + TIKTOK_CTA)
    if it.get("tour") and not it.get("has_music"):  # Therm's rule (Oct 28 2026)
        problems.append("home tour has no music: never post tours without music")
    if not isinstance(it.get("media"), list) or not it.get("media"):
        problems.append("media must be a non-empty list")
    for u in it.get("media") or []:
        if not str(u).startswith("https://"):
            problems.append(f"media must be a public https URL: {u}")
    return problems


def main():
    global CHECKPOINT
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--force", action="store_true", help="with --only: publish now regardless of time")
    a = ap.parse_args()
    CHECKPOINT = (lambda item: None) if a.dry_run else checkpoint

    items = load_items()
    t_now = now()
    horizon = t_now + dt.timedelta(minutes=LOOKAHEAD_MIN)
    summary, missing_report = [], {}

    def when(it):
        try:
            return parse(it["publish_at"]).astimezone(dt.timezone.utc)
        except Exception:
            return t_now

    def due(it):
        if a.only:
            return it.get("id") == a.only
        t = when(it)
        if it.get("platform") == "tiktok":  # hand to Buffer up to 26 h ahead (free plan holds 10 per channel)
            return t <= t_now + dt.timedelta(hours=26)
        return t <= horizon

    todo = [it for it in items if it.get("status") in ("queued", "retry") and due(it)]
    todo.sort(key=when)

    for it in todo:
        probs = validate(it)
        if probs:
            it["status"], it["error"] = "invalid", "; ".join(probs)
            summary.append(f"INVALID {it.get('id')}: {it['error']}")
            if not a.dry_run:
                save(it)
                git_commit(f"publisher: {it.get('id')} invalid")
            continue
        t = when(it)
        if not a.force and t_now - t > dt.timedelta(hours=STALE_HOURS):
            it["status"], it["error"] = "expired", f"not posted: more than {STALE_HOURS:g} h late"
            summary.append(f"EXPIRED {it['id']}")
            if not a.dry_run:
                save(it)
                git_commit(f"publisher: {it['id']} expired")
            continue
        ok, missing = platform_ready(it["platform"])
        if not ok:
            missing_report.setdefault(it["platform"], missing)
            summary.append(f"WAITING {it['id']}: {it['platform']} not set up ({', '.join(missing)})")
            continue
        try:
            for u in it["media"]:
                check_url(u)
        except Exception as e:
            summary.append(f"MEDIA {it['id']}: {redact(e)}")
            if not a.dry_run:
                it["attempts"] = it.get("attempts", 0) + 1
                it["error"] = redact(e)
                it["status"] = "failed" if it["attempts"] >= MAX_ATTEMPTS else "retry"
                save(it)
                git_commit(f"publisher: {it['id']} media problem")
            continue
        if a.dry_run:
            summary.append(f"DRY-RUN OK {it['id']} ({it['platform']} {it['type']}, {len(it['media'])} media) at {it['publish_at']}")
            continue
        wait = (t - now()).total_seconds()  # never post early: wait for the exact minute
        if wait > 0 and it["platform"] != "tiktok" and not a.force:
            print(f"waiting {int(wait)}s for {it['id']}")
            time.sleep(wait)
        # claim it (pushed) before touching the platform, so a crash can never lead to a repost
        it["status"], it["claimed_at"], it["publish_called"] = "publishing", now().isoformat(), False
        checkpoint(it)
        try:
            res = HANDLERS[it["platform"]](it)
            it["status"] = "scheduled_in_buffer" if it["platform"] == "tiktok" else "published"
            it.setdefault("result", {}).update(res)
            it["published_at"] = now().isoformat()
            it.pop("error", None)
            summary.append(f"OK {it['id']}: {res}")
        except SystemExit:
            raise
        except Exception as e:
            msg = redact(e)[:1000]
            it["attempts"] = it.get("attempts", 0) + 1
            it["error"] = msg
            if it.get("publish_called") and not (isinstance(e, PublishError) and not isinstance(e, UncertainError)):
                it["status"] = "needs_check"   # may already be live: a person checks, never auto-reposted
            else:
                it["status"] = "failed" if it["attempts"] >= MAX_ATTEMPTS else "retry"
            summary.append(f"FAILED {it['id']} -> {it['status']} (attempt {it['attempts']}): {msg}")
        it["publish_called"] = False
        checkpoint(it)

    for line in summary:
        print(line)
    if missing_report:
        print("Not set up yet:", json.dumps(missing_report))
    if not summary:
        print(f"Nothing due at {t_now.astimezone(ET):%Y-%m-%d %H:%M} ET")
    failed = [x for x in summary if x.startswith(("FAILED", "INVALID", "MEDIA"))]
    sys.exit(1 if failed else 0)  # a red run in GitHub Actions shows (and emails) the failure


if __name__ == "__main__":
    main()
