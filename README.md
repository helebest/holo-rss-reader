# Holo RSS Reader

Simple RSS/Atom feed reader.

## 功能

- 解析 RSS/Atom 订阅源
- 获取文章列表（标题、日期、链接）
- 支持 GitHub Gist OPML 导入
- 支持自定义获取数量

## 开发

```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest

# 运行覆盖率
uv run pytest --cov --cov-report=html
```

## 部署

```bash
# 部署到 OpenClaw skills 目录
./deploy_skill.sh <target-path>

# 示例
./openclaw_deploy_skill.sh $HOME/.openclaw/skills/holo-rss-reader
```

部署后的目录结构：

```
skill-name/
├── SKILL.md
└── scripts/
    ├── rss.sh
    ├── fetcher.py
    ├── gist.py
    ├── parser.py
    └── main.py
```

## 使用

```bash
# 列出订阅源
bash <skill-path>/scripts/rss.sh list

# 读取单个源
bash <skill-path>/scripts/rss.sh read "<feed-url>" <limit>

# 导入 Gist
bash <skill-path>/scripts/rss.sh import
```
