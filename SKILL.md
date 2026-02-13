---
name: holo-rss-reader
description: RSS/Atom 阅读器，支持从 GitHub Gist OPML 导入订阅源，获取文章列表。
homepage: https://github.com/helebest/holo-rss-reader
---

# Holo RSS Reader

RSS/Atom 阅读器，支持从 GitHub Gist OPML 导入订阅源，获取文章列表。

## 前置条件

1. uv 已安装
2. 网络访问：能够访问 GitHub API 和 RSS 订阅源

## 使用方法

### 列出订阅源

```bash
bash {baseDir}/scripts/rss.sh list [gist-url]
```

### 读取文章

```bash
bash {baseDir}/scripts/rss.sh read <feed-url> [limit]
```

### 导入并获取

```bash
bash {baseDir}/scripts/rss.sh import [gist-url] [limit]
```

## 默认 Gist

项目默认使用 [HN 2025 热门博客](https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b)，包含 92+ 个技术博客。

## 示例

```bash
# 列出默认 Gist 的订阅源
bash {baseDir}/scripts/rss.sh list

# 读取单个源（获取5条）
bash {baseDir}/scripts/rss.sh read "https://simonwillison.net/atom/everything/" 5
```

## 输出格式

- 标题
- 发布日期
- 链接
- 摘要（可选）
