# SKILL.md - Holo RSS Reader

## 描述

RSS/Atom 阅读器，支持从 GitHub Gist OPML 导入订阅源，获取文章列表。

## 前置条件

1. Python 依赖：`feedparser`, `requests`
2. 网络访问：能够访问 GitHub API 和 RSS 订阅源

## 安装

```bash
cd <skill-path>
uv sync
```

## 使用方法

### 列出订阅源

列出 Gist OPML 中的所有 RSS 订阅源：

```bash
bash {baseDir}/scripts/rss.sh list "<gist-url>"
```

### 读取文章

从单个 RSS 源读取文章：

```bash
bash {baseDir}/scripts/rss.sh read "<feed-url>" <limit>
```

### 导入并获取

从 Gist 导入订阅源并获取所有文章：

```bash
bash {baseDir}/scripts/rss.sh import "<gist-url>" <limit-per-feed>
```

## 默认 Gist

项目默认使用 [HN 2025 热门博客](https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b)，包含 92+ 个技术博客。

## 示例

```bash
# 列出默认 Gist 的订阅源
bash {baseDir}/scripts/rss.sh list

# 列出自定义 Gist
bash {baseDir}/scripts/rss.sh list "https://gist.github.com/username/gist-id"

# 读取单个源（获取5条）
bash {baseDir}/scripts/rss.sh read "https://simonwillison.net/atom/everything/" 5

# 导入并获取（每个源获取2条）
bash {baseDir}/scripts/rss.sh import "" 2
```

## 输出格式

- 标题
- 发布日期
- 链接
- 摘要（可选）
