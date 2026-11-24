# AGENTS.md — xuantie-endless-corridor 项目约定

## 先读这块（每次都要遵守）

1. **提交**：Conventional Commits + **简体中文主题** + 空行后 `Co-Authored-By` trailer；
   改完一个可验证单元就提交并推送 `dev`，不必逐次请示（详见「提交规范」）。
2. **公开仓库**：不得提交 token/私钥/真实 IP/端口/邮箱/真名，举例一律用占位符。
3. **剧情只放 `剧情/幕NN.json`**，`.xt` 只承载引擎与渲染。
4. **本仓库没有 CI**（无本地门禁、远端无 Actions/流水线），测试只能手动跑。
5. 改完跑**对应那一侧**再提交：
   - 渲染程序（`主函数.xt`/`scripts/`）→ `rvs scripts/test-macos.rvs`
   - TUI 播放器（`文字剧情/**`）→ `bash run-story.sh`
     + `python3 文字剧情/校验剧情.py 文字剧情/我还会回来 文字剧情/恐哀`

## 项目定位

「无尽回廊」是一款恐怖 RPG（对标 RPG Maker 系的同人恐怖改版一类：黑暗走廊、
有限光照、压抑氛围）。本项目是用**玄铁 (XuanTie) 中文编程语言 + 官方「渲染」库
（raylib 桥接）**实现的尝试性重构：

- 功能参考 `rust-bevy-endless-corridor`（Rust Bevy 版，只读）；
- 构建流程照搬 `xuantie-life-game`；工具链 `xtl-toolchain`（类 uv/cargo）。

⚠️ 玄铁当前 1.0-rc（单人开发、官方定位"游戏引擎让给 Unity/Godot"）。本项目是
**尝试性垂直验证**，不是稳定产品：先跑通最小切片，再逐步扩充。

## 构建与测试（macOS arm64）

```bash
cd /Users/user2/Documents/Code.localized/xuantie-endless-corridor
rvs scripts/build-macos.rvs     # 一键构建，产物 ./corridor
rvs scripts/test-macos.rvs      # 构建 + 短时运行验证（4 秒自动关闭）
bash scripts/运行.sh            # 日常启动：先关旧窗口再启动，永远一个实例
bash scripts/关闭.sh            # 关掉本项目所有残留窗口
bash run-story.sh               # TUI 剧情播放器（参数 2 跑《恐哀》）；
                                # 故事目录内也有 运行.sh，缺产物会自动重编译
bash tests/浮点内存阈值.sh      # 浮点内存回归判据（详见「已知坑」8）
```

- 渲染程序 `xtc tie` 链接阶段**必失败**（渲染包 raylib 是 Windows 构建，预期）：
  由 `scripts/xtc-抓IR.sh` 轮询截获 LLVM IR，再 clang 手动链接。
  **别试图把 macOS raylib 塞进 xtc-package 让它"链接成功"**，产物必崩，已还原。
- 短时运行验证在 `scripts/bash/run-check.sh`：SIGKILL 清理旧实例、单窗口跑 4 秒、
  强制关闭，结果写 `/tmp/xtl-test.state`（ALIVE/CRASHED/NO_BINARY）。

## ⚠️ 玄铁 1.0-rc 已知坑（实测，勿重踩）

1. **产物名不能与源码文本重名**：链接产物名若与源码里出现过的字样相同
   （如"主函数"是入口名、"无尽回廊"在标题里），启动即崩（Trace/BPT trap: 5，
   glfwInit → CFBundle 断言）。**规避：产物统一命名 `corridor`**。
   实测崩：`主函数`/`主函数b`/`无尽回廊`；正常：`corridor`/`改名测试`/`test-main`。
   **两个产物互不相干、各叫各的**：渲染程序 `corridor`，TUI 播放器 `play`（`-sc play`）。
   别为了"统一"把 `play` 改成 `corridor`。
2. **关窗必须在循环外**：循环体内调 `R.关闭窗口()` 后不跳出，下一轮 `开始绘图` 会在
   已销毁的 GL 上下文上跑（`DrawRectanglePro → rlVertex3f`，EXC_BAD_ACCESS）。
   **做法：按键只置 `退出 = 真`，循环末尾 `若 退出 { 断 }`，循环外再调一次关闭窗口**。
   `断`=break、`续`=continue。
3. **裸名撞渲染库导出**：`xtc` 只报 `W007 命名空间撞名（裸名绑定）`，照样出产物，
   运行时静默走错分支或崩。实测变量 `暂停` 撞 `公 函 暂停(秒数)`，改 `暂停中` 才干净。
   **起名先 grep 渲染库导出名**。
