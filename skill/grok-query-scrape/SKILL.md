---
name: grok-query-scrape
description: Submit prompts to https://grok.com using an authenticated cookie file and capture the generated answer verbatim. Use when the task requires raw prompt passthrough, raw Grok output capture, and reproducible artifacts without JSON parsing.
---

# Grok Query Scrape

Use this skill to run a repeatable Grok automation workflow:
- Load Netscape-format cookies (for logged-in session reuse)
- Open Grok in a browser session
- Submit the prompt exactly as provided
- Wait for answer generation to stabilize
- Return and save raw output only (no parsing)

## Workflow

1. Install runtime dependencies when missing:
```powershell
pip install patchright
```

2. Prepare a cookie file in Netscape format (example: `H:\cookies\grok.txt`).

3. Run the script:
```powershell
python E:\projectHome\skill_grok\skill\grok-query-scrape\scripts\query_grok.py `
  --cookie-file H:\cookies\grok.txt `
  --prompt "Find top 10 AI productivity tweets from the last 24 hours." `
  --output-dir E:\ `
  --basename grok_ai_top10 `
  --wait-seconds 240
```

4. Check outputs:
- `<stdout>`: Grok response text (verbatim capture from `main`)
- `<basename>_raw.txt`: same raw Grok response text saved to file
- `<basename>_meta.json`: run metadata and paths

## Script

Use [query_grok.py](scripts/query_grok.py) for execution.

Key flags:
- `--cookie-file`: Netscape cookie txt path (required)
- `--prompt`: inline prompt
- `--prompt-file`: prompt text file (alternative to `--prompt`)
- `--output-dir`: output folder (default `.`)
- `--basename`: output filename prefix (default `grok_result`)
- `--wait-seconds`: max wait for response stabilization (default `180`)
- `--headless`: run browser headless
- `--new-chat`: send `Ctrl+J` before query to reduce contamination (enabled by default)

## Prompting Guidance

This skill forwards the prompt as-is, so put all constraints directly into your prompt text.

## Failure Handling

If the output format is not what you need:
1. Keep `_raw.txt` as ground truth.
2. Tighten the prompt and retry.
3. Keep `--new-chat` enabled for isolation.
4. Increase `--wait-seconds` when generation is long.

If login fails:
1. Refresh cookie file from a valid browser session.
2. Keep domain/path/secure flags intact in Netscape format.
3. Retry with `--headless` disabled to inspect behavior.

### scripts/
- [query_grok.py](scripts/query_grok.py): submit prompt, wait for answer, return/save raw/meta only.
