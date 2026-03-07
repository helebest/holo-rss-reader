---
name: holo-rss-reader
description: RSS/Atom 阅读器，支持 Gist OPML 导入、并发抓取、日报与全文缓存。
homepage: https://github.com/helebest/holo-rss-reader
---

# Holo RSS Reader

RSS/Atom 阅读器，支持从 GitHub Gist OPML 导入订阅源并生成日报。

## 前置条件

1. Python 3.11+
2. 网络可访问 GitHub API 与目标 RSS 源
3. 建议先运行诊断：

```bash
bash {baseDir}/scripts/rss.sh doctor
```

## 使用方法

```bash
# 列出订阅源
bash {baseDir}/scripts/rss.sh list [gist-url]

# 读取单个源
bash {baseDir}/scripts/rss.sh read <feed-url> [limit]

# 导入并读取多个源
bash {baseDir}/scripts/rss.sh import [gist-url] [limit]

# 并发抓取并生成日报
bash {baseDir}/scripts/rss.sh fetch [gist-url] [limit] [workers]

# 查看今日日报
bash {baseDir}/scripts/rss.sh today

# 查看历史日报
bash {baseDir}/scripts/rss.sh history <YYYY-MM-DD>

# 抓取全文
bash {baseDir}/scripts/rss.sh full <article-url> [YYYY-MM-DD]

# 环境诊断
bash {baseDir}/scripts/rss.sh doctor
```

## 配置

- 数据目录：`RSS_DATA_DIR`（默认 `$HOME/data/rss`）
- 配置文件：`RSS_CONFIG`（可选，等价于 `--config`）
- Python 解释器：`RSS_PYTHON`（可选）

默认 Gist: [HN 2025 热门博客](https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b)

## 输出

- feed 列表
- 文章标题 / 日期 / 链接 / 摘要
- 每日 `digest.md` 与结构化 `digest.json`
- 全文缓存与 `full_index.json`
