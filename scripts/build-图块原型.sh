#!/bin/bash
# 图块原型构建：抓 IR → clang 编译 → 链接出 ./tilemap
# 复用 scripts/xtc-抓IR.sh（xtc tie 链接失败属预期），其余照搬 build-macos.rvs 的 7–9 步。
set -e
cd "$(dirname "$0")/.."
PROJ="$PWD"
XTC="$HOME/Library/Caches/xtl/core/darwin-arm64/xtc-package/xtc"
RT="$HOME/Library/Caches/xtl/core/darwin-arm64/xtc-package/runtime"
RL="$HOME/Library/Caches/xtl/raylib/darwin-arm64/libraylib.a"
BR="$HOME/Library/Caches/xtl/core/darwin-arm64/xtc-package/lib/渲染"

bash scripts/xtc-抓IR.sh "$XTC" "$PROJ" /tmp/tilemap.ll "原型/图块地图.xt" tilemap
clang -target arm64-apple-darwin -c /tmp/tilemap.ll -o /tmp/tilemap.o -Og
clang -target arm64-apple-darwin -c "$BR/渲染桥.c" -o /tmp/tilemap_bridge.o -I "$BR" -Og
clang /tmp/tilemap.o "$RT/xt_runtime.c" "$RT/xt_threadpool.c" "$RT/xt_net.c" "$RT/xt_tls.c" "$RT/xt_process.c" /tmp/tilemap_bridge.o "$RL" \
  -o tilemap -framework Cocoa -framework OpenGL -framework IOKit -framework CoreVideo
echo "✅ 构建完成: $PROJ/tilemap"
