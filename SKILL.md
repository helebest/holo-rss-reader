---
name: holo-rss-reader
description: RSS/Atom 阅读器技能。从 GitHub Gist OPML 导入订阅源，并发抓取文章，生成日报摘要，缓存全文。当用户要求阅读 RSS/Atom 订阅、获取新闻摘要、管理订阅源、查看每日文章汇总、抓取全文、或诊断 RSS 运行环境时使用此技能。
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
