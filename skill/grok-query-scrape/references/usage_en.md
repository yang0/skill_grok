# grok-query-scrape Usage Guide (English)

## 1. When to use this skill

Use this skill when you need to send the prompt to Grok as-is and store the response as-is.

Core behavior:

- reuse authenticated cookie session
- submit prompt automatically
- wait for answer stabilization
- return and persist raw text only (no JSON parsing)

---

## 2. Prerequisites

1. Python is available
2. Install dependency:
```powershell
pip install patchright
```
3. Prepare Netscape-format cookies (example: `H:\cookies\grok.txt`)

---

## 3. Quick start

```powershell
python E:\projectHome\skill_grok\skill\grok-query-scrape\scripts\query_grok.py `
  --cookie-file H:\cookies\grok.txt `
  --prompt "Please fetch top 10 AI productivity tweets in the last 24 hours with title, body, stats, and links." `
  --output-dir E:\projectHome\skill_grok\runs\run_demo `
  --basename grok_demo `
  --wait-seconds 240
```

---

## 4. Outputs

Default outputs:

- `<basename>_raw.txt`: full raw Grok response
- `<basename>_meta.json`: run metadata and output paths
- terminal `stdout`: same raw response text

---

## 5. Common flags

- `--cookie-file`: cookie file path (required)
- `--prompt`: inline prompt text
- `--prompt-file`: prompt file path (alternative to `--prompt`)
- `--output-dir`: output directory
- `--basename`: output file prefix
- `--wait-seconds`: max stabilization wait time
- `--headless`: run browser headless
- `--new-chat` / `--no-new-chat`: open a fresh chat first or not

---

## 6. Execution behavior

Default flow:

1. load cookies into browser context
2. open Grok
3. optionally start a new chat (`Ctrl+J`)
4. submit prompt
5. poll `main` content until stable
6. print and save raw output

---

## 7. Troubleshooting

1. Redirected to login / cannot submit
- cookie is likely expired; refresh and retry

2. Response not completed in time
- increase `--wait-seconds`
- run without `--headless` for inspection

3. Output format is not what you expected
- this skill does not parse or reformat output; tighten prompt constraints instead

