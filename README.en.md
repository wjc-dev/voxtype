# VoxType

English · [简体中文](./README.md)

Push-to-talk voice dictation for macOS. Hold a hotkey, speak, release — text lands at the caret.

It does not replace your system input method. Pinyin, Wubi, or Rime keep working; voice is one keystroke away when you need it.

## Why

- Love Sogou / Rime / Wubi but occasionally want voice — don't switch IMEs just to get dictation
- Bring your own credentials for Qwen Audio 3.0 ASR or Doubao Seed ASR 2.0
- Hold to talk, release to commit. No marked-text underline, no flow disruption
- Floating preview anchored at the bottom-center, never steals focus
- Menu-bar resident, native SwiftUI settings
- Recordings are not uploaded (local archive is off by default); logs do not capture recognized content
- MIT licensed, derived from ErlichLiu's Whisper-Input

## Install

Grab the latest [VoxType-vX.Y.Z-macOS-arm64-internal.dmg](https://github.com/wjc-dev/voxtype/releases), drag VoxType to Applications. On first launch grant Microphone and Accessibility permissions as prompted.

Requires macOS 13+ on Apple Silicon.

## Configure

1. Open VoxType, pick an engine (Qwen or Doubao), enter your API credentials.
2. Default hotkey is Right Option. On tightly managed Macs, switch to `⌃⌥Space`.
3. Save and restart. Focus any input field, hold the hotkey, speak, release.

## Run from source

```bash
git clone https://github.com/wjc-dev/voxtype.git
cd voxtype
uv venv --python 3.13 .venv
uv pip install -r requirements.txt
cp env.example .env          # fill in your Qwen or Doubao credentials
.venv/bin/python main.py
```

Requires macOS 13+, Apple Silicon, Xcode Command Line Tools, Python 3.13.

## Build .dmg / .pkg

```bash
zsh ./build-internal-dmg.command
```

Output in `dist-internal/`.

## Project layout

```
main.py            Entry point
settings_ui.py     Settings panel
src/
  audio/           Microphone capture
  transcription/   Qwen + Doubao engines
  keyboard/        Global hotkeys, text insertion
  ui/              Status bar, floating preview
native_settings/   SwiftUI native settings helper
packaging/         PyInstaller spec, icons
test/              Unit tests
```

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md). PRs must pass `pytest test/`.

## Security

Report vulnerabilities per [SECURITY.md](./SECURITY.md).

## License

[MIT](./LICENSE). Derived from [ErlichLiu/Whisper-Input](https://github.com/ErlichLiu) and [Mor-Li/Whisper-Input-Next](https://github.com/Mor-Li); original copyright notices preserved.
