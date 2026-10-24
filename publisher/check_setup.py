#!/usr/bin/env python3
"""Check the publisher's secrets and print the ids you need (run it from the
"Check publisher setup" workflow, or locally with the same environment variables).

It never prints tokens. For each platform it says READY or what is missing/wrong.
"""
import json, os, sys
import requests

GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v23.0")
e = lambda k: (os.environ.get(k) or "").strip()
ok_all = True


def say(name, ok, msg):
    global ok_all
    ok_all &= ok
    print(f"{'READY ' if ok else 'NOT READY'}  {name}: {msg}")


# Meta: Page token -> page + linked Instagram account
tok = e("META_PAGE_TOKEN")
if not tok:
    say("Instagram + Facebook", False, "add the META_PAGE_TOKEN secret")
else:
    r = requests.get(f"{GRAPH}/me", params={"fields": "id,name,instagram_business_account{id,username}", "access_token": tok}, timeout=30).json()
    if "error" in r:
        say("Instagram + Facebook", False, f"token rejected: {r['error'].get('message')}")
    else:
        ig = r.get("instagram_business_account") or {}
        print(f"  Page: {r.get('name')}  FB_PAGE_ID = {r.get('id')}")
        print(f"  Instagram: @{ig.get('username')}  IG_USER_ID = {ig.get('id')}")
        say("Facebook", e("FB_PAGE_ID") == r.get("id"), "FB_PAGE_ID matches" if e("FB_PAGE_ID") == r.get("id") else "set FB_PAGE_ID to the id above")
        if not ig:
            say("Instagram", False, "no Instagram professional account is linked to this Page")
        else:
            say("Instagram", e("IG_USER_ID") == ig.get("id"), "IG_USER_ID matches" if e("IG_USER_ID") == ig.get("id") else "set IG_USER_ID to the id above")
            lim = requests.get(f"{GRAPH}/{ig['id']}/content_publishing_limit", params={"fields": "quota_usage,config", "access_token": tok}, timeout=30).json()
            print(f"  Instagram publishing quota (24h): {json.dumps(lim.get('data', lim))[:300]}")

# Threads
tt = e("THREADS_TOKEN")
if not tt:
    say("Threads", False, "add the THREADS_TOKEN secret")
else:
    r = requests.get("https://graph.threads.net/v1.0/me", params={"fields": "id,username", "access_token": tt}, timeout=30).json()
    if "error" in r:
        say("Threads", False, f"token rejected: {r['error'].get('message')}")
    else:
        print(f"  Threads: @{r.get('username')}  THREADS_USER_ID = {r.get('id')}")
        say("Threads", e("THREADS_USER_ID") == r.get("id"), "THREADS_USER_ID matches" if e("THREADS_USER_ID") == r.get("id") else "set THREADS_USER_ID to the id above")

# Buffer (TikTok)
bk = e("BUFFER_API_KEY")
if not bk:
    say("TikTok (Buffer)", False, "add the BUFFER_API_KEY secret")
else:
    h = {"Authorization": f"Bearer {bk}", "Content-Type": "application/json"}
    r = requests.post("https://api.buffer.com", headers=h, timeout=30,
                      json={"query": "query { account { organizations { id name } } }"}).json()
    orgs = (((r.get("data") or {}).get("account") or {}).get("organizations")) or []
    if not orgs:
        say("TikTok (Buffer)", False, f"key rejected or no organization: {json.dumps(r)[:300]}")
    else:
        found = None
        for o in orgs:
            q = 'query { channels(input: {organizationId: %s}) { id name service } }' % json.dumps(o["id"])
            c = requests.post("https://api.buffer.com", headers=h, timeout=30, json={"query": q}).json()
            for ch in ((c.get("data") or {}).get("channels")) or []:
                print(f"  Buffer channel: {ch['service']} {ch['name']}  id = {ch['id']}")
                if ch.get("service", "").lower() == "tiktok":
                    found = ch["id"]
            if c.get("errors"):
                print("  Buffer channels query error:", json.dumps(c["errors"])[:300])
        if not found:
            say("TikTok (Buffer)", False, "connect TikTok in Buffer, then set BUFFER_TIKTOK_CHANNEL_ID")
        else:
            m = e("BUFFER_TIKTOK_CHANNEL_ID") == found
            say("TikTok (Buffer)", m, "BUFFER_TIKTOK_CHANNEL_ID matches" if m else f"set BUFFER_TIKTOK_CHANNEL_ID to {found}")

print("\nALL READY" if ok_all else "\nSome platforms are not ready yet (their posts wait in the queue).")
sys.exit(0 if ok_all else 1)
