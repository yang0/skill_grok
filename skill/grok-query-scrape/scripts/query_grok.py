#!/usr/bin/env python3
"""Submit a prompt to Grok and capture raw output only."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    from patchright.sync_api import sync_playwright
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'patchright'. Install with: pip install patchright"
    ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Submit a Grok prompt and return raw output without parsing."
    )
    parser.add_argument("--cookie-file", required=True, help="Netscape cookie txt file.")
    parser.add_argument("--prompt", help="Prompt text to send to Grok.")
    parser.add_argument("--prompt-file", help="UTF-8 text file containing prompt.")
    parser.add_argument("--output-dir", default=".", help="Directory for output files.")
    parser.add_argument("--basename", default="grok_result", help="Output file prefix.")
    parser.add_argument("--url", default="https://grok.com/", help="Target Grok URL.")
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=180,
        help="Max seconds to wait for answer stabilization.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser headless.",
    )
    parser.add_argument(
        "--new-chat",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Send Ctrl+J before prompt to start a new chat.",
    )
    return parser.parse_args()


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt is not None and args.prompt_file:
        raise ValueError("Use either --prompt or --prompt-file, not both.")
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if args.prompt is not None:
        return args.prompt
    raise ValueError("Provide --prompt or --prompt-file.")


def parse_netscape_cookies(cookie_path: Path) -> List[Dict[str, Any]]:
    cookies: List[Dict[str, Any]] = []
    for raw_line in cookie_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
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
            "httpOnly": False,
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


def run_query(
    *,
    cookies: List[Dict[str, Any]],
    prompt: str,
    url: str,
    wait_seconds: int,
    headless: bool,
    new_chat: bool,
) -> str:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1600, "height": 950})
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(5000)

        if new_chat:
            page.keyboard.press("Control+J")
            page.wait_for_timeout(1500)

        editor = page.locator('div[contenteditable="true"]').first
        editor.wait_for(timeout=30000)
        editor.click()
        page.keyboard.type(prompt)
        page.keyboard.press("Enter")

        main = page.locator("main").first
        main.wait_for(timeout=30000)
        initial = main.inner_text()
        last = initial
        stable_ticks = 0
        started = False

        loops = max(wait_seconds // 2, 1)
        for _ in range(loops):
            page.wait_for_timeout(2000)
            current = main.inner_text()
            if len(current) > len(initial) + 30:
                started = True
            if started:
                if current == last:
                    stable_ticks += 1
                else:
                    stable_ticks = 0
                if stable_ticks >= 4:
                    break
            last = current

        result = main.inner_text()
        browser.close()
        return result


def main() -> int:
    args = parse_args()
    try:
        prompt = load_prompt(args)
        cookie_file = Path(args.cookie_file)
        cookies = parse_netscape_cookies(cookie_file)
    except Exception as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / args.basename
    raw_path = Path(str(base) + "_raw.txt")
    meta_path = Path(str(base) + "_meta.json")

    try:
        raw_text = run_query(
            cookies=cookies,
            prompt=prompt,
            url=args.url,
            wait_seconds=args.wait_seconds,
            headless=args.headless,
            new_chat=args.new_chat,
        )
    except Exception as exc:
        print(f"Runtime error: {exc}", file=sys.stderr)
        return 3

    raw_path.write_text(raw_text, encoding="utf-8")
    meta = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "url": args.url,
        "headless": args.headless,
        "new_chat": args.new_chat,
        "wait_seconds": args.wait_seconds,
        "cookie_file": str(Path(args.cookie_file).resolve()),
        "raw_output": str(raw_path.resolve()),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Return the Grok response exactly as captured.
    print(raw_text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
