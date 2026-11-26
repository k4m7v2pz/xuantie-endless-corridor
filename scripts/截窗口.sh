#!/bin/bash
# 只抓指定进程的窗口（不拍桌面、不拍别的窗口）。
# 用法：
#   bash scripts/截窗口.sh <进程名> [输出路径]            整窗（带标题栏与红绿灯）
#   bash scripts/截窗口.sh <进程名> [输出路径] --内容 <内容高度pt>
#                                                        只要内容区：扔掉顶部标题栏，留下底部的画面
#
# 为什么不用 `screencapture -R`：那是"截屏幕上的一块矩形"，被别的窗口盖住时
# 截到的是盖住它的那个窗口（实测过，截成了聊天窗口）。按窗口号 -l 才只拿这个窗口。
# 说明：bash 变量名只能用 ASCII，所以这里只有局部短名，注释用中文。
set -e
proc="${1:?用法: 截窗口.sh <进程名> [输出] [--内容 高度pt]}"
out="${2:-/tmp/窗口-$proc.png}"
ch=""
if [ "$3" = "--内容" ]; then ch="${4:?--内容 需要高度(pt)}"; fi

here="$(cd "$(dirname "$0")" && pwd)"
swiftc -O "$here/窗号.swift" -o /tmp/窗号_bin
line=$(/tmp/窗号_bin "$proc" | head -1)
[ -n "$line" ] || { echo "❌ 没找到包含「$proc」的窗口"; exit 1; }
wid=$(echo "$line" | cut -d' ' -f1)
wlog=$(echo "$line" | cut -d' ' -f4)

screencapture -x -o -l "$wid" "$out"
echo "✅ 整窗 -> $out  (窗口 $wid，逻辑宽 $wlog)"

if [ -n "$ch" ]; then
    # 以底边为基准：留下面「内容高度×缩放」条像素，扔掉上面的标题栏（标题栏高度不猜）
    read -r pw ph <<<"$(python3 - "$out" <<'PY'
import struct, sys
d = open(sys.argv[1], 'rb').read(33)
print(*struct.unpack(">II", d[16:24]))
PY
)"
    scale=$(python3 -c "print(round($pw / $wlog))")
    cuth=$((ch * scale))
    cuty=$((ph - cuth))
    ffmpeg -v error -y -i "$out" -vf "crop=$pw:$cuth:0:$cuty" "${out%.png}-内容.png"
    echo "✅ 内容区 -> ${out%.png}-内容.png  (${pw}x${cuth}，缩放 ${scale}x)"
fi
