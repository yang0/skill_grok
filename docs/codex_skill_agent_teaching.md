# Codex 教学：Skill、Agent 与 AGENTS.md 编排

## 1. 教学目标

本文只回答三件事：

- `Skill` 和 `Agent` 的区别。
- 如何编排多 Agent。
- `AGENTS.md` 怎么写、怎么分层、怎么让 Codex 用起来。

---

## 2. Skill 和 Agent 的区别

## 2.1 Skill 是能力包

- 组成：`SKILL.md` + scripts + assets/templates。
- 作用：定义“怎么做”。
- 特点：可复用、可版本化、偏静态。

## 2.2 Agent 是执行者

- 组成：主 agent + 子 agent（如 explorer / worker / awaiter）。
- 作用：定义“谁来做、何时做、做到什么程度”。
- 特点：运行时协作、可并行、偏动态。

一句话：**Skill 管方法，Agent 管分工。**

---

## 3. 多 Agent 编排方法

先定目标和验收，再分工，不要反过来。

推荐最小编排：

1. `agent_scrape`：执行抓取，产出原始结果。
2. `agent_qc`：校验完整性与格式约束。
3. `agent_pack`：生成报告和交付物索引。
4. 主 agent：拆解任务、协调冲突、最终验收。

编排原则：

- 每个 agent 必须有明确文件所有权。
- 输入输出通过文件传递，不靠聊天上下文记忆。
- 验收必须可机器执行（命令或明确规则）。

---

## 4. 落盘规范（Runbook + 输出目录）

建议每次任务都有一个 runbook：

```text
orchestration/runbooks/run_<date>_<topic>.md
```

建议输出目录：

```text
runs/<run_id>/
  raw/
  media/
  report.md
  meta.json
```

runbook 至少写这四块：

1. 目标与范围。
2. agent 分工。
3. 输入输出路径。
4. 验收标准。

---

## 5. AGENTS.md 写作原则

`AGENTS.md` 写长期稳定规则，不写单次任务参数。

适合写：

- skill 路由规则（什么任务走哪个 skill）。
- agent 协作规则（如何拆分、是否并行、冲突处理）。
- I/O 规范（目录结构、命名方式、产物类型）。
- 质量门槛（成功条件、失败上报条件）。
- 安全边界（凭据、敏感信息处理）。

不适合写：

- 本次 prompt。
- 本次 cookie 路径。
- 本次 run_id。
- 本次临时验收细节。

这些应放 runbook。

---

## 6. 多个 AGENTS.md 的分层

一个仓库可以有多个 `AGENTS.md`，按作用域管理：

1. 根目录 `AGENTS.md`：全局规则。
2. 子目录 `AGENTS.md`：模块特定规则。
3. 就近规则优先，根规则兜底。

建议：

- 同一目录只放一个 `AGENTS.md`。
- 根文件简短稳定，模块文件具体可执行。

---

## 7. 传递给 Codex 的最小指令模板

当你要执行一个任务，给 Codex 的消息可以固定成：

```text
按 runbook 执行：
<absolute_path_to_runbook>

要求：
1) 使用 $<skill_name>
2) 按 AGENTS.md 协作规则分配 agent
3) 输出写入 <runs/run_id/...>
4) 结束时返回产物路径和验收结果
```

这样可以降低歧义，且便于复现。

---

## 8. Runbook 写法案例

## 8.1 通用模板（可直接复制）

```md
# Runbook: <run_id>

## 1) 任务目标
- <一句话目标>

## 2) 范围
- 包含：<要做的内容>
- 不包含：<明确不做的内容>

## 3) Skills
- 使用：$<skill_name_1>
- 使用：$<skill_name_2>（可选）

## 4) Agent 分工
1. `agent_scrape`
- 负责文件：`runs/<run_id>/raw/`
- 职责：抓取与原始落盘
2. `agent_qc`
- 负责文件：`runs/<run_id>/qc/`
- 职责：完整性检查与问题清单
3. `agent_pack`
- 负责文件：`runs/<run_id>/report.md`
- 职责：汇总与交付说明

## 5) 输入
- Cookie: `<absolute_cookie_path>`
- Prompt 文件：`runs/<run_id>/prompt.txt`（或内联 prompt）
- URL 清单：`runs/<run_id>/input_urls.txt`（如适用）

## 6) 输出
- `runs/<run_id>/raw/*.txt|json|jsonl`
- `runs/<run_id>/media/*`（如适用）
- `runs/<run_id>/meta.json`
- `runs/<run_id>/report.md`

## 7) 验收标准
1. 命令退出码为 0。
2. 关键输出文件存在且非空。
3. 满足任务条数/字段要求。
4. 最终回复必须返回所有产物绝对路径。

## 8) 失败处理
1. 记录失败步骤和错误信息到 `runs/<run_id>/report.md`。
2. 可重试项重试 1 次。
3. 不可恢复项停止并向用户请求决策。
```

## 8.2 案例 A：Grok 抓取任务

```md
# Runbook: run_2026-02-28_grok_top10

## 1) 任务目标
- 让 Grok 返回 24 小时内 top10 AI 增效相关推文。

## 2) Skills
- 使用：$grok-query-scrape

## 3) Agent 分工
1. `agent_scrape`
- 执行脚本并保存 raw/meta
2. `agent_qc`
- 检查 raw 非空、是否包含 10 条记录
3. `agent_pack`
- 生成 report.md 并列出产物路径

## 4) 输入
- Cookie: `H:\cookies\grok2.txt`
- Prompt: `请抓取24小时top10 ai增效相关的推文。返回结果请包含标题，正文，数据，链接`

## 5) 输出
- `runs/run_2026-02-28_grok_top10/raw/grok_raw.txt`
- `runs/run_2026-02-28_grok_top10/meta.json`
- `runs/run_2026-02-28_grok_top10/report.md`

## 6) 验收标准
1. 退出码 0。
2. `grok_raw.txt` 非空。
3. report 中写明产物绝对路径。
```

## 8.3 案例 B：X 全文 + 连载 + 图片

```md
# Runbook: run_2026-02-28_x_thread_media

## 1) 任务目标
- 从种子推文抓取正文全文、同作者连载推文、相关图片。

## 2) Skills
- 使用：$x-thread-scrape

## 3) Agent 分工
1. `agent_scrape`
- 抓正文和连载，写 `thread.json`
2. `agent_media`
- 下载图片到 `media/` 并生成 `manifest.json`
3. `agent_qc`
- 检查字段完整性与图片下载成功率
4. `agent_pack`
- 汇总 report 与路径索引

## 4) 输入
- Cookie: `H:\cookies\x.txt`
- URL 列表：`runs/run_2026-02-28_x_thread_media/input_urls.txt`

## 5) 输出
- `runs/run_2026-02-28_x_thread_media/raw/thread.json`
- `runs/run_2026-02-28_x_thread_media/raw/posts.jsonl`
- `runs/run_2026-02-28_x_thread_media/media/`
- `runs/run_2026-02-28_x_thread_media/media/manifest.json`
- `runs/run_2026-02-28_x_thread_media/report.md`

## 6) 验收标准
1. 每个种子 URL 至少抓到 1 条正文。
2. 有图片的推文必须有本地文件路径。
3. `report.md` 包含失败项与重试结果。
```

---

## 9. 推荐目录结构

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

## 10. 小结

稳定协作的关键是三点：

1. Skill 负责方法复用。
2. Agent 负责执行编排。
3. AGENTS.md 管长期规则，runbook 管本次任务。
