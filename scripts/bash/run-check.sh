#!/bin/bash
# ============================================================================
# run-check.sh — 短时运行验证 helper（供 test-macos.rvs 调用）
#
# 行为：
#   1. 先 SIGKILL 清理所有旧的玄铁 GUI 实例，避免窗口累积并列；
#   2. 后台启动 ./corridor，等待 4 秒；
#   3. 存活则标记 ALIVE 并 SIGKILL 关闭；崩溃则标记 CRASHED；
#   4. 再次确认无残留进程（raylib 主循环不响应 SIGTERM，必须 kill -9）。
# 全程只开一个新窗口、约 4 秒后强制关闭；结果写入 /tmp/xtl-test.state。
# ============================================================================
set -u
cd "$(dirname "$0")/../.."
LOG=/tmp/xtl-test-run.log
STATE=/tmp/xtl-test.state
rm -f "$STATE"

# ---- 1. SIGKILL 清理旧实例 ----------------------------------------------------
pkill -9 -f "\./corridor" 2>/dev/null
pkill -9 -f "\./测试" 2>/dev/null
pkill -9 -f "\./无尽回廊" 2>/dev/null
sleep 1

# ---- 2. 前置检查 -------------------------------------------------------------
if [ ! -x ./corridor ]; then
  echo "缺少可执行文件 ./corridor（先跑 rvs scripts/build-macos.rvs）" >&2
  echo "NO_BINARY" > "$STATE"
  exit 1
fi

# ---- 3. 短时运行（唯一一个窗口） ----------------------------------------------
./corridor >"$LOG" 2>&1 &
PID=$!
sleep 4

if kill -0 "$PID" 2>/dev/null; then
  echo "ALIVE" > "$STATE"
else
  echo "CRASHED" > "$STATE"
fi

# ---- 4. SIGKILL 强制关闭并确认无残留 ------------------------------------------
kill -9 "$PID" 2>/dev/null
wait "$PID" 2>/dev/null
sleep 1
if kill -0 "$PID" 2>/dev/null; then
  kill -9 "$PID" 2>/dev/null
fi
pkill -9 -f "\./corridor" 2>/dev/null
exit 0
