# x-thread-scrape 使用说明（中文）

## 1. 适用场景

当你需要从 X 的单条推文入口抓取以下信息时，使用本技能：

- 正文全文（seed tweet）
- 同作者的连载内容（continuation/thread）
- 相关图片（图片 URL + 本地下载文件）

---

## 2. 前置条件

1. Python 环境可用
2. 安装依赖：
```powershell
pip install patchright
```
3. 准备 Netscape 格式 cookie 文件（例如：`H:\cookies\x.txt`）

---

## 3. 快速开始

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

## 4. 输出说明

以上命令默认会生成：

- `ingliguori_demo_thread.json`
- `ingliguori_demo_posts.jsonl`
- `ingliguori_demo_meta.json`
- `ingliguori_demo_images/`

`thread.json` 中每条推文重点字段：

- `tweet_id`
- `status_url`
- `author_handle`
- `created_at`
- `text`
- `thread_index`
- `is_seed`
- `images[]`（含 `source_url`、`normalized_url`、`local_path`、`downloaded`、`error`）

---

## 5. 常用参数

- `--cookie-file`：cookie 文件路径（必填）
- `--tweet-url`：种子推文链接（必填）
- `--output-dir`：输出目录
- `--basename`：输出文件前缀
- `--wait-seconds`：抓取等待上限
- `--max-scrolls`：滚动次数上限
- `--scroll-wait-ms`：每次滚动等待毫秒
- `--headless`：无头模式
- `--include-all-authors`：包含非种子作者回复
- `--no-download-images`：不下载图片，仅保留图片链接

---

## 6. 抓取策略说明

默认策略是：

1. 打开 X 并加载 cookie 会话
2. 进入 seed tweet 详情页
3. 识别页面上可见推文卡片
4. 按作者过滤（默认仅 seed 作者）
5. 下拉加载连载并去重
6. 汇总文本和图片信息
7. 下载图片并写入结构化结果

---

## 7. 故障排查

1. 跳转登录页
- 通常是 cookie 失效，刷新 `H:\cookies\x.txt` 后重试

2. 抓不到正文
- 增大 `--wait-seconds` 与 `--max-scrolls`
- 去掉 `--headless` 观察页面行为

3. 图片下载失败
- 查看 `images[].error`
- 保留 `source_url` / `normalized_url` 做后续补抓

