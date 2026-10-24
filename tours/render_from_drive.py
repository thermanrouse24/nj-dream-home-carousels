#!/usr/bin/env python3
"""Render new Home Tour specs (runs in GitHub Actions: .github/workflows/tour-render.yml).

For every tours/specs/*.json with "status": "new":
  1. download the edited tour from Google Drive (drive_file_id)
       - with GDRIVE_SA_JSON (service account key) if that secret exists, else
       - with gdown, which works when the folder is shared "Anyone with the link: Viewer"
  2. run tours/make_tour.py (town big, county small for 2.5 s; business card end frame;
     a TikTok copy whose end card says DM ME "HOME")
  3. upload both MP4s to the GitHub release "tours" (big videos stay out of the repo)
  4. commit tours/previews/<id>_cover.jpg and _preview.jpg, and set the spec to "rendered"
     with ig_url / tiktok_url, or to "render_failed" with the error.
"""
import glob, json, os, subprocess, sys, tempfile, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.environ.get("GITHUB_REPOSITORY", "thermanrouse24/nj-dream-home-carousels")
TAG = "tours"


def sh(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if p.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {p.stderr[-800:]}")
    return p.stdout


def download(file_id, out):
    sa = os.environ.get("GDRIVE_SA_JSON", "").strip()
    if sa:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        creds = service_account.Credentials.from_service_account_info(
            json.loads(sa), scopes=["https://www.googleapis.com/auth/drive.readonly"])
        svc = build("drive", "v3", credentials=creds, cache_discovery=False)
        req = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
        with open(out, "wb") as fh:
            dl = MediaIoBaseDownload(fh, req, chunksize=32 * 1024 * 1024)
            done = False
            while not done:
                _, done = dl.next_chunk()
    else:
        import gdown
        gdown.download(id=file_id, output=out, quiet=True)
    if not os.path.exists(out) or os.path.getsize(out) < 100_000:
        raise RuntimeError("download failed: share the Drive folder as 'Anyone with the link: Viewer' "
                           "or add the GDRIVE_SA_JSON secret (see PUBLISHING.md, Home Tours)")


def main():
    specs = sorted(glob.glob(os.path.join(HERE, "specs", "*.json")))
    todo = [p for p in specs if json.load(open(p)).get("status") == "new"]
    if not todo:
        print("no new tour specs"); return
    # make sure the release exists
    if subprocess.run(["gh", "release", "view", TAG, "--repo", REPO], capture_output=True).returncode != 0:
        sh(["gh", "release", "create", TAG, "--repo", REPO, "--title", "Home tour videos",
            "--notes", "Rendered Home Tour Reels (made by tours/render_from_drive.py). Do not delete."])
    failed = 0
    for p in todo:
        spec = json.load(open(p))
        sid = spec["id"]
        tmp = tempfile.mkdtemp()
        try:
            src = os.path.join(tmp, "source.mp4")
            download(spec["drive_file_id"], src)
            prefix = os.path.join(tmp, sid)
            info = json.loads(sh([sys.executable, os.path.join(HERE, "make_tour.py"), src, prefix,
                                  "--town", spec["town"], "--county", spec["county"]]).strip().splitlines()[-1])
            for kind in ("ig", "tiktok"):
                sh(["gh", "release", "upload", TAG, f"{prefix}_{kind}.mp4", "--clobber", "--repo", REPO])
            os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
            for kind in ("cover", "preview"):
                os.replace(f"{prefix}_{kind}.jpg", os.path.join(HERE, "previews", f"{sid}_{kind}.jpg"))
            base = f"https://github.com/{REPO}/releases/download/{TAG}/"
            spec.update({"status": "rendered", "ig_url": base + f"{sid}_ig.mp4",
                         "tiktok_url": base + f"{sid}_tiktok.mp4",
                         "cover": f"tours/previews/{sid}_cover.jpg",
                         "preview": f"tours/previews/{sid}_preview.jpg", "render_info": info})
            spec.pop("error", None)
            print("rendered", sid, info)
        except Exception as e:
            failed += 1
            spec["status"] = "render_failed"
            spec["error"] = str(e)[:800]
            traceback.print_exc()
        with open(p, "w") as fh:
            json.dump(spec, fh, indent=1, ensure_ascii=False); fh.write("\n")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
