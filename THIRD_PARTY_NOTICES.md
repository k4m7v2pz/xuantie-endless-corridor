# 第三方组件与许可声明（Third-Party Notices）

本仓库（`xuantie-endless-corridor`）自身代码按木兰宽松许可证第 2 版（Mulan PSL v2）授权，
版权人见根目录 `LICENSE`。**下列内容不属于本仓库作者，版权归各自权利人**，本仓库只在
其原许可条件范围内使用与再分发。

## 1. 玄铁渲染库（XuanTieRendering）— MIT

- 上游仓库：https://gitcode.com/MARKJY/XuanTieRendering
- 作者署名：「问号盒」
- 许可：MIT（见渲染包 `lib/渲染/tiepm.toml` 中的 `许可 = "MIT"`）
- 本仓库中的衍生文件：`patches/渲染桥.c.macos` —— 改写自该包的 `lib/渲染/渲染桥.c`，
  仅追加 macOS 适配。**该文件的版权属于上游作者，不属于本仓库作者**；本仓库按 MIT
  条件再分发，并保留上游署名。
- 说明：上游已把 macOS 适配并入内置 `渲染桥.c`，`patches/` 中的副本仅作参考与回滚用。

MIT 许可正文（上游未在包内附版权行，以下为标准 MIT 文本，署名与年份以上游仓库为准）：

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 2. raylib 与 nanosvg — zlib

渲染库通过 `libraylib.a`（raylib，zlib 许可）与 `nanosvg.h` / `nanosvgrast.h`
（nanosvg，zlib 许可）提供底层绘制与 SVG 光栅化。

**本仓库不随包分发这些二进制与头文件**：它们由玄铁工具链（`xtl` / `xtc-package`）
安装在开发者本机，构建时链接。若要单独分发含 raylib 的可执行文件，须自行遵守
zlib 许可（保留其版权与许可声明，不得以作者名义背书）。

## 3. 玄铁语言与工具链

玄铁语言编译器与运行时由上游项目提供，本仓库只调用、不内嵌。其许可与使用条款以
上游为准；本仓库的 `LICENSE` 不覆盖上游组件。

## 4. 素材

美术、音效、图块在独立仓库 `k4m7v2pz/assets-endless-corridor`，许可为木兰开放作品
许可协议 署名-专利许可 第 1 版（Mulan OWL BY-PL v1），`audio/music/suno_ai/` 例外
（Suno 免费计划条款，仅个人非商业）。详见该仓库 `LICENSE` 与 `README.md`。

## 5. 第三方 IP

角色、名称、原作图像与音乐等第三方知识产权，本仓库不授予、也无权授予，需使用方自行
从权利人处取得。相关口径见 `docs/授权与合规问答.md` 第 4 节。
