#!/usr/bin/env python3
"""Runs in GitHub Actions (.github/workflows/shots.yml). The daily build can't reach most sites from
its sandbox, so it asks the robot for screenshots: shots/requests/<name>.json
  {"url": "https://www.fema.gov/...", "find": "text to circle", "scroll_to": "optional", "selector": "optional css",
   "width": 1200, "height": 900, "status": "new"}
Result: shots/<name>.png, and the request gets "status": "done" + "circle" (or "failed" + "error")."""
import glob, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in sorted(glob.glob(os.path.join(ROOT, "shots", "requests", "*.json"))):
    r = json.load(open(p))
    if r.get("status") != "new":
        continue
    name = os.path.splitext(os.path.basename(p))[0]
    out = os.path.join("shots", name + ".png")
    cmd = [sys.executable, os.path.join(ROOT, "tools", "shoot.py"), r["url"], os.path.join(ROOT, out),
           "--width", str(r.get("width", 1200)), "--height", str(r.get("height", 900))]
    for k, f in (("find", "--find"), ("scroll_to", "--scroll-to"), ("selector", "--selector")):
        if r.get(k):
            cmd += [f, r[k]]
    pr = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if pr.returncode == 0 and os.path.exists(os.path.join(ROOT, out)):
        r["status"] = "done"; r["shot"] = out
        for ln in pr.stdout.splitlines():
            if ln.startswith("{"):
                r.update(json.loads(ln))
    else:
        r["status"] = "failed"; r["error"] = (pr.stderr or pr.stdout)[-600:]
    json.dump(r, open(p, "w"), indent=1)
    print(name, r["status"])
