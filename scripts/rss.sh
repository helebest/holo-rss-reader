#!/bin/bash
#
# Holo RSS Reader - Bash wrapper
# 用法: bash rss.sh <command> [args...]

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 使用全局 venv（依赖由 openclaw_deploy_skill.sh 安装）
PYTHON_CMD="$HOME/.openclaw/.venv/bin/python3"

# 默认 Gist URL
DEFAULT_GIST="https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b"

# 命令
CMD="$1"
shift || true

case "$CMD" in
    list)
        GIST_URL="${1:-$DEFAULT_GIST}"
        $PYTHON_CMD "$SCRIPT_DIR/main.py" list --gist "$GIST_URL"
        ;;
    read)
        FEED_URL="$1"
        LIMIT="${2:-10}"
        if [ -z "$FEED_URL" ]; then
            echo "用法: bash rss.sh read <feed-url> [limit]"
            exit 1
        fi
        $PYTHON_CMD "$SCRIPT_DIR/main.py" read "$FEED_URL" --limit "$LIMIT"
        ;;
    import)
        GIST_URL="${1:-$DEFAULT_GIST}"
        LIMIT="${2:-3}"
        $PYTHON_CMD "$SCRIPT_DIR/main.py" import --gist "$GIST_URL" --limit "$LIMIT"
        ;;
    fetch)
        GIST_URL="${1:-$DEFAULT_GIST}"
        LIMIT="${2:-10}"
        WORKERS="${3:-5}"
        $PYTHON_CMD "$SCRIPT_DIR/main.py" fetch --gist "$GIST_URL" --limit "$LIMIT" --workers "$WORKERS"
        ;;
    today)
        $PYTHON_CMD "$SCRIPT_DIR/main.py" today
        ;;
    history)
        DATE="$1"
        if [ -z "$DATE" ]; then
            echo "用法: bash rss.sh history <YYYY-MM-DD>"
            exit 1
        fi
        $PYTHON_CMD "$SCRIPT_DIR/main.py" history "$DATE"
        ;;
    full)
        ARTICLE_URL="$1"
        DATE="$2"
        if [ -z "$ARTICLE_URL" ]; then
            echo "用法: bash rss.sh full <article-url> [YYYY-MM-DD]"
            exit 1
        fi
        if [ -n "$DATE" ]; then
            $PYTHON_CMD "$SCRIPT_DIR/main.py" full "$ARTICLE_URL" --date "$DATE"
        else
            $PYTHON_CMD "$SCRIPT_DIR/main.py" full "$ARTICLE_URL"
        fi
        ;;
    *)
        echo "Holo RSS Reader"
        echo ""
        echo "用法: bash rss.sh <command> [args...]"
        echo ""
        echo "命令:"
        echo "  list [gist-url]              列出订阅源"
        echo "  read <feed-url> [limit]      读取文章"
        echo "  import [gist-url] [limit]    导入并显示文章"
        echo "  fetch [gist-url] [limit] [workers]  抓取新文章，保存日报（默认5并发）"
        echo "  today                        查看今日日报"
        echo "  history <YYYY-MM-DD>         查看指定日期日报"
        echo "  full <article-url> [date]    抓取并保存全文"
        echo ""
        echo "默认 Gist: $DEFAULT_GIST"
        echo "存储位置: /mnt/usb/data/rss/"
        exit 1
        ;;
esac
