#!/bin/bash
# 启动游戏：先清掉旧窗口，永远只有一个实例
cd "$(dirname "$0")/.." || exit 1
bash scripts/关闭.sh >/dev/null
exec ./corridor
