---
name: holo-rss-reader
description: RSS/Atom feed reader and daily digest generator with WeChat public account support. Use this skill when the user wants to subscribe to RSS/Atom feeds, read blog articles, fetch news summaries, generate daily digests, manage feed subscriptions, cache full article text, subscribe to WeChat Official Accounts (微信公众号), or diagnose RSS runtime issues. Also triggers for: "今天有什么新闻", "帮我抓取文章", "check my feeds", "fetch latest articles", "订阅博客", "每日摘要".
homepage: https://github.com/helebest/holo-rss-reader
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

## 微信公众号订阅

通过 [wechat2rss](https://wechat2rss.xlab.app) 桥接服务订阅微信公众号。详见 [references/wechat.md](references/wechat.md)。

```bash
# 添加（account-id 从 wechat2rss.xlab.app/list/all/ 查询）
bash {baseDir}/scripts/rss.sh wechat add <account-id> --title <名称>
```

已验证的公众号：
- 新智元: `ede30346413ea70dbef5d485ea5cbb95cca446e7`
- 机器之心: `51e92aad2728acdd1fda7314be32b16639353001`
- 量子位: `7131b577c61365cb47e81000738c10d872685908`

**注意**：wechat2rss 收录的公众号有限（约 500 个，以安全/技术类为主）。若目标公众号未被收录，添加时会明确提示，此时无法通过本工具订阅。微信文章全文会自动从 feed 的 `content:encoded` 提取，无需单独抓取 `mp.weixin.qq.com` URL。

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
