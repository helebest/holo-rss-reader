# 输出样例

本文件记录 `fetch` / `today` / `full` 产生的文件格式，便于判断命令是否成功、字段是否齐全。

所有路径均位于 `$RSS_DATA_DIR`（默认 `$HOME/data/rss`）下，按日期分目录组织：

```
$RSS_DATA_DIR/
├── 2026-04-19/
│   ├── digest.md               # 人类可读日报
│   ├── digest.json             # 结构化日报（供合并 / 下游处理）
│   └── articles/               # 全文缓存（按源 + 文章 slug 命名）
│       └── xinzhiyuan--openai-gpt6-launch.md
├── full_index.json             # 全局 URL → 全文路径索引
└── state.json                  # feed 抓取元数据（ETag / Last-Modified / seen URLs）
```

---

## `digest.md` 样例

`fetch` 生成，`today` / `history` 直接读取此文件：

```markdown
# RSS 日报 — 2026-04-19

## 新智元

1. **GPT-6 正式发布：多模态 Agent 能力大幅提升**
   📅 2026-04-19 | 🔗 [mp.weixin.qq.com/...](https://mp.weixin.qq.com/s/xxxxx)
   > OpenAI 今日发布 GPT-6，支持原生视频理解与长程规划，在 AgentBench 上相较 GPT-5 提升 41%。本次发布同时引入 ...

2. **Anthropic 发布 Claude 5 系列**
   📅 2026-04-18 | 🔗 [anthropic.com/news/...](https://anthropic.com/news/claude-5)
   > Claude 5 在编码与长上下文任务上刷新 SOTA，支持 10M token 上下文窗口 ...

## Hacker News Top Posts

1. **Rust 2026 Edition finalized**
   📅 2026-04-19 | 🔗 [blog.rust-lang.org/...](https://blog.rust-lang.org/2026/04/19/rust-2026.html)
   > The Rust team announced the stabilization of the 2026 edition, introducing ...

---
*共抓取 2 个源，3 篇新文章*
```

**关键字段**：
- 一级标题固定为 `# RSS 日报 — YYYY-MM-DD`
- 二级标题是 feed `<title>`
- 每条文章：序号 + 粗体标题 + 日期（`YYYY-MM-DD`，截断自 RFC 3339）+ 短链 + 400 字摘要
- 末尾固定为 `*共抓取 N 个源，M 篇新文章*`；若当日无新文章，文件只有一行 `*今日无新文章。*`

---

## `digest.json` Schema

`fetch` 同时落盘；被 `full` 命令用作微信文章全文的数据源。

```json
{
  "新智元": {
    "feed_url": "https://wechat2rss.xlab.app/feed/ede30346413ea70dbef5d485ea5cbb95cca446e7.xml",
    "articles": [
      {
        "title": "GPT-6 正式发布：多模态 Agent 能力大幅提升",
        "link": "https://mp.weixin.qq.com/s/xxxxx",
        "published": "2026-04-19T08:30:00+08:00",
        "summary": "OpenAI 今日发布 GPT-6 ...",
        "content_encoded": "<p>完整 HTML 正文 ...</p>"
      }
    ]
  },
  "Hacker News Top Posts": {
    "feed_url": "https://news.ycombinator.com/rss",
    "articles": [ { "title": "...", "link": "...", "published": "...", "summary": "..." } ]
  }
}
```

**字段说明**：
- 顶层 key 是 feed `<title>`；若 feed 无标题则回退为 feed URL。
- `articles[].content_encoded`：仅微信 / RSS 2.0 源有；`full` 命令在无法走 HTTP 抓取时会从这里取正文。
- `published` 保留原始时区；`digest.md` 中会截断前 10 位。

---

## 全文缓存 `articles/<feed_slug>--<article_slug>.md`

`full` 命令产出，文件名由 `slugify(feed_title, 30) + "--" + slugify(article_title, 50)` 拼接：

```markdown
# GPT-6 正式发布：多模态 Agent 能力大幅提升

- **来源**: 新智元
- **日期**: 2026-04-19T08:30:00+08:00
- **链接**: https://mp.weixin.qq.com/s/xxxxx
- **抓取时间**: 2026-04-19T12:15:03.482911+00:00

---

OpenAI 今日发布 GPT-6 ...
（完整正文，HTML 已剥离为纯文本或保留轻量 Markdown）
```

---

## `full_index.json` Schema

全局索引，支持通过 URL 快速定位已缓存的全文路径（避免重复抓取）：

```json
{
  "articles": {
    "a1b2c3d4e5f6...": {
      "url": "https://mp.weixin.qq.com/s/xxxxx",
      "date": "2026-04-19",
      "path": "/home/user/data/rss/2026-04-19/articles/xinzhiyuan--gpt-6.md",
      "updated_at": "2026-04-19T12:15:03.482911+00:00"
    }
  }
}
```

**字段说明**：
- key 是 `sha256(url)` 的前 N 位，用于去重查询。
- `path` 是绝对路径；若文件被用户删除，`lookup_full_article` 会惰性清理该条目。

---

## 验证输出是否正常

| 命令 | 期望文件 | 快速检查 |
|------|----------|----------|
| `fetch` 成功 | `YYYY-MM-DD/digest.md`、`YYYY-MM-DD/digest.json` | 两文件同时存在且非空 |
| `today` 成功 | 直接 stdout 打印 `digest.md` 内容 | 退出码 0，stdout 含 `# RSS 日报` |
| `full <url>` 成功 | `YYYY-MM-DD/articles/*.md`、更新 `full_index.json` | 新增 MD 文件，索引含对应 URL 条目 |

若文件缺失或字段不全，先运行 `doctor`，再检查 `$RSS_DATA_DIR` 权限与磁盘空间（退出码 5）。
