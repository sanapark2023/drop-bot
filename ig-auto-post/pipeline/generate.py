#!/usr/bin/env python3
"""Phase 1 — watch the store, pick a product, render the carousel + caption.

Writes posts/<date>/slide_*.png + manifest.json, updates state.json.
Exit code 0 with manifest => there is something to publish.
Exit code 78 => nothing to post today (workflow treats as clean skip).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from slides import build_slides, render  # noqa: E402

SHOP_URL = "https://openai.com/ko-KR/supply/shop/"
ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state.json"
POSTS = ROOT / "posts"
KST = timezone(timedelta(hours=9))
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
PRICE_RE = re.compile(r"US\$\s?[\d,]+(?:\.\d{2})?")
FORCE = os.environ.get("FORCE_POST", "false").lower() == "true"


def parse_products(html):
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for a in soup.select('a[href*="/supply/product/"]'):
        m = re.search(r"/supply/product/([^/?#]+)", a.get("href", ""))
        if not m:
            continue
        slug = m.group(1)
        text = " ".join(a.get_text(" ", strip=True).split())
        pm = PRICE_RE.search(text)
        price = pm.group(0).replace(" ", "") if pm else None
        sold = "품절" in text or "sold out" in text.lower()
        name = PRICE_RE.sub("", text)
        for mk in ("품절", "Sold out", "Sold Out", "SOLD OUT"):
            name = name.replace(mk, "")
        name = name.strip(" ·-–|")
        half = len(name) // 2
        if half > 2 and name[:half].strip().lower() == name[half:].strip().lower():
            name = name[:half].strip()
        url = a["href"] if a["href"].startswith("http") else f"https://openai.com{a['href']}"
        if slug not in out or (out[slug]["price"] is None and price):
            out[slug] = {"name": name, "price": price, "sold_out": sold, "url": url}
    return out


def product_details(url):
    """Best-effort scrape of the product page for description + specs."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        desc = ""
        md = soup.find("meta", attrs={"name": "description"})
        if md and md.get("content"):
            desc = md["content"][:220]
        specs = []
        for li in soup.select("li"):
            txt = li.get_text(" ", strip=True)
            if 3 < len(txt) < 60 and any(k in txt for k in
                    ("면", "cotton", "온스", "oz", "핏", "fit", "세탁", "wash", "염색", "dye")):
                specs.append(("DETAIL", txt))
            if len(specs) >= 6:
                break
        return desc, specs
    except Exception as e:  # noqa: BLE001
        print(f"detail scrape skipped: {e}", file=sys.stderr)
        return "", []


def main():
    now = datetime.now(KST)
    r = requests.get(SHOP_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    current = parse_products(r.text)
    if not current:
        print("PARSE FAILURE — page structure may have changed", file=sys.stderr)
        return 1

    state = json.loads(STATE.read_text()) if STATE.exists() else {"products": {}, "posted": []}
    prev, posted = state.get("products", {}), set(state.get("posted", []))
    first_run = not prev

    new = [s for s in current if s not in prev] if not first_run else []
    restocked = [s for s, p_ in current.items()
                 if s in prev and prev[s].get("sold_out") and not p_["sold_out"]]

    # ---- choose what to post
    target, tag = None, "NEW DROP"
    candidates = [s for s in new if not current[s]["sold_out"]] or new
    if candidates:
        target = candidates[0]
    elif restocked:
        target, tag = restocked[0], "BACK IN STOCK"
    elif FORCE:
        pool = [s for s, p_ in current.items() if not p_["sold_out"] and s not in posted]
        if pool:
            target, tag = pool[0], "DROP WATCH"

    # ---- update state regardless
    state["products"] = current
    state["last_run"] = now.isoformat()

    if first_run and not FORCE:
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        print("first run — baseline saved, nothing to post")
        return 78
    if target is None:
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        print("no new drops / restocks — skipping (set FORCE_POST=true to force)")
        return 78

    p = dict(current[target])
    desc, specs = product_details(p["url"])
    if desc:
        p["desc"] = desc
    if specs:
        p["specs"] = specs

    shop = {"in_stock": [(v["name"], v["price"]) for v in current.values() if not v["sold_out"]],
            "sold_out": [v["name"] for v in current.values() if v["sold_out"]]}

    outdir = POSTS / now.strftime("%Y-%m-%d")
    outdir.mkdir(parents=True, exist_ok=True)
    paths = render(build_slides(p, shop, tag), outdir)

    caption = (
        f"{'🚨 New drop' if tag == 'NEW DROP' else '🔄 ' + tag.title()} on OpenAI Supply Co.: "
        f"{p['name']}{' — ' + p['price'] if p['price'] else ''} 🏁\n\n"
        "Full sheet in the slides — specs, the current lineup, what's already gone, "
        "and whether it's actually worth it.\n\n"
        f"Follow @aisn0207 for daily AI merch drops, restocks & resale intel.\n\n"
        "Not affiliated with OpenAI. Prices/stock accurate at post time.\n\n"
        "#openai #aimerch #techmerch #streetwear #merchdrop #dropalert #chatgpt #menswear"
    )

    manifest = {"date": now.strftime("%Y-%m-%d"), "slug": target, "tag": tag,
                "caption": caption, "images": [str(x.relative_to(ROOT)) for x in paths]}
    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (ROOT / "latest_manifest.txt").write_text(str((outdir / 'manifest.json').relative_to(ROOT)))

    state["posted"] = sorted(posted | {target})
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    print(f"generated: {target} ({tag}) -> {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
