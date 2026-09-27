#!/bin/bash
# ============================================================================
# 玄铁生命游戏构建 helper：调用新核心 xtc（自举版 v1.0.0）生成 LLVM IR 并截获。
#
# 背景：本项目是渲染程序，xtc tie 链接阶段因渲染包 raylib 为 Windows 构建而
# 失败（普通程序 xtc 可直接链接）；链接失败后 xtc 会清理全部中间产物（-bl 也
# 不保留）。但 IR 在 clang 编译对象之前已生成到 XuanTie 系统临时 Cache 目录
# （/var/folders/.../XuanTie/Cache/xt_*.ll，triple 已是 arm64-apple-darwin，
# 无需 sed 重定向）。本脚本在 xtc 运行期间以 20ms 间隔轮询该目录，抢在清理前
# 把 .ll 复制到指定输出路径。
#
# 用法: /bin/bash xtc-抓IR.sh <xtc路径> <项目目录> <输出.ll路径> [源文件] [输出名]
#   xtc 链接失败属预期（脚本会忽略其退出码），成功标志是输出 .ll 非空。
# ============================================================================
set -u
XTC="$1"
DIR="$2"
OUT="$3"
SRC="${4:-无尽回廊.xt}"
SC="${5:-dist/无尽回廊}"
# macOS 系统临时目录（本机实测；其他机器需按实际 /var/folders 路径替换）
CACHE="/var/folders/4x/d_1wt7n12njg88r4w2476rw00000gp/T/XuanTie/Cache"
MARKER="/tmp/xtc-catch-marker"

rm -f "$OUT"
touch "$MARKER"

(cd "$DIR" && "$XTC" tie "$SRC" -sc "$SC" -pt darwin -jg arm64 >/dev/null 2>&1) &
PID=$!
CAUGHT=""
while kill -0 "$PID" 2>/dev/null; do
  F=$(find "$CACHE" -name '*.ll' -newer "$MARKER" 2>/dev/null | head -1)
  if [ -n "$F" ]; then
    cp "$F" "$OUT" && CAUGHT="$F" && break
  fi
  sleep 0.02
done
wait "$PID" 2>/dev/null
if [ -z "$CAUGHT" ]; then
  F=$(find "$CACHE" -name '*.ll' -newer "$MARKER" 2>/dev/null | head -1)
  if [ -n "$F" ]; then cp "$F" "$OUT" && CAUGHT="$F"; fi
fi

if [ -s "$OUT" ]; then
  echo "IR 已截获: $CAUGHT -> $OUT ($(stat -f%z "$OUT") bytes)"
  exit 0
else
  echo "错误: 未截获到 IR 产物（xtc 可能未运行或 Cache 路径已变化）" >&2
  exit 1
fi
