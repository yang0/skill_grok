# x-thread-scrape Usage Guide (English)

## 1. When to use this skill

Use this skill when you need to capture, from a seed tweet URL:

- Full seed tweet text
- Same-author continuation posts in the thread
- Related images (URLs plus downloaded local files)

---

## 2. Prerequisites

1. Python is available
2. Install dependency:
```powershell
pip install patchright
```
3. Prepare a Netscape-format cookie file (example: `H:\cookies\x.txt`)

---

## 3. Quick start

```powershell
python E:\projectHome\skill_grok\skill\x-thread-scrape\scripts\query_x_thread.py `
  --cookie-file H:\cookies\x.txt `
  --tweet-url "https://x.com/ingliguori/status/2027449920685244517" `
  --output-dir E:\projectHome\skill_grok\runs\run_demo `
  --basename ingliguori_demo `
  --wait-seconds 180 `
  --max-scrolls 25 `
  --headless
```

---

## 4. Outputs

The command writes:

- `ingliguori_demo_thread.json`
- `ingliguori_demo_posts.jsonl`
- `ingliguori_demo_meta.json`
- `ingliguori_demo_images/`

Key fields per tweet in `thread.json`:

- `tweet_id`
- `status_url`
- `author_handle`
- `created_at`
- `text`
- `thread_index`
- `is_seed`
- `images[]` with `source_url`, `normalized_url`, `local_path`, `downloaded`, `error`

---

## 5. Common flags

- `--cookie-file`: cookie file path (required)
- `--tweet-url`: seed tweet URL (required)
- `--output-dir`: output directory
- `--basename`: output file prefix
- `--wait-seconds`: max wait budget
- `--max-scrolls`: max scroll attempts
- `--scroll-wait-ms`: wait time after each scroll
- `--headless`: run browser headless
- `--include-all-authors`: include non-seed-author posts
- `--no-download-images`: skip image download and keep URLs only

---

## 6. Capture behavior

Default behavior:

1. Open X with cookie session
2. Navigate to seed tweet detail page
3. Parse visible tweet cards
4. Filter by author (seed author by default)
5. Scroll and deduplicate continuation posts
6. Collect text and image metadata
7. Download images and write structured artifacts

---

## 7. Troubleshooting

1. Redirected to login
- Cookie is likely expired; refresh `H:\cookies\x.txt` and retry

2. Missing thread content
- Increase `--wait-seconds` and `--max-scrolls`
- Run without `--headless` to inspect page behavior

3. Image download errors
- Check `images[].error`
- Keep `source_url` / `normalized_url` for retry jobs

