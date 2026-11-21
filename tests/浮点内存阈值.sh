#!/bin/bash
# ============================================================================
# 浮点内存缺陷的回归判据（配套 docs/玄铁缺陷-浮点逐样本运算内存暴涨.md 第 3、4、9 节）
#
# 判据来自上游（玄铁语言维护）复核口径：
#   修好的充分条件不是"更快"，而是"内存不再随轮数涨"。
#   五点 RSS 的极差 < 10 MB，且 100 万轮 ≤ 20 MB → 回收生效。
#   不建议拿耗时当判据（当前本来就不慢，百万轮约 1.1 s，用时间判会长期误判成"没修"）。
#
# 现状：**红是预期**。缺陷未修时每点都在 70~700 MB，脚本会退出 1。
#
# 用法：
#   bash tests/浮点内存阈值.sh         # 五点常规检查（约 5 s，峰值 < 1 GB）
#   bash tests/浮点内存阈值.sh --压    # 千万轮重压，手动/周跑，不进每次提交门禁
#
# 千万轮那次现在必然被 SIGKILL（约 7 GB），会吃满内存，所以只允许手动触发。
#
# 注：脚本内变量一律用 ASCII —— bash 不支持中文标识符。
# ============================================================================
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
XTC="/Users/user2/Library/Caches/xtl/core/darwin-arm64/xtc-package/xtc"
SRC="$ROOT/tests/浮点内存探针.xt"
WORK="$ROOT/tests/.probe"

MB=1048576
LIMIT_MB=20
RANGE_MB=10
# 单位说明：这里按 MiB（1048576 字节）算。复核方那份表用的是 MB（10^6），
# 所以同一测量会差约 4%：本脚本 100 万轮 675 MiB ≈ 上游记的 709 MB。

[ -x "$XTC" ] || { echo "找不到 xtc：$XTC"; exit 2; }
mkdir -p "$WORK"

# 单点测量：替换轮数 → 编译（ASCII 产物名）→ /usr/bin/time -l 读峰值 RSS
# 输出一行：轮数 <TAB> 峰值 MB <TAB> 耗时 s ；被杀时输出"杀掉"标记
measure() {
    local rounds=$1
    local name="probe_${rounds}"
    sed "s/^设 轮数 = [0-9]*/设 轮数 = ${rounds}/" "$SRC" > "$WORK/${name}.xt" || return 1
    ( cd "$WORK" && "$XTC" tie "${name}.xt" -sc "$name" >/dev/null 2>&1 ) || return 1
    local out
    out=$( cd "$WORK" && /usr/bin/time -l "./$name" 2>&1 )
    local killed=$?
    local bytes msecs
    bytes=$(echo "$out" | awk '/maximum resident set size/{print $1}')
    msecs=$(echo "$out" | awk '/ real /{print $1}')
    if [ -z "$bytes" ]; then
        printf '%s\t%s\t%s\n' "$rounds" "KILLED" "${killed}"
        return 0
    fi
    printf '%s\t%s\t%s\n' "$rounds" "$((bytes / MB))" "$msecs"
}

if [ "${1:-}" = "--压" ]; then
    echo "【重压】千万轮，会吃数 GB 内存；修好前应被 SIGKILL。"
    measure 10000000
    echo
    echo "判据：必须跑完且 RSS 不破 2 GB。"
    exit 0
fi

printf '%s\n' "轮数	峰值 RSS	耗时 s"
printf '%s\n' "----	--------	-----"

min=""
max=""
all_ok=1
for n in 10000 108000 216000 432000 1000000; do
    line=$(measure "$n")
    rounds=$(echo "$line" | cut -f1)
    mb=$(echo "$line" | cut -f2)
    secs=$(echo "$line" | cut -f3)
    printf '%s\t%s MiB\t%s\n' "$rounds" "$mb" "$secs"
    case "$mb" in
        KILLED|'') all_ok=0; continue ;;
    esac
    [ -z "$min" ] || [ "$mb" -lt "$min" ] && min=$mb
    [ -z "$max" ] || [ "$mb" -gt "$max" ] && max=$mb
    if [ "$rounds" -ge 108000 ] && [ "$mb" -gt "$LIMIT_MB" ]; then all_ok=0; fi
done

echo
echo "极差：$((max - min)) MiB　阈值：单点 ≤ ${LIMIT_MB} MiB 且极差 < ${RANGE_MB} MiB"
if [ "$all_ok" = 1 ] && [ $((max - min)) -lt "$RANGE_MB" ]; then
    echo "结论：PASS —— 浮点对象已按轮回收到位。"
    exit 0
fi
echo "结论：FAIL —— 内存仍随轮数线性上涨（缺陷未修）。这是当前预期结果。"
exit 1