4. **字体与文案**：未进参考串的字符显示问号（含全角括号 `（）`、`Q`、`_`）；
   图集必须按「最大字号 × 屏幕像素比」光栅化，唯一入口是 `建字体(路径, 参考串, 像素比)`，
   **不要再直接调 `加载字体精准`**。界面文案走 `剧情/界面.json`（含 `字体`/`补充字`）。
   → 细则见 `docs/渲染-字体与Retina.md`。
5. **`示()` 恒带换行**；字符串字面量不支持 `\xNN`；`时.延时()` 编译过但运行炸（自建忙等）。
6. **`个 / 48000` 是整数除法**（恒 0），`小数(x) / 整数` 同样被截断
   → `docs/玄铁数值语义-小数除整数被截断.md`。写浮点探针必须 `个 * 1.0 / 率`。
7. **浮点长循环内存严格线性上涨**：单函数内逐样本浮点运算 + `数学.正弦`/`数学.幂`，
   每轮分配不回收，约 **709 字节/轮**（100 万轮 = 709 MB；时间不慢，1.1 s）。
   千万级才到 GB 并被 SIGKILL(137)，表现为"跑着跑着消失"。
   **长音频与大规模数值计算不要在玄铁里做**（秒级音频、几十万样本以上）：交给
   `文字剧情/生成音效.py` / `文字剧情/fm合成器.c` 这类外部程序
   生成文件，玄铁侧只 `加载音效`/读文件。完整复现与给上游的修法建议见
   `docs/玄铁缺陷-浮点逐样本运算内存暴涨.md`（含"修好了怎么验"的判据）。
   短音（90ms / 1984 样本）实测只要 1~2 ms、内存增量可忽略——限制来自"库里没有流式
   回调、采样循环在 C 层"，不是浮点缺陷。
   附带可用结论：`字节(n)` + `.追加(x)` + `文件.写(路径, 字节)` 是二进制安全的。
8. **回归判据**：`bash tests/浮点内存阈值.sh` 五点 RSS，约 5 s，未修时正常返回 FAIL；
   `--压` 是千万轮重压（现在必然被 SIGKILL）。**本仓库没有 CI**，它不会自动跑，
   别当门禁。

本机工具链路径（实测可用）：

- xtc：`~/Library/Caches/xtl/core/darwin-arm64/xtc-package/xtc`
- 运行时 C：`~/Library/Caches/xtl/core/darwin-arm64/xtc-package/runtime/`
- macOS raylib 6.0：`~/Library/Caches/xtl/raylib/darwin-arm64/libraylib.a`
- 玄铁临时 Cache（IR 截获轮询目录）：`/var/folders/4x/.../T/XuanTie/Cache`

查渲染库 API 请 grep 上面 xtc-package 里那份 `lib/渲染/渲染.xt`（当前 1.3.11，含
`合成音效`/`合成器(频率,毫秒,选项)`）。仓库内 `tiepm_modules/渲染/渲染.xt` 是**旧副本**，
没有这些入口——照它判断 API 会得出"库不支持合成器"的错误结论。

## 提交规范（简体中文 + Co-Authored-By）

- Conventional Commits（`feat:`/`fix:`/`docs:`/`refactor:`…），**主题用简体中文**；
  主题一行讲清"改了什么"，需要背景就空行后写正文。
- 末尾 trailer（空行隔开）`Co-Authored-By`：名字填**实际执行本次提交的 Agent/模型**
  （不是写代码的那个，二者可能不同）；无对应域名就只留名字。
  `Co-Authored-By: <Agent名> <noreply@<域名>>`。
- **一次提交 = 一个可验证的改动单元**；改完自动提交推送 `dev`，无需逐次请示。
- 公开仓库的**外发动作**（PR/issue/追评）不得声称"人类已批准/已审阅"未经批准的内容。

### 提交前防泄漏守卫（公开仓库，硬约束）

进入 git 的内容默认互联网可见。**禁止提交**：私钥/token/密码、个人邮箱、真实姓名、
私人服务器地址、代理端口、内部 IP、SSH 口令、VPS/VM 连接信息。
文档举例一律占位符：`<example@example.com>`、`<proxy-port>`、`<host>`。

提交前（不得跳过）：① `git diff --cached --name-only` 核对文件清单，无
`secrets/`、`*.pem`、`id_rsa`、`id_ed25519`、`*.key`、`credentials`；
② `git diff --cached` 扫内容，命中真实 IP/端口/邮箱/token 就
`git restore --staged <file>`，换占位符或删掉再 `git add`；③ 干净了再 commit。

## 资产仓库（美术 / 音效 / 图块）

