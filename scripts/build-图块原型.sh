#!/bin/bash
# 图块原型构建：抓 IR → clang 编译 → 链接出 ./tilemap
# 复用 scripts/xtc-抓IR.sh（xtc tie 链接失败属预期），其余照搬 build-macos.rvs 的 7–9 步。
set -e
cd "$(dirname "$0")/.."
PROJ="$PWD"

# 门禁：地图结构与门的对偶先过硬校验，错就不编译（人/AI 都会手抖，靠程序盯着）
python3 原型/造图.py --校验 原型/地图*.json || { echo "❌ 地图/门校验未过，停止构建"; exit 1; }

XTC="$HOME/Library/Caches/xtl/core/darwin-arm64/xtc-package/xtc"
RT="$HOME/Library/Caches/xtl/core/darwin-arm64/xtc-package/runtime"
RL="$HOME/Library/Caches/xtl/raylib/darwin-arm64/libraylib.a"
BR="$HOME/Library/Caches/xtl/core/darwin-arm64/xtc-package/lib/渲染"

bash scripts/xtc-抓IR.sh "$XTC" "$PROJ" /tmp/tilemap.ll "原型/图块地图.xt" tilemap
# 噪音静音：.ll 自带通用 target（会被覆盖成宿主 triple，无害）；
# xt_tls.c 里的 kTLSProtocol12 是运行时自身的老 API 用法，不影响我们。
# 只静这两类已知无害告警，真正出错仍然会打出来。
QUIET="-Wno-override-module -Wno-deprecated-declarations"
clang -target arm64-apple-darwin -c /tmp/tilemap.ll -o /tmp/tilemap.o -Og $QUIET
clang -target arm64-apple-darwin -c "$BR/渲染桥.c" -o /tmp/tilemap_bridge.o -I "$BR" -Og
clang $QUIET /tmp/tilemap.o "$RT/xt_runtime.c" "$RT/xt_threadpool.c" "$RT/xt_net.c" "$RT/xt_tls.c" "$RT/xt_process.c" /tmp/tilemap_bridge.o "$RL" \
  -o tilemap -framework Cocoa -framework OpenGL -framework IOKit -framework CoreVideo
echo "✅ 构建完成: $PROJ/tilemap"
