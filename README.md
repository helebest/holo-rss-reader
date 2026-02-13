# Holo RSS Reader

Simple RSS/Atom feed reader for OpenClaw.

## 功能

- 解析 RSS/Atom 订阅源
- 获取文章列表（标题、日期、链接）
- 支持自定义获取数量

## 安装

```bash
cd /mnt/usb/projects/holo-rss-reader
uv sync
```

## 使用

```bash
# 基本用法
python main.py <rss-url> [max-items]

# 示例
python main.py "https://news.ycombinator.com/rss" 5
```

## 开发

- 包管理：uv
- 依赖：feedparser, requests

## 部署到 OpenClaw

开发完成后，将相关文件复制到 OpenClaw 的 skills 目录。
