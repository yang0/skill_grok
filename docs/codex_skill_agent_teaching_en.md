# Codex Guide: Skill, Agent, and AGENTS.md Orchestration

## 1. Scope

This document focuses on three things:

- The difference between `Skill` and `Agent`
- How to orchestrate multiple agents
- How to write and structure `AGENTS.md`

---

## 2. Skill vs Agent

## 2.1 Skill

A skill is a reusable capability package:

- `SKILL.md` for workflow guidance
- `scripts/` for deterministic execution
- optional `references/` and `assets/`

It answers: **how to do the task**.

## 2.2 Agent

An agent is a runtime worker:

- main agent coordinates
- sub-agents execute scoped work

It answers: **who does what and when**.

In short: **Skill defines method, Agent defines execution.**

---

## 3. Multi-agent orchestration

Start from acceptance criteria, then split responsibilities.

Recommended baseline:

1. `agent_scrape`: collect raw artifacts
2. `agent_qc`: validate completeness and constraints
3. `agent_pack`: assemble report and delivery index
4. main agent: coordinate, resolve conflicts, finalize

Core rules:

- each agent owns explicit files
- pass data through files, not chat memory
- validation must be executable

---

## 4. Runbook + output layout

Create one runbook per run:

```text
orchestration/runbooks/run_<date>_<topic>.md
```

Write outputs under:

```text
runs/<run_id>/
  raw/
  media/
  report.md
  meta.json
```

Minimum runbook sections:

1. Goal and scope
2. Agent responsibilities
3. Input and output paths
4. Acceptance criteria

---

## 5. AGENTS.md writing rules

`AGENTS.md` should store stable rules, not one-off run parameters.

Include:

- skill routing rules
- agent collaboration rules
- I/O contracts
- quality gates
- security boundaries

Do not include:

- one-time prompt text
- one-time cookie path
- one-time run_id

Put those in the runbook.

---

## 6. Multiple AGENTS.md files

You can have multiple `AGENTS.md` files by scope:

1. root-level `AGENTS.md`: global defaults
2. subdirectory `AGENTS.md`: module-specific rules
3. nearest scope should take precedence

Recommendation:

- keep one `AGENTS.md` per directory
- keep root concise and module files specific

---

## 7. Message template for Codex

Use this minimal instruction format:

```text
Execute this runbook:
<absolute_path_to_runbook>

Requirements:
1) Use $<skill_name>
2) Follow AGENTS.md collaboration rules
3) Write outputs to <runs/run_id/...>
4) Return artifact paths and validation results
```

---

## 8. Runbook examples

## 8.1 Generic template

```md
# Runbook: <run_id>

## 1) Goal
- <one-line objective>

## 2) Scope
- In: <what to do>
- Out: <what not to do>

## 3) Skills
- Use: $<skill_name_1>
- Use: $<skill_name_2> (optional)

## 4) Agent roles
1. `agent_scrape`
- Owns: `runs/<run_id>/raw/`
- Job: scraping and raw write
2. `agent_qc`
- Owns: `runs/<run_id>/qc/`
- Job: checks and issue list
3. `agent_pack`
- Owns: `runs/<run_id>/report.md`
- Job: final report and delivery index

## 5) Inputs
- Cookie: `<absolute_cookie_path>`
- Prompt file: `runs/<run_id>/prompt.txt` (or inline prompt)
- URL list: `runs/<run_id>/input_urls.txt` (if needed)

## 6) Outputs
- `runs/<run_id>/raw/*.txt|json|jsonl`
- `runs/<run_id>/media/*` (if needed)
- `runs/<run_id>/meta.json`
- `runs/<run_id>/report.md`

## 7) Acceptance
1. Exit code is 0.
2. Required outputs exist and are non-empty.
3. Required record count and fields are satisfied.
4. Final response includes absolute artifact paths.

## 8) Failure handling
1. Record failures in `runs/<run_id>/report.md`.
2. Retry recoverable errors once.
3. Stop and ask user for non-recoverable blockers.
```

## 8.2 Example A: Grok capture

```md
# Runbook: run_2026-02-28_grok_top10

## Goal
- Get top 10 AI productivity tweets from Grok for last 24 hours.

## Skills
- Use: $grok-query-scrape

## Agent roles
1. `agent_scrape`: run script and save raw/meta
2. `agent_qc`: verify non-empty output and 10 records
3. `agent_pack`: publish report with artifact paths

## Inputs
- Cookie: `H:\cookies\grok2.txt`
- Prompt: `请抓取24小时top10 ai增效相关的推文。返回结果请包含标题，正文，数据，链接`

## Outputs
- `runs/run_2026-02-28_grok_top10/raw/grok_raw.txt`
- `runs/run_2026-02-28_grok_top10/meta.json`
- `runs/run_2026-02-28_grok_top10/report.md`
```

## 8.3 Example B: X full thread + images

```md
# Runbook: run_2026-02-28_x_thread_media

## Goal
- Capture seed tweet, same-author continuation posts, and related images.

## Skills
- Use: $x-thread-scrape

## Agent roles
1. `agent_scrape`: build `thread.json`
2. `agent_media`: download images and write manifest
3. `agent_qc`: validate fields and download success
4. `agent_pack`: publish report and path index

## Inputs
- Cookie: `H:\cookies\x.txt`
- URL list: `runs/run_2026-02-28_x_thread_media/input_urls.txt`

## Outputs
- `runs/run_2026-02-28_x_thread_media/raw/thread.json`
- `runs/run_2026-02-28_x_thread_media/raw/posts.jsonl`
- `runs/run_2026-02-28_x_thread_media/media/`
- `runs/run_2026-02-28_x_thread_media/report.md`
```

---

## 9. Suggested repository layout

```text
E:\projectHome\skill_grok\
  AGENTS.md
  skill\
    grok-query-scrape\
    x-thread-scrape\
  orchestration\
    runbooks\
  runs\
```

---

## 10. Summary

Reliable collaboration depends on:

1. Skill for reusable method
2. Agent for executable division of labor
3. AGENTS.md for stable rules, runbook for per-run parameters

