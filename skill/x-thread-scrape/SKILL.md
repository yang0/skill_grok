---
name: x-thread-scrape
description: Scrape full X tweet text from a seed tweet URL, including same-author continuation posts in the thread and related images, using patchright with Netscape cookies.
---

# X Thread Scrape

Use this skill when you need reproducible capture of:
- Seed tweet full text
- Same-author continuation posts in the thread
- Related image URLs and downloaded image files

Language guides:
- Chinese guide: [references/usage_zh.md](references/usage_zh.md)
- English guide: [references/usage_en.md](references/usage_en.md)

## Workflow

1. Install dependency (if missing):
```powershell
pip install patchright
```

2. Prepare cookie file in Netscape format (example: `H:\cookies\x.txt`).

3. Run script:
```powershell
python E:\projectHome\skill_grok\skill\x-thread-scrape\scripts\query_x_thread.py `
  --cookie-file H:\cookies\x.txt `
  --tweet-url "https://x.com/<handle>/status/<tweet_id>" `
  --output-dir E:\projectHome\skill_grok `
  --basename x_thread_result `
  --wait-seconds 240
```

4. Check outputs:
- `<basename>_thread.json`: structured thread output (tweets + images info)
- `<basename>_posts.jsonl`: one tweet per line
- `<basename>_meta.json`: run metadata and output paths
- `<basename>_images/`: downloaded images

## Script

Use [query_x_thread.py](scripts/query_x_thread.py).

Key flags:
- `--cookie-file`: Netscape cookie txt path (required)
- `--tweet-url`: X seed tweet URL (required)
- `--output-dir`: output directory (default `.`)
- `--basename`: output prefix (default `x_thread_result`)
- `--wait-seconds`: max thread expansion wait (default `180`)
- `--max-scrolls`: scroll attempts to load thread continuation (default `30`)
- `--scroll-wait-ms`: wait per scroll (default `1500`)
- `--headless`: run browser headless
- `--include-all-authors`: include non-seed-author tweets
- `--no-download-images`: keep image URLs only, skip image downloads

## Thread Semantics

Default behavior captures tweets authored by the same handle as the seed tweet URL.
Use `--include-all-authors` if you want replies from other authors too.

## Failure Handling

If thread capture is incomplete:
1. Increase `--wait-seconds` and `--max-scrolls`.
2. Run without `--headless` to inspect the page behavior.
3. Refresh cookie file and retry.

If image download fails:
1. Keep the image `source_url` and `normalized_url` from JSON as ground truth.
2. Retry with stable network or another cookie session.
