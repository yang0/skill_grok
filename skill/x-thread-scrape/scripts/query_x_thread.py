#!/usr/bin/env python3
"""Scrape full X thread text (seed + continuation) and related images."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

try:
    from patchright.sync_api import Page, sync_playwright
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'patchright'. Install with: pip install patchright"
    ) from exc


EXTRACT_VISIBLE_TWEETS_JS = r"""
() => {
  const toAbs = (href) => {
    if (!href) return "";
    try {
      return new URL(href, window.location.origin).toString();
    } catch {
      return href;
    }
  };

  const parseStatus = (href) => {
    if (!href) return null;
    const abs = toAbs(href);
    let m = abs.match(/https?:\/\/(?:www\.)?x\.com\/([^/?#]+)\/status\/(\d+)/i);
    if (!m) {
      m = abs.match(/\/([^/?#]+)\/status\/(\d+)/i);
    }
    if (!m) return null;
    return { handle: m[1], id: m[2], statusUrl: `https://x.com/${m[1]}/status/${m[2]}` };
  };

  const unique = (arr) => Array.from(new Set(arr));
  const tweets = [];
  const articles = Array.from(document.querySelectorAll('article[data-testid="tweet"]'));

  for (let idx = 0; idx < articles.length; idx += 1) {
    const article = articles[idx];
    const statusAnchors = Array.from(article.querySelectorAll('a[href*="/status/"]'));
    const parsedAnchors = statusAnchors
      .map((a) => parseStatus(a.getAttribute("href")))
      .filter(Boolean);
    if (!parsedAnchors.length) {
      continue;
    }

    const primary = parsedAnchors[0];
    const textNode = article.querySelector('div[data-testid="tweetText"]');
    const text = textNode ? textNode.innerText : article.innerText;
    const timeNode = article.querySelector("time");
    const createdAt = timeNode ? timeNode.getAttribute("datetime") : null;

    const imageUrls = unique(
      Array.from(article.querySelectorAll('img[src]'))
        .map((img) => img.getAttribute("src") || "")
        .filter((src) => src.includes("pbs.twimg.com/media") || src.includes("pbs.twimg.com/ext_tw_video_thumb"))
        .map((src) => toAbs(src))
    );

    tweets.push({
      index_on_page: idx,
      tweet_id: primary.id,
      status_url: primary.statusUrl,
      author_handle: primary.handle,
      created_at: createdAt,
      text: text || "",
      image_urls: imageUrls,
    });
  }

  return tweets;
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape a seed tweet, continuation thread posts, and related images."
    )
    parser.add_argument("--cookie-file", required=True, help="Netscape cookie txt file.")
    parser.add_argument("--tweet-url", required=True, help="Seed tweet URL on x.com.")
    parser.add_argument("--output-dir", default=".", help="Output directory.")
    parser.add_argument("--basename", default="x_thread_result", help="Output basename.")
    parser.add_argument("--url", default="https://x.com/", help="X base URL for warm-up.")
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=180,
        help="Max wait budget for thread expansion.",
    )
    parser.add_argument(
        "--max-scrolls",
        type=int,
        default=30,
        help="Maximum number of downward scroll attempts.",
    )
    parser.add_argument(
        "--scroll-wait-ms",
        type=int,
        default=1500,
        help="Wait milliseconds after each scroll.",
    )
    parser.add_argument("--headless", action="store_true", help="Run browser headless.")
    parser.add_argument(
        "--include-all-authors",
        action="store_true",
        help="Include tweets from authors other than seed handle.",
    )
    parser.add_argument(
        "--download-images",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Download image files locally (default: true).",
    )
    return parser.parse_args()


def parse_status_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    match = re.search(r"(?:https?://)?(?:www\.)?x\.com/([^/?#]+)/status/(\d+)", url)
    if not match:
        match = re.search(r"/([^/?#]+)/status/(\d+)", url)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def parse_netscape_cookies(cookie_path: Path) -> List[Dict[str, Any]]:
    cookies: List[Dict[str, Any]] = []
    raw_lines = cookie_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for raw_line in raw_lines:
        line = raw_line.strip()
        if not line:
            continue

        http_only = False
        if line.startswith("#HttpOnly_"):
            http_only = True
            line = line[len("#HttpOnly_") :]
        elif line.startswith("#"):
            continue

        parts = line.split("\t")
        if len(parts) != 7:
            continue
        domain, _include_subdomains, path, secure, expires, name, value = parts

        cookie: Dict[str, Any] = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": path or "/",
            "secure": secure.upper() == "TRUE",
            "httpOnly": http_only,
        }
        try:
            expires_int = int(expires)
            if expires_int > 0:
                cookie["expires"] = expires_int
        except ValueError:
            pass
        cookies.append(cookie)

    if not cookies:
        raise ValueError(f"No valid cookies parsed from: {cookie_path}")
    return cookies


def normalize_image_url(url: str) -> str:
    parsed = urlparse(url)
    if "pbs.twimg.com" not in parsed.netloc:
        return url

    query = parse_qs(parsed.query, keep_blank_values=True)
    if "name" in query:
        query["name"] = ["orig"]
    elif parsed.query:
        query["name"] = ["orig"]

    normalized_query = urlencode(query, doseq=True) if query else parsed.query
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            normalized_query,
            parsed.fragment,
        )
    )


def guess_extension(url: str) -> str:
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ext

    query = parse_qs(parsed.query, keep_blank_values=True)
    fmt = (query.get("format") or query.get("fm") or [None])[0]
    if fmt:
        fmt = fmt.lower()
        if fmt == "jpeg":
            fmt = "jpg"
        if fmt in {"jpg", "png", "webp", "gif"}:
            return f".{fmt}"
    return ".jpg"


def download_binary(url: str, output_path: Path) -> None:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as response:
        data = response.read()
    output_path.write_bytes(data)


def extract_visible_tweets(page: Page) -> List[Dict[str, Any]]:
    items = page.evaluate(EXTRACT_VISIBLE_TWEETS_JS)
    return items if isinstance(items, list) else []


def normalize_tweet(item: Dict[str, Any]) -> Dict[str, Any]:
    author = str(item.get("author_handle") or "").strip()
    tweet_id = str(item.get("tweet_id") or "").strip()
    status_url = str(item.get("status_url") or "").strip()
    if author and tweet_id:
        status_url = f"https://x.com/{author}/status/{tweet_id}"

    raw_images = item.get("image_urls")
    image_urls: List[str] = []
    if isinstance(raw_images, list):
        for image_url in raw_images:
            candidate = str(image_url or "").strip()
            if candidate:
                image_urls.append(candidate)

    return {
        "tweet_id": tweet_id,
        "status_url": status_url,
        "author_handle": author,
        "created_at": item.get("created_at"),
        "text": str(item.get("text") or "").strip(),
        "image_urls": list(dict.fromkeys(image_urls)),
    }


def capture_thread(
    *,
    page: Page,
    seed_url: str,
    wait_seconds: int,
    max_scrolls: int,
    scroll_wait_ms: int,
    include_all_authors: bool,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    seed_author, seed_tweet_id = parse_status_url(seed_url)
    seed_author_lc = seed_author.lower() if seed_author else None

    by_id: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    stagnant_ticks = 0
    last_count = 0
    max_ticks = max(wait_seconds * 1000 // max(scroll_wait_ms, 1), 1)
    loop_limit = min(max_scrolls, max_ticks)

    for _ in range(loop_limit):
        visible = extract_visible_tweets(page)
        for item in visible:
            tweet = normalize_tweet(item)
            tweet_id = tweet.get("tweet_id")
            author = str(tweet.get("author_handle") or "").lower()
            if not tweet_id:
                continue
            if seed_author_lc and not include_all_authors and author != seed_author_lc:
                continue
            if tweet_id in by_id:
                continue
            by_id[tweet_id] = tweet
            order.append(tweet_id)

        current_count = len(order)
        if current_count == last_count:
            stagnant_ticks += 1
        else:
            stagnant_ticks = 0
            last_count = current_count

        if stagnant_ticks >= 3 and current_count > 0:
            break

        page.evaluate("window.scrollBy(0, Math.floor(window.innerHeight * 0.9));")
        page.wait_for_timeout(scroll_wait_ms)

    tweets = [by_id[tweet_id] for tweet_id in order]
    for idx, tweet in enumerate(tweets, start=1):
        tweet["thread_index"] = idx
        tweet["is_seed"] = tweet.get("tweet_id") == seed_tweet_id

    info = {
        "seed_author": seed_author,
        "seed_tweet_id": seed_tweet_id,
        "captured_count": len(tweets),
        "included_all_authors": include_all_authors,
    }
    return tweets, info


def attach_image_artifacts(
    *,
    tweets: List[Dict[str, Any]],
    media_dir: Optional[Path],
    download_images: bool,
) -> int:
    downloaded_count = 0
    for tweet in tweets:
        image_urls = tweet.pop("image_urls", [])
        image_records: List[Dict[str, Any]] = []
        for idx, source_url in enumerate(image_urls, start=1):
            normalized_url = normalize_image_url(source_url)
            record: Dict[str, Any] = {
                "source_url": source_url,
                "normalized_url": normalized_url,
                "local_path": None,
                "downloaded": False,
                "error": None,
            }
            if download_images and media_dir is not None:
                ext = guess_extension(normalized_url)
                output_name = f"{tweet.get('tweet_id', 'tweet')}_{idx}{ext}"
                output_path = media_dir / output_name
                try:
                    download_binary(normalized_url, output_path)
                    record["local_path"] = str(output_path.resolve())
                    record["downloaded"] = True
                    downloaded_count += 1
                except Exception as exc:
                    record["error"] = str(exc)
            image_records.append(record)
        tweet["images"] = image_records
    return downloaded_count


def main() -> int:
    args = parse_args()
    try:
        cookie_file = Path(args.cookie_file)
        cookies = parse_netscape_cookies(cookie_file)
    except Exception as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / args.basename
    thread_path = Path(str(base) + "_thread.json")
    posts_jsonl_path = Path(str(base) + "_posts.jsonl")
    meta_path = Path(str(base) + "_meta.json")
    media_dir = Path(str(base) + "_images")
    if args.download_images:
        media_dir.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=args.headless)
            context = browser.new_context(viewport={"width": 1600, "height": 950})
            context.add_cookies(cookies)
            page = context.new_page()

            page.goto(args.url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3000)
            page.goto(args.tweet_url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(5000)

            title = page.title()
            if "Just a moment" in title:
                raise RuntimeError(
                    "Cloudflare challenge detected. Re-run without --headless and complete verification."
                )

            if "login" in page.url.lower():
                raise RuntimeError(
                    "Redirected to login page. Refresh cookie file and retry."
                )

            page.locator('article[data-testid="tweet"]').first.wait_for(timeout=45000)

            tweets, capture_info = capture_thread(
                page=page,
                seed_url=args.tweet_url,
                wait_seconds=args.wait_seconds,
                max_scrolls=args.max_scrolls,
                scroll_wait_ms=args.scroll_wait_ms,
                include_all_authors=args.include_all_authors,
            )

            browser.close()
    except Exception as exc:
        print(f"Runtime error: {exc}", file=sys.stderr)
        return 3

    if not tweets:
        print("Runtime error: no tweets captured from thread page.", file=sys.stderr)
        return 4

    downloaded_images = attach_image_artifacts(
        tweets=tweets,
        media_dir=media_dir if args.download_images else None,
        download_images=args.download_images,
    )

    now_utc = datetime.now(timezone.utc).isoformat()
    thread_payload = {
        "captured_at_utc": now_utc,
        "tweet_url": args.tweet_url,
        "seed_author": capture_info.get("seed_author"),
        "seed_tweet_id": capture_info.get("seed_tweet_id"),
        "include_all_authors": args.include_all_authors,
        "tweet_count": len(tweets),
        "tweets": tweets,
    }
    thread_path.write_text(
        json.dumps(thread_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with posts_jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for tweet in tweets:
            handle.write(json.dumps(tweet, ensure_ascii=False) + "\n")

    image_refs = sum(len(tweet.get("images", [])) for tweet in tweets)
    meta = {
        "created_at_utc": now_utc,
        "tweet_url": args.tweet_url,
        "headless": args.headless,
        "wait_seconds": args.wait_seconds,
        "max_scrolls": args.max_scrolls,
        "scroll_wait_ms": args.scroll_wait_ms,
        "include_all_authors": args.include_all_authors,
        "download_images": args.download_images,
        "cookie_file": str(Path(args.cookie_file).resolve()),
        "tweet_count": len(tweets),
        "image_references": image_refs,
        "images_downloaded": downloaded_images,
        "thread_output": str(thread_path.resolve()),
        "posts_jsonl_output": str(posts_jsonl_path.resolve()),
        "meta_output": str(meta_path.resolve()),
        "images_dir": str(media_dir.resolve()) if args.download_images else None,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"thread_output={thread_path.resolve()}")
    print(f"posts_jsonl_output={posts_jsonl_path.resolve()}")
    print(f"meta_output={meta_path.resolve()}")
    print(f"tweets={len(tweets)}")
    print(f"image_references={image_refs}")
    print(f"images_downloaded={downloaded_images}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
