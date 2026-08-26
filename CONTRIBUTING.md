# 开发、提交与发版

## 开发环境

要求 Apple 芯片 Mac、macOS 13+、Python 3.12 和 Xcode Command Line Tools。

```bash
git clone git@gitlab.alibaba-inc.com:wjc439800/voice_input.git
cd voice_input
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
./build-native-settings.command
python main.py
```

`.env` 只能放本人的测试凭证，绝不能提交。配置细节见 [docs/快速开始与API配置.md](./docs/快速开始与API配置.md)。

## 修改与验证

```bash
python -m compileall -q main.py src settings_ui.py
python -m unittest discover -s test -p 'test_*.py' -q
```

- Python 逻辑：修改 `main.py` 或 `src/`。
- 原生设置：修改 `native_settings/VoiceInputSettings.swift` 后运行 `./build-native-settings.command`。
- 快捷键与写入：修改后必须在至少 TextEdit、浏览器输入框和聊天输入框中人工验证短按、长按、Esc 取消、切窗和连续两段。
- ASR：需要比较引擎时用 `python tools/compare_asr_once.py --duration 12`；同一份音频按顺序发送给两端，音频不写盘。

## Codeup 分支与评审

不要直接在 `main` 上开发：

```bash
git switch -c feature/short-description
git add <明确的文件>
git commit -m "feat: describe the change"
git push -u origin feature/short-description
```

随后在 Codeup 创建代码评审，说明用户问题、修改范围、测试证据、隐私影响和回滚方式。不要使用 `git add .` 代替检查；提交前先看 `git status --short` 和 `git diff --cached`。

## 版本与安装包

1. 更新版本号与 `版本说明-vX.Y.Z.md`。
2. 运行全部自动测试。
3. 运行 `./build-internal-dmg.command`，生成 App、DMG、PKG、ZIP 与 SHA-256。
4. 在一台未装源码版的 Mac 上执行冒烟测试。
5. 安装包不要直接提交进 Git 历史；建议作为 Codeup 版本/制品附件发布，并附 SHA-256。

内测包为 ad-hoc 签名：每次构建都会改变 CDHash。用户覆盖升级后若快捷键失效，需要从“系统设置 → 隐私与安全性 → 辅助功能/输入监控”删除旧条目，重新加入当前 `/Applications/Veyqa Voice.app` 并重启。

## 源码包

```bash
./package-source.command
```

脚本会排除并审计凭证、本机纠错、恢复、日志、录音和虚拟环境。生成后仍应检查清单与哈希，再对外发送。
