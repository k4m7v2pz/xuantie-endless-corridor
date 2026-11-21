#!/bin/bash
# 文字剧情播放器入口（ASCII 路径，避免终端里输中文路径出错）
# 用法: bash run-story.sh        # 默认《我还会回来》
#       bash run-story.sh 2      # 恐哀
set -e
root="$(cd "$(dirname "$0")" && pwd)"
case "${1:-1}" in
  1|wo|我还会回来) target="$root/文字剧情/我还会回来" ;;
  2|kong|恐哀)     target="$root/文字剧情/恐哀" ;;
  *) echo "用法: bash run-story.sh [1|2]"; exit 1 ;;
esac
exec bash "$target/运行.sh"
