#!/bin/bash
# 关闭本项目所有 corridor 窗口（含崩溃/遗忘的残留实例）
# 按「进程 cwd == 项目根」判定，避免误杀其它项目的同名产物。
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
n=0
for pid in $(ps -eo pid,command | awk '$2=="./corridor"{print $1}'); do
  cwd=$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')
  if [ "$cwd" = "$PROJ" ]; then
    kill -9 "$pid" 2>/dev/null && n=$((n+1))
  fi
done
echo "已关闭 $n 个 corridor 窗口"
