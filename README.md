# VoxType

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

下载最新版 [VoxType-vX.Y.Z-macOS-arm64-internal.dmg](https://github.com/wjc-dev/voxtype/releases),把 VoxType 拖到应用程序。首次启动按系统提示授权麦克风和辅助功能。

需要 macOS 13+ 和 Apple Silicon。

## 配置

1. 打开 VoxType,在设置里选择引擎(千问或豆包),填入自己的 API 凭证。
2. 默认快捷键是右 Option。企业管控的机器可以换成 `⌃⌥Space`。
3. 保存并重启。把光标放进任何输入框,按住快捷键说话,松开提交。

## 从源码运行

```bash
git clone https://github.com/wjc-dev/voxtype.git
cd voxtype
uv venv --python 3.13 .venv
uv pip install -r requirements.txt
cp env.example .env          # 填入你的千问或豆包 API 凭证
.venv/bin/python main.py
```

需要 macOS 13+、Apple Silicon、Xcode Command Line Tools、Python 3.13。

## 构建 .dmg / .pkg

```bash
zsh ./build-internal-dmg.command
```

产物在 `dist-internal/`。

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

欢迎 Issue 和 PR。详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。所有 PR 需通过 `pytest test/`。

## 安全

报告安全漏洞请看 [SECURITY.md](./SECURITY.md)。

## 许可证

[MIT](./LICENSE)。基于 [ErlichLiu/Whisper-Input](https://github.com/ErlichLiu) 和 [Mor-Li/Whisper-Input-Next](https://github.com/Mor-Li) 衍生,保留原始版权声明。
