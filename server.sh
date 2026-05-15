#!/bin/bash
# 文件上传服务管理脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/data/.server.pid"
LOG_FILE="$SCRIPT_DIR/data/server.log"
SERVER_SCRIPT="$SCRIPT_DIR/upload_server.py"
DEFAULT_PORT=8000

PORT="${2:-$DEFAULT_PORT}"

start() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "⚠️  服务已在运行 (PID: $pid)"
            print_url
            return
        else
            rm -f "$PID_FILE"
        fi
    fi

    cd "$SCRIPT_DIR"
    mkdir -p data
    nohup python3 "$SERVER_SCRIPT" -p "$PORT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ 服务已启动 (PID: $(cat $PID_FILE))"
        print_url
    else
        echo "❌ 启动失败，检查日志: cat $LOG_FILE"
        rm -f "$PID_FILE"
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "ℹ️  服务未运行"
        return
    fi
    
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
        fi
        rm -f "$PID_FILE"
        echo "👋 服务已停止"
    else
        rm -f "$PID_FILE"
        echo "ℹ️  服务未运行"
    fi
}

restart() {
    stop
    sleep 2
    start
}

status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⏹️  服务未运行"
        return
    fi
    
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "✅ 服务运行中 (PID: $pid)"
        print_url
    else
        rm -f "$PID_FILE"
        echo "⏹️  服务未运行"
    fi
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
