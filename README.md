# Holo RSS Reader

Simple RSS/Atom feed reader for OpenClaw skills, with daily digest, full-article cache, and configurable safety/performance controls.

## 功能

- 解析 RSS/Atom 订阅源
- 从 GitHub Gist OPML 导入订阅源
- 并发抓取新文章并生成日报
- `ETag/Last-Modified` 条件请求，减少重复流量
- 全文抓取缓存（`full_index.json` 索引）
- 可配置网络超时、重试、响应体大小和安全模式
- `doctor` 诊断命令（环境、依赖、网络、存储）

## 开发

```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest

# 运行覆盖率
uv run pytest --cov --cov-report=html
```

## CLI

```bash
python3 scripts/main.py --help
python3 scripts/main.py --config "$RSS_DATA_DIR/config.json" --help
```

子命令：

- `list --gist <url>`: 列出 Gist 中订阅源
- `read <feed-url> --limit <n>`: 读取单个源
- `import --gist <url> --limit <n>`: 导入并读取多个源
- `fetch --gist <url> --limit <n> --workers <n> --retries <n> --connect-timeout <sec> --read-timeout <sec> --max-feed-bytes <bytes>`
- `today`: 查看今日日报
- `history <YYYY-MM-DD>`: 查看历史日报
- `full <article-url> --date <YYYY-MM-DD> --max-article-bytes <bytes>`
- `doctor`: 运行环境诊断

## 配置

默认配置文件：`$RSS_DATA_DIR/config.json`

```json
{
  "network": {
    "connect_timeout_sec": 5,
    "read_timeout_sec": 20,
    "max_feed_bytes": 2097152,
    "max_article_bytes": 8388608,
    "retries": 3
  },
  "fetch": {
    "workers": 8
  },
  "security": {
    "mode": "loose",
    "allowlist": []
  }
}
```

安全模式：

- `loose`（默认）：仅限制 URL 必须是 `http/https`
- `restricted`：额外阻止 `localhost`/内网等目标
- `allowlist`：仅允许白名单域名

## 部署到 OpenClaw Skill

```bash
./openclaw_deploy_skill.sh <absolute-target-path>
```

部署后常用命令：

```bash
bash <skill-path>/scripts/rss.sh list
bash <skill-path>/scripts/rss.sh fetch
bash <skill-path>/scripts/rss.sh doctor
```

`rss.sh` 解释器发现顺序：

1. `RSS_PYTHON`
2. `~/.openclaw/.venv/bin/python3`
3. `python3`（PATH）
