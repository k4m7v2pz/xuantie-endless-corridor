#!/bin/bash
# 没有 play 或源码更新过就先编译，再跑
set -e
cd "$(dirname "$0")" || exit 1
XTC="${XTC:-$HOME/Library/Caches/xtl/core/darwin-arm64/xtc-package/xtc}"
if [ ! -x "$XTC" ]; then
  echo "找不到 xtc：$XTC" >&2
  echo "先装工具链，或用 XTC=<xtc 路径> bash 运行.sh 指定" >&2
  exit 1
fi
if [ ! -x ./play ] || [ 剧情播放器.xt -nt ./play ]; then
  "$XTC" tie 剧情播放器.xt -sc play
fi
exec ./play
