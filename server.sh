#!/bin/bash
# 文件上传服务管理脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/data/.server.pid"
LOG_FILE="$SCRIPT_DIR/data/server.log"
SERVER_SCRIPT="$SCRIPT_DIR/upload_server.py"
DEFAULT_PORT=8000

PORT="${2:-$DEFAULT_PORT}"

start() {
    if is_running; then
        echo "⚠️  服务已在运行 (PID: $(cat $PID_FILE))"
        print_url
        return
    fi

    cd "$SCRIPT_DIR"
    mkdir -p data
    nohup python3 "$SERVER_SCRIPT" -p "$PORT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 1
    if is_running; then
        echo "✅ 服务已启动"
        print_url
    else
        echo "❌ 启动失败，检查日志: cat $LOG_FILE"
    fi
}

stop() {
    if ! is_running; then
        echo "ℹ️  服务未运行"
        return
    fi
    kill "$(cat "$PID_FILE")" 2>/dev/null
    sleep 1
    if ! is_running; then
        echo "👋 服务已停止"
    else
        echo "⚠️  强制停止中..."
        kill -9 "$(cat "$PID_FILE")" 2>/dev/null
    fi
    rm -f "$PID_FILE"
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if is_running; then
        echo "✅ 服务运行中 (PID: $(cat "$PID_FILE"))"
        print_url
    else
        echo "⏹️  服务未运行"
    fi
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        kill -0 "$pid" 2>/dev/null
        return $?
    fi
    return 1
}

print_url() {
    ip=$(hostname -I | awk '{print $1}')
    echo "📱 手机浏览器访问: http://$ip:$PORT"
}

# ── Commands ────────────────────────────────────────────────
case "${1}" in
    start)   start   ;;
    stop)    stop    ;;
    restart) restart ;;
    status)  status  ;;
    *)       echo "用法: $0 {start|stop|restart|status} [端口]" ;;
esac
