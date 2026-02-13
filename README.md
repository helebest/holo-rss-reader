# Holo RSS Reader

Simple RSS/Atom feed reader for OpenClaw.

## 功能

- 解析 RSS/Atom 订阅源
- 获取文章列表（标题、日期、链接）
- 支持 GitHub Gist OPML 导入
- 支持自定义获取数量

## 安装

```bash
uv sync
```

## 使用

```bash
# 列出 Gist 中的所有订阅源
python main.py list --gist "https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b"

# 读取单个 RSS 源
python main.py read "https://news.ycombinator.com/rss" --limit 5

# 导入 Gist 并获取所有源的文章
python main.py import --gist "https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b" --limit 2
```

## 默认订阅源

项目默认读取 [HN 2025 热门博客](https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b)，包含 92+ 个优质技术博客。

## 开发

- 包管理：uv
- 测试框架：pytest
- 核心依赖：feedparser, requests, responses

```bash
# 运行测试
uv run pytest

# 运行覆盖率
uv run pytest --cov --cov-report=html
```

## 部署到 OpenClaw

开发完成后，将 `holo_rss_reader/` 目录和 `main.py` 复制到 OpenClaw 的 skills 目录。
