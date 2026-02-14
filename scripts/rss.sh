#!/bin/bash
#
# Holo RSS Reader - Bash wrapper
# 用法: bash rss.sh <command> [args...]

# 获取脚本所在目录（也是项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 使用全局 venv 执行（依赖由 openclaw_deploy_skill.sh 安装）
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
    *)
        echo "Holo RSS Reader"
        echo ""
        echo "用法: bash rss.sh <command> [args...]"
        echo ""
        echo "命令:"
        echo "  list [gist-url]           列出订阅源"
        echo "  read <feed-url> [limit]   读取文章"
        echo "  import [gist-url] [limit] 导入并获取文章"
        echo ""
        echo "默认 Gist: $DEFAULT_GIST"
        exit 1
        ;;
esac
