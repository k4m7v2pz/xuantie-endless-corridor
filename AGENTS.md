# AGENTS.md — xuantie-endless-corridor 项目约定

## 项目定位

「无尽回廊」是一款恐怖 RPG（对标 RPG Maker XP/MV/MZ 系的喜羊羊恐怖改版一类：
黑暗走廊、有限光照、压抑氛围）。本项目是**用玄铁 (XuanTie) 中文编程语言
+ 官方「渲染」库（raylib 桥接）实现的尝试性重构**：

- 最终实现语言：玄铁（本项目）；
- 功能参考：`rust-bevy-endless-corridor`（Rust Bevy 版，只读参考）；
- 入门参考：`xuantie-life-game`（玄铁 + 渲染库的已验证范本，构建流程照搬自它）；
- 工具链：`xtl-toolchain`（玄铁 CLI，类 uv/cargo）。

⚠️ **项目定性**：玄铁语言当前为 1.0-rc（红色预发布徽章、单人开发、官方定位
"游戏引擎让给 Unity/Godot"）。本项目是**尝试性垂直验证**，不是稳定产品。
先跑通最小切片，再逐步扩充。

## 构建与测试（macOS arm64）

```bash
cd /Users/user2/Documents/Code.localized/xuantie-endless-corridor
rvs scripts/build-macos.rvs     # 一键构建，产物 ./corridor
rvs scripts/test-macos.rvs      # 构建 + 短时运行验证（4 秒自动关闭）
```

- 渲染程序 xtc tie 链接阶段必失败（渲染包 raylib 是 Windows 构建，预期）；
  由 `scripts/xtc-抓IR.sh` 轮询截获 LLVM IR，再 clang 手动链接
  （运行时 C + 渲染桥 + macOS raylib + frameworks）。
- 测试脚本的短时运行验证在 `scripts/bash/run-check.sh`：SIGKILL 清理旧实例、
  单窗口运行 4 秒、强制关闭、结果写入 `/tmp/xtl-test.state`（ALIVE/CRASHED/NO_BINARY）。

## ⚠️ 玄铁 1.0-rc 已知坑（实测，勿重踩）

1. **可执行产物名冲突崩溃**：若链接产物名与源码文本中的字样重名
   （如"主函数"是入口文件名、"无尽回廊"出现在注释/标题），启动即崩
   （Trace/BPT trap: 5，崩溃点 glfwInit → _glfwInitCocoa → CFBundle 断言）。
   **规避：产物统一命名 `corridor`**（源码入口仍为 `主函数.xt`，xtl.json 不变）。
   验证样本：`主函数`/`主函数b`/`无尽回廊` 作产物名均崩；
   `corridor`/`改名测试`/`test-main` 均正常。
2. 把 macOS raylib 替换进 xtc-package/lib/渲染/ 让 xtc 原生链接"成功"是死路
   （产物必崩），已还原；构建一律走 IR 截获 + clang 手动链接。
3. 本机工具链路径（实测可用）：
   - xtc：`~/Library/Caches/xtl/core/darwin-arm64/xtc-package/xtc`
   - 运行时 C：`~/Library/Caches/xtl/core/darwin-arm64/xtc-package/runtime/`
   - macOS raylib 6.0：`~/Library/Caches/xtl/raylib/darwin-arm64/libraylib.a`
   - 玄铁临时 Cache（IR 截获轮询目录）：
     `/var/folders/4x/.../T/XuanTie/Cache`

## 提交规范（简体中文 + Co-Authored-By）

- 提交信息用 Conventional Commits（`feat:` / `fix:` / `docs:` / `refactor:` 等），
  **主题用简体中文描述**；末尾 trailer（空行隔开）用 `Co-Authored-By`，
  名字填写**实际调用工具、执行本次提交的模型/Agent**（不是写代码的模型，
  二者可能不同）；`noreply@` 域名无对应则不写域名只留名字。
  格式示例：`Co-Authored-By: <实际提交的Agent名> <noreply@<对应域名>>`。

### Agent 自动提交推送约定（本仓库工作方式）

- 本项目的开发流程中，**AI agent 负责编码、提交、推送**（dev 分支），
  在人类视角上表现为"agent 自动提交推送"。
- Agent 完成一个可验证的改动单元后**自动提交并推送**到 `dev` 分支，
  无需逐次征求人类确认；提交信息遵守上方规范（简体中文 + Co-Authored-By）。
- 涉及公开仓库的**外发动作**（PR / issue / 追评）仍需如实标注
  人类参与程度，禁止声称"人类已批准/已审阅"未经批准的内容。

### 提交前防泄漏守卫（公开仓库，硬约束）

本仓库公开，进入 git 的内容默认互联网可见。**禁止提交**：
私钥/token/密码、个人邮箱、真实姓名、私人服务器地址、代理端口、
内部 IP、SSH 口令、VPS/VM 连接信息。

- 文档里举例远端/邮箱/端口一律用占位符：`<example@example.com>`、
  `<proxy-port>`、`<host>`。
- **提交前核对流程（不得跳过）**：
  1. `git add` 后先 `git diff --cached --name-only` 确认暂存区文件清单，
     无 `secrets/`、`*.pem`、`id_rsa`、`id_ed25519`、`*.key`、`credentials` 等；
  2. `git diff --cached` 扫内容，发现真实 IP / 端口 / 邮箱 / token →
     `git restore --staged <file>` 摘出，替换为占位符或删除后重新 `git add`；
  3. 确认无泄漏再 `git commit`。

## 目录结构

- `主函数.xt` — 入口（最小垂直切片：窗口+移动+地砖+暗角+手电筒光照）
- `scripts/build-macos.rvs` — macOS 一键构建（rvs 主脚本）
- `scripts/test-macos.rvs` — macOS 构建 + 短时运行验证
- `scripts/xtc-抓IR.sh` — xtc 链接失败时轮询截获 LLVM IR 的 helper
- `scripts/bash/run-check.sh` — 短时运行验证 helper（SIGKILL 清理）
- `patches/渲染桥.c.macos` — 渲染库 macOS 桥接补丁（复制自 xuantie-life-game）
- `tiepm_modules/渲染/` — 渲染库依赖（已打补丁；gitignore）
- `.tiepm/` — 布局桥接符号链接（gitignore，clone 后由构建脚本重建）