素材不随本仓库分发，在独立仓库 `k4m7v2pz/assets-endless-corridor`：
`git clone git@github.com:k4m7v2pz/assets-endless-corridor.git assets`（`assets/` 已 gitignore）。
目录：`sounds/`（按场景分子目录，如 `door/`、`paranoia/`）、`tiles/`（含 `@2x`）、
`design/`（FL Studio 工程与导出）。授权见该仓库 `LICENSE`
（木兰开放作品 BY-PL v1；`sounds/music/suno_ai/` 例外）。

## 授权与合规（硬口径，勿自行推断）

| 对象 | 授权 | 能否商用 |
|---|---|---|
| 引擎代码（本仓库） | 木兰 PSL v2，见根目录 `LICENSE` | 可以，许可证不禁止 |
| 素材（独立资产仓） | 木兰 OWL BY-PL v1，须署名 | 可以，须保留署名 |
| `assets/audio/music/suno_ai/` | Suno 免费计划条款 | **不可以**，仅个人非商业 |
| 角色/名称/贴图等第三方 IP、版号备案 | 本仓库不授予、不代办 | 需使用方自行取得 |
| 上游组件（渲染库 MIT、raylib/nanosvg zlib、玄铁工具链） | 各自许可，**不是本仓库作者的版权** | 按各自许可，见 `THIRD_PARTY_NOTICES.md` |

- 作者不收费 ≠ 许可证禁止下游收费：木兰 PSL v2 允许商用与收费。
- **责任边界**：作者只对引擎代码负责；素材是顺手提供的便利（另一份许可，可整体删除）；
  社区里「发网盘、无版号、大量同人」是观察到的事实，不是授权也不是背书。
  **作者不是第三方 IP 的权利人、不是监管、不是法院**：无权授权、无权认定合法、
  无法保证不被查处，只能提示后果自负。同人侵权与版号监管超出本仓库范围，不代办不兜底。
- 完整问答与固定表述见 `docs/授权与合规问答.md`；**涉及授权的回答一律以该文件为准**，
  不许把引擎说成 MIT/Apache/GPL，不许把 Suno 示例音乐当可商用素材，
  不许拿「社区都这么传」「没人管」当授权依据，不许对侵权/版号出具「没问题」的结论。

## 剧情与代码的分工（硬约束，勿违反）

- **剧情一律放 `剧情/幕NN.json`，`.xt` 只承载引擎与渲染。**
  理由：源码可外流（别人可能只传二进制和配置），源码里不该躺着剧情；
  引擎通用、剧情可换。新增/改剧情只动 JSON，不动 `.xt`。
- 节点类型由 JSON 的 `类型` 驱动：必经 / 谜题 / 绕过 / 分支 / 结局。
  引擎按类型分流，不为某一幕写特例。


- **写或改剧情前，先读 `文字剧情/README.md` 的「失败与重试」「写法约定」
  「场景转换的感官提示」三节**：
  危险/谜题前必须有看得见的场景提示、可交互物必须显眼、失败惩罚别落在重走路程上；
  跨场景节点（进地下室之类）要不要加气味/温度提示**先问人**，引擎不内置这类文案。
  这几条是交给写剧情的 Agent 的硬口径，不是建议。
- 每个解谜节点必须同时有 `对` 与 `错`（绕过节点），且 `错` 不能造成死局——
  玩家卡住时按 Q 或错满自动走绕过。
- 谜题答案为字符串，格式差异用 `可接受` 数组收（`7` 与 `07` 都算）；
  玩家输入只接受数字（汉字退格删不满一个字宽，实测出过问题）。

## 目录结构

- `主函数.xt` — 入口（最小垂直切片：窗口+移动+地砖+暗角+手电筒光照）
- `文字剧情/` — TUI 剧情播放器（`README.md` 是字段表与音频/打字机写法）、
  `校验剧情.py`、`生成音效.py`（FM→WAV）、`音效表.json`
- `scripts/` — `build-macos.rvs`、`test-macos.rvs`、`xtc-抓IR.sh`、
  `bash/run-check.sh`（各自用途见「构建与测试」）
- `tests/` — 浮点内存探针与阈值脚本（手动跑，无 CI）
- `docs/` — 缺陷记录、数值语义、渲染字体细则
- `patches/渲染桥.c.macos` — 渲染库 macOS 桥接，**同步自工具链内置**
  `xtc-package/lib/渲染/渲染桥.c`：上游已把 macOS 适配并入内置桥，旧版补丁
  缺 `XT_Translate3D`/`合成器` 等符号会链接失败
- `tiepm_modules/渲染/`、`.tiepm/` — 依赖与符号链接（均 gitignore，构建脚本重建）
