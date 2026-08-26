#!/usr/bin/env python3
"""Phase 2 — publish the rendered carousel to Instagram via the official API.

Requires env: IG_ACCESS_TOKEN, GITHUB_REPOSITORY (owner/repo), BRANCH (default main).
Images must already be pushed so raw.githubusercontent.com URLs resolve.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

GRAPH = "https://graph.instagram.com/v23.0"
ROOT = Path(__file__).resolve().parent.parent
TOKEN = os.environ["IG_ACCESS_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
BRANCH = os.environ.get("BRANCH", "main")


def api(method, path, **params):
    params["access_token"] = TOKEN
    r = requests.request(method, f"{GRAPH}/{path}", params=params, timeout=60)
    data = r.json()
    if r.status_code >= 400 or "error" in data:
        raise RuntimeError(f"IG API error on {path}: {json.dumps(data)[:500]}")
    return data


def wait_finished(container_id, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = api("GET", container_id, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st == "ERROR":
            raise RuntimeError(f"container {container_id} entered ERROR state")
        time.sleep(5)
    raise TimeoutError(f"container {container_id} not ready in {timeout}s")


def main():
    manifest_path = ROOT / (ROOT / "latest_manifest.txt").read_text().strip()
    m = json.loads(manifest_path.read_text())

    me = api("GET", "me", fields="user_id,username")
    ig_id = me.get("user_id") or me.get("id")
    print(f"publishing as @{me.get('username')} (id {ig_id})")

    raw_base = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
    children = []
    for rel in m["images"]:
        url = f"{raw_base}/{rel}"
        c = api("POST", f"{ig_id}/media", image_url=url, is_carousel_item="true")
        children.append(c["id"])
        print(f"  child container {c['id']} <- {rel}")

    for cid in children:
        wait_finished(cid)

    carousel = api("POST", f"{ig_id}/media", media_type="CAROUSEL",
                   children=",".join(children), caption=m["caption"])
    wait_finished(carousel["id"])
    result = api("POST", f"{ig_id}/media_publish", creation_id=carousel["id"])
    print(f"PUBLISHED ✅  media id: {result.get('id')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
