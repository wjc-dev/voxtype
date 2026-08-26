# Veyqa Voice

[English](./README.en.md) · 简体中文

macOS 上的语音速记工具。按住快捷键说话,松开,文字落到光标处。

不替换你的系统输入法。拼音、双拼、五笔继续用;需要语音的时候按住一个键就行。

## 为什么用它

- 喜欢搜狗 / 双拼 / Rime,但偶尔想用语音 → 不用为了语音能力换走你常用的输入法
- 千问 Audio 3.0 和豆包 Seed ASR 2.0 都能用,自带 API 凭证即可
- 按住说话、松开提交,没有 marked text 下划线,不打扰写作流
- 浮窗稳定在屏幕底部居中,不抢焦点
- 菜单栏常驻,SwiftUI 原生设置面板
- 不上传录音(默认关闭本地存档),日志不记识别内容
- MIT 协议,基于 ErlichLiu 的 Whisper-Input 衍生

## 安装

下载最新版 Veyqa Voice 安装包，把 Veyqa Voice 拖到应用程序。首次启动按系统提示授权麦克风和辅助功能。

需要 macOS 13+ 和 Apple Silicon。

## 配置

1. 打开 Veyqa Voice，在设置里选择引擎（千问或豆包），填入自己的 API 凭证。
2. 默认快捷键是 `⌃⌥Space`：由 macOS 注册，不需要“输入监控”权限，也能明确提示是否被其他 App 占用。设置页也可以直接录入其他“修饰键 + 普通键”组合。
3. 保存并重启。把光标放进任何输入框,按住快捷键说话,松开提交。

右/左 Option、Command、Control 或 Fn 也可以单独使用，但这类“单修饰键”必须通过只读键盘监听实现，需要“输入监控”权限，也更容易和系统、远程桌面、Karabiner 或企业安全软件冲突。若追求通用稳定，优先使用组合键。

## 后台运行与故障恢复

- 打包版使用 macOS 13+ 的 Service Management 注册一个轻量 supervisor。Veyqa Voice 意外消失时会恢复；若 60 秒内连续失败 3 次，会冷却 5 分钟，避免反复崩溃拉起。
- 快捷键监听被 macOS 暂停时会自动恢复；不允许 Quartz 只读监听的受管控电脑会降级到 AppKit 兼容模式。
- 菜单栏图标使用固定方形模板图标，并定时检查状态项。macOS 在菜单栏空间不足时仍可能临时隐藏任意第三方图标；这时从“应用程序”或 Spotlight 再打开 Veyqa Voice，会唤起同一个设置窗口，不会再启动一套服务。
- “恢复与诊断”页会显示后台启动、权限、快捷键后端和最近一次运行结果。升级自 Voice Input 时，如旧进程仍在运行，会明确提示先退出旧版，避免双快捷键监听。

正式对外分发仍应使用稳定的 Developer ID 对 App/PKG 签名并完成 Apple 公证。仓库生成的 `internal` 产物是 ad-hoc 签名测试包，不应直接当作面向所有用户的正式发布包。

## 从源码运行

```bash
git clone https://github.com/wjc-dev/voxtype.git
cd voxtype
uv venv --python 3.13 .venv
uv pip install -r requirements-dev.txt
cp env.example .env          # 填入你的千问或豆包 API 凭证
.venv/bin/python main.py
```

需要 macOS 13+、Apple Silicon、Xcode Command Line Tools、Python 3.13。

## 构建 .dmg / .pkg

```bash
zsh ./build-internal-dmg.command
```

产物在 `dist-internal/`。

提交候选版本前，可运行下面的隔离验收。它会执行完整测试、重新构建、检查签名与版本，并启动临时副本验证菜单栏和设置窗口；不会安装 App，也不会注册登录项。

```bash
zsh ./tools/verify-release-candidate.command
```

## 项目结构

```
main.py            主程序
settings_ui.py     设置面板
src/
  audio/           麦克风采集
  transcription/   千问 + 豆包引擎
  keyboard/        全局快捷键、文本插入
  ui/              状态栏、浮窗
native_settings/   SwiftUI 原生设置 helper
packaging/         PyInstaller spec、图标
test/              单元测试
```

## 贡献

欢迎 Issue 和 PR。详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。所有 PR 需通过 `.venv/bin/python -m pytest test/`。

## 安全

报告安全漏洞请看 [SECURITY.md](./SECURITY.md)。

## 许可证

[MIT](./LICENSE)。基于 [ErlichLiu/Whisper-Input](https://github.com/ErlichLiu) 和 [Mor-Li/Whisper-Input-Next](https://github.com/Mor-Li) 衍生,保留原始版权声明。
