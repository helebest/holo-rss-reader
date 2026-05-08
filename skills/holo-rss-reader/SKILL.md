---
name: holo-rss-reader
description: RSS/Atom feed reader and daily digest generator with WeChat Official Accounts (微信公众号) bridging via wechat2rss. Use this skill whenever the user wants to subscribe to RSS, Atom, or RDF feeds, import an OPML from a GitHub Gist, read blog articles, fetch news summaries, generate a daily digest, cache full article text, manage feed subscriptions, subscribe to 微信公众号, or diagnose RSS runtime issues. Trigger phrases include — "今天有什么新闻", "帮我抓取文章", "看看公众号更新", "公众号新文章", "RSS 订阅源", "OPML 导入", "文章全文缓存", "每日摘要", "订阅博客", "订阅 新智元", "check my feeds", "fetch latest articles", "generate today's digest". Do not use this skill for generic web scraping, Twitter/X timelines, or fetching arbitrary non-RSS webpages — it only handles RSS/Atom/RDF and wechat2rss-indexed accounts.
---

# Holo RSS Reader

RSS/Atom 阅读器，支持从 GitHub Gist OPML 导入订阅源、并发抓取文章、生成日报摘要、缓存全文，以及通过 wechat2rss 桥接订阅微信公众号。

## 快速开始

首次使用建议按以下流程操作：

```bash
# 1. 诊断运行环境（检查 Python、依赖、网络）
bash {baseDir}/scripts/rss.sh doctor

# 2. 并发抓取所有订阅源，生成今日日报
bash {baseDir}/scripts/rss.sh fetch

# 3. 查看今日日报
bash {baseDir}/scripts/rss.sh today

# 4. 对感兴趣的文章抓取全文
bash {baseDir}/scripts/rss.sh full <article-url>
```

## 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `list [gist-url]` | 列出订阅源 | `rss.sh list` |
| `read <feed-url> [limit]` | 读取单个源的文章 | `rss.sh read https://example.com/rss 5` |
| `import [gist-url] [limit]` | 导入 Gist OPML 并预览 | `rss.sh import` |
| `fetch [gist-url] [limit] [workers]` | 并发抓取新文章，生成日报 | `rss.sh fetch` |
| `today` | 查看今日日报 | `rss.sh today` |
| `history <YYYY-MM-DD>` | 查看指定日期日报 | `rss.sh history 2026-03-24` |
| `full <article-url> [date]` | 抓取并缓存全文 | `rss.sh full https://example.com/post` |
| `doctor` | 诊断运行环境和网络连通 | `rss.sh doctor` |
| `wechat add <id> [--title T]` | 添加微信公众号订阅 | `rss.sh wechat add abc123 --title 新智元` |
| `wechat list` | 列出微信订阅源 | `rss.sh wechat list` |
| `wechat remove <id\|url>` | 移除微信订阅源 | `rss.sh wechat remove abc123` |

所有命令前缀为 `bash {baseDir}/scripts/rss.sh`。

## 如何选择命令

日常主流程是 `fetch` → `today` →（可选）`full`。

- `fetch` 是唯一会触发网络 I/O 并落盘 `digest.md` / `digest.json` 的命令，也是所有后续命令的数据来源。
- `today` 和 `history <date>` 只读已生成的日报，不走网络、瞬时完成——用户说"看今天/昨天的摘要"就直接读，不要重新 `fetch`。
- `full <url>` 抓单篇文章正文。对普通 RSS 源会走 HTTP 下载；对微信公众号因 `mp.weixin.qq.com` 反爬，`full` 改从**当天** `fetch` 缓存的 `content:encoded` 提取，因此**必须先 `fetch` 再 `full`**。
- 首次使用或切换 Gist 时，先 `import` 预览订阅源，再 `fetch`；想临时看某个单独源但不落盘，用 `read`。
- 任何命令报错，先 `doctor` 定位是 Python、依赖、网络还是存储问题，再对症处理。
- 微信订阅的增删查用 `wechat add/list/remove`（见下节限制）。

## 微信公众号订阅

**覆盖限制**：wechat2rss 仅收录约 500 个公众号，以安全/技术类为主。**若用户想订阅的公众号不在 [wechat2rss.xlab.app/list/all/](https://wechat2rss.xlab.app/list/all/) 中，本工具无法订阅**——此时应直接告知用户，而不是反复尝试猜测 account-id。

通过 [wechat2rss](https://wechat2rss.xlab.app) 桥接服务订阅受支持的公众号。详见 [references/wechat.md](references/wechat.md)。

```bash
# 添加（account-id 从 wechat2rss.xlab.app/list/all/ 查询）
bash {baseDir}/scripts/rss.sh wechat add <account-id> --title <名称>
```

已验证的公众号：
- 新智元: `ede30346413ea70dbef5d485ea5cbb95cca446e7`
- 机器之心: `51e92aad2728acdd1fda7314be32b16639353001`
- 量子位: `7131b577c61365cb47e81000738c10d872685908`

微信文章全文由 feed 的 `content:encoded` 自动提取，无需单独抓取 `mp.weixin.qq.com` URL（反爬会失败）。

## 配置

- 数据目录：`RSS_DATA_DIR`（默认 `$HOME/data/rss`）
- 配置文件：`RSS_CONFIG`（可选，等价于 `--config`）
- Python 解释器：`RSS_PYTHON`（可选）
- 详细配置 schema 与取值范围见 [references/config.md](references/config.md)

默认 Gist: [HN 2025 热门博客](https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b)

## 输出

- feed 列表
- 文章标题 / 日期 / 链接 / 摘要
- 每日 `digest.md` 与结构化 `digest.json`
- 全文缓存与 `full_index.json`

具体文件布局、字段含义与最小样例见 [references/output-samples.md](references/output-samples.md)。

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 2 | 参数错误（URL 无效、Python 版本不符等） |
| 3 | 网络错误（连接超时、DNS 失败等） |
| 4 | 解析错误（Feed XML 格式异常、依赖缺失等） |
| 5 | 存储错误（目录不可写、磁盘满等） |

## 故障排查

命令失败时，先运行 `doctor` 定位问题类别：

```bash
bash {baseDir}/scripts/rss.sh doctor
```

根据 `❌` 项处理：
- **python** — 升级到 Python 3.11+
- **import:xxx** — 运行 `uv sync` 安装缺失依赖
- **storage** — 检查 `$RSS_DATA_DIR` 目录权限或磁盘空间
- **network:github** — 检查网络连通性或代理设置，确认可访问 GitHub API
- **network:rss** — 检查网络连通性，确认可访问外部 RSS 源
