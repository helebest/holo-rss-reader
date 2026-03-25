#!/bin/bash
#
# Holo RSS Reader - Bash wrapper
# 用法: bash rss.sh <command> [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# RSS 数据存储目录（可通过环境变量 RSS_DATA_DIR 覆盖）
export RSS_DATA_DIR="${RSS_DATA_DIR:-$HOME/data/rss}"

# 默认 Gist URL
DEFAULT_GIST="https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b"

resolve_python() {
    if [[ -n "${RSS_PYTHON:-}" ]]; then
        if [[ -x "$RSS_PYTHON" ]]; then
            echo "$RSS_PYTHON"
            return 0
        fi
        echo "❌ RSS_PYTHON is set but not executable: $RSS_PYTHON" >&2
        return 1
    fi

    local openclaw_python="$HOME/.openclaw/.venv/bin/python3"
    if [[ -x "$openclaw_python" ]]; then
        echo "$openclaw_python"
        return 0
    fi

    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return 0
    fi

    echo "❌ Python not found." >&2
    echo "   Fix: install python3 or set RSS_PYTHON to a valid interpreter." >&2
    return 1
}

PYTHON_CMD="$(resolve_python)" || exit 2

COMMON_ARGS=()
if [[ -n "${RSS_CONFIG:-}" ]]; then
    COMMON_ARGS+=("--config" "$RSS_CONFIG")
fi

run_main() {
    "$PYTHON_CMD" "$SCRIPT_DIR/main.py" ${COMMON_ARGS[@]+"${COMMON_ARGS[@]}"} "$@"
}

CMD="${1:-}"
shift || true

case "$CMD" in
    list)
        GIST_URL="${1:-$DEFAULT_GIST}"
        run_main list --gist "$GIST_URL"
        ;;
    read)
        FEED_URL="${1:-}"
        LIMIT="${2:-10}"
        if [[ -z "$FEED_URL" ]]; then
            echo "用法: bash rss.sh read <feed-url> [limit]" >&2
            exit 2
        fi
        run_main read "$FEED_URL" --limit "$LIMIT"
        ;;
    import)
        GIST_URL="${1:-$DEFAULT_GIST}"
        LIMIT="${2:-3}"
        run_main import --gist "$GIST_URL" --limit "$LIMIT"
        ;;
    fetch)
        GIST_URL="${1:-$DEFAULT_GIST}"
        LIMIT="${2:-10}"
        WORKERS="${3:-8}"
        run_main fetch --gist "$GIST_URL" --limit "$LIMIT" --workers "$WORKERS"
        ;;
    today)
        run_main today
        ;;
    history)
        DATE="${1:-}"
        if [[ -z "$DATE" ]]; then
            echo "用法: bash rss.sh history <YYYY-MM-DD>" >&2
            exit 2
        fi
        run_main history "$DATE"
        ;;
    full)
        ARTICLE_URL="${1:-}"
        DATE="${2:-}"
        if [[ -z "$ARTICLE_URL" ]]; then
            echo "用法: bash rss.sh full <article-url> [YYYY-MM-DD]" >&2
            exit 2
        fi
        if [[ -n "$DATE" ]]; then
            run_main full "$ARTICLE_URL" --date "$DATE"
        else
            run_main full "$ARTICLE_URL"
        fi
        ;;
    doctor)
        run_main doctor
        ;;
    *)
        echo "Holo RSS Reader"
        echo ""
        echo "用法: bash rss.sh <command> [args...]"
        echo ""
        echo "命令:"
        echo "  list [gist-url]                列出订阅源"
        echo "  read <feed-url> [limit]        读取文章"
        echo "  import [gist-url] [limit]      导入并显示文章"
        echo "  fetch [gist-url] [limit] [workers]  抓取新文章，保存日报"
        echo "  today                          查看今日日报"
        echo "  history <YYYY-MM-DD>           查看指定日期日报"
        echo "  full <article-url> [date]      抓取并保存全文"
        echo "  doctor                         诊断运行环境和网络连通"
        echo ""
        echo "默认 Gist: $DEFAULT_GIST"
        echo "存储位置: $RSS_DATA_DIR"
        if [[ -n "${RSS_CONFIG:-}" ]]; then
            echo "配置文件: $RSS_CONFIG"
        fi
        exit 2
        ;;
esac
