# VoxType 0.2.0 候选版验证记录

日期：2026-08-25
范围：macOS 13+、Apple Silicon、菜单栏常驻版内部候选包

## 本轮目标

把原 Voice Input / VoxType 从容易丢失菜单栏、快捷键配置受限、监听偶发失效、后台退出后不恢复的状态，改造成可配置、可诊断、可恢复的 macOS 菜单栏应用，同时保持千问/豆包和最终文本只提交一次的既有行为。

## 已实现

- 默认快捷键改为 macOS 注册型 `⌃⌥Space`，无需输入监控权限，并能明确报告快捷键冲突。
- 设置页可录制任意“修饰键 + 普通键”组合；同时保留左右 Option、Command、Control 和 Fn 单修饰键预设。
- 修复组合键录制被第一个修饰键抢先完成的问题：单修饰键在松开时确认，多个修饰键会继续等待普通键。
- 快捷键配置会校验键码、重复修饰键和未知修饰键；无效配置回退到 `⌃⌥Space`。
- 组合键强制使用 registered 后端，单修饰键强制使用 passive 后端，用户明确选择 off 时保持关闭。
- Quartz 只读监听被系统停用时自动恢复，失败时降级到 AppKit 全局监听。
- 打包版使用 `SMAppService` 注册轻量 supervisor。supervisor 按 bundle ID 检测主程序，意外退出后重启；60 秒三次失败后冷却 5 分钟。
- 用户主动“退出 VoxType”会写入暂停标记，supervisor 不会立即重新拉起；从 Finder 或 Spotlight 手动打开会恢复后台守护。
- `--background-login` 不会自动弹出设置页；保存或权限重启会重新打开设置并刷新当前 PID 的授权状态。
- 现代登录项启用后才迁移已知旧 LaunchAgent；不会删除旧 App、配置或用户数据。
- 菜单栏状态项使用保留引用的固定方形模板图标，每 3 秒自检；Finder/Spotlight 重开会唤起已有设置窗口。
- 修复设置 helper 启动握手竞态：快速连续打开不再因过早收到 `SIGUSR1` 而以 `-30` 退出。
- 权限页不再把用户困在灰色“继续”按钮前：提供“关闭设置窗口”和“重启并重新检查”，主程序已经退出时会明确指引重新打开 VoxType。
- 删除“企业兼容”“企业电脑推荐”等产品标签，按实现方式显示“系统注册组合键”或“只读键盘监听”。
- 将原来位于 Frameworks 中的裸 `VoiceInputSettings.appbin` 改成完整签名的嵌套 `Contents/Helpers/VoxTypeSettings.app`。旧结构曾在 AppKit 初始化的 `CFBundleCopyExecutableURL` 中产生 `EXC_BAD_ACCESS / SIGSEGV`，是设置窗口偶发消失的直接证据。
- 设置日志限制为 512 KiB 并滚动一次，日志写入失败不会终止常驻进程。
- 版本统一升级为 0.2.0；加入开发依赖清单和可重复的一键候选版验收脚本。

## 自动与隔离验证结果

执行：

```bash
zsh ./tools/verify-release-candidate.command
```

结果：通过。

- 单元测试：166 passed。
- Swift 设置核心：实际编码并保存 `⌃⌥Space` 与 `⌘⇧K` 两套组合键，拒绝空、未知、重复和越界配置，保存后的 `.env` 权限保持 0600。
- Swift 设置程序与 supervisor：编译通过。
- 主 App 与嵌套设置 App：Apple Silicon arm64，版本 0.2.0，深度 codesign 校验通过（内部 ad-hoc 签名）。
- LaunchAgent plist：`plutil` 校验通过。
- 隔离运行：主进程保持存活，菜单栏状态项创建成功，设置 helper 创建并复用成功。
- 快捷键线程：最终 0.2.0 冻结包确认 registered 后端注册成功，没有快捷键注册错误。
- 设置竞态：没有 `status=-30`、Traceback 或 CRITICAL。
- 设置 App 启动压力：源码 bundle 连续 10 次、最终 ZIP 中的嵌套 bundle 连续 5 次启动并完成单实例握手，没有新增崩溃报告。
- 内部 ad-hoc ZIP 第一次从全新路径启动设置 App 时曾在 `dyld_start` 等待约 8.3 秒，随后正常就绪；验收允许 20 秒冷启动。正式 Developer ID 签名和公证仍是公开分发前置条件。
- 外部状态：验证过程使用临时数据目录并设置 `VOICE_INPUT_DISABLE_LOGIN_SYNC=true`，未安装 App，未注册登录项，未修改 TCC、当前 `.env` 或旧 Voice Input。
- 最终冻结包全局事件验证：依次用隔离 `.env` 启动 `⌃⌥Space`、`⌃⇧K` 两套配置，Carbon 均注册成功；真实 CGEvent 按下/释放均产生一次开始和一次停止。F1–F12 仍受 macOS“功能键/媒体键”设置影响，不承诺在所有键盘上无需 Fn 即可触发。
- 临时权限窗回归：空凭证快捷键测试会正常打开设置页；验收等待每个设置 helper 完成单实例握手，再按“主程序 → 设置 helper”顺序终止，并以零残留为硬门禁。验证过程未修改现有 `/Applications/VoxType.app` 或保留的 `/Applications/Voice Input.app`。

最终内部产物：

- `VoxType-v0.2.0-macOS-arm64-internal.pkg`
  SHA-256 `8154379a2a3a7381e2368a4797abddbb56c1ccc61425f00beb4fddcb005c8fc5`
- `VoxType-v0.2.0-macOS-arm64-internal.zip`
  SHA-256 `c1a27718e20c22645a386bb7d6107aa1c63d9f44d7312e4b972bc2d6e5f0e6c6`
- `VoxType-v0.2.0-macOS-arm64-internal.dmg`
  SHA-256 `031a2544170fb5840c5fdd42308b6520c515c8a40c593bc7a8ef09ecfad0cd28`

## 仍需真实安装授权的验收

以下检查会影响 `/Applications`、后台项目或 macOS 隐私权限，因此未自动执行；完成前不能把本 Goal 判定为全部完成。

1. 正常退出当前 `/Applications/Voice Input.app`，安装 0.2.0 到 `/Applications/VoxType.app`。
2. 按 macOS 提示批准后台项目、麦克风和辅助功能；如果使用单修饰键，再批准输入监控。
3. 确认设置诊断页显示登录项 `enabled`，菜单栏图标可点击且重复从 Spotlight 打开只复用一个设置窗口。
4. 在 TextEdit、浏览器和常用聊天工具中分别验证 `⌃⌥Space` 按住/松开，确认每轮文本只落一次；再录制一个自定义组合键并复测。
5. 非主动退出地终止主进程，确认 supervisor 在合理时间内恢复；随后从菜单选择“退出 VoxType”，确认它保持退出，手动打开后才恢复。
6. 注销再登录或重启一次，确认 VoxType 自动出现、菜单栏图标存在、快捷键仍可用。
7. 连续后台运行至少 2 小时并进行 30 轮录音；候选用户测试建议延长到 24 小时，收集诊断页和脱敏日志。
8. 对外发布前改用稳定的 Developer ID Application / Installer 签名并完成 Apple 公证；当前 internal 包不应直接公开分发。
