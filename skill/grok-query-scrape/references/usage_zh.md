# grok-query-scrape 使用说明（中文）

## 1. 适用场景

当你需要把 Prompt 原样提交给 Grok，并将返回结果原样保存时，使用本技能。

主要能力：

- 复用 cookie 登录会话
- 自动提交 Prompt
- 等待回答稳定
- 返回并落盘原始文本（不做 JSON 解析）

---

## 2. 前置条件

1. Python 环境可用
2. 安装依赖：
```powershell
pip install patchright
```
3. 准备 Netscape 格式 cookie（例如 `H:\cookies\grok.txt`）

---

## 3. 快速开始

```powershell
python E:\projectHome\skill_grok\skill\grok-query-scrape\scripts\query_grok.py `
  --cookie-file H:\cookies\grok.txt `
  --prompt "请抓取24小时top10 ai增效相关的推文。返回结果请包含标题，正文，数据，链接" `
  --output-dir E:\projectHome\skill_grok\runs\run_demo `
  --basename grok_demo `
  --wait-seconds 240
```

---

## 4. 输出说明

默认输出：

- `<basename>_raw.txt`：Grok 原始回答全文
- `<basename>_meta.json`：运行参数和产物路径
- 终端 `stdout`：同样输出 Grok 原始回答

---

## 5. 常用参数

- `--cookie-file`：cookie 文件路径（必填）
- `--prompt`：直接传入 prompt 文本
- `--prompt-file`：从文件读取 prompt（与 `--prompt` 二选一）
- `--output-dir`：输出目录
- `--basename`：输出文件前缀
- `--wait-seconds`：等待回答稳定的最大时长
- `--headless`：无头浏览器模式
- `--new-chat` / `--no-new-chat`：是否先开新会话

---

## 6. 执行策略说明

默认策略：

1. 载入 cookie 到浏览器上下文
2. 打开 Grok 页面
3. （可选）`Ctrl+J` 开新会话
4. 输入并发送 prompt
5. 轮询 `main` 文本直到稳定
6. 输出并保存原始结果

---

## 7. 故障排查

1. 进入登录页或无法发送
- 通常是 cookie 失效，更新后重试

2. 长时间没有结果
- 增加 `--wait-seconds`
- 关闭 `--headless` 观察页面

3. 输出格式不符合预期
- 本技能不会解析/重排输出，请直接改 prompt 约束

